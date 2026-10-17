# Humanitarian Data Schema Analyzer

[![PyPI Version](https://img.shields.io/badge/pypi-v-blue.svg)](https://pypi.org/project/humanitarian-data-schema-analyzer/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated schema profiling, metadata extraction, and data quality standardisation framework for humanitarian datasets (CSV, HXL, JSON, XML, XLSForm).

---

## 1. Project Description
The **Humanitarian Data Schema Analyzer** (`hds-analyzer`) is a Python library and command-line tool engineered to address data interoperability challenges in humanitarian logistics, disaster response, and field operations. It automatically parses multi-format datasets, profiles column metrics and semantic attributes, generates standardized JSON Schema (Draft 2020-12), and produces interactive HTML analytical dashboards.

## 2. Problem Addressed
Humanitarian field data collected by UN agencies, non-governmental organisations (NGOs), and government bodies is fragmented across disparate formats (flat CSVs, HXL-tagged spreadsheets, XForms/XML, nested JSON, and ODK/KoboToolbox XLSForms). This structural heterogeneity causes schema drift, invalid type assumptions, data quality degradation, and delay in emergency response analytics. The Analyzer unifies these formats under a standardized schema pipeline.

## 3. Key Features
- **Multi-Format Ingestion**: Ingests tabular and semi-structured datasets seamlessly without manual preprocessing.
- **HXL Hashtag Extraction**: Detects and retains Humanitarian Exchange Language (HXL) hashtags (e.g., `#adm1+code`, `#affected+f+children`, `#loc+lat`).
- **Statistical Profiling**: Computes completeness scores, missing value counts/percentages, cardinality, min/max bounds, means, standard deviations, and date format patterns.
- **Draft 2020-12 JSON Schema**: Builds fully validated, interoperable JSON Schemas with nullable support, type definitions, HXL extensions (`x-hxl-tag`), and field examples.
- **Interactive HTML Dashboard**: Generates standalone HTML analytical reports with completeness metrics and quality badges.
- **Production CLI**: Standalone command-line executable (`hds-analyzer`).

## 4. Supported Formats
| Format | Extension / Structure | Parser Class | Semantic Tagging |
| :--- | :--- | :--- | :--- |
| **CSV** | `.csv` | `CSVParser` | Standard tabular columns |
| **HXL-CSV** | `.csv` (Row 2 `#hashtag`) | `CSVParser` | Native HXL hashtag mapping |
| **JSON** | `.json` (array or wrapped list) | `JSONParser` | Flattened dot-notation keys |
| **XML** | `.xml` (XForms / IATI) | `XMLParser` | Element & attribute extraction |
| **Excel / XLSForm** | `.xlsx`, `.xls` (`survey`/`choices`) | `XLSParser` | Survey questions & choice metadata |

## 5. Architecture Overview
```
Input Dataset (CSV, HXL, JSON, XML, XLSForm)
       ↓
Parser Selection (ParserFactory)
       ↓
Format-Specific Parser
       ↓
ParsedDataset (Standard Container)
       ↓
Data Profiling Engine (DataProfiler)
       ↓
Unified Schema Representation (UnifiedSchema)
       ├──────────────────────────┐
       ↓                          ↓
Schema Builder              HTML Report Generator
(JSON Schema Draft 2020-12) (Interactive Dashboard)
       ↓                          ↓
raw JSON Schema (.json)     HTML Report (.html)
```

## 6. Installation

Install via pip:

```bash
pip install humanitarian-data-schema-analyzer
```

For development:

```bash
git clone https://github.com/bwangamn/Humanitarian-Data-Schema-Analyser-.git
cd Humanitarian-Data-Schema-Analyser-
python -m venv humanitarian_env
.\humanitarian_env\Scripts\Activate.ps1
pip install -e .[dev]
```

## 7. Basic CLI Usage

Command signature:

```bash
hds-analyzer analyze <FILE_PATH> [OPTIONS]
```

### Command Options
- `FILE_PATH` (Required): Path to the target dataset file.
- `-o, --output <PATH>`: HTML report file path (default: `report.html`).
- `-s, --schema-output <PATH>`: Optional path to export raw JSON Schema (`.json`).
- `-f, --format <FORMAT>`: Format override (`csv`, `json`, `xml`, `xlsform`, `excel`).

## 8. Example Commands

Analyze a CSV dataset:
```bash
hds-analyzer analyze tests/fixtures/sample.csv --output report_csv.html
```

Analyze an HXL-tagged CSV dataset and export raw JSON Schema:
```bash
hds-analyzer analyze tests/fixtures/sample_hxl.csv --output report_hxl.html --schema-output schema_hxl.json
```

Analyze a JSON dataset:
```bash
hds-analyzer analyze tests/fixtures/sample.json --output report_json.html --schema-output schema_json.json
```

Analyze an ODK/XLSForm Excel survey file:
```bash
hds-analyzer analyze tests/fixtures/sample_xlsform.xlsx --output report_xlsform.html --schema-output schema_xlsform.json
```

## 9. Expected Outputs
When executing an analysis, the CLI outputs execution progress and status details:

```
Analyzing dataset: tests/fixtures/sample_hxl.csv
Successfully parsed as HXL-CSV format: 3 rows, 4 columns.
Detected 4 HXL semantic tags.
Running statistical profiling engine...
Generating Draft 2020-12 JSON Schema...
Exported JSON Schema to: schema_hxl.json
Generating interactive HTML dashboard...
Analysis complete! Report saved to: report_hxl.html
```

## 10. Unify Two JSON Schemas

`hds-analyzer unify` combines the `properties` and `required` arrays from two JSON Schema Draft 2020-12 files. It writes the result to the current working directory using both input stems; for example, `drc_schema.json` and `mali_schema.json` produce `drc_schema_mali_schema_unified.json`.

```bash
hds-analyzer unify path/to/drc_schema.json path/to/mali_schema.json
```

Fields found in only one input are copied to the unified schema. For fields with the same name and type, one property is retained and their `examples` arrays are combined with duplicates removed. If fields have the same name but different types, the command prints a warning and writes both types as a JSON Schema type array, such as `"type": ["integer", "string"]`.

## 11. Supported JSON Schema Output
The engine generates validated Draft 2020-12 JSON Schema definitions:

```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Humanitarian Dataset Schema (HXL-CSV)",
    "type": "object",
    "properties": {
        "adm1_code": {
            "type": "string",
            "x-hxl-tag": "#adm1+code",
            "examples": ["ZM-01", "ZM-02"]
        },
        "affected_count": {
            "type": "integer",
            "x-hxl-tag": "#affected+number",
            "minimum": 150.0,
            "maximum": 300.0,
            "examples": [150, 220, 300]
        }
    },
    "required": ["adm1_code", "affected_count"]
}
```

## 11. HTML Reporting
The HTML report provides:
- High-level metrics: Total Rows, Total Columns, Data Completeness Score (%), Format Badge.
- Detailed field quality table: Inferred Types, Missing Value Counts/Percentages, Unique Count, Sample Values, HXL Badges.
- Embedded JSON Schema block for copy-paste deployment.

## 12. Development Setup
```bash
git clone https://github.com/bwangamn/Humanitarian-Data-Schema-Analyser-.git
cd Humanitarian-Data-Schema-Analyser-
python -m venv humanitarian_env
.\humanitarian_env\Scripts\Activate.ps1
pip install -e .[dev]
```

## 13. Running Tests
Run the complete test suite with `pytest`:

```bash
pytest
```

To view test coverage:

```bash
pytest --cov=humanitarian_schema_analyzer
```

## 14. Project Structure
```
Humanitarian-Data-Schema-Analyser-/
├── src/
│   └── humanitarian_schema_analyzer/
│       ├── __init__.py
│       ├── parsers/
│       │   ├── base_parser.py
│       │   ├── csv_parser.py
│       │   ├── json_parser.py
│       │   ├── xml_parser.py
│       │   ├── xls_parser.py
│       │   └── factory.py
│       ├── profiling/
│       │   └── profiler.py
│       ├── schema/
│       │   ├── unified_model.py
│       │   └── schema_builder.py
│       ├── reports/
│       │   └── html_report.py
│       └── cli/
│           └── main.py
├── tests/
│   ├── fixtures/
│   │   ├── sample.csv
│   │   ├── sample_hxl.csv
│   │   ├── sample.json
│   │   ├── sample.xml
│   │   ├── sample.xlsx
│   │   └── sample_xlsform.xlsx
│   ├── test_cli.py
│   ├── test_csv_parser.py
│   ├── test_hxl_type_inference.py
│   ├── test_json_parser.py
│   ├── test_profiler.py
│   ├── test_schema_builder.py
│   ├── test_xls_parser.py
│   └── test_xml_parser.py
├── data/
├── docs/
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## 15. Limitations
- Large datasets (>1GB) are loaded in-memory via Pandas DataFrames; streaming chunked profiling is planned for future releases.
- Deeply nested custom XML structures are flattened to first-level child nodes.

## 16. License
Distributed under the MIT License. See [LICENSE](LICENSE) for details.

## 17. Repository / Project Information
- **Domain**: Data Engineering / Humanitarian Data / Data Quality
- **Supervisor**: Mr. Mofya Phiri
- **Author**: Bwanga Nyirenda
- **Repository**: [GitHub](https://github.com/bwangamn/Humanitarian-Data-Schema-Analyser-)
