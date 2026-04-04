"""
database.py
-----------
Core database connection manager with context management,
transaction support, and query execution utilities.
"""

import sqlite3
import os
import time
from contextlib import contextmanager
from typing import Optional
from core.schema import CREATE_SCHEMA_SQL


class DatabaseManager:
    """
    Manages SQLite database connections with:
      - WAL journal mode for better concurrency
      - Foreign key enforcement
      - Optimised PRAGMA settings
      - Context manager for transactions
    """

    def __init__(self, db_path: str = "data/ecommerce.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Open and configure a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row          # Dict-like rows
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        return conn

    @contextmanager
    def transaction(self):
        """Context manager that auto-commits or rolls back."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def initialise(self):
        """Create schema (tables, indexes, views, triggers)."""
        with self.transaction() as conn:
            conn.executescript(CREATE_SCHEMA_SQL)
        print(f"  Database initialised: {self.db_path}")

    def execute_query(self, sql: str, params: tuple = ()) -> list:
        """Execute a SELECT query and return all rows as dicts."""
        with self.transaction() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_many(self, sql: str, data: list):
        """Bulk insert/update using executemany."""
        with self.transaction() as conn:
            conn.executemany(sql, data)

    def execute_write(self, sql: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE, return lastrowid or rowcount."""
        with self.transaction() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid

    def timed_query(self, sql: str, params: tuple = (), label: str = "") -> tuple:
        """Run a query and return (results, elapsed_ms)."""
        start = time.perf_counter()
        results = self.execute_query(sql, params)
        elapsed = (time.perf_counter() - start) * 1000
        return results, elapsed

    def explain_query(self, sql: str, params: tuple = ()) -> list:
        """Return EXPLAIN QUERY PLAN output for a given SQL statement."""
        return self.execute_query(f"EXPLAIN QUERY PLAN {sql}", params)

    def get_table_stats(self) -> list:
        """Return row counts for all user tables."""
        tables = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        stats = []
        for t in tables:
            name = t["name"]
            count = self.execute_query(f"SELECT COUNT(*) AS cnt FROM {name}")[0]["cnt"]
            stats.append({"table": name, "rows": count})
        return stats

    def get_index_list(self) -> list:
        """Return all indexes in the database."""
        return self.execute_query(
            "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )

    def vacuum(self):
        """Reclaim unused space and defragment the database."""
        conn = self.get_connection()
        conn.execute("VACUUM")
        conn.close()
        print("  VACUUM complete.")
