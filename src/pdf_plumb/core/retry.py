"""
Retry mechanisms for transient PDF processing failures.

Provides decorators and utility functions for automatically retrying
operations that may fail due to temporary issues like file locks,
memory pressure, or network issues.
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional, Any
from .exceptions import PDFPlumbError, PDFExtractionError, MemoryError as PDFMemoryError


def retry_on_transient_errors(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (OSError, PermissionError, PDFMemoryError)
) -> Callable:
    """
    Decorator that retries function calls on transient errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_multiplier: Multiplier for exponential backoff
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        # Last attempt failed, re-raise the exception
                        raise
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff_multiplier
                    
                except Exception as e:
                    # Non-transient error, don't retry
                    raise
                    
            # This should never be reached due to the re-raise above
            raise RuntimeError("Retry logic error")
            
        return wrapper
    return decorator


def retry_pdf_operation(
    operation: Callable,
    pdf_path: str,
    max_attempts: int = 3,
    delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Retry a PDF operation with exponential backoff.
    
    Args:
        operation: Function to retry
        pdf_path: Path to PDF file for error context
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        **kwargs: Additional arguments passed to operation
        
    Returns:
        Result of the operation
        
    Raises:
        PDFExtractionError: If all retry attempts fail
    """
    current_delay = delay
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return operation(**kwargs)
        except (OSError, PermissionError, PDFMemoryError) as e:
            last_exception = e
            if attempt < max_attempts - 1:
                time.sleep(current_delay)
                current_delay *= 2.0
            continue
        except Exception as e:
            # Non-retryable error
            raise PDFExtractionError(
                f"PDF operation failed: {str(e)}",
                pdf_path=pdf_path,
                original_error=e,
                context={"operation": operation.__name__, "attempt": attempt + 1}
            )
    
    # All retry attempts exhausted
    raise PDFExtractionError(
        f"PDF operation failed after {max_attempts} attempts: {str(last_exception)}",
        pdf_path=pdf_path,
        original_error=last_exception,
        suggestion="Check if the file is locked by another process or if you have sufficient permissions",
        context={"operation": operation.__name__, "total_attempts": max_attempts}
    )


class RetryableExtractor:
    """
    Wrapper class that adds retry logic to PDF extraction operations.
    """
    
    def __init__(self, extractor, max_attempts: int = 3, delay: float = 1.0):
        self.extractor = extractor
        self.max_attempts = max_attempts
        self.delay = delay
    
    @retry_on_transient_errors(max_attempts=3, delay=1.0)
    def extract_with_retry(self, pdf_path: str) -> dict:
        """
        Extract PDF with automatic retry on transient errors.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extraction results dictionary
        """
        return self.extractor.extract_from_pdf(pdf_path)
    
    def extract_robust(self, pdf_path: str) -> dict:
        """
        Extract PDF with comprehensive error handling and retry logic.
        
        This method provides the most robust extraction by:
        1. Retrying on transient errors
        2. Providing detailed error context
        3. Graceful degradation when possible
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extraction results dictionary
        """
        try:
            return self.extract_with_retry(pdf_path)
        except PDFMemoryError as e:
            # For memory errors, suggest reducing processing load
            raise PDFExtractionError(
                f"Insufficient memory to process PDF: {pdf_path}",
                pdf_path=pdf_path,
                suggestion="Try processing the PDF in smaller chunks or increase available memory",
                original_error=e
            )
        except (OSError, PermissionError) as e:
            # For file system errors, provide specific guidance
            raise PDFExtractionError(
                f"File system error processing PDF: {str(e)}",
                pdf_path=pdf_path,
                suggestion="Check file permissions and ensure the PDF is not locked by another application",
                original_error=e
            )