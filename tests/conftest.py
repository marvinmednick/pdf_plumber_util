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


# TOC Testing Infrastructure

@pytest.fixture
def toc_test_fixtures():
    """Provide access to TOC test fixtures and utilities."""
    from .fixtures.toc_fixtures import TOCTestFixtures
    return TOCTestFixtures


@pytest.fixture
def minimal_toc_fixture(toc_test_fixtures):
    """Single page with basic TOC structure for unit testing."""
    return toc_test_fixtures.create_comprehensive_toc_fixture(
        pages_with_toc=[1],
        pages_without_toc=[],
        fixture_name="minimal_toc_single_page"
    )


@pytest.fixture
def mixed_content_toc_fixture(toc_test_fixtures):
    """Mixed content fixture with both TOC and non-TOC pages."""
    return toc_test_fixtures.create_comprehensive_toc_fixture(
        pages_with_toc=[2, 3],
        pages_without_toc=[1, 4],
        fixture_name="mixed_toc_and_regular_content"
    )


@pytest.fixture
def hierarchical_toc_fixture(toc_test_fixtures):
    """Multi-page hierarchical TOC structure for comprehensive testing."""
    return toc_test_fixtures.create_comprehensive_toc_fixture(
        pages_with_toc=[1, 2, 3],
        pages_without_toc=[],
        fixture_name="hierarchical_multi_page_toc"
    )


@pytest.fixture
def h264_toc_fixture_path():
    """Path to the H.264 TOC golden document fixture."""
    return Path(__file__).parent / "fixtures" / "test_h264_toc_pages.json"


@pytest.fixture
def h264_no_toc_fixture_path():
    """Path to the H.264 no-TOC golden document fixture."""
    return Path(__file__).parent / "fixtures" / "test_table_titles_not_section_headings.json"


@pytest.fixture
def mock_toc_enhanced_llm_response():
    """Mock LLM response for TOC-enhanced HeaderFooterAnalysisState testing."""
    return {
        "per_page_analysis": [
            {
                "page_index": 0,
                "document_elements": {
                    "section_headings": [
                        {
                            "text": "Table of Contents",
                            "confidence": "High",
                            "bbox": {"x0": 72, "top": 100, "x1": 300, "bottom": 116}
                        }
                    ],
                    "figure_titles": [],
                    "table_titles": [],
                    "table_of_contents": [
                        {
                            "text": "1. Introduction",
                            "page_number": "5",
                            "level": 1,
                            "bbox": {"x0": 72, "top": 130, "x1": 250, "bottom": 146}
                        },
                        {
                            "text": "1.1 Overview",
                            "page_number": "5",
                            "level": 2,
                            "bbox": {"x0": 92, "top": 150, "x1": 200, "bottom": 166}
                        },
                        {
                            "text": "2. Methods",
                            "page_number": "12",
                            "level": 1,
                            "bbox": {"x0": 72, "top": 170, "x1": 180, "bottom": 186}
                        }
                    ]
                }
            }
        ],
        "document_element_analysis": {
            "table_of_contents": {
                "detected": True,
                "toc_pages": [0],
                "structure_type": "hierarchical",
                "patterns": [
                    "Numbered sections (1., 1.1, 2.)",
                    "Page number references with dot leaders",
                    "Hierarchical indentation structure"
                ]
            }
        }
    }


@pytest.fixture
def mock_no_toc_llm_response():
    """Mock LLM response for documents without TOC content."""
    return {
        "per_page_analysis": [
            {
                "page_index": 0,
                "document_elements": {
                    "section_headings": [
                        {
                            "text": "Chapter 5: Implementation",
                            "confidence": "High",
                            "bbox": {"x0": 72, "top": 100, "x1": 350, "bottom": 116}
                        }
                    ],
                    "figure_titles": [],
                    "table_titles": [
                        {
                            "text": "Table 5-1: Configuration Parameters",
                            "confidence": "High",
                            "bbox": {"x0": 72, "top": 200, "x1": 400, "bottom": 216}
                        }
                    ],
                    "table_of_contents": []  # No TOC entries
                }
            }
        ],
        "document_element_analysis": {
            "table_of_contents": {
                "detected": False,
                "toc_pages": [],
                "structure_type": "none",
                "patterns": []
            }
        }
    }


@pytest.fixture
def toc_analysis_context():
    """Standard context structure for TOC analysis testing."""
    return {
        'save_results': False,
        'output_dir': None,
        'config': None,
        'workflow_results': {},
        'accumulated_knowledge': {}
    }