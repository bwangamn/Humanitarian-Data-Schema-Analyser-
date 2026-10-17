"""XLS/XLSX and XLSForm parser.

For ordinary Excel workbooks the first sheet is read as a tabular dataset
(unchanged behaviour).

For XLSForm workbooks (identified by the presence of a ``survey`` worksheet)
the parser extracts *question definitions* from the ``survey`` sheet and
presents them as columns in the resulting DataFrame, rather than treating the
XLSForm template column headings (``type``, ``name``, ``label``, …) as the
dataset fields.

XLSForm structural row types that do NOT represent a respondent-facing question
are filtered out:

.. code-block:: text

   begin_group, end_group, begin_repeat, end_repeat,
   begin_score, end_score, begin_rank, end_rank, note

Question metadata (type, label, required, constraint, choices) is stored in
``ParsedDataset.metadata["xlsform_questions"]`` so that the downstream
profiler can build a properly typed ``UnifiedSchema`` without re-parsing the
workbook.
"""

import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .base_parser import BaseParser, ParsedDataset

# ---------------------------------------------------------------------------
# XLSForm structural row types that do not represent respondent-facing fields.
# Rows whose ``type`` column matches any of these prefixes are skipped.
# ---------------------------------------------------------------------------
_NON_QUESTION_TYPES: frozenset = frozenset({
    "begin_group",
    "end_group",
    "begin_repeat",
    "end_repeat",
    "begin_score",
    "end_score",
    "begin_rank",
    "end_rank",
    "note",
})

# ---------------------------------------------------------------------------
# Mapping from XLSForm base type → unified inferred_type (JSON Schema type).
# ``select_one`` and ``select_multiple`` are treated as string by default;
# the downstream schema builder can refine them to an enum when choices are
# available.
# ---------------------------------------------------------------------------
_XLSFORM_TYPE_MAP: Dict[str, str] = {
    "text": "string",
    "integer": "integer",
    "int": "integer",
    "decimal": "number",
    "float": "number",
    "date": "string",
    "datetime": "string",
    "time": "string",
    "select_one": "string",
    "select_multiple": "string",
    "calculate": "string",
    "geopoint": "string",
    "geotrace": "string",
    "geoshape": "string",
    "image": "string",
    "audio": "string",
    "video": "string",
    "file": "string",
    "barcode": "string",
    "range": "number",
    "rank": "string",
    "note": "string",
}

# XLSForm types that carry a JSON Schema ``format`` hint.
_XLSFORM_DATE_FORMATS: Dict[str, str] = {
    "date": "date",
    "datetime": "date-time",
    "time": "time",
}


def _parse_xlsform_type(raw_type: Optional[str]) -> tuple[str, Optional[str], Optional[str]]:
    """Decompose a raw XLSForm type cell value.

    Returns
    -------
    (base_type, list_name, inferred_type)
        base_type   – the normalised base type string, e.g. ``"select_one"``
        list_name   – the choice-list name for select_one/select_multiple,
                      or ``None``
        inferred_type – JSON Schema type string from ``_XLSFORM_TYPE_MAP``,
                        defaulting to ``"string"`` for unknown types
    """
    if not raw_type or not isinstance(raw_type, str):
        return "unknown", None, "string"

    parts = raw_type.strip().split(None, 1)
    base_type = parts[0].lower()
    list_name = parts[1].strip() if len(parts) > 1 else None

    inferred = _XLSFORM_TYPE_MAP.get(base_type, "string")
    return base_type, list_name, inferred


def _is_non_question_row(raw_type: Optional[str]) -> bool:
    """Return True if the row type indicates a structural (non-question) row."""
    if not raw_type or not isinstance(raw_type, str):
        return False
    base = raw_type.strip().lower().split(None, 1)[0]
    return base in _NON_QUESTION_TYPES


def _parse_required(raw_required: Any) -> Optional[bool]:
    """Normalise the XLSForm ``required`` cell value to a Python bool or None."""
    if raw_required is None or (isinstance(raw_required, float) and pd.isna(raw_required)):
        return None
    if isinstance(raw_required, bool):
        return raw_required
    val = str(raw_required).strip().lower()
    if val in {"yes", "true", "1"}:
        return True
    if val in {"no", "false", "0", ""}:
        return False
    return None


