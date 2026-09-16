import pandas as pd
import numpy as np
from typing import Dict, Any, List
from parsers.base_parser import ParsedDataset
from schema.unified_model import UnifiedSchema, ColumnProfile


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