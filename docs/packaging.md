# Python Packaging & Distribution Guide

## Overview

The **Humanitarian Data Schema Analyzer** (`humanitarian-data-schema-analyzer`) is packaged using modern Python packaging standards (`pyproject.toml`, PEP 517 / PEP 621) following a clean `src/` layout.

## Package Architecture

```
project-root/
│
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
│
├── tests/
│   └── fixtures/
│       ├── sample.csv
│       ├── sample_hxl.csv
│       ├── sample.json
│       ├── sample.xml
│       ├── sample.xlsx
│       └── sample_xlsform.xlsx
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
└── requirements.txt
```

## CLI Entrypoint

When installed via pip, the command `hds-analyzer` is registered via `pyproject.toml`:

```toml
[project.scripts]
hds-analyzer = "humanitarian_schema_analyzer.cli.main:app"
```

## Building the Package

1. Ensure `build` is installed:
   ```bash
   pip install build
   ```

2. Build source distribution (`.tar.gz`) and wheel (`.whl`):
   ```bash
   python -m build
   ```
   Artifacts are output to `dist/`.

## Validating Package Metadata

Validate distribution integrity using `twine`:

```bash
python -m twine check dist/*
```

## Publishing Workflow

### TestPyPI (Staging)

```bash
python -m twine upload --repository testpypi dist/*
```

### Production PyPI

```bash
python -m twine upload dist/*
```
