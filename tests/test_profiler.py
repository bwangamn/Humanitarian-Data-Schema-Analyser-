import pandas as pd
from parsers.base_parser import ParsedDataset
from profiling.profiler import DataProfiler


def test_data_profiler():
    df = pd.DataFrame({
        "age": [20, 30, 40, None],
        "city": ["Lusaka", "Ndola", "Lusaka", "Kitwe"],
        "registered": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
    })

    parsed = ParsedDataset(df=df, format_name="CSV", hxl_tags={"age": "#age"})
    profiler = DataProfiler(parsed)
    schema = profiler.profile()

    assert schema.row_count == 4
    assert schema.column_count == 3
    assert schema.columns["age"].missing_count == 1
    assert schema.columns["age"].missing_percentage == 25.0
    assert schema.columns["age"].min_value == 20.0
    assert schema.columns["age"].max_value == 40.0
    assert schema.columns["registered"].is_date is True
    assert schema.columns["age"].hxl_tag == "#age"
