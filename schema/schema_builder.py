from typing import Dict, Any
from schema.unified_model import UnifiedSchema


class SchemaBuilder:
    """Builds a standardized JSON Schema (Draft 2020-12) from a UnifiedSchema."""

    def __init__(self, unified_schema: UnifiedSchema):
        self.unified_schema = unified_schema

    def build(self) -> Dict[str, Any]:
        """Generate a JSON Schema representation."""
        properties: Dict[str, Any] = {}
        required_fields = []

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