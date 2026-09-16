import os
from typing import Optional
from parsers.base_parser import BaseParser
from parsers.csv_parser import CSVParser
from parsers.json_parser import JSONParser
from parsers.xml_parser import XMLParser
from parsers.xls_parser import XLSParser


class ParserFactory:
    """Factory to inspect input files and return the appropriate parser instance."""

    @staticmethod
    def get_parser(file_path: str, format_hint: Optional[str] = None) -> BaseParser:
        if format_hint:
            fmt = format_hint.lower().strip()
            if fmt == "csv":
                return CSVParser(file_path)
            elif fmt == "json":
                return JSONParser(file_path)
            elif fmt == "xml":
                return XMLParser(file_path)
            elif fmt in ["xls", "xlsx", "xlsform", "excel"]:
                return XLSParser(file_path)
            else:
                raise ValueError(f"Unsupported format override: {format_hint}")

        # Auto-detect by extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == ".csv":
            return CSVParser(file_path)
        elif ext == ".json":
            return JSONParser(file_path)
        elif ext == ".xml":
            return XMLParser(file_path)
        elif ext in [".xls", ".xlsx"]:
            return XLSParser(file_path)
        else:
            raise ValueError(
                f"Unsupported file extension '{ext}'. Please specify a format using --format."
            )
