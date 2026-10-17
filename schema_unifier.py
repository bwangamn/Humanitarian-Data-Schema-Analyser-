"""Command-line utility for combining two JSON Schema documents.

Run ``python schema_unifier.py unify schema1.json schema2.json`` to write a
combined schema into the current working directory.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer


app = typer.Typer(help="Combine the properties and required fields of JSON Schemas.")


@app.callback()
def main() -> None:
    """Provide the ``unify`` command namespace."""


def _unique_values(values: Sequence[Any]) -> List[Any]:
    """Return JSON-compatible values in first-seen order without duplicates."""
    unique: List[Any] = []
    for value in values:
        if value not in unique:
            unique.append(copy.deepcopy(value))
    return unique


def _type_values(schema_type: Any) -> List[Any]:
    """Normalize a JSON Schema type declaration to an ordered list."""
    return list(schema_type) if isinstance(schema_type, list) else [schema_type]


def load_schema(path: Path) -> Dict[str, Any]:
    """Load and validate the portions of a JSON Schema used by the unifier."""
    if not path.is_file():
        raise FileNotFoundError(f"Schema file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in '{path}': {error.msg}") from error
    except OSError as error:
        raise OSError(f"Could not read schema file '{path}': {error}") from error

    if not isinstance(schema, dict):
        raise ValueError(f"Schema '{path}' must contain a JSON object.")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError(f"Schema '{path}' has a non-object 'properties' section.")

    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(name, str) for name in required):
        raise ValueError(f"Schema '{path}' has an invalid 'required' section; it must be an array of names.")

    return schema


def _merge_property(
    field_name: str, first: Mapping[str, Any], second: Mapping[str, Any]
) -> tuple[Dict[str, Any], bool]:
    """Merge two same-named property definitions and flag type conflicts."""
    merged = copy.deepcopy(dict(first))
    first_type = first.get("type")
    second_type = second.get("type")
    type_conflict = first_type != second_type

    if type_conflict:
        merged["type"] = _unique_values(_type_values(first_type) + _type_values(second_type))

    # Preserve schema details from the first input, while retaining details only
    # supplied by the second input. Examples are the one explicitly combined key.
    for key, value in second.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)

    examples = _unique_values(
        list(first.get("examples", [])) + list(second.get("examples", []))
    )
    if examples:
        merged["examples"] = examples

    return merged, type_conflict


def unify_schemas(schema1: Mapping[str, Any], schema2: Mapping[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """Combine schema properties and required names, returning conflicting fields."""
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})
    if not isinstance(properties1, Mapping) or not isinstance(properties2, Mapping):
        raise ValueError("Both schemas must have an object 'properties' section.")

    unified_properties: Dict[str, Any] = copy.deepcopy(dict(properties1))
    conflicts: List[str] = []
    for field_name, second_property in properties2.items():
        if not isinstance(second_property, Mapping):
            raise ValueError(f"Property '{field_name}' must be a JSON object.")
        if field_name not in unified_properties:
            unified_properties[field_name] = copy.deepcopy(second_property)
            continue

        first_property = unified_properties[field_name]
        if not isinstance(first_property, Mapping):
            raise ValueError(f"Property '{field_name}' must be a JSON object.")
        merged_property, has_conflict = _merge_property(field_name, first_property, second_property)
        unified_properties[field_name] = merged_property
        if has_conflict:
            conflicts.append(field_name)

    required1 = schema1.get("required", [])
    required2 = schema2.get("required", [])
    if not isinstance(required1, list) or not isinstance(required2, list):
        raise ValueError("Both schemas must have an array 'required' section.")

    return {
        "$schema": schema1.get("$schema", schema2.get("$schema", "https://json-schema.org/draft/2020-12/schema")),
        "type": "object",
        "properties": unified_properties,
        "required": _unique_values(required1 + required2),
    }, conflicts


@app.command()
def unify(
    schema1_path: Path = typer.Argument(..., help="Path to the first JSON Schema file."),
    schema2_path: Path = typer.Argument(..., help="Path to the second JSON Schema file."),
) -> None:
    """Create a unified JSON Schema from two input schema files."""
    try:
        schema1 = load_schema(schema1_path)
        schema2 = load_schema(schema2_path)
        unified_schema, conflicts = unify_schemas(schema1, schema2)

        output_path = Path.cwd() / f"{schema1_path.stem}_{schema2_path.stem}_unified.json"
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(unified_schema, output_file, indent=2)
            output_file.write("\n")

        for field_name in conflicts:
            typer.echo(
                f"Warning: type mismatch for '{field_name}'; retained both types in the unified schema.",
                err=True,
            )
        typer.echo(f"Unified schema saved to: {output_path}")
    except (FileNotFoundError, OSError, ValueError, TypeError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


if __name__ == "__main__":
    app()
