"""
PDF Plumb Exception Classes

Structured exception hierarchy for better error handling and user experience.
Provides context, suggestions, and recovery mechanisms for PDF processing errors.
"""

from typing import Optional, Dict, Any


class PDFPlumbError(Exception):
    """Base exception class for PDF Plumb errors."""
    
    def __init__(
        self, 
        message: str, 
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
        self.original_error = original_error
        super().__init__(message)


class PDFExtractionError(PDFPlumbError):
    """Raised when PDF text extraction fails."""
    
    def __init__(
        self, 
        message: str, 
        pdf_path: Optional[str] = None,
        extraction_method: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            'pdf_path': pdf_path,
            'extraction_method': extraction_method
        })
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class PDFNotFoundError(PDFExtractionError):
    """Raised when PDF file cannot be found or accessed."""
    
    def __init__(self, pdf_path: str, **kwargs):
        message = f"PDF file not found: {pdf_path}"
        suggestion = "Check the file path and ensure the PDF exists and is readable"
        super().__init__(message, pdf_path=pdf_path, suggestion=suggestion, **kwargs)


class PDFCorruptedError(PDFExtractionError):
    """Raised when PDF file is corrupted or invalid."""
    
    def __init__(self, pdf_path: str, **kwargs):
        message = f"PDF file appears corrupted or invalid: {pdf_path}"
        suggestion = "Try opening the PDF in a viewer to verify it's not damaged"
        super().__init__(message, pdf_path=pdf_path, suggestion=suggestion, **kwargs)


class PDFPermissionError(PDFExtractionError):
    """Raised when PDF has permission restrictions."""
    
    def __init__(self, pdf_path: str, **kwargs):
        message = f"PDF has permission restrictions: {pdf_path}"
        suggestion = "The PDF may be password protected or have text extraction disabled"
        super().__init__(message, pdf_path=pdf_path, suggestion=suggestion, **kwargs)


class AnalysisError(PDFPlumbError):
    """Raised when document analysis fails."""
    
    def __init__(
        self, 
        message: str, 
        analysis_stage: Optional[str] = None,
        page_number: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            'analysis_stage': analysis_stage,
            'page_number': page_number
        })
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class SpacingAnalysisError(AnalysisError):
    """Raised when spacing analysis fails."""
    
    def __init__(self, message: str, **kwargs):
        suggestion = "Try adjusting spacing thresholds or check document structure"
        super().__init__(message, analysis_stage="spacing_analysis", suggestion=suggestion, **kwargs)


class BlockFormationError(AnalysisError):
    """Raised when block formation fails."""
    
    def __init__(self, message: str, **kwargs):
        suggestion = "Check font size detection or adjust block formation parameters"
        super().__init__(message, analysis_stage="block_formation", suggestion=suggestion, **kwargs)


class HeaderFooterError(AnalysisError):
    """Raised when header/footer detection fails."""
    
    def __init__(self, message: str, **kwargs):
        suggestion = "Adjust header/footer zone thresholds or spacing parameters"
        super().__init__(message, analysis_stage="header_footer_detection", suggestion=suggestion, **kwargs)


class VisualizationError(PDFPlumbError):
    """Raised when PDF visualization fails."""
    
    def __init__(
        self, 
        message: str, 
        visualization_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({'visualization_type': visualization_type})
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class ConfigurationError(PDFPlumbError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        context.update({'config_field': config_field})
        kwargs['context'] = context
        suggestion = "Check configuration values and ensure they meet validation requirements"
        super().__init__(message, suggestion=suggestion, **kwargs)


class FileHandlingError(PDFPlumbError):
    """Raised when file operations fail."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({
            'file_path': file_path,
            'operation': operation
        })
        kwargs['context'] = context
        super().__init__(message, **kwargs)


class OutputWriteError(FileHandlingError):
    """Raised when output file writing fails."""
    
    def __init__(self, file_path: str, **kwargs):
        message = f"Failed to write output file: {file_path}"
        suggestion = "Check write permissions and available disk space"
        super().__init__(message, file_path=file_path, operation="write", suggestion=suggestion, **kwargs)


class MemoryError(PDFPlumbError):
    """Raised when operations exceed memory limits."""
    
    def __init__(self, message: str, **kwargs):
        suggestion = "Try processing smaller sections or increase available memory"
        super().__init__(message, suggestion=suggestion, **kwargs)


class ValidationError(PDFPlumbError):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        message: str, 
        validation_field: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        context.update({'validation_field': validation_field})
        kwargs['context'] = context
        super().__init__(message, **kwargs)