"""
queries.py
----------
Collection of optimised SQL queries demonstrating:
  - JOINs (INNER, LEFT, self-join)
  - Subqueries and CTEs (WITH clause)
  - Window functions (RANK, ROW_NUMBER, LAG)
  - Aggregations (GROUP BY, HAVING)
  - Query optimisation techniques
"""

# ── BASIC QUERIES ──────────────────────────────────────────────────────────────

Q_ALL_CUSTOMERS = """
SELECT customer_id, first_name || ' ' || last_name AS name,
       email, city, country, loyalty_points
FROM customers
ORDER BY last_name, first_name;
"""

Q_ACTIVE_PRODUCTS = """
SELECT product_id, name, category, price, cost,
       ROUND(price - cost, 2) AS margin
FROM products
WHERE is_active = 1
ORDER BY category, price DESC;
"""

Q_LOW_STOCK = """
SELECT * FROM v_low_stock;
"""

# ── INTERMEDIATE — JOINs ───────────────────────────────────────────────────────

Q_ORDER_DETAILS = """
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.first_name || ' ' || c.last_name  AS customer,
    c.email,
    p.name                               AS product,
    p.category,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    ROUND(oi.quantity * oi.unit_price * (1 - oi.discount), 2) AS line_total
FROM orders o
JOIN customers   c  ON o.customer_id  = c.customer_id
JOIN order_items oi ON o.order_id     = oi.order_id
JOIN products    p  ON oi.product_id  = p.product_id
ORDER BY o.order_date DESC, o.order_id, p.name;
"""

Q_EMPLOYEE_HIERARCHY = """
SELECT
    e.employee_id,
    e.first_name || ' ' || e.last_name    AS employee,
    e.salary,
    d.name                                 AS department,
    m.first_name || ' ' || m.last_name    AS manager
FROM employees e
JOIN departments d ON e.department_id = d.department_id
LEFT JOIN employees m ON e.manager_id = m.employee_id
ORDER BY d.name, e.last_name;
"""

# ── ADVANCED — Aggregations & HAVING ──────────────────────────────────────────

Q_REVENUE_BY_CATEGORY = """
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)              AS orders,
    SUM(oi.quantity)                         AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue,
    ROUND(AVG(oi.unit_price), 2)             AS avg_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status != 'cancelled'
GROUP BY p.category
HAVING revenue > 0
ORDER BY revenue DESC;
"""

Q_TOP_CUSTOMERS = """
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer,
    c.city,
    c.country,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    ROUND(SUM(o.total_amount), 2)       AS lifetime_value,
    ROUND(AVG(o.total_amount), 2)       AS avg_order_value,
    c.loyalty_points
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status != 'cancelled'
GROUP BY c.customer_id
HAVING total_orders >= 2
ORDER BY lifetime_value DESC
LIMIT 20;
"""

Q_MONTHLY_REVENUE = """
SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(order_id)               AS orders,
    ROUND(SUM(total_amount), 2)   AS revenue,
    ROUND(AVG(total_amount), 2)   AS avg_order
FROM orders
WHERE status != 'cancelled'
GROUP BY month
ORDER BY month DESC;
"""

Q_DEPT_SALARY_STATS = """
SELECT
    d.name                          AS department,
    COUNT(e.employee_id)            AS headcount,
    ROUND(MIN(e.salary), 2)         AS min_salary,
    ROUND(MAX(e.salary), 2)         AS max_salary,
    ROUND(AVG(e.salary), 2)         AS avg_salary,
    ROUND(SUM(e.salary), 2)         AS total_payroll,
    ROUND(d.budget, 2)              AS dept_budget,
    ROUND(SUM(e.salary)/d.budget*100, 1) AS payroll_pct_budget
FROM employees e
JOIN departments d ON e.department_id = d.department_id
GROUP BY d.department_id
ORDER BY total_payroll DESC;
"""

# ── ADVANCED — CTEs (Common Table Expressions) ────────────────────────────────

Q_CTE_CUSTOMER_SEGMENTS = """
WITH customer_spending AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer,
        c.country,
        COALESCE(SUM(o.total_amount), 0)    AS total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
        AND o.status != 'cancelled'
    GROUP BY c.customer_id
),
segmented AS (
    SELECT *,
        CASE
            WHEN total_spent >= 1000 THEN 'VIP'
            WHEN total_spent >= 500  THEN 'Gold'
            WHEN total_spent >= 100  THEN 'Silver'
            WHEN total_spent > 0     THEN 'Bronze'
            ELSE 'Inactive'
        END AS segment
    FROM customer_spending
)
SELECT
    segment,
    COUNT(*)                        AS customers,
    ROUND(AVG(total_spent), 2)      AS avg_spend,
    ROUND(SUM(total_spent), 2)      AS total_revenue
FROM segmented
GROUP BY segment
ORDER BY avg_spend DESC;
"""

Q_CTE_PRODUCT_RANK = """
WITH product_sales AS (
    SELECT
        p.product_id,
        p.name,
        p.category,
        p.price,
        COALESCE(SUM(oi.quantity), 0)   AS units_sold,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id AND o.status != 'cancelled'
    WHERE p.is_active = 1
    GROUP BY p.product_id
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank_in_category
    FROM product_sales
)
SELECT *
FROM ranked
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;
"""

Q_CTE_ROLLING_REVENUE = """
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        ROUND(SUM(total_amount), 2)   AS revenue
    FROM orders
    WHERE status != 'cancelled'
    GROUP BY month
)
SELECT
    month,
    revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3mo_avg
FROM monthly
ORDER BY month;
"""

