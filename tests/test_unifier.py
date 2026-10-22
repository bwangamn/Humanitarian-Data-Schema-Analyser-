"""Tests for the ``hds-analyzer unify`` command."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from typer.testing import CliRunner

from humanitarian_schema_analyzer.cli.main import app


runner = CliRunner()


def _write_schema(
    path: Path, properties: Dict[str, Dict[str, Any]], required: Optional[List[str]] = None
) -> Path:
    """Write a minimal JSON Schema fixture and return its path."""
    path.write_text(
        json.dumps({"type": "object", "properties": properties, "required": required or []}),
        encoding="utf-8",
    )
    return path


def test_unify_successful_merge(tmp_path: Path, monkeypatch: Any) -> None:
    """Unique fields from both input schemas appear in the output schema as optional fields."""
    first = _write_schema(
        tmp_path / "drc_schema.json", {"cases": {"type": "integer"}}, ["cases"]
    )
    second = _write_schema(
        tmp_path / "mali_schema.json", {"region": {"type": "string"}}, ["region"]
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output_path = tmp_path / "drc_schema_mali_schema_unified.json"
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert set(output["properties"]) == {"cases", "region"}
    # "cases" and "region" are each required by only one schema, so neither stays required.
    assert output["required"] == []


def test_unify_matching_fields(tmp_path: Path, monkeypatch: Any) -> None:
    """Matching field types retain one field with deduplicated examples."""
    first = _write_schema(
        tmp_path / "first.json",
        {"location": {"type": "string", "examples": ["Lusaka"]}},
        ["location"],
    )
    second = _write_schema(
        tmp_path / "second.json",
        {"location": {"type": "string", "examples": ["Lusaka", "Mansa"]}},
        ["location"],
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert output["properties"]["location"] == {
        "type": "string",
        "examples": ["Lusaka", "Mansa"],
    }
    assert output["required"] == ["location"]


def test_unify_type_conflict(tmp_path: Path, monkeypatch: Any) -> None:
    """Conflicting field types are represented by one ordered type array."""
    first = _write_schema(tmp_path / "first.json", {"cases": {"type": "integer"}})
    second = _write_schema(tmp_path / "second.json", {"cases": {"type": "string"}})
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert output["properties"]["cases"]["type"] == ["integer", "string"]
    assert "Warning: Field 'cases' has conflicting types" in result.stderr


def test_unify_mapping_merges_renamed_fields(tmp_path: Path, monkeypatch: Any) -> None:
    """A mapping file merges fields with different names into one field."""
    first = _write_schema(
        tmp_path / "first.json",
        {"age": {"type": "integer", "examples": [4]}, "region": {"type": "string"}},
    )
    second = _write_schema(
        tmp_path / "second.json",
        {"child_age": {"type": "integer", "examples": [7]}, "district": {"type": "string"}},
    )
    mapping = tmp_path / "mapping.csv"
    mapping.write_text("schema1_field,schema2_field\nage,child_age\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second), "--mapping", str(mapping)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert set(output["properties"]) == {"age", "region", "district"}
    assert output["properties"]["age"]["examples"] == [4, 7]


def test_unify_without_mapping_keeps_renamed_fields_separate(tmp_path: Path, monkeypatch: Any) -> None:
    """Without a mapping, only identical names are merged."""
    first = _write_schema(tmp_path / "first.json", {"age": {"type": "integer"}})
    second = _write_schema(tmp_path / "second.json", {"child_age": {"type": "integer"}})
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert set(output["properties"]) == {"age", "child_age"}


def test_unify_required_is_intersection(tmp_path: Path, monkeypatch: Any) -> None:
    """Only fields required by both schemas stay required, so either dataset still validates."""
    from jsonschema import Draft202012Validator

    first = _write_schema(
        tmp_path / "first.json",
        {"age": {"type": "integer"}, "region": {"type": "string"}},
        ["age", "region"],
    )
    second = _write_schema(
        tmp_path / "second.json",
        {"child_age": {"type": "integer"}, "district": {"type": "string"}},
        ["child_age", "district"],
    )
    mapping = tmp_path / "mapping.csv"
    mapping.write_text("age,child_age\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second), "-m", str(mapping)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert output["required"] == ["age"]
    validator = Draft202012Validator(output)
    assert validator.is_valid({"age": 5, "region": "Ituri"})
    assert validator.is_valid({"age": 7, "district": "Bunia"})


def test_unify_mapping_warns_for_unknown_field(tmp_path: Path, monkeypatch: Any) -> None:
    """A mapping row naming a field that is not in the second schema is reported."""
    first = _write_schema(tmp_path / "first.json", {"age": {"type": "integer"}})
    second = _write_schema(tmp_path / "second.json", {"child_age": {"type": "integer"}})
    mapping = tmp_path / "mapping.csv"
    mapping.write_text("age,child_age\nregion,missing_field\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second), "-m", str(mapping)])

    assert result.exit_code == 0, result.output
    assert "Mapping ignored" in result.output


def test_unify_rejects_malformed_mapping(tmp_path: Path, monkeypatch: Any) -> None:
    """A mapping row without exactly two columns stops the command with an error."""
    first = _write_schema(tmp_path / "first.json", {"age": {"type": "integer"}})
    second = _write_schema(tmp_path / "second.json", {"child_age": {"type": "integer"}})
    mapping = tmp_path / "mapping.csv"
    mapping.write_text("age,child_age,extra\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second), "-m", str(mapping)])

    assert result.exit_code == 1
    assert "two non-empty columns" in result.output
