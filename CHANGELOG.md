# Changelog

All notable changes to the **Humanitarian Data Schema Analyzer** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-30

### Added
- **Modular Parser Architecture**: Extensible parser hierarchy for multi-format dataset ingestion:
  - CSV parser with automatic delimiter inspection.
  - HXL-CSV parser for Humanitarian Exchange Language tag detection and semantic metadata extraction.
  - JSON parser for flat, array, and nested record structures.
  - XML parser for XForms and IATI (International Aid Transparency Initiative) structures.
  - Excel & XLSForm parser for multi-sheet survey and choices extraction (`.xlsx`/`.xls`).
- **Statistical Profiling Engine**: Automated missing value analysis, data completeness scoring, unique value counting, sample extraction, numeric summary statistics, and date format detection.
- **Unified Internal Schema Representation**: Decoupled `UnifiedSchema` and `ColumnProfile` data structures.
- **Standardised JSON Schema Generation**: Fully compliant JSON Schema (Draft 2020-12) builder supporting nullable types, numeric range constraints (`minimum`, `maximum`), HXL extension attributes (`x-hxl-tag`), and field examples.
- **Interactive HTML Dashboard Report Generator**: Modern, responsive HTML report generator with quality badges, completeness metrics, and JSON Schema visualization.
- **CLI Interface**: Typer-based command-line tool (`hds-analyzer`) with options for dataset parsing, format overrides, raw JSON Schema exports (`-s`), and HTML dashboard output (`-o`).
- **Python Packaging & Distribution Setup**:
  - Reorganized project codebase into `src/` layout (`src/humanitarian_schema_analyzer`).
  - Standardized `pyproject.toml` packaging setup with `setuptools.build_meta`.
  - Console script entrypoint `hds-analyzer`.
  - Comprehensive unit and integration test suite with `pytest`.
  - Deterministic test fixtures for all supported dataset formats under `tests/fixtures/`.
