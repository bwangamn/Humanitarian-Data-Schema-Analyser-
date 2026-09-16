from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import pandas as pd


@dataclass
class ParsedDataset:
    """Standard internal container representing a parsed dataset."""
    df: pd.DataFrame
    format_name: str
    hxl_tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """Abstract base parser interface for humanitarian data formats."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def parse(self) -> ParsedDataset:
        """Parse the input file and return a ParsedDataset object."""
        pass
