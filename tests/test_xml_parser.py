import pytest
from parsers.xml_parser import XMLParser


def test_xml_parser(tmp_path):
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<root><item><name>Alpha</name><qty>10</qty></item><item><name>Beta</name><qty>20</qty></item></root>")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()

    assert "XML" in parsed.format_name
    assert len(parsed.df) == 2
    assert "name" in parsed.df.columns
