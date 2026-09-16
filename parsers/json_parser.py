import json
import os
import pandas as pd
from parsers.base_parser import BaseParser, ParsedDataset


class JSONParser(BaseParser):
    """Parser responsible for reading JSON datasets."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"JSON file not found: {self.file_path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                df = pd.json_normalize(data)
            elif isinstance(data, dict):
                # Try finding list under common data keys
                list_key = None
                for key in ["data", "records", "items", "results", "features"]:
                    if key in data and isinstance(data[key], list):
                        list_key = key
                        break

                if list_key:
                    df = pd.json_normalize(data[list_key])
                else:
                    df = pd.json_normalize([data])
            else:
                raise ValueError("Unsupported JSON root element structure.")

            if df.empty:
                raise ValueError("The JSON dataset is empty.")

            return ParsedDataset(
                df=df,
                format_name="JSON",
                metadata={"file_path": self.file_path, "raw_type": type(data).__name__}
            )

        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON format: {error}")
        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise error
            raise RuntimeError(f"Failed to parse JSON file: {error}")
