# Evaluation Plan: Humanitarian Data Schema Analyser

## 1. Overview
This evaluation plan outlines the formal procedures, metrics, and target benchmarks used to validate the performance, accuracy, and completeness of the **Humanitarian Data Schema Analyser**. Grounded directly in Section 3.3 of the project proposal (*Evaluation Criteria*), this framework evaluates the core parsing engine, data profiler, unified schema representation model, JSON schema generator, report generator, and CLI interface using objective quantitative criteria.

---

## 2. Evaluation Criteria

The quantitative evaluation framework relies on 5 primary metrics defined prior to system benchmarking:

| Criterion | Description | Mathematical Formula | Target Benchmark |
| :--- | :--- | :--- | :--- |
| **Parser Success Rate** | Percentage of valid evaluation files successfully parsed for each supported format (CSV, HXL-CSV, JSON, XML, XLSForm) | $\frac{\text{Successfully Processed Files}}{\text{Total Evaluated Files}} \times 100\%$ | $\ge 95\%$ |
| **Field Extraction Accuracy** | Percentage of fields in dataset correctly detected relative to manually verified ground-truth schemas | $\frac{\text{Correctly Extracted Fields}}{\text{Total Ground-Truth Fields}} \times 100\%$ | $\ge 95\%$ |
| **Type Inference Accuracy** | Percentage of fields whose inferred primitive type matches the expected ground-truth type | $\frac{\text{Correctly Inferred Field Types}}{\text{Total Evaluated Fields}} \times 100\%$ | $\ge 90\%$ |
| **JSON Schema Validity** | Percentage of generated schema files that validate cleanly against JSON Schema Draft 2020-12 | $\frac{\text{Valid Draft 2020-12 Schemas}}{\text{Total Generated Schemas}} \times 100\%$ | $100\%$ |
| **Automated Test Pass Rate** | Percentage of automated unit, integration, and parser regression tests passing cleanly | $\frac{\text{Passed Automated Tests}}{\text{Total Executed Tests}} \times 100\%$ | $100\%$ (Critical Path) |

### Rationale for Thresholds
- **Parser Success Rate ($\ge 95\%$)**: Ensures high operational robustness across heterogeneous data collection exports without crashing on non-standard formatting.
- **Field Extraction Accuracy ($\ge 95\%$)**: Guarantees high structural coverage so downstream data integration pipelines do not suffer missing fields.
- **Type Inference Accuracy ($\ge 90\%$)**: Accounts for ambiguous string-encoded data in field datasets while maintaining reliable primitive type mapping (`integer`, `number`, `boolean`, `date`, `string`).
- **JSON Schema Validity ($100\%$)**: Strict requirement ensuring zero syntactical or structural schema errors for machine-to-machine integration.
- **Automated Test Pass Rate ($100\%$ Critical Path)**: Ensures zero regression across core parser, profiling, schema builder, and CLI workflows.

---

## 3. Evaluation Methodologies & Protocols

### 3.1 Ground-Truth Preparation
Ground-truth schemas are constructed for representative sample datasets across all supported formats:
- **CSV**: Standard comma-separated files.
- **HXL-CSV**: Tabular CSV datasets embedded with HXL hashtag lines (`#affected+f+num`, `#adm1+name`).
- **JSON**: Single objects, object arrays, and nested metadata blocks.
- **XML**: XForms instances and IATI activity metadata.
- **XLSForm**: Excel workbooks containing `survey` and `choices` sheets.

### 3.2 Evaluation Execution Protocol
1. **Parsing Verification**: Execute parser on each evaluation dataset. Record success/failure status.
2. **Field Extraction Audit**: Compare extracted column names against ground-truth schema fields.
3. **Type Inference Audit**: Compare inferred primitive types (`integer`, `number`, `boolean`, `string`) against ground-truth field types.
4. **Schema Validation Suite**: Pass every generated JSON Schema output to `jsonschema.Draft202012Validator.check_schema()`.
5. **CLI & Pipeline Testing**: Execute end-to-end CLI commands verifying exit codes and output file integrity.

---

## 4. Test Environment & Automation

- **Testing Framework**: `pytest`
- **Execution Command**:
  ```bash
  pytest --verbose tests/
  ```
- **Evaluation Benchmark Datasets**: Sourced from HDX (Humanitarian Data Exchange: `https://data.humdata.org`), IATI Registry samples, ODK form templates, and synthetic edge-case fixtures.
