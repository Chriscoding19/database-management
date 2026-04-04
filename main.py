#!/usr/bin/env python3
"""
main.py — Database Management System
=====================================

Full pipeline:
  1. Initialise schema (tables, indexes, views, triggers)
  2. Seed with realistic sample data
  3. Run all SQL queries (basic, joins, CTEs, window functions, subqueries)
  4. Benchmark query performance
  5. Analyse indexes and query plans
  6. Generate HTML report

Usage:
  python3 main.py
  python3 main.py --no-report
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from core.database import DatabaseManager
from data.seed_data import seed_all
from queries.queries import ALL_QUERIES
from utils.optimizer import QueryOptimizer
from reports.report_generator import generate_html_report


def parse_args():
    p = argparse.ArgumentParser(description="Database Management System")
    p.add_argument("--no-report", action="store_true", help="Skip HTML report")
    p.add_argument("--db",        default="data/ecommerce.db", help="Database path")
    return p.parse_args()


def print_header():
    print("\n" + "═"*65)
    print("   🗄️  DATABASE MANAGEMENT SYSTEM")
    print("   Relational DB · SQL · Indexing · Query Optimisation")
    print("═"*65)


def section(title):
    print(f"\n┌─────────────────────────────────────────────────────────────┐")
    print(f"│  {title}")
    print(f"└─────────────────────────────────────────────────────────────┘")


def main():
    args  = parse_args()
    start = time.time()
    print_header()

    # ── Step 1: Initialise ─────────────────────────────────────────
    section("STEP 1/5 — Initialise Schema")
    db = DatabaseManager(args.db)
    db.initialise()

    opt = QueryOptimizer(db)

    print("\n  Tables created:")
    for t in ["customers","products","orders","order_items",
              "employees","departments","suppliers","inventory"]:
        print(f"    ✓ {t}")
    print("\n  Views created:")
    for v in ["v_order_summary","v_product_performance","v_customer_stats","v_low_stock"]:
        print(f"    ✓ {v}")
    print("\n  Triggers created:")
    for tr in ["trg_inventory_updated","trg_order_total_on_insert",
               "trg_order_total_on_update","trg_order_total_on_delete"]:
        print(f"    ✓ {tr}")

    # ── Step 2: Seed Data ──────────────────────────────────────────
    section("STEP 2/5 — Seed Sample Data")
    seed_all(db)

    print("\n  Database statistics:")
    opt.table_stats()

    # ── Step 3: Run Queries ────────────────────────────────────────
    section("STEP 3/5 — Running SQL Queries")

    query_results = {}
    categories = {
        "Basic":          ["All Customers","Active Products","Low Stock Alert"],
        "JOINs":          ["Order Details","Employee Hierarchy","Supplier Performance"],
        "Aggregations":   ["Revenue by Category","Top Customers","Monthly Revenue","Dept Salary Stats"],
        "CTEs":           ["CTE: Customer Segments","CTE: Product Rank by Category","CTE: Rolling 3-Month Revenue"],
        "Window Funcs":   ["Window: Employee Salary Rank","Window: Monthly Order Trends","Window: Purchase Sequence"],
        "Subqueries":     ["Subquery: Above Avg Products","Subquery: Never Ordered"],
    }

    for cat, query_names in categories.items():
        print(f"\n  [{cat}]")
        for name in query_names:
            if name not in ALL_QUERIES:
                continue
            sql  = ALL_QUERIES[name]
            rows = db.execute_query(sql)
            query_results[name] = rows
            print(f"    ✓ {name:<42} → {len(rows):>4} rows")

    # ── Step 4: Benchmark ──────────────────────────────────────────
    section("STEP 4/5 — Query Performance Benchmarks")

    benchmark_queries = {
        "Revenue by Category":          ALL_QUERIES["Revenue by Category"],
        "Top Customers":                ALL_QUERIES["Top Customers"],
        "CTE: Customer Segments":       ALL_QUERIES["CTE: Customer Segments"],
        "Window: Employee Salary Rank": ALL_QUERIES["Window: Employee Salary Rank"],
        "CTE: Product Rank by Category":ALL_QUERIES["CTE: Product Rank by Category"],
        "Subquery: Above Avg Products": ALL_QUERIES["Subquery: Above Avg Products"],
    }
    bench_results = opt.benchmark(benchmark_queries, runs=5)

    # ── Step 5: Index Analysis ─────────────────────────────────────
    section("STEP 5/5 — Index Analysis & Query Plans")

    print("\n  Registered indexes:")
    index_list = opt.index_report()

    print("\n  Query plan — Top Customers (uses idx_orders_customer):")
    opt.explain(ALL_QUERIES["Top Customers"], "Top Customers")

    print("\n  Query plan — Revenue by Category (uses idx_products_category):")
    opt.explain(ALL_QUERIES["Revenue by Category"], "Revenue by Category")

    # ── Report ─────────────────────────────────────────────────────
    if not args.no_report:
        section("GENERATING HTML REPORT")
        table_stats = db.get_table_stats()
        html_path = generate_html_report(
            table_stats, index_list, query_results, bench_results
        )
        print(f"\n  Open in browser:")
        print(f"    explorer.exe {html_path.replace('/', os.sep)}")

    elapsed = time.time() - start
    print(f"\n{'═'*65}")
    print(f"  ✅  Complete! Total time: {elapsed:.1f}s")
    print(f"  🗄️   Database : {args.db}")
    print(f"  📊  Report   : reports/db_report_*.html")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
