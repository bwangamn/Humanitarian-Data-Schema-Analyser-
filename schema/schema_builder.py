import pandas as pd


class SchemaBuilder:
    """Builds a JSON Schema representation from a DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def _map_type(self, dtype) -> str:
        """Map Pandas data types to JSON Schema types."""

        if pd.api.types.is_integer_dtype(dtype):
            return "integer"

        if pd.api.types.is_float_dtype(dtype):
            return "number"

        if pd.api.types.is_bool_dtype(dtype):
            return "boolean"

        return "string"

    def build(self) -> dict:
        """Generate a JSON Schema."""

        properties = {}

        for column in self.df.columns:

            properties[column] = {
                "type": self._map_type(
                    self.df[column].dtype
                )
            }

        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Humanitarian Dataset Schema",
            "type": "object",
            "properties": properties
        }

        return schema