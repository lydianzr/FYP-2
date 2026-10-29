# modules/extract/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from modules.schema import get_empty_schema

class BaseExtractor(ABC):
    """Abstract base class for all logistics document extractors."""

    @abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extracts key attributes and returns populated Canonical Schema dict."""
        pass

    def _clean_schema(self, raw_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Enforces schema consistency against CANONICAL_SCHEMA key contract."""
        schema = get_empty_schema()
        for key in schema.keys():
            if key in raw_dict:
                schema[key] = raw_dict[key]
        return schema