import pytest
from parsers.json_parser import JSONParser


def test_json_parser_list(tmp_path):
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"id": 1, "name": "Item A"}, {"id": 2, "name": "Item B"}]')

    parser = JSONParser(str(json_file))
    parsed = parser.parse()

    assert parsed.format_name == "JSON"
    assert len(parsed.df) == 2
    assert "id" in parsed.df.columns


def test_json_parser_wrapped(tmp_path):
    json_file = tmp_path / "wrapped.json"
    json_file.write_text('{"data": [{"id": 10, "val": 99.5}]}')

    parser = JSONParser(str(json_file))
    parsed = parser.parse()

    assert len(parsed.df) == 1
    assert parsed.df.iloc[0]["id"] == 10
