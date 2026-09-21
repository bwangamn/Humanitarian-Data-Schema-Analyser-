import pytest
import os
import openpyxl
from parsers.xls_parser import XLSParser
from profiling.profiler import DataProfiler
from schema.schema_builder import SchemaBuilder
import jsonschema


def test_xls_parser_survey_and_choices():
    """Verify that XLSParser correctly identifies XLSForm survey and choices sheets

    and extracts expected field metadata.
    """
    fixture_path = os.path.join("tests", "fixtures", "sample_xlsform.xlsx")
    assert os.path.exists(fixture_path), "XLSForm fixture file not found."

    parser = XLSParser(fixture_path)
    parsed = parser.parse()

    assert parsed.format_name == "XLSForm"
    assert parsed.metadata["is_xlsform"] is True
    assert parsed.metadata["sheet_name"].lower() == "survey"
    assert "choices" in parsed.metadata

    # Verify extracted field names in survey dataframe
    expected_fields = {"type", "name", "label", "required", "constraint"}
    assert expected_fields.issubset(set(parsed.df.columns))

    # Verify rows in survey sheet
    assert len(parsed.df) == 5
    field_names = list(parsed.df["name"])
    assert "respondent_name" in field_names
    assert "age" in field_names
    assert "household_income" in field_names
    assert "gender" in field_names
    assert "survey_date" in field_names

    # Verify choices sheet metadata
    choices = parsed.metadata["choices"]
    assert len(choices) == 3
    gender_choices = [c["name"] for c in choices if c["list_name"] == "gender_list"]
    assert set(gender_choices) == {"male", "female", "other"}


def test_xls_parser_end_to_end_profiling_and_schema():
    """Verify end-to-end profiling and JSON Schema generation for an XLSForm workbook."""
    fixture_path = os.path.join("data", "sample_xlsform.xlsx")
    parsed = XLSParser(fixture_path).parse()

    profiler = DataProfiler(parsed)
    unified_schema = profiler.profile()

    assert unified_schema.format_name == "XLSForm"
    assert unified_schema.column_count == len(parsed.df.columns)
    assert unified_schema.row_count == len(parsed.df)

    # Build JSON Schema & validate Draft 2020-12 compliance
    schema_builder = SchemaBuilder(unified_schema)
    json_schema = schema_builder.build()

    jsonschema.Draft202012Validator.check_schema(json_schema)
    assert json_schema["type"] == "object"
    assert "properties" in json_schema


def test_xls_parser_file_not_found():
    """Verify FileNotFoundError handling when file does not exist."""
    with pytest.raises(FileNotFoundError):
        XLSParser("non_existent_file.xlsx").parse()
