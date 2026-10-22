"""Utilities for combining JSON Schema Draft 2020-12 documents."""

from __future__ import annotations

import copy
import csv
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union


DEFAULT_DRAFT_2020_12_SCHEMA = "https://json-schema.org/draft/2020-12/schema"


def _unique_values(values: Sequence[Any]) -> List[Any]:
    """Return values in their original order with duplicates removed."""
    unique: List[Any] = []
    for value in values:
        if value not in unique:
            unique.append(copy.deepcopy(value))
    return unique


def _normalise_types(schema_type: Any) -> List[Any]:
    """Represent a JSON Schema type declaration as a list."""
    return list(schema_type) if isinstance(schema_type, list) else [schema_type]


def _merge_property(
    field_name: str, first_property: Mapping[str, Any], second_property: Mapping[str, Any]
) -> Tuple[Dict[str, Any], str | None]:
    """Merge two definitions for one field and report a type conflict, if any."""
    merged_property = copy.deepcopy(dict(first_property))
    first_type = first_property.get("type")
    second_type = second_property.get("type")
    warning: str | None = None

    if first_type != second_type:
        merged_property["type"] = _unique_values(
            _normalise_types(first_type) + _normalise_types(second_type)
        )
        warning = (
            f"Field '{field_name}' has conflicting types "
            f"({first_type!r} and {second_type!r}); retained both types."
        )

    # The first schema remains authoritative for overlapping metadata. Preserve
    # metadata that is present only in the second schema, and merge examples.
    for key, value in second_property.items():
        if key not in merged_property:
            merged_property[key] = copy.deepcopy(value)

    first_examples = first_property.get("examples", [])
    second_examples = second_property.get("examples", [])
    if not isinstance(first_examples, list) or not isinstance(second_examples, list):
        raise ValueError(f"Field '{field_name}' has a non-array 'examples' value.")
    examples = _unique_values(first_examples + second_examples)
    if examples:
        merged_property["examples"] = examples

    return merged_property, warning


def load_field_mapping(path: Union[str, Path]) -> Dict[str, str]:
    """Read a two-column CSV that maps second-schema field names to first-schema names.

    Each row is ``schema1_field,schema2_field``. A header row with those names is
    optional and blank rows are ignored. The returned dictionary is keyed by the
    second-schema name, so that a field recorded as ``child_age`` in the second
    schema can be merged with ``age`` in the first.
    """
    mapping: Dict[str, str] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as mapping_file:
        for line_number, row in enumerate(csv.reader(mapping_file), start=1):
            if not row or all(not cell.strip() for cell in row):
                continue
            if len(row) != 2 or not row[0].strip() or not row[1].strip():
                raise ValueError(
                    f"Mapping line {line_number} must have exactly two non-empty columns."
                )
            first_name, second_name = row[0].strip(), row[1].strip()
            if line_number == 1 and (first_name.lower(), second_name.lower()) == (
                "schema1_field",
                "schema2_field",
            ):
                continue
            if second_name in mapping:
                raise ValueError(f"Field '{second_name}' is mapped more than once.")
            mapping[second_name] = first_name
    return mapping


def unify_schemas(
    schema1: Mapping[str, Any],
    schema2: Mapping[str, Any],
    field_mapping: Optional[Mapping[str, str]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Merge two JSON Schema objects and return the schema plus warnings.

    Unique fields are copied unchanged. Same-name fields with equal ``type``
    values merge their examples; mismatched types become a deduplicated type
    array and produce a warning for the caller to present.

    ``field_mapping`` maps second-schema field names to first-schema names, so
    that differently named fields describing the same concept are merged. The
    merged ``required`` list holds only the fields required by both schemas
    (after mapping), so that a record valid under either input schema is not
    rejected for lacking a field the other schema requires.
    """
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})
    if not isinstance(properties1, Mapping) or not isinstance(properties2, Mapping):
        raise ValueError("Both schemas must have an object 'properties' section.")

    warnings: List[str] = []
    rename = dict(field_mapping or {})
    for second_name in list(rename):
        if second_name not in properties2:
            warnings.append(
                f"Mapping ignored: field '{second_name}' is not in the second schema."
            )
            del rename[second_name]
    targets = list(rename.values())
    if len(set(targets)) != len(targets):
        raise ValueError("Two second-schema fields are mapped to the same first-schema field.")
    for second_name, first_name in rename.items():
        if first_name != second_name and first_name in properties2:
            raise ValueError(
                f"Cannot map '{second_name}' to '{first_name}': the second schema already has a field with that name."
            )
    properties2 = {rename.get(name, name): value for name, value in properties2.items()}

    unified_properties: Dict[str, Any] = copy.deepcopy(dict(properties1))
    for field_name, second_property in properties2.items():
        if not isinstance(second_property, Mapping):
            raise ValueError(f"Property '{field_name}' must be a JSON object.")

        if field_name not in unified_properties:
            unified_properties[field_name] = copy.deepcopy(dict(second_property))
            continue

        first_property = unified_properties[field_name]
        if not isinstance(first_property, Mapping):
            raise ValueError(f"Property '{field_name}' must be a JSON object.")
        merged_property, warning = _merge_property(
            field_name, first_property, second_property
        )
        unified_properties[field_name] = merged_property
        if warning:
            warnings.append(warning)

    required1 = schema1.get("required", [])
    required2 = schema2.get("required", [])
    if not isinstance(required1, list) or not isinstance(required2, list):
        raise ValueError("Both schemas must have an array 'required' section.")
    if not all(isinstance(field_name, str) for field_name in required1 + required2):
        raise ValueError("Both schemas must contain only field names in 'required'.")
    required2 = [rename.get(field_name, field_name) for field_name in required2]

    unified_schema: Dict[str, Any] = {
        "$schema": schema1.get(
            "$schema", schema2.get("$schema", DEFAULT_DRAFT_2020_12_SCHEMA)
        ),
        "type": "object",
        "properties": unified_properties,
        "required": [name for name in _unique_values(required1) if name in required2],
    }
    return unified_schema, warnings
