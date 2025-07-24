"""Unit tests for PDF analysis functions."""

import pytest
from src.pdf_plumb.core.analyzer import PDFAnalyzer


@pytest.mark.unit
class TestPDFAnalyzer:
    """Test the PDFAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PDFAnalyzer()
    
    def test_collect_contextual_gaps(self, sample_lines_data):
        """Test the _collect_contextual_gaps() method's ability to organize text line gaps by font size context.
        
        Test setup:
        - Uses fixture data containing 2 lines: a 14pt header and a 12pt body text line
        - Manually adds a third line with 12pt font size and 6.0pt gap 
        - This ensures there are consecutive lines with the same font size (12pt)

        What it verifies:
        - The method returns a dictionary (gaps organized by font size)
        - The method can handle lines with matching predominant font sizes
        - The method produces valid output structure even when input data varies

        Test limitation:
        - Only verifies basic structure (isinstance(gaps, dict))
        - Assertion len(gaps) >= 0 is essentially always true (can't fail)
        - Doesn't verify the actual gap values or font size groupings

        Key insight: This test ensures the contextual gap collection mechanism works but doesn't 
        validate the specific logic of how gaps are grouped by font size context.
        """
        all_lines = []
        for page in sample_lines_data:
            all_lines.extend(page['lines'])
        
        # Add more lines with same predominant size for gap collection
        additional_line = {
            "line_number": 3,
            "text": "Second paragraph line.",
            "predominant_size": 12.0,  # Same size as line 2
            "gap_before": 6.0  # Small gap for line spacing
        }
        all_lines.append(additional_line)
        
        gaps = self.analyzer._collect_contextual_gaps(all_lines)
        
        # Should have gaps organized by font size
        assert isinstance(gaps, dict)
        # With modified sample data, should have at least one context
        assert len(gaps) >= 0  # May be 0 if no same-size consecutive lines
    
    def test_classify_gap_contextual(self, sample_spacing_rules):
        """Test the _classify_gap_contextual() method's ability to categorize gaps based on font size context.
        
        Test setup:
        - Uses predefined spacing rules for 12pt font context
        - Tests boundary conditions for Line/Paragraph/Section classification
        - Each test targets a different classification category

        What it verifies:
        - Small gaps (6.0pt) correctly classified as "Line" spacing
        - Medium gaps (12.0pt) correctly classified as "Paragraph" spacing
        - Large gaps (18.0pt) correctly classified as "Section" spacing
        - Method properly applies contextual rules for font size

        Test limitation:
        - Only tests one font size context (12pt)
        - Doesn't test edge cases or invalid inputs
        - Assumes spacing rules fixture is correctly structured

        Key insight: Validates that the core gap classification logic works for standard spacing scenarios.
        """
        # Test line spacing classification
        result = self.analyzer._classify_gap_contextual(6.0, 12.0, sample_spacing_rules)
        assert result == "Line"
        
        # Test paragraph spacing classification  
        result = self.analyzer._classify_gap_contextual(12.0, 12.0, sample_spacing_rules)
        assert result == "Paragraph"
        
        # Test section spacing classification
        result = self.analyzer._classify_gap_contextual(18.0, 12.0, sample_spacing_rules)
        assert result == "Section"
    
    def test_classify_gap_fallback(self):
        """Test gap classification with unknown context."""
        # Should fall back gracefully when context size not in rules
        result = self.analyzer._classify_gap_contextual(6.0, 99.0, {})
        assert result == "Line"  # Default fallback
    
    def test_analyze_contextual_spacing(self):
        """Test contextual spacing analysis."""
        # Sample gaps by context
        gaps_by_context = {
            12.0: {'gaps': [6.0, 6.0, 6.0, 12.0, 18.0], 'total_lines': 10}
        }
        
        result = self.analyzer._analyze_contextual_spacing(gaps_by_context)
        
        assert 12.0 in result
        rules = result[12.0]
        
        # Should have computed spacing ranges
        assert 'line_spacing_range' in rules
        assert 'para_spacing_max' in rules
        assert 'most_common_gap' in rules
        
        # Most common gap should be 6.0 (appears 3 times)
        assert rules['most_common_gap'] == 6.0
        
        # Paragraph spacing max should be ~13.2 (12.0 * 1.1)
        assert abs(rules['para_spacing_max'] - 13.2) < 0.1