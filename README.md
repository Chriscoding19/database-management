# 🗄️ Database Management System

A fully-featured relational database system built with SQLite demonstrating professional SQL techniques including schema design, indexing strategies, CTEs, window functions, triggers, views, and query optimisation.

---

## 📐 Architecture

```
database-management/
├── main.py                          ← Full pipeline entry point
├── requirements.txt                 ← No external deps (stdlib only!)
├── core/
│   ├── database.py                  ← Connection manager + transaction context
│   └── schema.py                    ← Full schema: tables, indexes, views, triggers
├── data/
│   └── seed_data.py                 ← Realistic sample data generator
├── queries/
│   └── queries.py                   ← 18 optimised SQL queries
├── utils/
│   └── optimizer.py                 ← EXPLAIN QUERY PLAN + benchmarking
├── reports/
│   └── report_generator.py          ← HTML report output
└── tests/
    └── test_database.py             ← 20 unit tests (all passing ✅)
```

---

## 🚀 Quick Start

```bash
# No dependencies needed — pure Python stdlib!
python3 main.py

# Run unit tests
python3 tests/test_database.py

# View report
explorer.exe reports/db_report_*.html
```

---

## 🏗️ Database Schema (8 Tables)

| Table | Description |
|---|---|
| `customers` | 200 customer accounts |
| `products` | 25 products across 10 categories |
| `orders` | 500 orders with statuses |
| `order_items` | Line items with quantities and prices |
| `employees` | 50 staff records |
| `departments` | 6 company departments |
| `suppliers` | 8 product suppliers |
| `inventory` | Stock levels per product |

---

## 🔍 SQL Techniques Demonstrated

### Basic
- Filtered SELECT with WHERE clauses
- ORDER BY and LIMIT

### JOINs
- INNER JOIN across 4 tables
- LEFT JOIN for optional relationships
- Self-join for employee hierarchy (manager/subordinate)

### Aggregations
- GROUP BY with HAVING filters
- Multi-table revenue rollups

### CTEs (Common Table Expressions)
- Customer segmentation (VIP/Gold/Silver/Bronze/Inactive)
- Product ranking per category
- Rolling 3-month revenue average

### Window Functions
- `RANK()` — salary ranking within department
- `LAG()` — month-over-month revenue change
- `ROW_NUMBER()` — customer purchase sequence
- `NTILE(4)` — salary quartiles
- `AVG() OVER (PARTITION BY ...)` — dept average vs individual

### Subqueries
- Correlated subqueries for above-average products
- NOT IN subquery for customers who never ordered

---

## ⚡ Indexing Strategy (14 Indexes)

| Index | Type | Purpose |
|---|---|---|
| `idx_orders_customer` | B-tree | Fast order lookups by customer |
| `idx_orders_status` | B-tree | Filter by order status |
| `idx_orders_customer_date` | Composite | Customer order history sorted by date |
| `idx_active_products` | Partial | Only indexes active products |
| `idx_inventory_reorder` | Covering | All columns for reorder query |
| `idx_products_category` | B-tree | Category filtering |

---

## 🔁 Triggers (4)

- `trg_order_total_on_insert` — Auto-calculates order total on item insert
- `trg_order_total_on_update` — Recalculates on item update
- `trg_order_total_on_delete` — Recalculates on item delete
- `trg_inventory_updated` — Stamps last_updated on stock change

---

## 👁️ Views (4)

- `v_order_summary` — Order + customer + employee joined
- `v_product_performance` — Sales, revenue, margin per product
- `v_customer_stats` — Lifetime value, order count, avg spend
- `v_low_stock` — Products below reorder level

---

## 🛠 Technologies

- **Language**: Python 3.10+ (zero external dependencies)
- **Database**: SQLite 3 with WAL journal mode
- **Concepts**: Foreign keys, CHECK constraints, UNIQUE, CASCADE delete
- **Output**: HTML report with all query results
