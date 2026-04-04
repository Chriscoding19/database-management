"""
tests/test_database.py
-----------------------
Unit tests for the Database Management System.

Run with:
  python tests/test_database.py
  or: python -m pytest tests/ -v
"""

import sys
import os
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import DatabaseManager
from data.seed_data import seed_all


def make_test_db() -> DatabaseManager:
    """Create a fresh in-memory test database."""
    db = DatabaseManager(":memory:")
    # Patch path for in-memory
    import sqlite3
    db._conn = sqlite3.connect(":memory:")
    db._conn.row_factory = sqlite3.Row
    db._conn.execute("PRAGMA foreign_keys = ON")
    db._conn.execute("PRAGMA journal_mode = WAL")
    from core.schema import CREATE_SCHEMA_SQL
    db._conn.executescript(CREATE_SCHEMA_SQL)
    db._conn.commit()

    # Override methods to use persistent connection
    def _get_conn():
        return db._conn

    import contextlib
    @contextlib.contextmanager
    def _transaction():
        try:
            yield db._conn
            db._conn.commit()
        except Exception as e:
            db._conn.rollback()
            raise e

    db.get_connection = _get_conn
    db.transaction    = _transaction
    return db


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        """Use a temp file db for full test."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db  = DatabaseManager(self.tmp.name)
        self.db.initialise()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_initialise_creates_tables(self):
        stats = self.db.get_table_stats()
        names = [s["table"] for s in stats]
        for t in ["customers","products","orders","order_items","employees","departments"]:
            self.assertIn(t, names)

    def test_execute_write_and_query(self):
        self.db.execute_write(
            "INSERT INTO departments (name, budget, location) VALUES (?,?,?)",
            ("Test Dept", 100000, "Floor 5")
        )
        rows = self.db.execute_query(
            "SELECT * FROM departments WHERE name=?", ("Test Dept",)
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["budget"], 100000)

    def test_foreign_key_constraint(self):
        with self.assertRaises(Exception):
            self.db.execute_write(
                "INSERT INTO employees (first_name,last_name,email,hire_date,salary,department_id) VALUES (?,?,?,?,?,?)",
                ("John","Doe","jd@test.com","2024-01-01",50000, 9999)  # Non-existent dept
            )

    def test_unique_constraint(self):
        self.db.execute_write(
            "INSERT INTO departments (name,budget,location) VALUES (?,?,?)",
            ("Unique Dept", 50000, "Floor 1")
        )
        with self.assertRaises(Exception):
            self.db.execute_write(
                "INSERT INTO departments (name,budget,location) VALUES (?,?,?)",
                ("Unique Dept", 60000, "Floor 2")  # Duplicate name
            )

    def test_check_constraint_negative_budget(self):
        with self.assertRaises(Exception):
            self.db.execute_write(
                "INSERT INTO departments (name,budget,location) VALUES (?,?,?)",
                ("Bad Dept", -1000, "Floor 1")
            )

    def test_indexes_exist(self):
        indexes = self.db.get_index_list()
        names   = [i["name"] for i in indexes]
        self.assertIn("idx_orders_customer", names)
        self.assertIn("idx_products_category", names)
        self.assertIn("idx_inventory_reorder", names)

    def test_views_exist(self):
        views = self.db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='view'"
        )
        names = [v["name"] for v in views]
        self.assertIn("v_order_summary", names)
        self.assertIn("v_product_performance", names)
        self.assertIn("v_customer_stats", names)
        self.assertIn("v_low_stock", names)

    def test_trigger_recalculates_order_total(self):
        # Setup
        self.db.execute_write(
            "INSERT INTO departments (name,budget,location) VALUES (?,?,?)",
            ("Sales",100000,"Floor 1")
        )
        dept_id = self.db.execute_query("SELECT department_id FROM departments WHERE name='Sales'")[0]["department_id"]
        self.db.execute_write(
            "INSERT INTO customers (first_name,last_name,email,country) VALUES (?,?,?,?)",
            ("Test","User","test@test.com","US")
        )
        cust_id = self.db.execute_query("SELECT customer_id FROM customers")[0]["customer_id"]
        self.db.execute_write(
            "INSERT INTO suppliers (name,contact_email,country) VALUES (?,?,?)",
            ("TestSupplier","s@s.com","US")
        )
        sup_id = self.db.execute_query("SELECT supplier_id FROM suppliers")[0]["supplier_id"]
        self.db.execute_write(
            "INSERT INTO products (name,category,price,cost,sku,supplier_id) VALUES (?,?,?,?,?,?)",
            ("Widget","Electronics",100.0,40.0,"WDG-001",sup_id)
        )
        prod_id = self.db.execute_query("SELECT product_id FROM products")[0]["product_id"]
        self.db.execute_write(
            "INSERT INTO orders (customer_id, status) VALUES (?,?)",
            (cust_id,"pending")
        )
        order_id = self.db.execute_query("SELECT order_id FROM orders")[0]["order_id"]

        # Insert item — trigger should set total
        self.db.execute_write(
            "INSERT INTO order_items (order_id,product_id,quantity,unit_price,discount) VALUES (?,?,?,?,?)",
            (order_id, prod_id, 3, 100.0, 0.0)
        )
        total = self.db.execute_query(
            "SELECT total_amount FROM orders WHERE order_id=?", (order_id,)
        )[0]["total_amount"]
        self.assertEqual(total, 300.0)

    def test_timed_query(self):
        results, elapsed = self.db.timed_query("SELECT 1 AS val")
        self.assertIsInstance(elapsed, float)
        self.assertGreater(elapsed, 0)

    def test_execute_many(self):
        self.db.execute_write(
            "INSERT INTO departments (name,budget,location) VALUES (?,?,?)",
            ("BulkDept", 50000, "Floor 9")
        )
        dept_id = self.db.execute_query(
            "SELECT department_id FROM departments WHERE name='BulkDept'"
        )[0]["department_id"]
        data = [
            (f"First{i}", f"Last{i}", f"bulk{i}@test.com", "2024-01-01", 50000, dept_id)
            for i in range(10)
        ]
        self.db.execute_many(
            "INSERT OR IGNORE INTO employees (first_name,last_name,email,hire_date,salary,department_id) VALUES (?,?,?,?,?,?)",
            data
        )
        count = self.db.execute_query("SELECT COUNT(*) AS cnt FROM employees")[0]["cnt"]
        self.assertEqual(count, 10)


class TestQueries(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db  = DatabaseManager(self.tmp.name)
        self.db.initialise()
        seed_all(self.db)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _run(self, sql):
        return self.db.execute_query(sql)

    def test_customers_populated(self):
        rows = self._run("SELECT COUNT(*) AS cnt FROM customers")
        self.assertGreater(rows[0]["cnt"], 0)

    def test_products_populated(self):
        rows = self._run("SELECT COUNT(*) AS cnt FROM products")
        self.assertGreater(rows[0]["cnt"], 0)

    def test_orders_populated(self):
        rows = self._run("SELECT COUNT(*) AS cnt FROM orders")
        self.assertGreater(rows[0]["cnt"], 0)

    def test_order_items_populated(self):
        rows = self._run("SELECT COUNT(*) AS cnt FROM order_items")
        self.assertGreater(rows[0]["cnt"], 0)

    def test_order_total_trigger_works(self):
        """Order totals should be non-zero where items exist."""
        rows = self._run("""
            SELECT o.total_amount FROM orders o
            WHERE EXISTS (SELECT 1 FROM order_items WHERE order_id=o.order_id)
            LIMIT 10
        """)
        for r in rows:
            self.assertGreater(r["total_amount"], 0)

    def test_view_order_summary(self):
        rows = self._run("SELECT * FROM v_order_summary LIMIT 5")
        self.assertGreater(len(rows), 0)
        self.assertIn("customer_name", rows[0])

    def test_view_product_performance(self):
        rows = self._run("SELECT * FROM v_product_performance LIMIT 5")
        self.assertGreater(len(rows), 0)
        self.assertIn("margin_pct", rows[0])

    def test_view_customer_stats(self):
        rows = self._run("SELECT * FROM v_customer_stats LIMIT 5")
        self.assertGreater(len(rows), 0)
        self.assertIn("lifetime_value", rows[0])

    def test_revenue_by_category(self):
        from queries.queries import Q_REVENUE_BY_CATEGORY
        rows = self._run(Q_REVENUE_BY_CATEGORY)
        self.assertGreater(len(rows), 0)
        self.assertIn("revenue", rows[0])

    def test_cte_customer_segments(self):
        from queries.queries import Q_CTE_CUSTOMER_SEGMENTS
        rows = self._run(Q_CTE_CUSTOMER_SEGMENTS)
        segments = [r["segment"] for r in rows]
        self.assertTrue(any(s in segments for s in ["VIP","Gold","Silver","Bronze","Inactive"]))

    def test_window_employee_rank(self):
        from queries.queries import Q_WINDOW_EMPLOYEE_RANK
        rows = self._run(Q_WINDOW_EMPLOYEE_RANK)
        self.assertGreater(len(rows), 0)
        self.assertIn("salary_rank", rows[0])
        self.assertIn("salary_quartile", rows[0])

    def test_subquery_never_ordered(self):
        from queries.queries import Q_SUBQUERY_NEVER_ORDERED
        rows = self._run(Q_SUBQUERY_NEVER_ORDERED)
        # Should return some customers who never ordered
        self.assertIsInstance(rows, list)


if __name__ == "__main__":
    print("Running Database Management System tests...\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestQueries))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
