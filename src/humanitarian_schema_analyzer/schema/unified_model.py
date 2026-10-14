from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union


@dataclass
class ColumnProfile:
    """Statistical and structural metadata for a single field/column.

    For XLSForm datasets the standard statistical fields (missing_count,
    min_value, etc.) are set to neutral defaults because the form definition
    itself does not contain response data.  The xlsform_* fields carry the
    question metadata that was read from the survey worksheet.
    """
    name: str
    data_type: str
    inferred_type: Union[str, List[str]]
    missing_count: int
    missing_percentage: float
    unique_count: int
    hxl_tag: Optional[str] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    is_date: bool = False
    date_format: Optional[str] = None
    sample_values: List[Any] = field(default_factory=list)

    # Observation metadata: whether string column values appear numeric
    is_numeric_string: bool = False
    potential_type: Optional[str] = None

    # Nested schema representation (for complex object / array columns)
    nested_schema: Optional[Dict[str, Any]] = None

    # XLSForm-specific metadata (None for non-XLSForm datasets)
    xlsform_type: Optional[str] = None       # raw XLSForm type string, e.g. "select_one gender_list"
    xlsform_label: Optional[str] = None      # human-readable question label
    xlsform_required: Optional[bool] = None  # True/False/None (None means not specified)
    xlsform_constraint: Optional[str] = None # original XLSForm constraint expression (not enforced in JSON Schema)
    xlsform_choices: Optional[List[str]] = None  # choice names for select_one / select_multiple


@dataclass
class UnifiedSchema:
    """Unified internal representation of a profiled dataset."""
    format_name: str
    row_count: int
    column_count: int
    columns: Dict[str, ColumnProfile]
    metadata: Dict[str, Any] = field(default_factory=dict)
