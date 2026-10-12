"""XML and IATI parser for humanitarian data formats.

Supports arbitrary XML and humanitarian formats like IATI activities and XForms.
Preserves:
- Nested elements at arbitrary depths (retaining text and structure).
- Repeated elements as lists rather than overwriting earlier occurrences.
- XML attributes (stored with '@' prefix, e.g. '@currency').
- Logical record/activity boundaries across multiple activities.
- Compatibility with pandas DataFrame, DataProfiler, and SchemaBuilder.
"""

import os
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET
import pandas as pd
from .base_parser import BaseParser, ParsedDataset


class XMLNode(dict):
    """Dictionary representing an XML element with structured children and attributes.

    Provides ergonomic attribute and text access:
    - Attributes can be accessed with '@attr' or 'attr' (if 'attr' does not collide with a child tag).
    - Text can be accessed via '#text', 'text', or 'value' (if not colliding with a child tag).
    - Can be compared to strings or numbers when representing a scalar value or single text child.
    """

    def __getitem__(self, key: Any) -> Any:
        if super().__contains__(key):
            return super().__getitem__(key)
        if isinstance(key, str) and not key.startswith("@") and super().__contains__(f"@{key}"):
            return super().__getitem__(f"@{key}")
        if key in ("#text", "text", "value"):
            if super().__contains__("#text"):
                return super().__getitem__("#text")
            if len(self) == 1:
                val = next(iter(self.values()))
                if isinstance(val, (str, int, float)):
                    return val
        raise KeyError(key)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: Any) -> bool:
        if super().__contains__(key):
            return True
        if isinstance(key, str) and not key.startswith("@") and super().__contains__(f"@{key}"):
            return True
        if key in ("#text", "text", "value"):
            if super().__contains__("#text"):
                return True
            if len(self) == 1 and isinstance(next(iter(self.values())), (str, int, float)):
                return True
        return False

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (str, int, float)):
            if super().__contains__("#text"):
                val = super().__getitem__("#text")
                if isinstance(other, (int, float)):
                    try:
                        return float(val) == float(other)
                    except (ValueError, TypeError):
                        pass
                return str(val) == str(other)
            if len(self) == 1:
                val = next(iter(self.values()))
                if isinstance(val, (str, int, float)):
                    if isinstance(other, (int, float)):
                        try:
                            return float(val) == float(other)
                        except (ValueError, TypeError):
                            pass
                    return str(val) == str(other)
        return super().__eq__(other)


def _clean_tag(tag: str) -> str:
    """Strip XML namespace prefix if present."""
    return tag.split("}")[-1] if "}" in tag else tag


def _element_to_data(elem: ET.Element) -> Any:
    """Recursively convert an XML element into a Python data structure.

    - Leaf element without attributes: returns stripped text (or None if empty).
    - Leaf element with attributes: returns an XMLNode with '@attr' keys and '#text'.
    - Complex element with children: returns an XMLNode mapping child tag names to
      their data. Repeated child tags are collected into lists.
    """
    text = elem.text.strip() if elem.text and elem.text.strip() else None
    children = list(elem)
    has_attribs = bool(elem.attrib)

    if not children and not has_attribs:
        return text

    node = XMLNode()
    for k, v in elem.attrib.items():
        node[f"@{_clean_tag(k)}"] = v

    if text:
        node["#text"] = text

    for child in children:
        child_tag = _clean_tag(child.tag)
        child_data = _element_to_data(child)
        if child_tag not in node:
            node[child_tag] = child_data
        elif isinstance(node[child_tag], list):
            node[child_tag].append(child_data)
        else:
            node[child_tag] = [node[child_tag], child_data]

    return node


def _extract_records(root: ET.Element) -> List[Dict[str, Any]]:
    """Identify record boundaries and extract structured rows from the XML tree."""
    children = list(root)
    if not children:
        return []

    # Check if root's children represent individual records (e.g. <iati-activity>, <item>)
    child_tags = [_clean_tag(c.tag) for c in children]
    has_repeated_tags = len(child_tags) > len(set(child_tags))
    children_have_subelements = any(len(list(c)) > 0 for c in children)
    root_tag = _clean_tag(root.tag).lower()
    is_container_root = (
        any(root_tag.endswith(sfx) for sfx in ("activities", "items", "records", "rows", "list", "collection", "entries", "dataset"))
        or root_tag in ("root", "data", "catalog")
    )

    if has_repeated_tags or children_have_subelements or (is_container_root and len(children) > 0):
        records = []
        for child in children:
            data = _element_to_data(child)
            if isinstance(data, dict):
                records.append(data)
            else:
                tag_name = _clean_tag(child.tag)
                records.append({tag_name: data})
        return records
    else:
        # Flat root element is the record itself
        data = _element_to_data(root)
        if isinstance(data, dict):
            return [data]
        tag_name = _clean_tag(root.tag)
        return [{tag_name: data}]


class XMLParser(BaseParser):
    """Parser responsible for reading XML (XForms/IATI) data formats."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"XML file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            records = _extract_records(root)

            if not records:
                raise ValueError("The XML file contains no record elements.")

            df = pd.DataFrame(records)

            if df.empty:
                raise ValueError("The XML file contains no record elements.")

            root_tag = _clean_tag(root.tag)
            format_name = (
                "XML (IATI)" if "iati" in root.tag.lower()
                else "XML (XForms)" if "data" in root.tag.lower()
                else "XML"
            )

            metadata = {
                "file_path": self.file_path,
                "root_tag": root_tag,
                "records": records,
            }

            return ParsedDataset(
                df=df,
                format_name=format_name,
                metadata=metadata
            )

        except ET.ParseError as error:
            raise ValueError(f"Invalid XML syntax: {error}")
        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise error
            raise RuntimeError(f"Failed to parse XML file: {error}")
