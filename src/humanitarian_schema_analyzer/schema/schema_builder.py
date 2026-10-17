"""JSON Schema (Draft 2020-12) builder.

For ordinary datasets each column becomes a JSON Schema property.
Following Strategy A (Preserve original input types):

- The schema faithfully represents the input data's actual types.

- A numeric-looking string column retains "type": "string" so that raw records
  validate against the schema without transformation.

- Columns with mixed primitive types emit union type definitions (e.g. ["string", "integer"]).

- Observed sample minimum and maximum values are recorded as informational
  metadata (x-observed-minimum, x-observed-maximum) rather than rigid validation
  constraints, separating sample observations from enforced domain rules.
  An explicit parameter ``enforce_observed_ranges=True`` can be passed when
  enforcing bounds is desired by policy.

For XLSForm datasets the builder uses the XLSForm-specific metadata stored in
each ``ColumnProfile``:

* ``x-xlsform-type``    – the original XLSForm type string

* ``x-xlsform-label``   – the human-readable question label

* ``x-xlsform-constraint`` – the original constraint expression

* ``enum``              – choice names for select_one

* ``"items": {"type": "string"}`` with ``x-xlsform-choices`` – for select_multiple

* ``required`` array reflects questions marked as required in the XLSForm.
"""

from typing import Any, Dict, List, Optional
from .unified_model import UnifiedSchema


class SchemaBuilder:
    """Builds a standardized JSON Schema (Draft 2020-12) from a UnifiedSchema."""

    def __init__(self, unified_schema: UnifiedSchema, enforce_observed_ranges: bool = False):
        self.unified_schema = unified_schema
        self.enforce_observed_ranges = enforce_observed_ranges

    def build(self) -> Dict[str, Any]:
        """Generate a JSON Schema representation."""
        is_xlsform = self.unified_schema.metadata.get("is_xlsform", False)

        if is_xlsform:
            return self._build_xlsform_schema()
        return self._build_tabular_schema()

    # ------------------------------------------------------------------
    # XLSForm schema path
    # ------------------------------------------------------------------

    def _build_xlsform_schema(self) -> Dict[str, Any]:
        """Build a JSON Schema from XLSForm question metadata."""
        properties: Dict[str, Any] = {}
        required_fields: List[str] = []

        for col_name, col in self.unified_schema.columns.items():
            xlsform_type_raw = col.xlsform_type or ""
            base_type = xlsform_type_raw.split()[0].lower() if xlsform_type_raw else "unknown"

            prop_def: Dict[str, Any] = {"type": col.inferred_type}

            # Date/time format hint
            if col.is_date and col.date_format:
                prop_def["format"] = col.date_format

            # select_one: emit enum from choice list when available
            if base_type == "select_one":
                if col.xlsform_choices:
                    prop_def["enum"] = col.xlsform_choices

            # select_multiple: array of strings from choice list
            elif base_type == "select_multiple":
                prop_def["type"] = "array"
                prop_def["items"] = {"type": "string"}
                if col.xlsform_choices:
                    prop_def["items"]["enum"] = col.xlsform_choices
                    prop_def["x-xlsform-choices"] = col.xlsform_choices

            # XLSForm metadata extensions
            if col.xlsform_type:
                prop_def["x-xlsform-type"] = col.xlsform_type

            if col.xlsform_label:
                prop_def["x-xlsform-label"] = col.xlsform_label
                prop_def["description"] = col.xlsform_label

            if col.xlsform_constraint is not None:
                prop_def["x-xlsform-constraint"] = col.xlsform_constraint

            if col.xlsform_required is not None:
                prop_def["x-xlsform-required"] = col.xlsform_required

            properties[col_name] = prop_def

            if col.xlsform_required is True:
                required_fields.append(col_name)

        schema: Dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"Humanitarian Dataset Schema ({self.unified_schema.format_name})",
            "type": "object",
            "properties": properties,
        }

        if required_fields:
            schema["required"] = required_fields

        return schema

    # ------------------------------------------------------------------
    # Standard tabular schema path
    # ------------------------------------------------------------------

    def _build_tabular_schema(self) -> Dict[str, Any]:
        """Build a JSON Schema from statistical column profiles."""
        properties: Dict[str, Any] = {}
        required_fields: List[str] = []

        for col_name, col in self.unified_schema.columns.items():
            if getattr(col, "nested_schema", None):
                prop_def: Dict[str, Any] = dict(col.nested_schema)
                if col.missing_count > 0:
                    if "type" in prop_def:
                        if isinstance(prop_def["type"], list):
                            prop_def["type"] = list(dict.fromkeys(prop_def["type"] + ["null"]))
                        else:
                            prop_def["type"] = [prop_def["type"], "null"]
                    elif "anyOf" in prop_def:
                        prop_def["anyOf"].append({"type": "null"})
                else:
                    required_fields.append(col_name)
            else:
                # Support nullable types and union types
                if isinstance(col.inferred_type, list):
                    if col.missing_count > 0:
                        col_type = list(dict.fromkeys(col.inferred_type + ["null"]))
                    else:
                        col_type = col.inferred_type
                        required_fields.append(col_name)
                else:
                    if col.missing_count > 0:
                        col_type = [col.inferred_type, "null"]
                    else:
                        col_type = col.inferred_type
                        required_fields.append(col_name)

                prop_def = {"type": col_type}

            if col.is_date and col.date_format:
                prop_def["format"] = col.date_format

            if col.hxl_tag:
                prop_def["x-hxl-tag"] = col.hxl_tag

            # Informational observation annotations for numeric-looking strings
            if getattr(col, "is_numeric_string", False):
                prop_def["x-numeric-string"] = True
                if getattr(col, "potential_type", None):
                    prop_def["x-potential-type"] = col.potential_type

            # Observed min/max: separate sample observations from enforced domain constraints
            if self.enforce_observed_ranges:
                if col.min_value is not None:
                    prop_def["minimum"] = col.min_value
                if col.max_value is not None:
                    prop_def["maximum"] = col.max_value
            else:
                # Retain observed statistics as schema metadata without enforcing them as constraints
                if col.min_value is not None:
                    prop_def["x-observed-minimum"] = col.min_value
                if col.max_value is not None:
                    prop_def["x-observed-maximum"] = col.max_value

            if col.sample_values:
                prop_def["examples"] = col.sample_values

            properties[col_name] = prop_def

        schema: Dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"Humanitarian Dataset Schema ({self.unified_schema.format_name})",
            "type": "object",
            "properties": properties
        }

        if required_fields:
            schema["required"] = required_fields

        return schema
