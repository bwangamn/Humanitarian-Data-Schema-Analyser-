"""Utilities for combining JSON Schema Draft 2020-12 documents."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping, Sequence, Tuple


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


def unify_schemas(
    schema1: Mapping[str, Any], schema2: Mapping[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    """Merge two JSON Schema objects and return the schema plus conflict warnings.

    Unique fields are copied unchanged. Same-name fields with equal ``type``
    values merge their examples; mismatched types become a deduplicated type
    array and produce a warning for the caller to present.
    """
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})
    if not isinstance(properties1, Mapping) or not isinstance(properties2, Mapping):
        raise ValueError("Both schemas must have an object 'properties' section.")

    unified_properties: Dict[str, Any] = copy.deepcopy(dict(properties1))
    warnings: List[str] = []
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

    unified_schema: Dict[str, Any] = {
        "$schema": schema1.get(
            "$schema", schema2.get("$schema", DEFAULT_DRAFT_2020_12_SCHEMA)
        ),
        "type": "object",
        "properties": unified_properties,
        "required": _unique_values(required1 + required2),
    }
    return unified_schema, warnings
