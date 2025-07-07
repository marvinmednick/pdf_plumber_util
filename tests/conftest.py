"""Shared pytest fixtures for PDF Plumb tests."""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, List


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_lines_data():
    """Sample lines data for testing analysis functions."""
    return [
        {
            "page": 1,
            "lines": [
                {
                    "line_number": 1,
                    "text": "Chapter 1: Introduction",
                    "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116},
                    "text_segments": [
                        {
                            "font": "Arial-Bold",
                            "reported_size": 14.0,
                            "rounded_size": 14.0,
                            "direction": "upright",
                            "text": "Chapter 1: Introduction",
                            "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116}
                        }
                    ],
                    "predominant_size": 14.0,
                    "predominant_font": "Arial-Bold",
                    "predominant_size_coverage": 100.0,
                    "predominant_font_coverage": 100.0,
                    "gap_before": 18.0,
                    "gap_after": 12.0
                },
                {
                    "line_number": 2,
                    "text": "This is the first paragraph of body text.",
                    "bbox": {"x0": 72, "top": 128, "x1": 400, "bottom": 140},
                    "text_segments": [
                        {
                            "font": "Arial",
                            "reported_size": 12.0,
                            "rounded_size": 12.0,
                            "direction": "upright",
                            "text": "This is the first paragraph of body text.",
                            "bbox": {"x0": 72, "top": 128, "x1": 400, "bottom": 140}
                        }
                    ],
                    "predominant_size": 12.0,
                    "predominant_font": "Arial",
                    "predominant_size_coverage": 100.0,
                    "predominant_font_coverage": 100.0,
                    "gap_before": 12.0,
                    "gap_after": 6.0
                }
            ],
            "page_width": 612,
            "page_height": 792
        }
    ]


@pytest.fixture
def sample_lines_file(temp_output_dir, sample_lines_data):
    """Create a temporary lines JSON file for testing."""
    lines_file = temp_output_dir / "test_lines.json"
    with open(lines_file, 'w') as f:
        json.dump(sample_lines_data, f, indent=2)
    return lines_file


@pytest.fixture
def sample_spacing_rules():
    """Sample spacing rules for testing contextual analysis."""
    return {
        12.0: {
            'line_spacing_range': (5.0, 7.0),
            'para_spacing_max': 13.2,
            'most_common_gap': 6.0,
            'gap_distribution': {6.0: 10, 12.0: 5, 18.0: 2},
            'line_gaps': {6.0: 10},
            'para_gaps': {12.0: 5},
            'section_gaps': {18.0: 2},
            'total_gaps': 17,
            'total_lines': 20
        },
        14.0: {
            'line_spacing_range': (6.0, 8.0),
            'para_spacing_max': 15.4,
            'most_common_gap': 7.0,
            'gap_distribution': {7.0: 5, 14.0: 3, 21.0: 1},
            'line_gaps': {7.0: 5},
            'para_gaps': {14.0: 3},
            'section_gaps': {21.0: 1},
            'total_gaps': 9,
            'total_lines': 8
        }
    }