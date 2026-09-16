import os
import pandas as pd
from parsers.base_parser import BaseParser, ParsedDataset


class CSVParser(BaseParser):
    """Parser responsible for reading CSV files and extracting HXL semantic tags."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        try:
            # Read first few lines to inspect HXL hashtags
            preview_df = pd.read_csv(self.file_path, nrows=5, header=None)
            if preview_df.empty:
                raise ValueError("The CSV file is empty.")

            # Check if line index 1 (or 0) starts with '#' indicating HXL tags
            has_hxl = False
            hxl_row_idx = -1

            for idx in range(min(len(preview_df), 3)):
                row_vals = preview_df.iloc[idx].astype(str).str.strip()
                if any(val.startswith('#') for val in row_vals if val):
                    has_hxl = True
                    hxl_row_idx = idx
                    break

            hxl_tags = {}
            if has_hxl and hxl_row_idx == 1:
                # Standard HXL CSV: Row 0 is header, Row 1 is HXL tags
                raw_df = pd.read_csv(self.file_path, header=0)
                if not raw_df.empty:
                    tag_row = raw_df.iloc[0]
                    for col in raw_df.columns:
                        val = str(tag_row[col]).strip()
                        if val.startswith('#'):
                            hxl_tags[col] = val
                    df = raw_df.iloc[1:].reset_index(drop=True)
                else:
                    df = raw_df
            else:
                df = pd.read_csv(self.file_path)

            if df.empty and len(df.columns) == 0:
                raise ValueError("The CSV file is empty.")

            return ParsedDataset(
                df=df,
                format_name="CSV" if not has_hxl else "HXL-CSV",
                hxl_tags=hxl_tags,
                metadata={"file_path": self.file_path, "has_hxl": has_hxl}
            )

        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty.")
        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise error
            raise RuntimeError(f"Failed to parse CSV file: {error}")