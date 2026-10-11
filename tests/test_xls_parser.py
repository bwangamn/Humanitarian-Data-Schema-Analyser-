"""Tests for the XLS/XLSForm parser, end-to-end profiling, and schema generation.

R1 regression tests verify that:
  1.  The XLSForm fixture is recognised and parsed successfully.
  2.  The extracted fields are the five question names, NOT the XLSForm
      template column headings (type, name, label, required, constraint).
  3.  The generated JSON Schema contains the five expected question properties.
  4.  question types are mapped correctly (integer for age, number for
      household_income).
  5.  gender retains its select_one semantics and choice list.
  6.  Requiredness and constraint expressions are preserved in metadata.
  7.  Ordinary Excel parsing remains functional.
  8.  All existing XLSForm tests that were NOT about the defective behaviour
      continue to pass.
"""

import pytest
import os
import openpyxl
import jsonschema

from humanitarian_schema_analyzer.parsers.xls_parser import XLSParser
from humanitarian_schema_analyzer.profiling.profiler import DataProfiler
from humanitarian_schema_analyzer.schema.schema_builder import SchemaBuilder


# ---------------------------------------------------------------------------
# Helper paths
# ---------------------------------------------------------------------------

XLSFORM_FIXTURE = os.path.join("tests", "fixtures", "sample_xlsform.xlsx")
EXCEL_FIXTURE = os.path.join("tests", "fixtures", "sample.xlsx")

# Expected question names in the fixture
EXPECTED_QUESTION_NAMES = {
    "respondent_name",
    "age",
    "household_income",
    "gender",
    "survey_date",
}

# XLSForm template column headings that must NOT appear as schema properties
XLSFORM_TEMPLATE_COLUMNS = {"type", "name", "label", "required", "constraint"}


# ---------------------------------------------------------------------------
# R1-1 / R1-2: Parser recognises XLSForm and extracts question names as columns
# ---------------------------------------------------------------------------

def test_xlsform_parsed_as_xlsform_format():
    """R1-1: XLSForm fixture is parsed as format_name='XLSForm' with is_xlsform=True."""
    assert os.path.exists(XLSFORM_FIXTURE), "XLSForm fixture not found."
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    assert parsed.format_name == "XLSForm"
    assert parsed.metadata["is_xlsform"] is True
    assert parsed.metadata["sheet_name"].lower() == "survey"


def test_xlsform_question_names_are_columns():
    """R1-2a: DataFrame columns are the five question names, not template headings."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    df_columns = set(parsed.df.columns)

    # All five expected question names must be present
    assert EXPECTED_QUESTION_NAMES.issubset(df_columns), (
        f"Missing question columns: {EXPECTED_QUESTION_NAMES - df_columns}"
    )


def test_xlsform_template_headings_not_columns():
    """R1-2b: XLSForm template column headings must NOT be the DataFrame columns.

    This test fails against the old defective behaviour where the parser treated
    the survey worksheet as an ordinary table, making 'type', 'name', etc. the
    dataset fields.
    """
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    df_columns = set(parsed.df.columns)

    overlap = XLSFORM_TEMPLATE_COLUMNS & df_columns
    assert not overlap, (
        f"XLSForm template headings must not appear as dataset columns, but found: {overlap}"
    )


def test_xlsform_question_metadata_stored():
    """R1-2c: xlsform_questions metadata list contains the five expected questions."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    assert "xlsform_questions" in parsed.metadata

    questions = parsed.metadata["xlsform_questions"]
    question_names = {q["name"] for q in questions}
    assert question_names == EXPECTED_QUESTION_NAMES


# ---------------------------------------------------------------------------
# R1-3: Generated JSON Schema contains the five question properties
# ---------------------------------------------------------------------------

def test_xlsform_schema_has_question_properties():
    """R1-3: JSON Schema properties contain the five expected question names."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    props = schema.get("properties", {})
    for name in EXPECTED_QUESTION_NAMES:
        assert name in props, f"Expected property '{name}' missing from JSON Schema."


def test_xlsform_schema_does_not_contain_template_headings():
    """R1-4: JSON Schema must not use template headings as its five main survey properties."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    props = schema.get("properties", {})
    # None of the template column headings should be the *only* top-level properties.
    # (It is acceptable if some coincidentally appear as extension keys, but they
    # must not replace the actual question names.)
    question_props = set(props.keys()) & EXPECTED_QUESTION_NAMES
    assert len(question_props) == 5, (
        f"Expected all 5 question properties in schema, found: {question_props}"
    )

    # Verify that the schema is not the old defective one (where template headings
    # were the only properties).
    template_only = set(props.keys()) == XLSFORM_TEMPLATE_COLUMNS
    assert not template_only, (
        "JSON Schema properties are still the XLSForm template headings, not question names."
    )


# ---------------------------------------------------------------------------
# R1-5: age → integer, household_income → number
# ---------------------------------------------------------------------------

def test_xlsform_age_type_is_integer():
    """R1-5a: 'age' question (XLSForm type 'integer') maps to inferred_type='integer'."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()

    age_col = unified.columns.get("age")
    assert age_col is not None
    assert age_col.inferred_type == "integer", (
        f"Expected 'integer' for 'age', got '{age_col.inferred_type}'"
    )


def test_xlsform_household_income_type_is_number():
    """R1-5b: 'household_income' (XLSForm type 'decimal') maps to inferred_type='number'."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()

    col = unified.columns.get("household_income")
    assert col is not None
    assert col.inferred_type == "number", (
        f"Expected 'number' for 'household_income', got '{col.inferred_type}'"
    )


