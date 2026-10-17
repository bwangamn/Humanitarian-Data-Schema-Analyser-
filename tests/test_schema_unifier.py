"""Tests for the standalone JSON Schema unifier CLI."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from typer.testing import CliRunner

from schema_unifier import app


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
    """Fields unique to either schema are included in the generated file."""
    first = _write_schema(tmp_path / "drc_schema.json", {"cases": {"type": "integer"}}, ["cases"])
    second = _write_schema(tmp_path / "mali_schema.json", {"region": {"type": "string"}}, ["region"])
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "drc_schema_mali_schema_unified.json").read_text(encoding="utf-8"))
    assert set(output["properties"]) == {"cases", "region"}
    assert output["required"] == ["cases", "region"]


def test_unify_matching_fields(tmp_path: Path, monkeypatch: Any) -> None:
    """Same-name fields with matching types retain one field and merged examples."""
    first = _write_schema(tmp_path / "first.json", {"location": {"type": "string", "examples": ["Lusaka"]}}, ["location"])
    second = _write_schema(tmp_path / "second.json", {"location": {"type": "string", "examples": ["Lusaka", "Mansa"]}}, ["location"])
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert output["properties"]["location"] == {"type": "string", "examples": ["Lusaka", "Mansa"]}
    assert output["required"] == ["location"]


def test_unify_type_conflict(tmp_path: Path, monkeypatch: Any) -> None:
    """Same-name fields with differing types retain an ordered type array."""
    first = _write_schema(tmp_path / "first.json", {"cases": {"type": "integer"}})
    second = _write_schema(tmp_path / "second.json", {"cases": {"type": "string"}})
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["unify", str(first), str(second)])

    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "first_second_unified.json").read_text(encoding="utf-8"))
    assert output["properties"]["cases"]["type"] == ["integer", "string"]
    assert "Warning: type mismatch for 'cases'" in result.stderr
