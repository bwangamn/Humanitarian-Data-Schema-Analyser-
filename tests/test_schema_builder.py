"""Tests for SchemaBuilder and type inference semantics (Task R3).

Verifies:
- Consistency between inferred types, emitted examples, and generated schema.
- Strategy A: preservation of original input types (numeric-looking strings infer
  'string' so raw records validate).
- Actual numeric values infer genuine numeric types and validate.
- Mixed numeric and string representations infer union types and validate.
- Null values and requiredness follow JSON Schema Draft 2020-12 specifications.
- Separation of sample-derived min/max statistics from enforced validation constraints.
- Metaschema validation against Draft 2020-12 meta-schema.
"""

import json
import pytest
import pandas as pd
import jsonschema

from humanitarian_schema_analyzer.parsers.base_parser import ParsedDataset
from humanitarian_schema_analyzer.parsers.json_parser import JSONParser
from humanitarian_schema_analyzer.profiling.profiler import DataProfiler
from humanitarian_schema_analyzer.schema.schema_builder import SchemaBuilder


def test_schema_builder_validation():
    """Verify standard CSV schema generation with required fields and Draft 2020-12 schema."""
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [88.5, 92.0, None]
    })

    parsed = ParsedDataset(df=df, format_name="CSV")
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    builder = SchemaBuilder(unified)
    json_schema = builder.build()

    assert json_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "id" in json_schema["properties"]
    assert "required" in json_schema
    assert "id" in json_schema["required"]
    assert "name" in json_schema["required"]
    assert json_schema["type"] == "object"


# ---------------------------------------------------------------------------
# Test A: Numeric-looking strings (the reviewer's defect)
# ---------------------------------------------------------------------------

def test_numeric_looking_strings_data_validation(tmp_path):
    """Test A: Input containing numeric-looking strings ('10', '20') preserves string type.

    Under Strategy A, the schema defines the property as 'string' so that the
    original input records pass JSON Schema data validation.
    """
    json_content = '[{"amount": "10"}, {"amount": "20"}]'
    json_file = tmp_path / "numeric_strings.json"
    json_file.write_text(json_content, encoding="utf-8")

    parsed = JSONParser(str(json_file)).parse()
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    # Column profile must reflect string type while noting numeric potential in metadata
    amount_col = unified.columns["amount"]
    assert amount_col.inferred_type == "string"
    assert amount_col.is_numeric_string is True
    assert amount_col.potential_type == "integer"

    builder = SchemaBuilder(unified)
    json_schema = builder.build()

    # Schema must specify type "string", not "integer"
    prop = json_schema["properties"]["amount"]
    assert prop["type"] == "string"
    assert prop.get("x-numeric-string") is True

    # Emitted examples must agree with the schema type (strings, not ints)
    assert prop.get("examples") == ["10", "20"]

    # Metaschema validation must pass
    jsonschema.Draft202012Validator.check_schema(json_schema)

    # DATA VALIDATION: Original raw records must satisfy the generated schema!
    raw_records = json.loads(json_content)
    for record in raw_records:
        jsonschema.validate(instance=record, schema=json_schema)

    # Verify original file content was not silently mutated
    assert json_file.read_text(encoding="utf-8") == json_content


# ---------------------------------------------------------------------------
# Test B: Actual numeric values
# ---------------------------------------------------------------------------

def test_actual_numeric_values_data_validation(tmp_path):
    """Test B: Genuine numeric values (10, 20) are typed as integer and validate."""
    json_content = '[{"amount": 10}, {"amount": 20}]'
    json_file = tmp_path / "actual_numbers.json"
    json_file.write_text(json_content, encoding="utf-8")

    parsed = JSONParser(str(json_file)).parse()
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    amount_col = unified.columns["amount"]
    assert amount_col.inferred_type == "integer"

    builder = SchemaBuilder(unified)
    json_schema = builder.build()

    prop = json_schema["properties"]["amount"]
    assert prop["type"] == "integer"
    assert prop["examples"] == [10, 20]

    # Metaschema validation
    jsonschema.Draft202012Validator.check_schema(json_schema)

    # Data validation: original integer records pass
    raw_records = json.loads(json_content)
    for record in raw_records:
        jsonschema.validate(instance=record, schema=json_schema)

    # String input is correctly rejected by genuine integer schema
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance={"amount": "10"}, schema=json_schema)


# ---------------------------------------------------------------------------
# Test C: Mixed numeric and string values
# ---------------------------------------------------------------------------

