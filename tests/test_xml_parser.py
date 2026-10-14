import os
import pytest
import jsonschema
from humanitarian_schema_analyzer.parsers.xml_parser import XMLParser, XMLNode
from humanitarian_schema_analyzer.profiling.profiler import DataProfiler
from humanitarian_schema_analyzer.schema.schema_builder import SchemaBuilder


# ---------------------------------------------------------------------------
# 8. Backward compatibility: existing XML tests and standard XML fixture
# ---------------------------------------------------------------------------

def test_xml_parser(tmp_path):
    """Preserve existing test: verify flat repeated items parse correctly."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<root><item><name>Alpha</name><qty>10</qty></item><item><name>Beta</name><qty>20</qty></item></root>")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()

    assert "XML" in parsed.format_name
    assert len(parsed.df) == 2
    assert "name" in parsed.df.columns


def test_xml_parser_sample_fixture():
    """Verify standard sample.xml parses into expected rows and columns."""
    fixture_path = os.path.join("tests", "fixtures", "sample.xml")
    assert os.path.exists(fixture_path), "sample.xml fixture not found."

    parser = XMLParser(fixture_path)
    parsed = parser.parse()

    assert "XML" in parsed.format_name
    assert len(parsed.df) == 2
    assert "title" in parsed.df.columns
    assert "budget" in parsed.df.columns
    assert parsed.df.iloc[0]["title"] == "Nutrition Intervention Program"
    assert parsed.df.iloc[1]["title"] == "Child Protection and Education"


# ---------------------------------------------------------------------------
# 1-4. Reviewer IATI example: nested narrative, repeated transactions, values, attributes
# ---------------------------------------------------------------------------

def test_xml_parser_nested_title_narrative(tmp_path):
    """Requirement 1: Title with nested narrative retains 'Flood response' (not None)."""
    xml_content = """<iati-activities>
        <iati-activity>
            <title>
                <narrative>Flood response</narrative>
            </title>
            <transaction>
                <value currency="USD">100</value>
            </transaction>
            <transaction>
                <value currency="USD">200</value>
            </transaction>
        </iati-activity>
    </iati-activities>"""
    xml_file = tmp_path / "iati_single.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()

    assert len(parsed.df) == 1
    row = parsed.df.iloc[0]

    # Nested title narrative must not be None
    assert row["title"] is not None
    # Access via nested dictionary key 'narrative'
    assert row["title"]["narrative"] == "Flood response"
    # Access via string representation / equality comparison
    assert row["title"] == "Flood response"
    assert "Flood response" in str(row["title"])


def test_xml_parser_repeated_transactions_distinct(tmp_path):
    """Requirement 2: Both transaction elements survive as distinct entries (not overwritten)."""
    xml_content = """<iati-activities>
        <iati-activity>
            <title><narrative>Flood response</narrative></title>
            <transaction>
                <value currency="USD">100</value>
            </transaction>
            <transaction>
                <value currency="USD">200</value>
            </transaction>
        </iati-activity>
    </iati-activities>"""
    xml_file = tmp_path / "iati_tx.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()
    row = parsed.df.iloc[0]

    transactions = row["transaction"]
    assert isinstance(transactions, list), "Repeated <transaction> elements must be represented as a list."
    assert len(transactions) == 2, f"Expected 2 transactions, got {len(transactions)}"


def test_xml_parser_transaction_values_retained(tmp_path):
    """Requirement 3: Values 100 and 200 are retained and associated with correct transactions."""
    xml_content = """<iati-activities>
        <iati-activity>
            <title><narrative>Flood response</narrative></title>
            <transaction>
                <value currency="USD">100</value>
            </transaction>
            <transaction>
                <value currency="USD">200</value>
            </transaction>
        </iati-activity>
    </iati-activities>"""
    xml_file = tmp_path / "iati_values.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()
    transactions = parsed.df.iloc[0]["transaction"]

    tx1, tx2 = transactions[0], transactions[1]

    # Check text value access via '#text', 'value', or scalar comparison
    assert tx1["value"]["#text"] == "100"
    assert tx1["value"]["value"] == "100"
    assert tx1["value"] == 100

    assert tx2["value"]["#text"] == "200"
    assert tx2["value"]["value"] == "200"
    assert tx2["value"] == 200


def test_xml_parser_attributes_preserved(tmp_path):
    """Requirement 4: Each transaction's currency attribute is preserved as 'USD'."""
    xml_content = """<iati-activities>
        <iati-activity>
            <transaction>
                <value currency="USD">100</value>
            </transaction>
            <transaction>
                <value currency="USD">200</value>
            </transaction>
        </iati-activity>
    </iati-activities>"""
    xml_file = tmp_path / "iati_attribs.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()
    transactions = parsed.df.iloc[0]["transaction"]

    for tx in transactions:
        val = tx["value"]
        # Attributes are accessible via '@currency' and 'currency'
        assert val["@currency"] == "USD"
        assert val["currency"] == "USD"
        assert val.get("@currency") == "USD"
        assert val.get("currency") == "USD"


