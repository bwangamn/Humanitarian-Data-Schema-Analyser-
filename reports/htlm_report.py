import json


class HTMLReportGenerator:
    """Generates an HTML report from profiling and schema data."""

    def __init__(self, profile: dict, schema: dict):
        self.profile = profile
        self.schema = schema

    def generate(self, output_path: str):
        """Generate and save an HTML report."""

        html = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Humanitarian Data Schema Report</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}

        th {{
            background-color: #f2f2f2;
        }}

        .summary {{
            margin-bottom: 30px;
        }}
    </style>
</head>

<body>

<h1>Humanitarian Data Schema Report</h1>

<div class="summary">

<h2>Dataset Summary</h2>

<p>
<strong>Rows:</strong>
{self.profile["row_count"]}
</p>

<p>
<strong>Columns:</strong>
{self.profile["column_count"]}
</p>

</div>

<h2>Column Profile</h2>

<table>

<tr>
    <th>Column</th>
    <th>Data Type</th>
    <th>Missing Values</th>
    <th>Missing %</th>
    <th>Unique Values</th>
</tr>
"""

        for column, information in self.profile["columns"].items():

            html += f"""
<tr>
    <td>{column}</td>
    <td>{information["data_type"]}</td>
    <td>{information["missing_values"]}</td>
    <td>{information["missing_percentage"]}%</td>
    <td>{information["unique_values"]}</td>
</tr>
"""

        html += f"""
</table>

<h2>Generated JSON Schema</h2>

<pre>
{json.dumps(self.schema, indent=4)}
</pre>

</body>
</html>
"""

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(html)