"""TOC test fixtures and utilities for PDF document analysis testing.

This module provides utilities for creating, validating, and managing TOC test data
for comprehensive testing of TOC detection and analysis capabilities.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class TOCTestFixtures:
    """Utility class for managing TOC test fixtures and validation."""

    @staticmethod
    def create_synthetic_toc_page(
        page_number: int,
        toc_entries: List[Dict[str, Any]],
        has_header: bool = True,
        page_width: float = 612,
        page_height: float = 792
    ) -> Dict[str, Any]:
        """Create synthetic page data with TOC entries for unit testing.
        
        Args:
            page_number: Page number for the synthetic page
            toc_entries: List of TOC entries with text, page_number, level
            has_header: Whether to include TOC header ("Table of Contents")
            page_width: Page width in points
            page_height: Page height in points
            
        Returns:
            Synthetic page data in PDF analysis format
        """
        lines = []
        line_number = 1
        y_position = 100
        
        # Add TOC header if requested
        if has_header:
            lines.append({
                "line_number": line_number,
                "text": "Table of Contents",
                "bbox": {"x0": 72, "top": y_position, "x1": 300, "bottom": y_position + 16},
                "text_segments": [{
                    "font": "TimesNewRomanPS-BoldMT",
                    "reported_size": 14.0,
                    "rounded_size": 14.0,
                    "direction": "upright",
                    "text": "Table of Contents",
                    "bbox": {"x0": 72, "top": y_position, "x1": 300, "bottom": y_position + 16}
                }],
                "predominant_size": 14.0,
                "predominant_font": "TimesNewRomanPS-BoldMT",
                "predominant_size_coverage": 100.0,
                "predominant_font_coverage": 100.0,
                "gap_before": 0.0,
                "gap_after": 20.0
            })
            line_number += 1
            y_position += 30
        
        # Add TOC entries
        for entry in toc_entries:
            # Calculate indentation based on level
            indent = 72 + (entry.get('level', 1) - 1) * 20
            
            # Create TOC entry text with dot leaders
            text = entry['text']
            page_ref = entry.get('page_number', '1')
            
            # Simulate dot leader pattern
            if len(text) + len(page_ref) < 70:
                dots_needed = 70 - len(text) - len(page_ref)
                dot_leader = '.' * min(dots_needed, 30)
                full_text = f"{text} {dot_leader} {page_ref}"
            else:
                full_text = f"{text} {page_ref}"
            
            lines.append({
                "line_number": line_number,
                "text": full_text,
                "bbox": {"x0": indent, "top": y_position, "x1": 500, "bottom": y_position + 12},
                "text_segments": [{
                    "font": "TimesNewRomanPSMT",
                    "reported_size": 10.0,
                    "rounded_size": 10.0,
                    "direction": "upright",
                    "text": full_text,
                    "bbox": {"x0": indent, "top": y_position, "x1": 500, "bottom": y_position + 12}
                }],
                "predominant_size": 10.0,
                "predominant_font": "TimesNewRomanPSMT",
                "predominant_size_coverage": 100.0,
                "predominant_font_coverage": 100.0,
                "gap_before": 12.0,
                "gap_after": 0.0
            })
            line_number += 1
            y_position += 15
        
        # Create page structure
        return {
            "page": page_number,
            "blocks": [{
                "lines": lines,
                "text": "\n".join(line["text"] for line in lines),
                "predominant_size": 10.0,
                "gap_before": 0.0,
                "gap_after": 0.0,
                "size_coverage": 1.0,
                "predominant_font": "TimesNewRomanPSMT",
                "font_coverage": 1.0,
                "bbox": {
                    "x0": min(line["bbox"]["x0"] for line in lines),
                    "x1": max(line["bbox"]["x1"] for line in lines),
                    "top": min(line["bbox"]["top"] for line in lines),
                    "bottom": max(line["bbox"]["bottom"] for line in lines)
                }
            }],
            "page_width": page_width,
            "page_height": page_height
        }

    @staticmethod
    def create_comprehensive_toc_fixture(
        pages_with_toc: List[int],
        pages_without_toc: List[int] = None,
        fixture_name: str = "comprehensive_toc_test"
    ) -> Dict[str, Any]:
        """Create comprehensive TOC test fixture with mixed content.
        
        Args:
            pages_with_toc: List of page numbers that should contain TOC
            pages_without_toc: List of page numbers without TOC content
            fixture_name: Name for the test fixture
            
        Returns:
            Complete fixture data structure for testing
        """
        pages_without_toc = pages_without_toc or []
        all_pages = []
        
        # Sample hierarchical TOC entries
        sample_toc_entries = [
            {"text": "1. Introduction", "page_number": "5", "level": 1},
            {"text": "1.1 Overview", "page_number": "5", "level": 2},
            {"text": "1.2 Scope", "page_number": "7", "level": 2},
            {"text": "1.2.1 Technical Requirements", "page_number": "8", "level": 3},
            {"text": "2. Methodology", "page_number": "12", "level": 1},
            {"text": "2.1 Analysis Framework", "page_number": "15", "level": 2},
            {"text": "2.2 Implementation", "page_number": "18", "level": 2},
            {"text": "3. Results and Discussion", "page_number": "25", "level": 1},
            {"text": "3.1 Experimental Results", "page_number": "27", "level": 2},
            {"text": "3.1.1 Performance Metrics", "page_number": "29", "level": 3},
            {"text": "3.1.2 Validation Tests", "page_number": "31", "level": 3}
        ]
        
        # Create pages without TOC
        for page_num in pages_without_toc:
            page_data = {
                "page": page_num,
                "blocks": [{
                    "lines": [{
                        "line_number": 1,
                        "text": f"This is regular content on page {page_num} with no TOC.",
                        "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116},
                        "text_segments": [{
                            "font": "TimesNewRomanPSMT",
                            "reported_size": 12.0,
                            "rounded_size": 12.0,
                            "direction": "upright",
                            "text": f"This is regular content on page {page_num} with no TOC.",
                            "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116}
                        }],
                        "predominant_size": 12.0,
                        "predominant_font": "TimesNewRomanPSMT",
                        "predominant_size_coverage": 100.0,
                        "predominant_font_coverage": 100.0,
                        "gap_before": 0.0,
                        "gap_after": 12.0
                    }],
                    "text": f"This is regular content on page {page_num} with no TOC.",
                    "predominant_size": 12.0,
                    "gap_before": 0.0,
                    "gap_after": 12.0,
                    "size_coverage": 1.0,
                    "predominant_font": "TimesNewRomanPSMT",
                    "font_coverage": 1.0
                }],
                "page_width": 612,
                "page_height": 792
            }
            all_pages.append(page_data)
        
        # Create pages with TOC - distribute entries across pages
        entries_per_page = max(1, len(sample_toc_entries) // len(pages_with_toc))
        
        for i, page_num in enumerate(pages_with_toc):
            start_idx = i * entries_per_page
            end_idx = start_idx + entries_per_page
            if i == len(pages_with_toc) - 1:  # Last page gets remaining entries
                end_idx = len(sample_toc_entries)
            
            page_entries = sample_toc_entries[start_idx:end_idx]
            has_header = (i == 0)  # Only first TOC page has header
            
            page_data = TOCTestFixtures.create_synthetic_toc_page(
                page_num, page_entries, has_header
            )
            all_pages.append(page_data)
        
        # Sort pages by page number
        all_pages.sort(key=lambda p: p["page"])
        
        return {
            "test_info": {
                "description": f"Comprehensive TOC test fixture: {fixture_name}",
                "source_document": "synthetic_fixture",
                "extracted_pages": sorted(pages_without_toc + pages_with_toc),
                "total_pages": len(all_pages),
                "created_by": "TOCTestFixtures.create_comprehensive_toc_fixture",
                "toc_structure": {
                    "pages_with_toc": pages_with_toc,
                    "pages_without_toc": pages_without_toc,
                    "hierarchical_levels": 3,
                    "total_entries": len(sample_toc_entries),
                    "has_multi_level_nesting": True
                }
            },
            "document_info": {
                "original_total_pages": len(all_pages),
                "page_dimensions": {"width": 612, "height": 792},
                "extraction_method": "synthetic_generation"
            },
            "pages": all_pages
        }

    @staticmethod
    def validate_toc_fixture_structure(fixture_data: Dict[str, Any]) -> List[str]:
        """Validate TOC fixture structure for completeness.
        
        Args:
            fixture_data: Fixture data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ['test_info', 'document_info', 'pages']
        for field in required_fields:
            if field not in fixture_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate test_info structure
        if 'test_info' in fixture_data:
            test_info = fixture_data['test_info']
            required_test_fields = ['description', 'extracted_pages', 'total_pages']
            for field in required_test_fields:
                if field not in test_info:
                    errors.append(f"Missing required test_info field: {field}")
        
        # Validate pages structure
        if 'pages' in fixture_data:
            pages = fixture_data['pages']
            if not isinstance(pages, list):
                errors.append("Pages must be a list")
            elif not pages:
                errors.append("Pages cannot be empty")
            else:
                # Validate first page structure
                sample_page = pages[0]
                required_page_fields = ['page', 'blocks']
                for field in required_page_fields:
                    if field not in sample_page:
                        errors.append(f"Missing required page field: {field}")
                
                # Check for blocks structure
                if 'blocks' in sample_page and sample_page['blocks']:
                    sample_block = sample_page['blocks'][0]
                    if 'lines' not in sample_block:
                        errors.append("Blocks must contain lines")
                    elif sample_block['lines']:
                        sample_line = sample_block['lines'][0]
                        required_line_fields = ['text', 'bbox']
                        for field in required_line_fields:
                            if field not in sample_line:
                                errors.append(f"Missing required line field: {field}")
        
        return errors

    @staticmethod
    def extract_expected_toc_patterns(fixture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract expected TOC patterns from fixture for validation.
        
        Args:
            fixture_data: Fixture data to analyze
            
        Returns:
            Dictionary of expected patterns for test validation
        """
        patterns = {
            'has_toc_header': False,
            'hierarchical_entries': [],
            'page_references': [],
            'multi_level_sections': [],
            'toc_pages': []
        }
        
        if 'pages' not in fixture_data:
            return patterns
        
        for page in fixture_data['pages']:
            page_num = page['page']
            has_toc_content = False
            
            for block in page.get('blocks', []):
                for line in block.get('lines', []):
                    text = line.get('text', '')
                    
                    # Check for TOC header
                    if 'Table of Contents' in text:
                        patterns['has_toc_header'] = True
                        has_toc_content = True
                    
                    # Check for hierarchical entries (e.g., "1.1", "2.3.1")
                    import re
                    if re.search(r'\d+\.\d+', text):
                        patterns['hierarchical_entries'].append(text.strip())
                        has_toc_content = True
                    
                    # Check for page references (numbers at end of line)
                    if re.search(r'\.\s*\d+\s*$', text):
                        patterns['page_references'].append(text.strip())
                        has_toc_content = True
                    
                    # Check for multi-level sections (e.g., "1.2.3")
                    if re.search(r'\d+\.\d+\.\d+', text):
                        patterns['multi_level_sections'].append(text.strip())
            
            if has_toc_content:
                patterns['toc_pages'].append(page_num)
        
        return patterns


def load_toc_fixture(fixture_path: Path) -> Dict[str, Any]:
    """Load TOC fixture from JSON file with validation.
    
    Args:
        fixture_path: Path to the fixture file
        
    Returns:
        Fixture data dictionary
        
    Raises:
        FileNotFoundError: If fixture file doesn't exist
        ValueError: If fixture structure is invalid
    """
    if not fixture_path.exists():
        raise FileNotFoundError(f"TOC fixture not found: {fixture_path}")
    
    with open(fixture_path, 'r') as f:
        fixture_data = json.load(f)
    
    # Validate fixture structure
    errors = TOCTestFixtures.validate_toc_fixture_structure(fixture_data)
    if errors:
        raise ValueError(f"Invalid fixture structure: {'; '.join(errors)}")
    
    return fixture_data


def save_toc_fixture(fixture_data: Dict[str, Any], fixture_path: Path) -> None:
    """Save TOC fixture to JSON file with validation.
    
    Args:
        fixture_data: Fixture data to save
        fixture_path: Path where to save the fixture
        
    Raises:
        ValueError: If fixture structure is invalid
    """
    # Validate before saving
    errors = TOCTestFixtures.validate_toc_fixture_structure(fixture_data)
    if errors:
        raise ValueError(f"Cannot save invalid fixture: {'; '.join(errors)}")
    
    # Create parent directory if needed
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(fixture_path, 'w') as f:
        json.dump(fixture_data, f, indent=2)


# Commonly used test fixtures for different scenarios
MINIMAL_TOC_FIXTURE = TOCTestFixtures.create_comprehensive_toc_fixture(
    pages_with_toc=[1],
    pages_without_toc=[],
    fixture_name="minimal_single_page_toc"
)

MIXED_CONTENT_FIXTURE = TOCTestFixtures.create_comprehensive_toc_fixture(
    pages_with_toc=[2, 3],
    pages_without_toc=[1, 4],
    fixture_name="mixed_content_toc_and_regular"
)

HIERARCHICAL_TOC_FIXTURE = TOCTestFixtures.create_comprehensive_toc_fixture(
    pages_with_toc=[1, 2, 3],
    pages_without_toc=[],
    fixture_name="comprehensive_hierarchical_toc"
)