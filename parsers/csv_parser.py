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
            if has_hxl and hxl_row_idx >= 0:
                # Extract HXL tags using header row 0 and tag row hxl_row_idx
                for col_idx in range(len(preview_df.columns)):
                    col_name = str(preview_df.iloc[0, col_idx]).strip()
                    tag_val = str(preview_df.iloc[hxl_row_idx, col_idx]).strip()
                    if tag_val.startswith('#'):
                        hxl_tags[col_name] = tag_val
                
                # Load df by skipping the HXL tag row (hxl_row_idx) so pandas performs standard dtype inference on data rows
                df = pd.read_csv(self.file_path, header=0, skiprows=[hxl_row_idx])
                if df.empty and len(df.columns) == 0:
                    raise ValueError("The CSV file is empty.")
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