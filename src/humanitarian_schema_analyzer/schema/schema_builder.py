"""JSON Schema (Draft 2020-12) builder.

For ordinary datasets each column becomes a JSON Schema property with
statistical constraints (minimum/maximum) and format hints.

For XLSForm datasets the builder uses the XLSForm-specific metadata stored in
each ``ColumnProfile`` to produce richer schema properties:

* ``x-xlsform-type``    – the original XLSForm type string (e.g. "select_one gender_list")
* ``x-xlsform-label``   – the human-readable question label
* ``x-xlsform-constraint`` – the original constraint expression (preserved as metadata;
                             **not** enforced as a JSON Schema validation rule because
                             arbitrary XLSForm expressions cannot be mechanically
                             translated to JSON Schema constraints without risking
                             semantically incorrect validation)
* ``enum``              – for ``select_one`` questions the known choice names are
                          emitted as a JSON Schema ``enum`` when available
* ``"items": {"type": "string"}`` with ``x-xlsform-choices`` – for
                         ``select_multiple`` questions
* The JSON Schema ``required`` array reflects questions marked as required
  in the XLSForm (``xlsform_required == True``), replacing the statistical
  missing-count heuristic used for ordinary datasets.
"""

from typing import Any, Dict, List

from .unified_model import UnifiedSchema


class SchemaBuilder:
    """Builds a standardized JSON Schema (Draft 2020-12) from a UnifiedSchema."""

    def __init__(self, unified_schema: UnifiedSchema):
        self.unified_schema = unified_schema

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
                    # enum already constrains type; keep "type" for clarity
                # else: no choices available – emit string type only

            # select_multiple: array of strings from choice list
            elif base_type == "select_multiple":
                prop_def["type"] = "array"
                prop_def["items"] = {"type": "string"}
                if col.xlsform_choices:
                    prop_def["items"]["enum"] = col.xlsform_choices
                    prop_def["x-xlsform-choices"] = col.xlsform_choices

            # XLSForm metadata extensions (x- prefixed to keep schema valid)
            if col.xlsform_type:
                prop_def["x-xlsform-type"] = col.xlsform_type

            if col.xlsform_label:
                prop_def["x-xlsform-label"] = col.xlsform_label
                # Also set the standard JSON Schema description
                prop_def["description"] = col.xlsform_label

            if col.xlsform_constraint is not None:
                # Preserved as metadata only – NOT translated to JSON Schema
                # validation keywords because XLSForm constraint expressions
                # (e.g. ". >= 18") are not safely mappable to JSON Schema
                # without a full XLSForm constraint language interpreter.
                prop_def["x-xlsform-constraint"] = col.xlsform_constraint

            if col.xlsform_required is not None:
                prop_def["x-xlsform-required"] = col.xlsform_required

            properties[col_name] = prop_def

            # Build required list from XLSForm required flag
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
    # Standard tabular schema path (unchanged logic)
    # ------------------------------------------------------------------

    def _build_tabular_schema(self) -> Dict[str, Any]:
        """Build a JSON Schema from statistical column profiles."""
        properties: Dict[str, Any] = {}
        required_fields: List[str] = []

        for col_name, col in self.unified_schema.columns.items():
            # Support nullable types
            if col.missing_count > 0:
                col_type = [col.inferred_type, "null"]
            else:
                col_type = col.inferred_type
                required_fields.append(col_name)

            prop_def: Dict[str, Any] = {"type": col_type}

            if col.is_date and col.date_format:
                prop_def["format"] = col.date_format

            if col.hxl_tag:
                prop_def["x-hxl-tag"] = col.hxl_tag

            if col.min_value is not None:
                prop_def["minimum"] = col.min_value

            if col.max_value is not None:
                prop_def["maximum"] = col.max_value

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
