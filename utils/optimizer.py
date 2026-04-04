"""
optimizer.py
------------
Demonstrates query optimisation techniques:
  - EXPLAIN QUERY PLAN analysis
  - Comparing queries with/without indexes
  - Index usage reporting
  - Query timing benchmarks
"""

import time
from core.database import DatabaseManager


class QueryOptimizer:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def explain(self, sql: str, label: str = ""):
        """Print the EXPLAIN QUERY PLAN for a SQL statement."""
        plan = self.db.explain_query(sql)
        print(f"\n  EXPLAIN QUERY PLAN: {label or sql[:60]}")
        print(f"  {'─'*60}")
        for row in plan:
            detail = row.get("detail", row.get("Detail", ""))
            print(f"    {detail}")

    def benchmark(self, queries: dict, runs: int = 3) -> list:
        """
        Benchmark a dict of {label: sql} queries.
        Returns list of {label, avg_ms, rows}.
        """
        results = []
        print(f"\n  {'QUERY':<45} {'ROWS':>6}  {'AVG ms':>8}")
        print(f"  {'─'*45} {'─'*6}  {'─'*8}")

        for label, sql in queries.items():
            times = []
            rows  = 0
            for _ in range(runs):
                t0  = time.perf_counter()
                res = self.db.execute_query(sql)
                t1  = time.perf_counter()
                times.append((t1-t0)*1000)
                rows = len(res)

            avg_ms = sum(times) / len(times)
            results.append({"label": label, "avg_ms": avg_ms, "rows": rows})
            print(f"  {label:<45} {rows:>6}  {avg_ms:>8.3f}")

        return results

    def index_report(self) -> list:
        """Report all custom indexes in the database."""
        indexes = self.db.get_index_list()
        print(f"\n  {'INDEX NAME':<40} {'TABLE':<20}")
        print(f"  {'─'*40} {'─'*20}")
        for idx in indexes:
            print(f"  {idx['name']:<40} {idx['tbl_name']:<20}")
        return indexes

    def table_stats(self):
        """Print row counts for all tables."""
        stats = self.db.get_table_stats()
        print(f"\n  {'TABLE':<25} {'ROWS':>8}")
        print(f"  {'─'*25} {'─'*8}")
        for s in stats:
            print(f"  {s['table']:<25} {s['rows']:>8,}")
        return stats
