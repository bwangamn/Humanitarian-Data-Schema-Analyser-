import pytest
import os
from parsers.csv_parser import CSVParser
from profiling.profiler import DataProfiler


def test_hxl_vs_csv_type_inference_consistency():
    """Verify that equivalent CSV and HXL-CSV datasets infer identical primitive field types

    while HXL-CSV retains HXL semantic metadata.
    """
    csv_path = os.path.join("data", "sample.csv")
    hxl_path = os.path.join("data", "sample_hxl.csv")

    assert os.path.exists(csv_path), "sample.csv missing from data/"
    assert os.path.exists(hxl_path), "sample_hxl.csv missing from data/"

    parsed_csv = CSVParser(csv_path).parse()
    profile_csv = DataProfiler(parsed_csv).profile()

    parsed_hxl = CSVParser(hxl_path).parse()
    profile_hxl = DataProfiler(parsed_hxl).profile()

    # Column sets should be identical
    assert set(profile_csv.columns.keys()) == set(profile_hxl.columns.keys())

    # Dynamically verify each column without hardcoding specific column names
    for col_name, col_csv in profile_csv.columns.items():
        col_hxl = profile_hxl.columns[col_name]

        # Primitive type inference must be identical
        assert col_csv.inferred_type == col_hxl.inferred_type, (
            f"Type mismatch for column '{col_name}': "
            f"CSV inferred '{col_csv.inferred_type}' vs HXL inferred '{col_hxl.inferred_type}'"
        )

        # Row counts must match
        assert profile_csv.row_count == profile_hxl.row_count

        # Missing counts must match
        assert col_csv.missing_count == col_hxl.missing_count

    # HXL dataset must retain HXL semantic tags
    assert len(parsed_hxl.hxl_tags) > 0
    assert any(tag.startswith('#') for tag in parsed_hxl.hxl_tags.values())
