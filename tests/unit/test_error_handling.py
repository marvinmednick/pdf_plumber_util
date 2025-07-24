"""
Tests for enhanced error handling and exception classes.

Tests the structured exception hierarchy, error messages, and suggestions
introduced in Phase 2.2.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.pdf_plumb.core.exceptions import (
    PDFPlumbError,
    PDFExtractionError,
    PDFNotFoundError,
    PDFCorruptedError,
    PDFPermissionError,
    AnalysisError,
    SpacingAnalysisError,
    BlockFormationError,
    HeaderFooterError,
    VisualizationError,
    ConfigurationError,
    FileHandlingError,
    OutputWriteError,
    MemoryError as PDFMemoryError,
    ValidationError
)
from src.pdf_plumb.core.extractor import PDFExtractor
from src.pdf_plumb.core.analyzer import DocumentAnalyzer, PDFAnalyzer


class TestExceptionHierarchy:
    """Test the exception class hierarchy and basic functionality."""
    
    def test_base_exception_creation(self):
        """Test PDFPlumbError base exception creation."""
        error = PDFPlumbError(
            message="Test error",
            suggestion="Test suggestion",
            context={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.suggestion == "Test suggestion"
        assert error.context == {"key": "value"}
        assert str(error) == "Test error"
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from PDFPlumbError."""
        exceptions = [
            PDFExtractionError("test"),
            AnalysisError("test"),
            VisualizationError("test"),
            ConfigurationError("test"),
            FileHandlingError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, PDFPlumbError)
    
    def test_pdf_not_found_error(self):
        """Test PDFNotFoundError with automatic suggestion."""
        error = PDFNotFoundError("/nonexistent/file.pdf")
        
        assert "not found" in error.message
        assert "Check the file path" in error.suggestion
        assert error.context["pdf_path"] == "/nonexistent/file.pdf"
    
    def test_pdf_corrupted_error(self):
        """Test PDFCorruptedError with automatic suggestion."""
        error = PDFCorruptedError("/corrupted/file.pdf")
        
        assert "corrupted" in error.message
        assert "opening the PDF in a viewer" in error.suggestion
        assert error.context["pdf_path"] == "/corrupted/file.pdf"
    
    def test_analysis_error_with_context(self):
        """Test AnalysisError with stage and page context."""
        error = AnalysisError(
            "Spacing analysis failed",
            analysis_stage="spacing_analysis",
            page_number=5
        )
        
        assert error.context["analysis_stage"] == "spacing_analysis"
        assert error.context["page_number"] == 5


class TestExtractorErrorHandling:
    """Test error handling in the PDFExtractor class."""
    
    def test_pdf_not_found_handling(self):
        """Test that PDFNotFoundError is raised for missing files."""
        extractor = PDFExtractor()
        
        with pytest.raises(PDFNotFoundError) as exc_info:
            extractor.extract_from_pdf("/nonexistent/file.pdf")
        
        assert "/nonexistent/file.pdf" in str(exc_info.value)
        assert exc_info.value.suggestion is not None
    
    @patch('src.pdf_plumb.core.extractor.pdfplumber.open')
    def test_permission_error_handling(self, mock_open):
        """Test handling of PDF permission errors."""
        # Create a temporary file that exists
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Mock pdfplumber to raise PermissionError
            mock_open.side_effect = PermissionError("Access denied")
            
            extractor = PDFExtractor()
            
            with pytest.raises(PDFPermissionError) as exc_info:
                extractor.extract_from_pdf(tmp_path)
            
            assert "permission" in str(exc_info.value).lower()
            assert exc_info.value.suggestion is not None
            assert exc_info.value.original_error is not None
        finally:
            os.unlink(tmp_path)
    
    @patch('src.pdf_plumb.core.extractor.pdfplumber.open')
    def test_corrupted_pdf_handling(self, mock_open):
        """Test handling of corrupted PDF files."""
        # Create a temporary file that exists
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Mock pdfplumber to raise ValueError (common for corrupted PDFs)
            mock_open.side_effect = ValueError("Invalid PDF structure")
            
            extractor = PDFExtractor()
            
            with pytest.raises(PDFCorruptedError) as exc_info:
                extractor.extract_from_pdf(tmp_path)
            
            assert "corrupted" in str(exc_info.value).lower()
            assert exc_info.value.suggestion is not None
        finally:
            os.unlink(tmp_path)


