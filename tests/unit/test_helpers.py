"""Unit tests for utility helper functions."""

import pytest
from pathlib import Path
from src.pdf_plumb.utils.helpers import normalize_line, get_base_name, round_to_nearest


class TestNormalizeLine:
    """Test the normalize_line function."""
    
    def test_normalize_whitespace(self):
        """Test that multiple whitespace is normalized to single spaces."""
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
        """Test handling of whitespace-only string."""
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
        """Test complex filename handling."""
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
        """Test rounding to nearest 0.25."""
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