# ── ADVANCED — Window Functions ────────────────────────────────────────────────

Q_WINDOW_EMPLOYEE_RANK = """
SELECT
    e.first_name || ' ' || e.last_name  AS employee,
    d.name                               AS department,
    e.salary,
    RANK()       OVER (PARTITION BY d.name ORDER BY e.salary DESC) AS salary_rank,
    ROUND(AVG(e.salary) OVER (PARTITION BY d.name), 2)             AS dept_avg_salary,
    ROUND(e.salary - AVG(e.salary) OVER (PARTITION BY d.name), 2)  AS vs_dept_avg,
    NTILE(4)     OVER (ORDER BY e.salary DESC)                      AS salary_quartile
FROM employees e
JOIN departments d ON e.department_id = d.department_id
ORDER BY d.name, salary_rank;
"""

Q_WINDOW_ORDER_TRENDS = """
SELECT
    strftime('%Y-%m', order_date)  AS month,
    COUNT(order_id)                 AS orders,
    ROUND(SUM(total_amount), 2)     AS revenue,
    ROUND(LAG(SUM(total_amount)) OVER (ORDER BY strftime('%Y-%m', order_date)), 2) AS prev_month,
    ROUND(
        (SUM(total_amount) - LAG(SUM(total_amount)) OVER (ORDER BY strftime('%Y-%m', order_date)))
        / NULLIF(LAG(SUM(total_amount)) OVER (ORDER BY strftime('%Y-%m', order_date)), 0) * 100
    , 1) AS pct_change
FROM orders
WHERE status != 'cancelled'
GROUP BY month
ORDER BY month;
"""

Q_WINDOW_CUSTOMER_PURCHASE_SEQUENCE = """
SELECT
    c.first_name || ' ' || c.last_name AS customer,
    o.order_id,
    o.order_date,
    o.total_amount,
    ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date) AS purchase_number,
    LAG(o.order_date) OVER (PARTITION BY o.customer_id ORDER BY o.order_date) AS prev_order_date,
    ROUND(JULIANDAY(o.order_date) - JULIANDAY(
        LAG(o.order_date) OVER (PARTITION BY o.customer_id ORDER BY o.order_date)
    ), 0) AS days_since_last_order
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status != 'cancelled'
ORDER BY o.customer_id, purchase_number;
"""

# ── SUBQUERIES ─────────────────────────────────────────────────────────────────

Q_SUBQUERY_ABOVE_AVG_PRODUCTS = """
SELECT
    p.name, p.category, p.price,
    ROUND(p.price - avg_prices.avg_cat_price, 2) AS above_avg_by
FROM products p
JOIN (
    SELECT category, ROUND(AVG(price), 2) AS avg_cat_price
    FROM products WHERE is_active = 1
    GROUP BY category
) avg_prices ON p.category = avg_prices.category
WHERE p.price > avg_prices.avg_cat_price
  AND p.is_active = 1
ORDER BY p.category, above_avg_by DESC;
"""

Q_SUBQUERY_NEVER_ORDERED = """
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer,
    c.email,
    c.created_at
FROM customers c
WHERE c.customer_id NOT IN (
    SELECT DISTINCT customer_id FROM orders
)
ORDER BY c.created_at DESC;
"""

Q_SUPPLIER_PERFORMANCE = """
SELECT
    s.name                              AS supplier,
    s.country,
    s.rating,
    COUNT(DISTINCT p.product_id)        AS products_supplied,
    COALESCE(SUM(oi.quantity), 0)       AS total_units_ordered,
    ROUND(COALESCE(SUM(oi.quantity * oi.unit_price), 0), 2) AS total_order_value
FROM suppliers s
LEFT JOIN products    p  ON s.supplier_id  = p.supplier_id
LEFT JOIN order_items oi ON p.product_id   = oi.product_id
LEFT JOIN orders      o  ON oi.order_id    = o.order_id
    AND o.status != 'cancelled'
GROUP BY s.supplier_id
ORDER BY total_order_value DESC;
"""

# All named queries for easy iteration
ALL_QUERIES = {
    "All Customers":                    Q_ALL_CUSTOMERS,
    "Active Products":                  Q_ACTIVE_PRODUCTS,
    "Low Stock Alert":                  Q_LOW_STOCK,
    "Order Details":                    Q_ORDER_DETAILS,
    "Employee Hierarchy":               Q_EMPLOYEE_HIERARCHY,
    "Revenue by Category":              Q_REVENUE_BY_CATEGORY,
    "Top Customers":                    Q_TOP_CUSTOMERS,
    "Monthly Revenue":                  Q_MONTHLY_REVENUE,
    "Dept Salary Stats":                Q_DEPT_SALARY_STATS,
    "CTE: Customer Segments":           Q_CTE_CUSTOMER_SEGMENTS,
    "CTE: Product Rank by Category":    Q_CTE_PRODUCT_RANK,
    "CTE: Rolling 3-Month Revenue":     Q_CTE_ROLLING_REVENUE,
    "Window: Employee Salary Rank":     Q_WINDOW_EMPLOYEE_RANK,
    "Window: Monthly Order Trends":     Q_WINDOW_ORDER_TRENDS,
    "Window: Purchase Sequence":        Q_WINDOW_CUSTOMER_PURCHASE_SEQUENCE,
    "Subquery: Above Avg Products":     Q_SUBQUERY_ABOVE_AVG_PRODUCTS,
    "Subquery: Never Ordered":          Q_SUBQUERY_NEVER_ORDERED,
    "Supplier Performance":             Q_SUPPLIER_PERFORMANCE,
}
