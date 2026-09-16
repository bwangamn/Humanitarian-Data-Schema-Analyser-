from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ColumnProfile:
    """Statistical and structural metadata for a single field/column."""
    name: str
    data_type: str
    inferred_type: str
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


@dataclass
class UnifiedSchema:
    """Unified internal representation of a profiled dataset."""
    format_name: str
    row_count: int
    column_count: int
    columns: Dict[str, ColumnProfile]
    metadata: Dict[str, Any] = field(default_factory=dict)
