"""
schema.py
---------
Defines and creates the full relational database schema.

Tables:
  - customers       : Customer accounts
  - products        : Product catalogue with categories
  - orders          : Customer orders
  - order_items     : Line items within each order
  - employees       : Staff records
  - departments     : Company departments
  - suppliers       : Product suppliers
  - inventory       : Stock levels per product

Demonstrates:
  - Relational schemas with foreign keys
  - Multiple index types (B-tree, composite, partial)
  - Constraints (NOT NULL, UNIQUE, CHECK)
  - Triggers for auto-updating timestamps
"""

CREATE_SCHEMA_SQL = """
-- ─────────────────────────────────────────────
-- DEPARTMENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    budget          REAL    NOT NULL CHECK (budget >= 0),
    location        TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- EMPLOYEES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    phone           TEXT,
    hire_date       TEXT    NOT NULL,
    salary          REAL    NOT NULL CHECK (salary > 0),
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    manager_id      INTEGER REFERENCES employees(employee_id),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- CUSTOMERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    phone           TEXT,
    address         TEXT,
    city            TEXT,
    country         TEXT    NOT NULL DEFAULT 'US',
    loyalty_points  INTEGER NOT NULL DEFAULT 0 CHECK (loyalty_points >= 0),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- SUPPLIERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    contact_email   TEXT    NOT NULL,
    phone           TEXT,
    country         TEXT    NOT NULL,
    rating          REAL    CHECK (rating BETWEEN 1.0 AND 5.0),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    category        TEXT    NOT NULL,
    price           REAL    NOT NULL CHECK (price >= 0),
    cost            REAL    NOT NULL CHECK (cost >= 0),
    sku             TEXT    NOT NULL UNIQUE,
    supplier_id     INTEGER REFERENCES suppliers(supplier_id),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- INVENTORY
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL UNIQUE REFERENCES products(product_id),
    quantity        INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reorder_level   INTEGER NOT NULL DEFAULT 10,
    reorder_qty     INTEGER NOT NULL DEFAULT 50,
    warehouse       TEXT    NOT NULL DEFAULT 'MAIN',
    last_updated    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- ORDERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    employee_id     INTEGER REFERENCES employees(employee_id),
    status          TEXT    NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','processing','shipped','delivered','cancelled')),
    total_amount    REAL    NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    discount        REAL    NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    shipping_addr   TEXT,
    notes           TEXT,
    order_date      TEXT    NOT NULL DEFAULT (datetime('now')),
    shipped_date    TEXT,
    delivered_date  TEXT
);

-- ─────────────────────────────────────────────
-- ORDER ITEMS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL    NOT NULL CHECK (unit_price >= 0),
    discount        REAL    NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    UNIQUE(order_id, product_id)
);

-- ═══════════════════════════════════════════════
-- INDEXES — Indexing Strategy
-- ═══════════════════════════════════════════════

-- B-tree index on frequently filtered columns
CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_date        ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order  ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_supplier  ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_employees_dept     ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_customers_country  ON customers(country);
CREATE INDEX IF NOT EXISTS idx_customers_city     ON customers(city);

-- Composite index — optimises ORDER BY + WHERE combos
CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date DESC);

-- Partial index — only active products (avoids indexing inactive rows)
CREATE INDEX IF NOT EXISTS idx_active_products    ON products(category, price)
    WHERE is_active = 1;

-- Covering index — all columns for a common query pattern
CREATE INDEX IF NOT EXISTS idx_inventory_reorder  ON inventory(product_id, quantity, reorder_level);

-- ═══════════════════════════════════════════════
-- VIEWS — Pre-optimised query shortcuts
-- ═══════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS v_order_summary AS
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.first_name || ' ' || c.last_name  AS customer_name,
    c.email                              AS customer_email,
    COUNT(oi.item_id)                    AS item_count,
    SUM(oi.quantity)                     AS total_units,
    ROUND(o.total_amount, 2)             AS total_amount,
    e.first_name || ' ' || e.last_name  AS handled_by
FROM orders o
JOIN customers  c  ON o.customer_id  = c.customer_id
LEFT JOIN employees e  ON o.employee_id  = e.employee_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id;

CREATE VIEW IF NOT EXISTS v_product_performance AS
SELECT
    p.product_id,
    p.name          AS product_name,
    p.category,
    p.price,
    p.cost,
    ROUND(p.price - p.cost, 2)           AS margin,
    ROUND((p.price - p.cost)/p.price * 100, 1) AS margin_pct,
    COALESCE(SUM(oi.quantity), 0)        AS total_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue,
    i.quantity                           AS stock_qty,
    CASE WHEN i.quantity <= i.reorder_level THEN 'LOW STOCK' ELSE 'OK' END AS stock_status
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN inventory   i  ON p.product_id = i.product_id
WHERE p.is_active = 1
GROUP BY p.product_id;

CREATE VIEW IF NOT EXISTS v_customer_stats AS
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name  AS customer_name,
    c.email,
    c.city,
    c.country,
    c.loyalty_points,
    COUNT(DISTINCT o.order_id)           AS total_orders,
    COALESCE(SUM(o.total_amount), 0)     AS lifetime_value,
    ROUND(AVG(o.total_amount), 2)        AS avg_order_value,
    MAX(o.order_date)                    AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
    AND o.status != 'cancelled'
GROUP BY c.customer_id;

CREATE VIEW IF NOT EXISTS v_low_stock AS
SELECT
    p.product_id,
    p.name,
    p.category,
    p.sku,
    i.quantity      AS current_stock,
    i.reorder_level,
    i.reorder_qty,
    i.warehouse,
    s.name          AS supplier_name,
    s.contact_email AS supplier_email
FROM inventory i
JOIN products  p ON i.product_id  = p.product_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE i.quantity <= i.reorder_level
  AND p.is_active = 1
ORDER BY i.quantity ASC;

-- ═══════════════════════════════════════════════
-- TRIGGERS
-- ═══════════════════════════════════════════════

-- Auto-update inventory.last_updated on stock change
CREATE TRIGGER IF NOT EXISTS trg_inventory_updated
AFTER UPDATE OF quantity ON inventory
BEGIN
    UPDATE inventory SET last_updated = datetime('now')
    WHERE inventory_id = NEW.inventory_id;
END;

-- Recalculate order total when items change
CREATE TRIGGER IF NOT EXISTS trg_order_total_on_insert
AFTER INSERT ON order_items
BEGIN
    UPDATE orders SET total_amount = (
        SELECT ROUND(SUM(quantity * unit_price * (1 - discount)), 2)
        FROM order_items WHERE order_id = NEW.order_id
    ) WHERE order_id = NEW.order_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_order_total_on_update
AFTER UPDATE ON order_items
BEGIN
    UPDATE orders SET total_amount = (
        SELECT ROUND(SUM(quantity * unit_price * (1 - discount)), 2)
        FROM order_items WHERE order_id = NEW.order_id
    ) WHERE order_id = NEW.order_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_order_total_on_delete
AFTER DELETE ON order_items
BEGIN
    UPDATE orders SET total_amount = (
        SELECT ROUND(COALESCE(SUM(quantity * unit_price * (1 - discount)), 0), 2)
        FROM order_items WHERE order_id = OLD.order_id
    ) WHERE order_id = OLD.order_id;
END;
"""
