# Changelog

All notable changes to the **Humanitarian Data Schema Analyzer** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-10-22

### Added
- **Field Mapping for `unify`**: `hds-analyzer unify --mapping <file.csv>` accepts a two-column CSV (`schema1_field,schema2_field`) so that differently named fields, such as `age` and `child_age`, are merged into one field. Mapping rows that name a field missing from the second schema produce a warning.
- **Tests**: `tests/test_unifier.py` covers mapping, unmapped renamed fields, the required-field rule and malformed mapping files. `tests/test_html_report.py` checks that HTML-like input is escaped.

### Fixed
- **HTML Report Escaping**: Column names, HXL tags, sample values, type names, format names and the embedded JSON Schema are now written with `html.escape`, so a data file containing HTML-like text can no longer change the report page.
- **Merged `required` List**: The unified schema now lists only fields required by both input schemas (after mapping), instead of the union. Previously a record valid under one schema could fail the merged schema.
- **Version Strings**: `__version__` in `__init__.py` now matches `pyproject.toml`, and the README badge reads the version from PyPI.
- **Reproducible Benchmark Data**: `generated_datasets.py` sets a fixed random seed (2026).

## [0.2.1] - 2026-10-17

### Added
- **JSON Schema Unification**: Added `hds-analyzer unify <schema1_path> <schema2_path>` to combine two system-generated JSON Schema Draft 2020-12 documents into one schema in the current working directory.
- **Schema Unifier Module**: Added `humanitarian_schema_analyzer.schema.unifier.unify_schemas()`, which merges unique properties, deduplicates `required` field names, and combines duplicate field `examples` arrays.
- **Type Conflict Reporting**: When matching property names have different types, the unified schema retains both types as a JSON Schema type array (for example, `["integer", "string"]`) and the CLI prints a highlighted warning.
- **Unifier CLI Tests**: Added `tests/test_unifier.py` covering non-overlapping fields, matching fields with merged examples, and type-conflict resolution through the main Typer application.

### Changed
- **CLI Schema Handling**: Added JSON file validation and clear error messages for missing, unreadable, malformed, or non-object schema files passed to `hds-analyzer unify`.
- **Documentation**: Added `hds-analyzer unify` usage and conflict-resolution behaviour to the README.
- **Unifier Delivery**: Migrated schema unification from the standalone script into the installed `hds-analyzer` CLI and package schema module.

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

## [0.1.1] - 2026-10-12

### Fixed
- **XLSForm Parsing**: Survey questions are extracted as dataset fields.
- **XML Parsing**: Nested elements, repeated tags and attributes are preserved.
- **Schema Builder**: Original input types are preserved, and observed statistics are kept separate from validation constraints.

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
