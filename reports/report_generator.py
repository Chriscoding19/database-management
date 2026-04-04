"""
report_generator.py
--------------------
Generates a professional HTML report of database analysis results.
"""

import os
import json
from datetime import datetime


def generate_html_report(table_stats, index_list, query_results, benchmark_results,
                          output_dir="reports") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"db_report_{ts}.html")

    # Table stats rows
    table_rows = "".join(
        f"<tr><td>{s['table']}</td><td style='text-align:right'>{s['rows']:,}</td></tr>"
        for s in table_stats
    )

    # Index rows
    index_rows = "".join(
        f"<tr><td style='font-family:monospace'>{i['name']}</td><td>{i['tbl_name']}</td></tr>"
        for i in index_list
    )

    # Benchmark rows
    bench_rows = "".join(
        f"<tr><td>{b['label']}</td><td style='text-align:right'>{b['rows']:,}</td>"
        f"<td style='text-align:right'>{b['avg_ms']:.3f} ms</td></tr>"
        for b in benchmark_results
    )

    # Query result sections
    query_sections = ""
    for name, rows in query_results.items():
        if not rows:
            continue
        headers = list(rows[0].keys())
        thead   = "".join(f"<th>{h}</th>" for h in headers)
        tbody   = ""
        for row in rows[:20]:  # Max 20 rows per table
            tbody += "<tr>" + "".join(f"<td>{row.get(h,'')}</td>" for h in headers) + "</tr>"
        query_sections += f"""
        <h3 style="color:#79c0ff;margin:1.5rem 0 0.5rem">{name}</h3>
        <div style="overflow-x:auto">
        <table>
          <thead><tr>{thead}</tr></thead>
          <tbody>{tbody}</tbody>
        </table>
        </div>
        {"<p style='color:#8b949e;font-size:0.8rem'>Showing first 20 rows</p>" if len(rows) > 20 else ""}
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Database Management System Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  h1 {{ color: #58a6ff; font-size: 2rem; margin-bottom: 0.3rem; }}
  h2 {{ color: #79c0ff; font-size: 1.3rem; margin: 2rem 0 1rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }}
  h3 {{ color: #79c0ff; }}
  .meta {{ color: #8b949e; margin-bottom: 2rem; font-size: 0.9rem; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; }}
  .card h3 {{ color: #79c0ff; margin-bottom: 1rem; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; margin-bottom: 1rem; }}
  th {{ background: #21262d; color: #8b949e; text-align: left; padding: 0.6rem 1rem; font-size: 0.8rem; text-transform: uppercase; }}
  td {{ padding: 0.6rem 1rem; border-top: 1px solid #21262d; font-size: 0.85rem; }}
  tr:hover td {{ background: #1c2128; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .summary-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.2rem; text-align: center; }}
  .summary-card .number {{ font-size: 2rem; font-weight: bold; }}
  .summary-card .label  {{ font-size: 0.75rem; color: #8b949e; text-transform: uppercase; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; background: #0d2a14; color: #3fb950; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
  <h1>🗄️ Database Management System</h1>
  <div class="meta">
    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp;
    Engine: SQLite with WAL mode &nbsp;|&nbsp;
    Schema: E-Commerce relational database
  </div>

  <div class="summary-grid">
    <div class="summary-card"><div class="number" style="color:#58a6ff">{sum(s['rows'] for s in table_stats):,}</div><div class="label">Total Records</div></div>
    <div class="summary-card"><div class="number" style="color:#3fb950">{len(table_stats)}</div><div class="label">Tables</div></div>
    <div class="summary-card"><div class="number" style="color:#d29922">{len(index_list)}</div><div class="label">Indexes</div></div>
    <div class="summary-card"><div class="number" style="color:#bc8cff">{len(query_results)}</div><div class="label">Queries</div></div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>Table Statistics</h3>
      <table><thead><tr><th>Table</th><th>Rows</th></tr></thead>
      <tbody>{table_rows}</tbody></table>
    </div>
    <div class="card">
      <h3>Index Inventory ({len(index_list)} indexes)</h3>
      <table><thead><tr><th>Index Name</th><th>Table</th></tr></thead>
      <tbody>{index_rows}</tbody></table>
    </div>
  </div>

  <h2>Query Benchmark Results</h2>
  <table>
    <thead><tr><th>Query</th><th>Rows Returned</th><th>Avg Time</th></tr></thead>
    <tbody>{bench_rows}</tbody>
  </table>

  <h2>Query Results</h2>
  {query_sections}
</div>
</body>
</html>"""

    with open(filename, "w") as f:
        f.write(html)
    print(f"  HTML report saved: {filename}")
    return filename
