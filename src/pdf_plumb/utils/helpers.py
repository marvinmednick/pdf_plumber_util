"""Shared helper functions for the pdf_plumb package."""

import re
from typing import Any, Dict, List, Optional
from ..config import get_config


def round_to_nearest(value: float, nearest: float = None) -> float:
    """Round value to the nearest specified increment (e.g., 0.5 or 0.25)."""
    if nearest is None:
        config = get_config()
        nearest = config.round_to_nearest_pt
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
    """Get the base name for output files.
    
    Args:
        input_path: Path to the input file
        basename: Optional explicit base name to use
        
    Returns:
        Base name for output files, with any known intermediate file suffixes removed
    """
    import os
    if basename:
        return basename
        
    # Get the filename without extension
    base = os.path.splitext(os.path.basename(input_path))[0]
    
    # Remove known intermediate file suffixes
    known_suffixes = ['_lines', '_full_lines', '_words', '_compare', '_info']
    for suffix in known_suffixes:
        if base.endswith(suffix):
            return base[:-len(suffix)]
            
    return base 