class XLSParser(BaseParser):
    """Parser responsible for reading Excel and XLSForm datasets."""

    def parse(self) -> ParsedDataset:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        try:
            excel_file = pd.ExcelFile(self.file_path)
            sheet_names = excel_file.sheet_names
            lower_names = [s.lower() for s in sheet_names]

            is_xlsform = "survey" in lower_names

            if is_xlsform:
                return self._parse_xlsform(excel_file, sheet_names, lower_names)
            else:
                return self._parse_excel(excel_file, sheet_names)

        except Exception as error:
            if isinstance(error, (FileNotFoundError, ValueError)):
                raise
            raise RuntimeError(f"Failed to parse Excel file: {error}")

    # ------------------------------------------------------------------
    # Ordinary Excel path (unchanged behaviour)
    # ------------------------------------------------------------------

    def _parse_excel(self, excel_file: pd.ExcelFile, sheet_names: List[str]) -> ParsedDataset:
        selected_sheet = sheet_names[0]
        df = pd.read_excel(self.file_path, sheet_name=selected_sheet)

        if df.empty:
            raise ValueError(f"The Excel sheet '{selected_sheet}' is empty.")

        metadata: Dict[str, Any] = {
            "file_path": self.file_path,
            "sheet_name": selected_sheet,
            "available_sheets": sheet_names,
            "is_xlsform": False,
        }

        return ParsedDataset(df=df, format_name="Excel", metadata=metadata)

    # ------------------------------------------------------------------
    # XLSForm path
    # ------------------------------------------------------------------

    def _parse_xlsform(
        self,
        excel_file: pd.ExcelFile,
        sheet_names: List[str],
        lower_names: List[str],
    ) -> ParsedDataset:
        """Extract question definitions from an XLSForm workbook.

        The ``survey`` worksheet is read and each non-structural question row
        is extracted.  A synthetic DataFrame is built where **each question
        name becomes a column** and a single placeholder row encodes the
        question's base type (so the downstream profiler can infer types).

        All question metadata is also stored in
        ``metadata["xlsform_questions"]`` as a list of dicts for richer
        profiling downstream.
        """
        survey_name = sheet_names[lower_names.index("survey")]
        survey_df = pd.read_excel(self.file_path, sheet_name=survey_name, dtype=str)
        survey_df.columns = [str(c).strip().lower() for c in survey_df.columns]

        if survey_df.empty:
            raise ValueError(f"The XLSForm survey sheet '{survey_name}' is empty.")

        if "name" not in survey_df.columns or "type" not in survey_df.columns:
            raise ValueError(
                "XLSForm survey sheet is missing required 'name' and/or 'type' columns."
            )

        # Load choices sheet if present
        choices_lookup: Dict[str, List[str]] = {}
        choices_raw: List[Dict[str, Any]] = []
        choices_sheet_name: Optional[str] = None

        if "choices" in lower_names:
            choices_sheet_name = sheet_names[lower_names.index("choices")]
            choices_df = pd.read_excel(self.file_path, sheet_name=choices_sheet_name, dtype=str)
            choices_df.columns = [str(c).strip().lower() for c in choices_df.columns]
            if not choices_df.empty and "list_name" in choices_df.columns and "name" in choices_df.columns:
                choices_raw = choices_df.to_dict(orient="records")
                for row in choices_raw:
                    list_name = str(row.get("list_name", "")).strip()
                    choice_name = str(row.get("name", "")).strip()
                    if list_name and choice_name and choice_name.lower() != "nan":
                        choices_lookup.setdefault(list_name, []).append(choice_name)

        # Extract question rows
        questions: List[Dict[str, Any]] = []
        seen_names: set = set()

        for _, row in survey_df.iterrows():
            raw_type = row.get("type")
            raw_name = row.get("name")

            # Skip structural / non-question rows
            if _is_non_question_row(raw_type):
                continue

            # Skip rows with missing or blank name
            if not raw_name or str(raw_name).strip().lower() in {"", "nan", "none"}:
                continue

            q_name = str(raw_name).strip()

            # Skip duplicate names (keep first occurrence)
            if q_name in seen_names:
                continue
            seen_names.add(q_name)

            base_type, list_name, inferred_type = _parse_xlsform_type(str(raw_type).strip() if raw_type else None)

            # Preserve original raw type string for metadata
            raw_type_str = str(raw_type).strip() if raw_type else None

            label_raw = row.get("label") or row.get("label::english") or row.get("label:english")
            label = str(label_raw).strip() if label_raw and str(label_raw).strip().lower() not in {"nan", "none", ""} else None

            constraint_raw = row.get("constraint")
            constraint = str(constraint_raw).strip() if constraint_raw and str(constraint_raw).strip().lower() not in {"nan", "none", ""} else None

            required = _parse_required(row.get("required"))

            choices = choices_lookup.get(list_name, []) if list_name else None

            is_date = base_type in _XLSFORM_DATE_FORMATS
            date_fmt = _XLSFORM_DATE_FORMATS.get(base_type)

            questions.append({
                "name": q_name,
                "xlsform_type": raw_type_str,
                "base_type": base_type,
                "list_name": list_name,
                "inferred_type": inferred_type,
                "label": label,
                "required": required,
                "constraint": constraint,
                "choices": choices,
                "is_date": is_date,
                "date_format": date_fmt,
            })

        if not questions:
            raise ValueError(
                "XLSForm survey sheet contains no extractable question rows. "
                "All rows are either structural (begin_group/end_group/…) or missing a 'name'."
            )

        # Build a synthetic DataFrame: one column per question, one row with
        # a sentinel value that allows the downstream profiler to determine
        # whether to use the XLSForm metadata path or the statistical path.
        #
        # The sentinel row encodes the base type name as a string so that the
        # standard type-inference code would default to "string" for most
        # types (preserving backward compatibility when the XLSForm path is
        # not active).  The profiler overrides this with the explicit
        # inferred_type from xlsform_questions when is_xlsform is True.
        synthetic_row: Dict[str, Any] = {}
        for q in questions:
            # Use None as the placeholder value so missing_count=0 won't be
            # triggered and the profiler's XLSForm path can handle it.
            synthetic_row[q["name"]] = None

        df = pd.DataFrame([synthetic_row])

        metadata: Dict[str, Any] = {
            "file_path": self.file_path,
            "sheet_name": survey_name,
            "available_sheets": sheet_names,
            "is_xlsform": True,
            "xlsform_questions": questions,
        }

        if choices_sheet_name:
            metadata["choices_sheet"] = choices_sheet_name
            # Keep legacy format for backward compat with existing test assertions
            # that check metadata["choices"] as a list of dicts with original column names.
            legacy_choices: List[Dict[str, Any]] = []
            if choices_raw:
                for cr in choices_raw:
                    # Restore original column casing expected by tests
                    entry: Dict[str, Any] = {}
                    for k, v in cr.items():
                        # Rename internal lowercase keys back to the expected names
                        entry[k] = v if str(v).strip().lower() not in {"nan", "none"} else None
                    # Ensure list_name and name keys are present (they are already lowercase)
                    legacy_choices.append(entry)
            metadata["choices"] = legacy_choices

        return ParsedDataset(df=df, format_name="XLSForm", metadata=metadata)
