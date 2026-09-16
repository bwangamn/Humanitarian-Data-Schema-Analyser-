import os
import xml.etree.ElementTree as ET
import pandas as pd
from parsers.base_parser import BaseParser, ParsedDataset


class XMLParser(BaseParser):
    """Parser responsible for reading XML (XForms/IATI) data formats."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"XML file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            records = []
            # Detect repeated child records
            children = list(root)
            if not children:
                # Flat single root record
                row = {elem.tag: elem.text for elem in root}
                records.append(row)
            else:
                for child in children:
                    row = {}
                    # Add child tag attributes if present
                    for k, v in child.attrib.items():
                        row[f"@{k}"] = v
                    # Add child sub-elements text
                    if len(list(child)) > 0:
                        for subelem in child:
                            tag_name = subelem.tag.split('}')[-1] if '}' in subelem.tag else subelem.tag
                            row[tag_name] = subelem.text
                    else:
                        tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        row[tag_name] = child.text
                    records.append(row)

            df = pd.DataFrame(records)

            if df.empty:
                raise ValueError("The XML file contains no record elements.")

            root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            format_name = "XML (IATI)" if "iati" in root.tag.lower() else "XML (XForms)" if "data" in root.tag.lower() else "XML"

            return ParsedDataset(
                df=df,
                format_name=format_name,
                metadata={"file_path": self.file_path, "root_tag": root_tag}
            )

        except ET.ParseError as error:
            raise ValueError(f"Invalid XML syntax: {error}")
        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise error
            raise RuntimeError(f"Failed to parse XML file: {error}")
