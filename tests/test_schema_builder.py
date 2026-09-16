import pandas as pd
import jsonschema
from parsers.base_parser import ParsedDataset
from profiling.profiler import DataProfiler
from schema.schema_builder import SchemaBuilder


def test_schema_builder_validation():
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

    # Validate schema itself against Draft 2020-12 meta-schema or check valid structure
    assert json_schema["type"] == "object"
