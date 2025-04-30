"""Shared helper functions for the pdf_plumb package."""

import re
from typing import Any, Dict, List, Optional
from .constants import ROUND_TO_NEAREST_PT


def round_to_nearest(value: float, nearest: float = ROUND_TO_NEAREST_PT) -> float:
    """Round value to the nearest specified increment (e.g., 0.5 or 0.25)."""
    return round(value / nearest) * nearest


def normalize_line(line: str) -> str:
    """Normalize whitespace in a line of text."""
    return re.sub(r'\s+', ' ', line).strip()


def ensure_output_dir(output_dir: str) -> str:
    """Ensure the output directory exists and return its path."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def get_base_name(input_path: str, basename: Optional[str] = None) -> str:
    """Get the base name for output files."""
    import os
    if basename:
        return basename
    return os.path.splitext(os.path.basename(input_path))[0]


def save_json(data: Any, path: str, indent: int = 2) -> None:
    """Save data to a JSON file."""
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False) 