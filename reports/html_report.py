import json
import os
from typing import Dict, Any
from schema.unified_model import UnifiedSchema


class HTMLReportGenerator:
    """Generates a modern, responsive HTML report from a UnifiedSchema and JSON Schema."""

    def __init__(self, unified_schema: UnifiedSchema, json_schema: Dict[str, Any]):
        self.schema = unified_schema
        self.json_schema = json_schema

    def generate(self, output_path: str):
        """Generate and save the HTML report."""

        # Calculate overall completeness score
        total_cells = self.schema.row_count * self.schema.column_count
        total_missing = sum(col.missing_count for col in self.schema.columns.values())
        completeness_pct = round(((total_cells - total_missing) / total_cells * 100), 1) if total_cells > 0 else 100.0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Humanitarian Data Schema Report</title>
    <style>
        :root {{
            --primary: #0066cc;
            --primary-dark: #004999;
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #212529;
            --border: #dee2e6;
            --badge-green: #d4edda;
            --badge-green-text: #155724;
            --badge-red: #f8d7da;
            --badge-red-text: #721c24;
            --badge-blue: #cce5ff;
            --badge-blue-text: #004085;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        h1 {{
            margin: 0;
            color: var(--primary);
            font-size: 26px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 5px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid var(--border);
        }}
        .metric-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6c757d;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--primary-dark);
        }}
        .table-card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid var(--border);
            margin-bottom: 30px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: #f1f3f5;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-hxl {{
            background: var(--badge-blue);
            color: var(--badge-blue-text);
            font-family: monospace;
        }}
        .badge-good {{
            background: var(--badge-green);
            color: var(--badge-green-text);
        }}
        .badge-warn {{
            background: var(--badge-red);
            color: var(--badge-red-text);
        }}
        pre {{
            background: #272822;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Humanitarian Data Schema Report</h1>
                <div class="subtitle">Automated Schema Profiling & Standardisation • UNZA Final Year Project</div>
            </div>
            <div>
                <span class="badge badge-hxl">Format: {self.schema.format_name}</span>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="card">
                <div class="metric-title">Total Rows</div>
                <div class="metric-value">{self.schema.row_count:,}</div>
            </div>
            <div class="card">
                <div class="metric-title">Total Columns</div>
                <div class="metric-value">{self.schema.column_count}</div>
            </div>
            <div class="card">
                <div class="metric-title">Data Completeness</div>
                <div class="metric-value">{completeness_pct}%</div>
            </div>
            <div class="card">
                <div class="metric-title">Detected Format</div>
                <div class="metric-value" style="font-size: 20px;">{self.schema.format_name}</div>
            </div>
        </div>

        <div class="table-card">
            <h2>Column Profile & Quality Assessment</h2>
            <table>
                <thead>
                    <tr>
                        <th>Column Name</th>
                        <th>HXL Tag</th>
                        <th>Inferred Type</th>
                        <th>Missing Values</th>
                        <th>Missing %</th>
                        <th>Unique Values</th>
                        <th>Sample Values</th>
                    </tr>
                </thead>
                <tbody>"""

        for col in self.schema.columns.values():
            hxl_badge = f'<span class="badge badge-hxl">{col.hxl_tag}</span>' if col.hxl_tag else '-'
            missing_badge = f'<span class="badge badge-warn">{col.missing_percentage}%</span>' if col.missing_percentage > 0 else f'<span class="badge badge-good">0%</span>'
            samples_str = ", ".join(map(str, col.sample_values)) if col.sample_values else "-"

            html += f"""
                    <tr>
                        <td><strong>{col.name}</strong></td>
                        <td>{hxl_badge}</td>
                        <td><code>{col.inferred_type}</code></td>
                        <td>{col.missing_count}</td>
                        <td>{missing_badge}</td>
                        <td>{col.unique_count}</td>
                        <td><small>{samples_str}</small></td>
                    </tr>"""

        html += f"""
                </tbody>
            </table>
        </div>

        <div class="table-card">
            <h2>Standardised JSON Schema (Draft 2020-12)</h2>
            <pre>{json.dumps(self.json_schema, indent=4)}</pre>
        </div>
    </div>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
