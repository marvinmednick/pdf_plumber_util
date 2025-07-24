"""Unit tests for utility helper functions."""

import pytest
from pathlib import Path
from src.pdf_plumb.utils.helpers import normalize_line, get_base_name, round_to_nearest


class TestNormalizeLine:
    """Test the normalize_line function."""
    
    def test_normalize_whitespace(self):
        """Test normalize_line() collapses multiple whitespace characters (spaces, tabs) into single spaces.
        
        Test setup:
        - Input string contains multiple consecutive spaces and tabs between words
        - Tests the core whitespace normalization functionality
        
        What it verifies:
        - Multiple spaces (4 spaces) are reduced to single space
        - Multiple tabs (\t\t) are reduced to single space 
        - Mixed whitespace types are handled consistently
        - Word content is preserved unchanged
        
        Key insight: Ensures consistent spacing normalization for PDF text extraction cleanup.
        """
        assert normalize_line("word1    word2\t\tword3") == "word1 word2 word3"
    
    def test_strip_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        assert normalize_line("  word1 word2  ") == "word1 word2"
    
    def test_normalize_newlines(self):
        """Test that newlines are converted to spaces."""
        assert normalize_line("word1\nword2\r\nword3") == "word1 word2 word3"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_line("") == ""
    
    def test_whitespace_only(self):
        """Test normalize_line() properly handles strings containing only whitespace characters.
        
        Test setup:
        - Input string contains mixed whitespace: spaces, tabs, and newlines
        - No actual text content to preserve
        - Tests edge case where entire string should be eliminated
        
        What it verifies:
        - Whitespace-only strings are reduced to empty string
        - All whitespace types (spaces, tabs, newlines) are handled
        - Function doesn't leave residual whitespace characters
        - Edge case handling prevents unexpected output
        
        Key insight: Ensures empty lines in PDF text are properly cleaned rather than becoming single spaces.
        """
        assert normalize_line("   \t\n  ") == ""


class TestGetBaseName:
    """Test the get_base_name function."""
    
    def test_pdf_file_without_custom_name(self):
        """Test extracting base name from PDF file path."""
        assert get_base_name("/path/to/document.pdf") == "document"
        assert get_base_name("document.pdf") == "document"
    
    def test_pdf_file_with_custom_name(self):
        """Test using custom base name when provided."""
        assert get_base_name("/path/to/document.pdf", "custom_name") == "custom_name"
    
    def test_complex_filename(self):
        """Test get_base_name() handles complex filenames with hyphens, underscores, and version numbers.
        
        Test setup:
        - Input path contains complex filename: "my-document_v2.pdf"
        - Tests realistic filename with mixed separators and version indicators
        - Verifies preservation of meaningful filename components
        
        What it verifies:
        - Hyphens in filename are preserved ("my-document")
        - Underscores in filename are preserved ("_v2")
        - Version numbers and patterns are maintained
        - Only the .pdf extension is removed, not other punctuation
        
        Key insight: Ensures base name extraction preserves meaningful filename structure for output file naming.
        """
        assert get_base_name("/path/to/my-document_v2.pdf") == "my-document_v2"
    
    def test_no_extension(self):
        """Test filename without extension."""
        assert get_base_name("/path/to/document") == "document"


class TestRoundToNearest:
    """Test the round_to_nearest function."""
    
    def test_round_to_half(self):
        """Test rounding to nearest 0.5."""
        assert round_to_nearest(12.3, 0.5) == 12.5
        assert round_to_nearest(12.1, 0.5) == 12.0
        assert round_to_nearest(12.7, 0.5) == 12.5
    
    def test_round_to_quarter(self):
        """Test round_to_nearest() accuracy with quarter-point precision for font size analysis.
        
        Test setup:
        - Tests three values around quarter boundaries: 12.3, 12.1, 12.15
        - Uses 0.25 increment which is common for font size rounding
        - Tests both rounding up (12.3→12.25) and down (12.1→12.0) scenarios
        
        What it verifies:
        - 12.3 rounds down to nearest quarter (12.25)
        - 12.1 rounds down to whole number (12.0) 
        - 12.15 rounds up to next quarter (12.25) - tests exact midpoint
        - Quarter-point precision is maintained consistently
        
        Key insight: Validates quarter-point rounding accuracy needed for precise font size categorization in PDF analysis.
        """
        assert round_to_nearest(12.3, 0.25) == 12.25
        assert round_to_nearest(12.1, 0.25) == 12.0
        assert round_to_nearest(12.15, 0.25) == 12.25
    
    def test_round_to_integer(self):
        """Test rounding to nearest integer."""
        assert round_to_nearest(12.3, 1.0) == 12.0
        assert round_to_nearest(12.7, 1.0) == 13.0
    
    def test_exact_values(self):
        """Test values that are already exact."""
        assert round_to_nearest(12.5, 0.5) == 12.5
        assert round_to_nearest(12.0, 0.5) == 12.0