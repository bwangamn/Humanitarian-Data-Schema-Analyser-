# Changelog

All notable changes to the **Humanitarian Data Schema Analyzer** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-14

### Fixed
- **XML Repeated Element Normalization**: Repeated XML elements (e.g., IATI `<transaction>`) are now consistently normalized to arrays even when only a single occurrence is present in a record. This eliminates the inconsistency where multiple occurrences produced a list while a single occurrence produced a plain object, which caused the generated JSON Schema to reject valid data.
- **Nested XML Schema Representation**: Complex nested XML elements (e.g., `<title>`, `<transaction>`) now emit full inner property definitions in the generated JSON Schema instead of shallow `"type": "object"` or `"type": "array"` declarations. For example, `<title>` now generates `{"type": "object", "properties": {"narrative": {"type": "string"}}}`.
- **Mixed Object/Array Type Inference**: `DataProfiler._infer_type()` now correctly handles columns containing both objects and arrays by inferring a sorted union type (e.g., `["object", "array"]`) instead of defaulting to `"object"`.
- **Schema Builder Nested Schema Propagation**: `SchemaBuilder._build_tabular_schema()` now propagates `ColumnProfile.nested_schema` into the generated JSON Schema, ensuring full structural fidelity for complex data types.

### Added
- **`_find_repeated_tags()`** in `xml_parser.py`: Detects repeated element tags across the XML document tree, extracted records, and a known-repeatable tag set (`KNOWN_REPEATED_TAGS`).
- **`_normalize_record()`** in `xml_parser.py`: Recursively wraps single occurrences of repeated tags into single-item lists to ensure consistent array representation.
- **`_infer_nested_schema()`** in `profiler.py`: Recursively infers JSON Schema definitions for nested structures (objects, arrays, and primitives) with full inner property and item schema support.
- **`nested_schema` field** on `ColumnProfile` (`unified_model.py`): Stores the recursively inferred JSON Schema for complex columns, consumed by `SchemaBuilder`.
- **`tests/test_validation.py`**: Parametrized validation test that parses every fixture in `tests/fixtures/`, generates a JSON Schema, and validates every parsed record against it (Draft 2020-12 compliance).
- **`test_xml_parser_single_transaction_normalized_to_array`** in `test_xml_parser.py`: Locks in the normalization of single `<transaction>` elements to arrays.
- **`test_profiler_mixed_object_array_type_inference`** in `test_profiler.py`: Locks in consistent union type inference for mixed object/array columns.
- **Enhanced `test_xml_parser_pipeline_profiling_and_schema`**: Now verifies inner property definitions for `<title>` and `<transaction>` and validates all records against the generated schema.

### Changed
- **XLSForm Parser**: Extracted XLSForm survey questions as dataset fields with type mapping, choice list resolution, constraint preservation, and requiredness propagation.
- **Schema Builder Strategy A**: Numeric-looking string columns preserve `"type": "string"` with `x-numeric-string` and `x-potential-type` metadata annotations. Observed min/max values are emitted as `x-observed-minimum`/`x-observed-maximum` metadata instead of rigid validation constraints.
- **Test Suite Expansion**: Test suite expanded from 13 to 60 automated test cases across all parsers, profiler, schema builder, CLI, and cross-format validation.
- **Report Documentation**: Updated `FINAL_YEAR_PROJECT_REPORT.md` Section 5.6 and Table 6.1 with the XML repeated element defect fix documentation and new test entries.

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
