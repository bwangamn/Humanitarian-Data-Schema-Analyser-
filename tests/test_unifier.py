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
    """Unique fields from both input schemas appear in the output schema."""
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
    assert output["required"] == ["cases", "region"]


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
