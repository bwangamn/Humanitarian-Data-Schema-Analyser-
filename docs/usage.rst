Usage Guide
===========

Command Line Interface (CLI)
----------------------------

The primary entry point for analyzing humanitarian datasets is the CLI module built with Typer.

Basic Usage
~~~~~~~~~~~

Analyze a dataset file and generate an HTML report:

.. code-block:: powershell

   python -m cli.main analyze data/sample.csv --output report.html

If your virtual environment is not active, run directly using the interpreter path:

.. code-block:: powershell

   .\humanitarian_env\Scripts\python.exe -m cli.main analyze data/sample.csv --output report.html

Command Options
~~~~~~~~~~~~~~~

.. code-block:: text

   Usage: python -m cli.main analyze [OPTIONS] FILE

   Arguments:
     FILE  Path to the dataset file (CSV, JSON, XML, Excel/XLSForm). [required]

   Options:
     -o, --output TEXT        Path to save the generated HTML report. [default: report.html]
     -s, --schema-output TEXT Optional path to export the raw JSON Schema file.
     -f, --format TEXT        Explicit format override (csv, json, xml, xlsform).
     --help                   Show this message and exit.

Exporting Raw JSON Schema
~~~~~~~~~~~~~~~~~~~~~~~~~

To generate both an HTML report and export the Draft 2020-12 JSON Schema to a file:

.. code-block:: powershell

   python -m cli.main analyze data/sample_hxl.csv -o report_hxl.html -s schema_hxl.json

Programmatic Python Usage
-------------------------

You can also use the core packages programmatically in Python scripts:

.. code-block:: python

   from parsers.factory import ParserFactory
   from profiling.profiler import DataProfiler
   from schema.schema_builder import SchemaBuilder
   from reports.html_report import HTMLReportGenerator

   # 1. Parse dataset
   parser = ParserFactory.get_parser("data/sample.csv")
   parsed_dataset = parser.parse()

   # 2. Profile dataset
   profiler = DataProfiler(parsed_dataset)
   unified_schema = profiler.profile()

   # 3. Build JSON Schema
   builder = SchemaBuilder(unified_schema)
   json_schema = builder.build()

   # 4. Generate HTML Report
   generator = HTMLReportGenerator(unified_schema, json_schema)
   generator.generate("report.html")
