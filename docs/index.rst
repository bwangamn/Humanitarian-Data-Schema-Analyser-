Humanitarian Data Schema Analyser
====================================

.. image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://www.python.org/
.. image:: https://img.shields.io/badge/JSON%20Schema-Draft%202020--12-green.svg
   :target: https://json-schema.org/

**Humanitarian Data Schema Analyser** is a Python framework and CLI tool designed to profile diverse humanitarian datasets (CSV, JSON, XML, Excel/XLSForm) and produce standardized Draft 2020-12 JSON Schema definitions and interactive HTML reports.

Features
--------

* **Multi-Format Dataset Ingestion**: Automatic parser selection for CSV, JSON, XML, and Excel (XLSForm) datasets.
* **HXL Tag Detection**: Native identification of Humanitarian Exchange Language (HXL) semantic tags.
* **Statistical Profiling**: Type inference, completeness analysis, uniqueness ratios, numeric distributions, and date pattern recognition.
* **Unified JSON Schema Export**: Generates compliant Draft 2020-12 JSON Schema representations with custom ``x-hxl-tag`` extensions.
* **Interactive HTML Dashboard**: Self-contained visual report with dataset metrics, search filtering, and schema inspection.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   usage

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
