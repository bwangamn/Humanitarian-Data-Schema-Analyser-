import pytest
from parsers.csv_parser import CSVParser


def test_csv_parser_standard(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,age\n1,Alice,30\n2,Bob,25\n")

    parser = CSVParser(str(csv_file))
    parsed = parser.parse()

    assert parsed.format_name == "CSV"
    assert len(parsed.df) == 2
    assert list(parsed.df.columns) == ["id", "name", "age"]
    assert len(parsed.hxl_tags) == 0


def test_csv_parser_hxl(tmp_path):
    csv_file = tmp_path / "hxl_test.csv"
    csv_file.write_text("id,name,age\n#sub-id,#name,#age\n1,Alice,30\n2,Bob,25\n")

    parser = CSVParser(str(csv_file))
    parsed = parser.parse()

    assert parsed.format_name == "HXL-CSV"
    assert len(parsed.df) == 2
    assert parsed.hxl_tags == {"id": "#sub-id", "name": "#name", "age": "#age"}


def test_csv_parser_file_not_found():
    parser = CSVParser("non_existent_file.csv")
    with pytest.raises(FileNotFoundError):
        parser.parse()
