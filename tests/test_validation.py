"""Comprehensive record validation tests across all fixtures (Task 3).

Verifies that for every fixture file in tests/fixtures/, each parsed record
validates cleanly against the JSON Schema (Draft 2020-12) generated from it.
"""

import os
import pytest
import jsonschema
import pandas as pd

from humanitarian_schema_analyzer.parsers.factory import ParserFactory
from humanitarian_schema_analyzer.profiling.profiler import DataProfiler
from humanitarian_schema_analyzer.schema.schema_builder import SchemaBuilder

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SUPPORTED_FIXTURE_EXTENSIONS = {".csv", ".json", ".xml", ".xls", ".xlsx"}
ALL_FIXTURES = [
    f for f in sorted(os.listdir(FIXTURES_DIR))
    if (
        os.path.isfile(os.path.join(FIXTURES_DIR, f))
        and os.path.splitext(f)[1].lower() in SUPPORTED_FIXTURE_EXTENSIONS
    )
]


@pytest.mark.parametrize("fixture_name", ALL_FIXTURES)
def test_fixture_records_validate_against_generated_schema(fixture_name):
    """For every fixture in tests/fixtures/, check that each parsed record validates against its schema."""
    fixture_path = os.path.join(FIXTURES_DIR, fixture_name)
    assert os.path.exists(fixture_path), f"Fixture not found: {fixture_name}"

    parser = ParserFactory.get_parser(fixture_path)
    parsed = parser.parse()

    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    builder = SchemaBuilder(unified)
    schema = builder.build()

    # Verify that the generated schema adheres to JSON Schema Draft 2020-12
    jsonschema.Draft202012Validator.check_schema(schema)

    # Determine parsed records for validation
    if parsed.metadata and parsed.metadata.get("is_xlsform"):
        # XLSForm represents a questionnaire definition without raw survey responses.
        # Construct a representative response record based on the form questions and choice lists.
        questions = parsed.metadata.get("xlsform_questions", [])
        record = {}
        for q in questions:
            name = q["name"]
            inferred = q.get("inferred_type", "string")
            choices = q.get("choices")
            if choices:
                record[name] = choices[0]
            elif inferred == "integer":
                record[name] = 25
            elif inferred == "number":
                record[name] = 100.0
            elif q.get("is_date"):
                record[name] = "2023-01-01"
            else:
                record[name] = "Sample Respondent"
        records = [record]
    elif parsed.metadata and "records" in parsed.metadata:
        records = parsed.metadata["records"]
    else:
        # Standard tabular DataFrame (CSV, HXL, JSON, Excel):
        # Convert rows to record dictionaries, casting NaNs to None for JSON Schema null compatibility
        clean_df = parsed.df.astype(object).where(pd.notna(parsed.df), None)
        records = clean_df.to_dict(orient="records")

    validator = jsonschema.Draft202012Validator(schema)
    for idx, rec in enumerate(records):
        errors = list(validator.iter_errors(rec))
        assert not errors, (
            f"Fixture '{fixture_name}', record {idx} failed validation:\n"
            f"Record: {rec}\n"
            f"Error: {errors[0].message}"
        )