# ---------------------------------------------------------------------------
# 5. Multiple activities in the same document
# ---------------------------------------------------------------------------

def test_xml_parser_multiple_activities_distinct():
    """Requirement 5: Two activities remain distinct records with their own transactions."""
    fixture_path = os.path.join("tests", "fixtures", "sample_iati.xml")
    assert os.path.exists(fixture_path), "sample_iati.xml fixture not found."

    parser = XMLParser(fixture_path)
    parsed = parser.parse()

    assert len(parsed.df) == 2, "Document with 2 activities must yield exactly 2 records."

    act1 = parsed.df.iloc[0]
    act2 = parsed.df.iloc[1]

    # Activity 1: XM-DAC-001, Flood response, 2 USD transactions (100, 200)
    assert act1["iati-identifier"] == "XM-DAC-001"
    assert act1["title"]["narrative"] == "Flood response"
    assert isinstance(act1["transaction"], list)
    assert len(act1["transaction"]) == 2
    assert act1["transaction"][0]["value"] == 100
    assert act1["transaction"][0]["value"]["currency"] == "USD"
    assert act1["transaction"][1]["value"] == 200
    assert act1["transaction"][1]["value"]["currency"] == "USD"

    # Activity 2: XM-DAC-002, Emergency shelter support, 1 EUR transaction (500)
    assert act2["iati-identifier"] == "XM-DAC-002"
    assert act2["title"]["narrative"] == "Emergency shelter support"
    # Single transaction in activity 2
    tx2 = act2["transaction"]
    if isinstance(tx2, list):
        assert len(tx2) == 1
        tx2_val = tx2[0]["value"]
    else:
        tx2_val = tx2["value"]
    assert tx2_val == 500
    assert tx2_val["currency"] == "EUR"


# ---------------------------------------------------------------------------
# 6. Arbitrary nesting unrelated to IATI tag names
# ---------------------------------------------------------------------------

def test_xml_parser_arbitrary_nesting(tmp_path):
    """Requirement 6: Generic XML with deep arbitrary nesting parses correctly."""
    xml_content = """<humanitarian-clusters>
        <cluster code="WASH">
            <lead>
                <agency id="UNICEF">
                    <contact>
                        <email>wash@unicef.org</email>
                    </contact>
                </agency>
            </lead>
            <indicator unit="percent">85</indicator>
        </cluster>
    </humanitarian-clusters>"""
    xml_file = tmp_path / "clusters.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()

    assert len(parsed.df) == 1
    row = parsed.df.iloc[0]

    assert row["@code"] == "WASH"
    assert row["lead"]["agency"]["@id"] == "UNICEF"
    assert row["lead"]["agency"]["contact"]["email"] == "wash@unicef.org"
    assert row["indicator"]["@unit"] == "percent"
    assert row["indicator"]["#text"] == "85"
    assert row["indicator"] == 85


# ---------------------------------------------------------------------------
# 7. Single occurrence elements representation
# ---------------------------------------------------------------------------

def test_xml_parser_single_occurrence_representation(tmp_path):
    """Requirement 7: Single elements remain scalars or structured objects (not lists)."""
    xml_content = """<records>
        <record>
            <single_text>Only One</single_text>
            <single_nested><subfield>Inner</subfield></single_nested>
        </record>
    </records>"""
    xml_file = tmp_path / "single.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parser = XMLParser(str(xml_file))
    parsed = parser.parse()
    row = parsed.df.iloc[0]

    # Leaf without attributes is a scalar string
    assert isinstance(row["single_text"], str)
    assert row["single_text"] == "Only One"

    # Single nested structure is an XMLNode/dict, NOT wrapped in a list
    assert isinstance(row["single_nested"], dict)
    assert not isinstance(row["single_nested"], list)
    assert row["single_nested"]["subfield"] == "Inner"