def test_xlsform_survey_date_type_and_format():
    """survey_date (XLSForm type 'date') maps to inferred_type='string' with format 'date'."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()

    col = unified.columns.get("survey_date")
    assert col is not None
    assert col.inferred_type == "string"
    assert col.is_date is True
    assert col.date_format == "date"


# ---------------------------------------------------------------------------
# R1-6: gender retains select_one semantics and choice list
# ---------------------------------------------------------------------------

def test_xlsform_gender_select_one_semantics():
    """R1-6a: 'gender' question retains select_one semantics and xlsform_type."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()

    col = unified.columns.get("gender")
    assert col is not None
    assert col.xlsform_type is not None
    assert "select_one" in col.xlsform_type.lower()


def test_xlsform_gender_choices_in_profile():
    """R1-6b: 'gender' ColumnProfile contains the three gender choice names."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()

    col = unified.columns.get("gender")
    assert col is not None
    assert col.xlsform_choices is not None
    assert set(col.xlsform_choices) == {"male", "female", "other"}, (
        f"Expected gender choices {{male, female, other}}, got {col.xlsform_choices}"
    )


def test_xlsform_gender_schema_has_enum():
    """R1-6c: JSON Schema for 'gender' includes an enum with the three choices."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    gender_prop = schema["properties"].get("gender", {})
    assert "enum" in gender_prop, "Expected 'enum' key in gender property."
    assert set(gender_prop["enum"]) == {"male", "female", "other"}


# ---------------------------------------------------------------------------
# R1-7: Requiredness and constraint expressions preserved
# ---------------------------------------------------------------------------

def test_xlsform_required_fields_in_schema():
    """R1-7a: Questions marked required=yes appear in JSON Schema 'required' array."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    required = schema.get("required", [])
    # respondent_name, age, gender, survey_date are required=yes in the fixture
    for name in ("respondent_name", "age", "gender", "survey_date"):
        assert name in required, f"Expected '{name}' in schema required array."


def test_xlsform_optional_field_not_required():
    """R1-7b: 'household_income' (required=no) must not appear in schema required array."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    required = schema.get("required", [])
    assert "household_income" not in required, (
        "'household_income' is optional in the XLSForm but was placed in required."
    )


def test_xlsform_constraint_preserved_as_metadata():
    """R1-7c: Constraint expressions are preserved in ColumnProfile and schema extension."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    # age has constraint '. >= 18'
    age_col = unified.columns["age"]
    assert age_col.xlsform_constraint is not None
    assert ">= 18" in age_col.xlsform_constraint

    # household_income has constraint '. >= 0'
    income_col = unified.columns["household_income"]
    assert income_col.xlsform_constraint is not None
    assert ">= 0" in income_col.xlsform_constraint

    # Constraints emitted as x-xlsform-constraint in schema (not as JSON Schema keywords)
    age_prop = schema["properties"]["age"]
    assert "x-xlsform-constraint" in age_prop
    assert ">= 18" in age_prop["x-xlsform-constraint"]

    # Constraint must NOT be enforced as JSON Schema 'minimum' (not safely translatable)
    # (Acceptable if present, but this verifies intent)
    # Note: the schema builder deliberately omits 'minimum' for XLSForm questions.
    assert "minimum" not in age_prop, (
        "XLSForm constraints should not be translated to JSON Schema 'minimum' "
        "because the translation is not guaranteed to be correct."
    )


# ---------------------------------------------------------------------------
# Choices sheet backward compatibility
# ---------------------------------------------------------------------------

def test_xlsform_choices_metadata_present():
    """Choices sheet metadata is accessible in parsed.metadata['choices']."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    assert "choices" in parsed.metadata
    choices = parsed.metadata["choices"]
    assert len(choices) == 3
    gender_names = {c["name"] for c in choices if c.get("list_name") == "gender_list"}
    assert gender_names == {"male", "female", "other"}


# ---------------------------------------------------------------------------
# R1-8: Ordinary Excel parsing unaffected
# ---------------------------------------------------------------------------

def test_xls_parser_standard_excel():
    """R1-8: Standard non-XLSForm Excel workbook parses correctly (regression)."""
    assert os.path.exists(EXCEL_FIXTURE), "Standard Excel fixture not found."
    parsed = XLSParser(EXCEL_FIXTURE).parse()

    assert parsed.format_name == "Excel"
    assert parsed.metadata["is_xlsform"] is False
    assert len(parsed.df) == 3
    assert "district" in parsed.df.columns


def test_xls_parser_standard_excel_no_xlsform_metadata():
    """Ordinary Excel parse must not produce xlsform_questions metadata."""
    parsed = XLSParser(EXCEL_FIXTURE).parse()
    assert "xlsform_questions" not in parsed.metadata


# ---------------------------------------------------------------------------
# End-to-end: JSON Schema Draft 2020-12 compliance
# ---------------------------------------------------------------------------

def test_xlsform_end_to_end_schema_draft_2020_12_valid():
    """End-to-end: generated schema is valid according to JSON Schema Draft 2020-12."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    schema = SchemaBuilder(unified).build()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"
    assert "properties" in schema

    # Validate schema structure against the Draft 2020-12 meta-schema
    jsonschema.Draft202012Validator.check_schema(schema)


def test_xlsform_end_to_end_column_count():
    """End-to-end: profiled schema has exactly 5 question columns."""
    parsed = XLSParser(XLSFORM_FIXTURE).parse()
    unified = DataProfiler(parsed).profile()
    assert unified.column_count == 5


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_xls_parser_file_not_found():
    """FileNotFoundError raised when file does not exist."""
    with pytest.raises(FileNotFoundError):
        XLSParser("non_existent_file.xlsx").parse()
