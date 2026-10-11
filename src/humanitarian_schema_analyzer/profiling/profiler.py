"""Statistical and pattern-based profiling engine for humanitarian datasets.

For ordinary CSV/JSON/XML/Excel datasets the profiler performs column-level
statistical analysis as before.

For XLSForm datasets (``parsed_dataset.metadata["is_xlsform"] is True``) the
profiler uses a dedicated path that builds ``ColumnProfile`` objects directly
from the ``xlsform_questions`` metadata extracted by the parser, rather than
computing statistics over an empty/synthetic DataFrame.  This preserves the
XLSForm question type, label, requiredness, and constraint expressions in the
profile without fabricating misleading statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from ..parsers.base_parser import ParsedDataset
from ..schema.unified_model import UnifiedSchema, ColumnProfile


class DataProfiler:
    """Statistical and pattern-based profiling engine for humanitarian datasets."""

    def __init__(self, parsed_dataset: ParsedDataset):
        self.parsed_dataset = parsed_dataset
        self.df = parsed_dataset.df
        self.format_name = parsed_dataset.format_name
        self.hxl_tags = parsed_dataset.hxl_tags

    def _infer_type(self, series: pd.Series) -> tuple[str, bool, str | None]:
        """Infer detailed type (integer, float, boolean, date, string) and check date formats."""
        non_null = series.dropna()
        if non_null.empty:
            return "string", False, None

        dtype = series.dtype

        if pd.api.types.is_integer_dtype(dtype):
            return "integer", False, None
        if pd.api.types.is_float_dtype(dtype):
            # Check if all floats are integers
            if (non_null % 1 == 0).all():
                return "integer", False, None
            return "number", False, None
        if pd.api.types.is_bool_dtype(dtype):
            return "boolean", False, None

        # Check if object/string series contains numeric integer or float values
        if pd.api.types.is_object_dtype(dtype) or dtype == object:
            try:
                num_series = pd.to_numeric(non_null, errors='coerce')
                if num_series.notna().all() and not num_series.empty:
                    if (num_series % 1 == 0).all():
                        return "integer", False, None
                    return "number", False, None
            except Exception:
                pass

        # Check date string patterns
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "string", True, "date-time"

        # Try converting string series to datetime
        sample_str = non_null.astype(str).head(10)
        try:
            parsed_dates = pd.to_datetime(sample_str, errors='coerce', format='mixed')
            if parsed_dates.notna().sum() > len(sample_str) * 0.8:
                return "string", True, "date"
        except Exception:
            pass

        return "string", False, None

    def profile(self) -> UnifiedSchema:
        """Generate unified schema profile with statistical and pattern analysis.

        For XLSForm datasets the profiling is driven by the question metadata
        in ``parsed_dataset.metadata["xlsform_questions"]`` rather than by
        statistical analysis of the DataFrame columns.
        """
        if self.parsed_dataset.metadata.get("is_xlsform") and \
                "xlsform_questions" in self.parsed_dataset.metadata:
            return self._profile_xlsform()
        return self._profile_tabular()

    # ------------------------------------------------------------------
    # XLSForm-specific profiling path
    # ------------------------------------------------------------------

    def _profile_xlsform(self) -> UnifiedSchema:
        """Build a UnifiedSchema from XLSForm question definitions.

        Each question becomes a ColumnProfile.  Statistical fields that require
        response data (min/max/mean/std/sample_values) are left as None/empty
        because the XLSForm is a form definition, not a data table.
        """
        questions: List[Dict[str, Any]] = self.parsed_dataset.metadata["xlsform_questions"]
        columns_profile: Dict[str, ColumnProfile] = {}

        for q in questions:
            name: str = q["name"]
            inferred_type: str = q.get("inferred_type", "string")
            is_date: bool = q.get("is_date", False)
            date_fmt = q.get("date_format")

            columns_profile[name] = ColumnProfile(
                name=name,
                data_type="xlsform",        # sentinel: not a pandas dtype
                inferred_type=inferred_type,
                missing_count=0,
                missing_percentage=0.0,
                unique_count=0,
                hxl_tag=None,
                min_value=None,
                max_value=None,
                mean_value=None,
                std_value=None,
                is_date=is_date,
                date_format=date_fmt,
                sample_values=[],
                # XLSForm-specific fields
                xlsform_type=q.get("xlsform_type"),
                xlsform_label=q.get("label"),
                xlsform_required=q.get("required"),
                xlsform_constraint=q.get("constraint"),
                xlsform_choices=q.get("choices"),
            )

        return UnifiedSchema(
            format_name=self.format_name,
            row_count=0,   # form definition has no response rows
            column_count=len(columns_profile),
            columns=columns_profile,
            metadata=self.parsed_dataset.metadata,
        )

    # ------------------------------------------------------------------
    # Standard tabular profiling path (unchanged)
    # ------------------------------------------------------------------

    def _profile_tabular(self) -> UnifiedSchema:
        """Generate unified schema profile with statistical and pattern analysis."""
        row_count = len(self.df)
        column_count = len(self.df.columns)
        columns_profile: Dict[str, ColumnProfile] = {}

        for column in self.df.columns:
            series = self.df[column]
            missing_count = int(series.isna().sum())
            missing_pct = round((missing_count / row_count * 100), 2) if row_count > 0 else 0.0
            unique_count = int(series.nunique(dropna=True))

            inferred_type, is_date, date_fmt = self._infer_type(series)

            # Sample non-null values
            non_null_vals = series.dropna().unique()
            samples = [val.item() if hasattr(val, 'item') else val for val in non_null_vals[:3]]

            # Numeric metrics
            min_val, max_val, mean_val, std_val = None, None, None, None
            if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
                min_val = float(series.min())
                max_val = float(series.max())
                mean_val = round(float(series.mean()), 4)
                std_val = round(float(series.std()), 4) if len(series.dropna()) > 1 else 0.0

            hxl_tag = self.hxl_tags.get(str(column))

            columns_profile[str(column)] = ColumnProfile(
                name=str(column),
                data_type=str(series.dtype),
                inferred_type=inferred_type,
                missing_count=missing_count,
                missing_percentage=missing_pct,
                unique_count=unique_count,
                hxl_tag=hxl_tag,
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                std_value=std_val,
                is_date=is_date,
                date_format=date_fmt,
                sample_values=samples
            )

        return UnifiedSchema(
            format_name=self.format_name,
            row_count=row_count,
            column_count=column_count,
            columns=columns_profile,
            metadata=self.parsed_dataset.metadata
        )