# ---------------------------------------------------------------------------
# 9. Pipeline integration: Profiling and JSON Schema generation
# ---------------------------------------------------------------------------

def test_xml_parser_pipeline_profiling_and_schema():
    """Requirement 9: Parsed XML with nested/repeated elements profiles and generates JSON Schema."""
    fixture_path = os.path.join("tests", "fixtures", "sample_iati.xml")
    parsed = XMLParser(fixture_path).parse()

    profiler = DataProfiler(parsed)
    schema = profiler.profile()

    assert schema.row_count == 2
    assert "title" in schema.columns
    assert "transaction" in schema.columns

    # Check inferred types for complex columns
    assert schema.columns["title"].inferred_type == "object"
    assert schema.columns["transaction"].inferred_type in ("array", "object")

    # Generate JSON Schema Draft 2020-12
    builder = SchemaBuilder(schema)
    json_schema = builder.build()

    # Meta-schema validation
    jsonschema.Draft202012Validator.check_schema(json_schema)
    assert json_schema["type"] == "object"
    assert "properties" in json_schema
    assert "title" in json_schema["properties"]
    assert "transaction" in json_schema["properties"]

    # Nested values represented with inner properties
    title_prop = json_schema["properties"]["title"]
    assert "properties" in title_prop
    assert "narrative" in title_prop["properties"]
    assert title_prop["properties"]["narrative"]["type"] == "string"

    tx_prop = json_schema["properties"]["transaction"]
    assert tx_prop["type"] == "array"
    assert "items" in tx_prop
    assert "properties" in tx_prop["items"]
    assert "value" in tx_prop["items"]["properties"]
    assert "properties" in tx_prop["items"]["properties"]["value"]
    assert "@currency" in tx_prop["items"]["properties"]["value"]["properties"]
    assert "#text" in tx_prop["items"]["properties"]["value"]["properties"]

    # Data validation: both activities validate against the generated schema
    for record in parsed.metadata["records"]:
        jsonschema.validate(instance=record, schema=json_schema)


def test_xml_parser_single_transaction_normalized_to_array(tmp_path):
    """Verify that a single occurrence of a repeated element (<transaction>) is normalized to an array."""
    xml_content = """<iati-activities>
        <iati-activity>
            <iati-identifier>TEST-001</iati-identifier>
            <transaction>
                <value currency="USD">750</value>
            </transaction>
        </iati-activity>
    </iati-activities>"""
    xml_file = tmp_path / "single_tx.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parsed = XMLParser(str(xml_file)).parse()
    row = parsed.df.iloc[0]

    # Single transaction must be normalized to a list (array)
    assert isinstance(row["transaction"], list)
    assert len(row["transaction"]) == 1
    assert row["transaction"][0]["value"] == 750

    profiler = DataProfiler(parsed)
    schema = profiler.profile()
    assert schema.columns["transaction"].inferred_type == "array"

    builder = SchemaBuilder(schema)
    json_schema = builder.build()
    jsonschema.Draft202012Validator.check_schema(json_schema)
    assert json_schema["properties"]["transaction"]["type"] == "array"
    assert "items" in json_schema["properties"]["transaction"]

    # Verify record validates against generated schema
    jsonschema.validate(instance=parsed.metadata["records"][0], schema=json_schema)



# ---------------------------------------------------------------------------
# 10. Malformed or missing XML error handling
# ---------------------------------------------------------------------------

def test_xml_parser_file_not_found():
    """Requirement 10a: FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError):
        XMLParser("non_existent_file.xml").parse()


def test_xml_parser_invalid_syntax(tmp_path):
    """Requirement 10b: ValueError with clear syntax message for invalid XML."""
    bad_xml = tmp_path / "bad.xml"
    bad_xml.write_text("<root><unclosed></root>", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid XML syntax"):
        XMLParser(str(bad_xml)).parse()


def test_xml_parser_empty_xml(tmp_path):
    """Requirement 10c: ValueError when XML has no records."""
    empty_xml = tmp_path / "empty.xml"
    empty_xml.write_text("<root></root>", encoding="utf-8")

    with pytest.raises(ValueError, match="contains no record elements"):
        XMLParser(str(empty_xml)).parse()
