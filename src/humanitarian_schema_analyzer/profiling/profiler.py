"""Statistical and pattern-based profiling engine for humanitarian datasets.

For ordinary CSV/JSON/XML/Excel datasets the profiler performs column-level
statistical analysis.

Following Strategy A (Preserve original input types):
- Values are profiled according to their actual input encoding in the dataset.
- String fields (even if numeric-looking such as "10" or "20") are inferred as
  'string', preserving the original data encoding and guaranteeing that the
  generated JSON Schema validates the source records.
- Potential numeric interpretations are noted via observation metadata
  (``is_numeric_string``, ``potential_type``) rather than overriding the schema type.
- Columns containing mixed types (e.g. both integers and strings) infer a union
  type (e.g. ['string', 'integer']).
- Sample minimum and maximum statistics are recorded as observed metrics and
  kept distinct from enforced JSON Schema validation constraints.

For XLSForm datasets (``parsed_dataset.metadata["is_xlsform"] is True``) the
profiler uses a dedicated path that builds ``ColumnProfile`` objects directly
from the ``xlsform_questions`` metadata extracted by the parser.
"""

import json
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd
from ..parsers.base_parser import ParsedDataset
from ..schema.unified_model import UnifiedSchema, ColumnProfile


class DataProfiler:
    """Statistical and pattern-based profiling engine for humanitarian datasets."""

    def __init__(self, parsed_dataset: ParsedDataset):
        self.parsed_dataset = parsed_dataset
        self.df = parsed_dataset.df
        self.format_name = parsed_dataset.format_name
        self.hxl_tags = parsed_dataset.hxl_tags

    def _check_numeric_string(self, series: pd.Series) -> tuple[bool, Optional[str]]:
        """Check if an all-string column contains numeric-looking values without mutating its type.

        This observation is preserved as metadata for profiling reports rather than
        silently overriding the actual JSON/data type.
        """
        non_null = series.dropna()
        if non_null.empty:
            return False, None

        # Only evaluate if all non-null values are strings
        if not all(isinstance(x, str) for x in non_null):
            return False, None

        try:
            num_series = pd.to_numeric(non_null, errors='coerce')
            if num_series.notna().all() and not num_series.empty:
                if (num_series % 1 == 0).all():
                    return True, "integer"
                return True, "number"
        except Exception:
            pass

        return False, None

    def _infer_type(self, series: pd.Series) -> tuple[Union[str, List[str]], bool, Optional[str]]:
        """Infer detailed type (integer, number, boolean, date, string, object, array).

        Preserves original input types:
        - Strings (even if numeric-looking) infer 'string'.
        - Genuine integers and numbers infer 'integer' and 'number'.
        - Columns containing mixed types infer a union list (e.g. ['string', 'integer']).
        """
        non_null = series.dropna()
        if non_null.empty:
            return "string", False, None

        # 1. Complex nested types (dict / list / XMLNode)
        has_complex = any(isinstance(x, (dict, list)) for x in non_null)
        if has_complex:
            if all(isinstance(x, list) for x in non_null):
                return "array", False, None
            if all(isinstance(x, dict) for x in non_null):
                return "object", False, None
            return "object", False, None

        dtype = series.dtype

        # 2. Native pandas/numpy numeric & boolean types
        if pd.api.types.is_integer_dtype(dtype):
            return "integer", False, None
        if pd.api.types.is_bool_dtype(dtype):
            return "boolean", False, None
        if pd.api.types.is_float_dtype(dtype):
            # Check if all non-null floats are mathematically integers (e.g. integer col with NaNs)
            try:
                if (non_null % 1 == 0).all():
                    return "integer", False, None
            except Exception:
                pass
            return "number", False, None
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "string", True, "date-time"

        # 3. Object dtype: examine the actual Python types of elements
        if pd.api.types.is_object_dtype(dtype) or dtype == object:
            observed_types = set()
            all_str = True

            for val in non_null:
                # Check bool before int because bool is a subclass of int in Python
                if isinstance(val, bool):
                    observed_types.add("boolean")
                    all_str = False
                elif isinstance(val, int):
                    observed_types.add("integer")
                    all_str = False
                elif isinstance(val, float):
                    if val % 1 == 0:
                        observed_types.add("integer")
                    else:
                        observed_types.add("number")
                    all_str = False
                elif isinstance(val, str):
                    observed_types.add("string")
                else:
                    observed_types.add("string")
                    all_str = False

            # Multiple distinct primitive types present (mixed column)
            if len(observed_types) > 1:
                type_order = ["string", "integer", "number", "boolean", "object", "array"]
                sorted_types = sorted(
                    observed_types,
                    key=lambda t: type_order.index(t) if t in type_order else 99
                )
                return sorted_types, False, None

            # All values are strings
            if all_str:
                # Check date patterns on string samples
                sample_str = non_null.astype(str).head(10)
                try:
                    parsed_dates = pd.to_datetime(sample_str, errors='coerce', format='mixed')
                    if parsed_dates.notna().sum() > len(sample_str) * 0.8:
                        return "string", True, "date"
                except Exception:
                    pass
                return "string", False, None

            # Single non-string type in object Series (e.g. all ints in object dtype)
            if len(observed_types) == 1:
                return next(iter(observed_types)), False, None

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
        """Build a UnifiedSchema from XLSForm question definitions."""
        questions: List[Dict[str, Any]] = self.parsed_dataset.metadata["xlsform_questions"]
        columns_profile: Dict[str, ColumnProfile] = {}

        for q in questions:
            name: str = q["name"]
            inferred_type: str = q.get("inferred_type", "string")
            is_date: bool = q.get("is_date", False)
            date_fmt = q.get("date_format")

            columns_profile[name] = ColumnProfile(
                name=name,
                data_type="xlsform",
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
                xlsform_type=q.get("xlsform_type"),
                xlsform_label=q.get("label"),
                xlsform_required=q.get("required"),
                xlsform_constraint=q.get("constraint"),
                xlsform_choices=q.get("choices"),
            )

        return UnifiedSchema(
            format_name=self.format_name,
            row_count=0,
            column_count=len(columns_profile),
            columns=columns_profile,
            metadata=self.parsed_dataset.metadata,
        )

    # ------------------------------------------------------------------
    # Standard tabular profiling path
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

            # Calculate unique count safely for unhashable types (dicts, lists)
            try:
                unique_count = int(series.nunique(dropna=True))
            except TypeError:
                try:
                    unique_count = len({json.dumps(x, sort_keys=True, default=str) for x in series.dropna()})
                except Exception:
                    unique_count = len(series.dropna())

            inferred_type, is_date, date_fmt = self._infer_type(series)
            is_num_str, potential_type = self._check_numeric_string(series)

            # Sample non-null values safely for unhashable types
            try:
                non_null_vals = series.dropna().unique()
            except TypeError:
                seen_reprs = set()
                non_null_vals = []
                for val in series.dropna():
                    val_repr = repr(val)
                    if val_repr not in seen_reprs:
                        seen_reprs.add(val_repr)
                        non_null_vals.append(val)

            samples = [
                val.item() if hasattr(val, 'item') and not isinstance(val, (dict, list)) else val
                for val in non_null_vals[:3]
            ]

            # Numeric metrics: only compute min/max/mean/std for genuine numeric data
            min_val, max_val, mean_val, std_val = None, None, None, None
            if pd.api.types.is_numeric_dtype(series) and not series.dropna().empty:
                min_val = float(series.min())
                max_val = float(series.max())
                mean_val = round(float(series.mean()), 4)
                std_val = round(float(series.std()), 4) if len(series.dropna()) > 1 else 0.0
            elif not is_num_str:
                # In object series with genuine numbers (e.g. mixed types)
                nums = [x for x in series.dropna() if isinstance(x, (int, float)) and not isinstance(x, bool)]
                if nums:
                    min_val = float(min(nums))
                    max_val = float(max(nums))
                    mean_val = round(float(np.mean(nums)), 4)
                    std_val = round(float(np.std(nums)), 4) if len(nums) > 1 else 0.0

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
                sample_values=samples,
                is_numeric_string=is_num_str,
                potential_type=potential_type,
            )

        return UnifiedSchema(
            format_name=self.format_name,
            row_count=row_count,
            column_count=column_count,
            columns=columns_profile,
            metadata=self.parsed_dataset.metadata
        )