class TestAnalyzerErrorHandling:
    """Test error handling in the DocumentAnalyzer class."""
    
    def test_missing_lines_file(self):
        """Test handling of missing lines file."""
        analyzer = DocumentAnalyzer()
        
        with pytest.raises(FileHandlingError) as exc_info:
            analyzer.analyze_document("/nonexistent/lines.json")
        
        assert "not found" in str(exc_info.value)
        assert exc_info.value.context["file_path"] == "/nonexistent/lines.json"
    
    def test_invalid_json_format(self):
        """Test handling of invalid JSON in lines file."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write("{invalid json content")
            tmp_path = tmp.name
        
        try:
            analyzer = DocumentAnalyzer()
            
            with pytest.raises(ValidationError) as exc_info:
                analyzer.analyze_document(tmp_path)
            
            assert "json" in str(exc_info.value).lower()
            assert exc_info.value.context["file_path"] == tmp_path
        finally:
            os.unlink(tmp_path)
    
    @patch('src.pdf_plumb.core.analyzer.get_config')
    def test_spacing_analysis_error(self, mock_config):
        """Test handling of spacing analysis errors."""
        # Mock config to raise an error
        mock_config.side_effect = KeyError("missing_config_key")
        
        analyzer = PDFAnalyzer()
        
        with pytest.raises(SpacingAnalysisError) as exc_info:
            analyzer._analyze_contextual_spacing({})
        
        assert "spacing analysis" in str(exc_info.value).lower()
        assert exc_info.value.suggestion is not None


class TestErrorMessageFormatting:
    """Test error message formatting and suggestions."""
    
    def test_error_context_preservation(self):
        """Test that error context is preserved through the exception chain."""
        original_error = ValueError("Original error")
        
        extraction_error = PDFExtractionError(
            "Extraction failed",
            pdf_path="/test/file.pdf",
            extraction_method="test_method",
            original_error=original_error
        )
        
        assert extraction_error.original_error is original_error
        assert extraction_error.context["pdf_path"] == "/test/file.pdf"
        assert extraction_error.context["extraction_method"] == "test_method"
    
    def test_suggestion_generation(self):
        """Test automatic suggestion generation for common errors."""
        errors_with_suggestions = [
            PDFNotFoundError("/test/file.pdf"),
            PDFCorruptedError("/test/file.pdf"),
            PDFPermissionError("/test/file.pdf"),
            OutputWriteError("/test/output.txt"),
            SpacingAnalysisError("Analysis failed"),
        ]
        
        for error in errors_with_suggestions:
            assert error.suggestion is not None
            assert len(error.suggestion) > 0
    
    def test_error_chaining(self):
        """Test that original errors are properly chained."""
        original = FileNotFoundError("File not found")
        
        wrapped = FileHandlingError(
            "Wrapped error",
            file_path="/test/file.txt",
            operation="read",
            original_error=original
        )
        
        assert wrapped.original_error is original
        assert wrapped.context["file_path"] == "/test/file.txt"
        assert wrapped.context["operation"] == "read"


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling across the system."""
    
    def test_cli_error_handling_pipeline(self):
        """Test that errors flow properly through CLI to user."""
        # This would test the full pipeline but requires CLI runner
        # For now, verify that CLI imports work
        from src.pdf_plumb.cli import console
        assert console is not None
    
    def test_exception_imports(self):
        """Test that all exceptions can be imported properly."""
        from src.pdf_plumb.core.exceptions import (
            PDFPlumbError, PDFExtractionError, AnalysisError
        )
        
        # Create instances to verify they work
        base_error = PDFPlumbError("test")
        extraction_error = PDFExtractionError("test")
        analysis_error = AnalysisError("test")
        
        assert isinstance(extraction_error, PDFPlumbError)
        assert isinstance(analysis_error, PDFPlumbError)