def test_mixed_numeric_and_string_values(tmp_path):
    """Test C: Mixed values (10 and '20') infer union types and validate both."""
    json_content = '[{"amount": 10}, {"amount": "20"}]'
    json_file = tmp_path / "mixed.json"
    json_file.write_text(json_content, encoding="utf-8")

    parsed = JSONParser(str(json_file)).parse()
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    amount_col = unified.columns["amount"]
    # Inferred type must be a union list containing both types
    assert isinstance(amount_col.inferred_type, list)
    assert set(amount_col.inferred_type) == {"string", "integer"}

    builder = SchemaBuilder(unified)
    json_schema = builder.build()

    prop = json_schema["properties"]["amount"]
    assert set(prop["type"]) == {"string", "integer"}

    # Metaschema validation
    jsonschema.Draft202012Validator.check_schema(json_schema)

    # Data validation: both forms of records pass!
    jsonschema.validate(instance={"amount": 10}, schema=json_schema)
    jsonschema.validate(instance={"amount": "20"}, schema=json_schema)

    # Incompatible types (boolean, array) are rejected
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance={"amount": True}, schema=json_schema)


# ---------------------------------------------------------------------------
# Test D: Null values and requiredness
# ---------------------------------------------------------------------------

def test_null_values_and_requiredness(tmp_path):
    """Test D: Fields with null values become nullable and are not in 'required'."""
    json_content = '[{"id": 1, "note": "available"}, {"id": 2, "note": null}]'
    json_file = tmp_path / "nulls.json"
    json_file.write_text(json_content, encoding="utf-8")

    parsed = JSONParser(str(json_file)).parse()
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    builder = SchemaBuilder(unified)
    json_schema = builder.build()

    # 'id' has no nulls: type is "integer", and must be in required
    assert json_schema["properties"]["id"]["type"] == "integer"
    assert "id" in json_schema.get("required", [])

    # 'note' has nulls: type is ["string", "null"], must NOT be in required
    note_type = json_schema["properties"]["note"]["type"]
    assert isinstance(note_type, list)
    assert set(note_type) == {"string", "null"}
    assert "note" not in json_schema.get("required", [])

    # Metaschema validation
    jsonschema.Draft202012Validator.check_schema(json_schema)

    # Data validation: both records pass
    raw_records = json.loads(json_content)
    for record in raw_records:
        jsonschema.validate(instance=record, schema=json_schema)

    # Missing optional field passes
    jsonschema.validate(instance={"id": 3}, schema=json_schema)

    # Missing required field fails
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance={"note": "missing id"}, schema=json_schema)


# ---------------------------------------------------------------------------
# Test E: Observed minimum and maximum separation
# ---------------------------------------------------------------------------

def test_observed_min_max_separated_from_constraints():
    """Test E: Sample min/max statistics are not automatically emitted as rigid validation constraints."""
    df = pd.DataFrame({"age": [18, 30, 65]})
    parsed = ParsedDataset(df=df, format_name="CSV")
    profiler = DataProfiler(parsed)
    unified = profiler.profile()

    # Observed statistics remain available in the profile
    assert unified.columns["age"].min_value == 18.0
    assert unified.columns["age"].max_value == 65.0

    # Default builder (enforce_observed_ranges=False) must NOT emit minimum/maximum constraints
    default_schema = SchemaBuilder(unified).build()
    age_prop = default_schema["properties"]["age"]
    assert "minimum" not in age_prop, "Observed min must not be emitted as a validation constraint"
    assert "maximum" not in age_prop, "Observed max must not be emitted as a validation constraint"

    # Informational metadata is preserved
    assert age_prop.get("x-observed-minimum") == 18.0
    assert age_prop.get("x-observed-maximum") == 65.0

    # Records outside sample bounds validate successfully
    jsonschema.validate(instance={"age": 10}, schema=default_schema)
    jsonschema.validate(instance={"age": 80}, schema=default_schema)

    # Explicit policy builder (enforce_observed_ranges=True) emits constraints when requested
    enforced_schema = SchemaBuilder(unified, enforce_observed_ranges=True).build()
    assert enforced_schema["properties"]["age"]["minimum"] == 18.0
    assert enforced_schema["properties"]["age"]["maximum"] == 65.0

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance={"age": 10}, schema=enforced_schema)


# ---------------------------------------------------------------------------
# Test F: Schema metaschema validation
# ---------------------------------------------------------------------------

def test_schema_metaschema_validation_all_variants():
    """Test F: Generated schemas for numeric strings, actual numbers, and mixed types pass Draft 2020-12 metaschema."""
    datasets = [
        pd.DataFrame({"amount": ["10", "20"]}),
        pd.DataFrame({"amount": [10, 20]}),
        pd.DataFrame({"amount": [10, "20"]}),
        pd.DataFrame({"amount": [10.5, 20.2]}),
        pd.DataFrame({"amount": [10, None]}),
    ]

    for df in datasets:
        parsed = ParsedDataset(df=df, format_name="JSON")
        unified = DataProfiler(parsed).profile()
        schema = SchemaBuilder(unified).build()

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        # Metaschema validation must succeed
        jsonschema.Draft202012Validator.check_schema(schema)
