import os
import pandas as pd
from parsers.base_parser import BaseParser, ParsedDataset


class XLSParser(BaseParser):
    """Parser responsible for reading Excel and XLSForm datasets."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        try:
            excel_file = pd.ExcelFile(self.file_path)
            sheet_names = excel_file.sheet_names

            is_xlsform = "survey" in [s.lower() for s in sheet_names]
            target_sheet = "survey" if is_xlsform else sheet_names[0]

            # Find matching sheet case-insensitively
            selected_sheet = next((s for s in sheet_names if s.lower() == target_sheet.lower()), sheet_names[0])
            df = pd.read_excel(self.file_path, sheet_name=selected_sheet)

            if df.empty:
                raise ValueError(f"The Excel sheet '{selected_sheet}' is empty.")

            format_name = "XLSForm" if is_xlsform else "Excel"

            return ParsedDataset(
                df=df,
                format_name=format_name,
                metadata={
                    "file_path": self.file_path,
                    "sheet_name": selected_sheet,
                    "available_sheets": sheet_names,
                    "is_xlsform": is_xlsform
                }
            )

        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise error
            raise RuntimeError(f"Failed to parse Excel file: {error}")
