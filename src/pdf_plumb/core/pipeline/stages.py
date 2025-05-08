"""Pipeline stages for PDF processing."""

from typing import Dict, Any
from pathlib import Path
from ..utils.file_handler import FileHandler


class PipelineStage:
    """Base class for pipeline stages."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize the stage.
        
        Args:
            output_dir: Directory to save output files
        """
        self.file_handler = FileHandler(output_dir=output_dir)
        
    def process(self, data: Dict[str, Any], base_name: str) -> Dict[str, Any]:
        """Process the data.
        
        Args:
            data: Input data to process
            base_name: Base name for output files
            
        Returns:
            Processed data
        """
        raise NotImplementedError("Subclasses must implement process()")


class ExtractStage(PipelineStage):
    """Stage for extracting text from PDF."""
    
    def process(self, data: Dict[str, Any], base_name: str) -> Dict[str, Any]:
        """Process the extraction data.
        
        Args:
            data: Dictionary containing extraction results
            base_name: Base name for output files
            
        Returns:
            Processed data
        """
        # Save full lines data
        self.file_handler.save_json(data['lines_json_by_page'], base_name, "full_lines")
        
        # Save processed lines data
        self.file_handler.save_json(data['processed_lines'], base_name, "lines")
        
        return data


class AnalyzeSpacingStage(PipelineStage):
    """Stage for analyzing spacing patterns."""
    
    def process(self, data: Dict[str, Any], base_name: str) -> Dict[str, Any]:
        """Process the spacing analysis data.
        
        Args:
            data: Dictionary containing spacing analysis results
            base_name: Base name for output files
            
        Returns:
            Processed data
        """
        # Save spacing analysis results
        self.file_handler.save_json(data['spacing_analysis'], base_name, "spacing")
        
        return data


class AnalyzeHeadersFootersStage(PipelineStage):
    """Stage for analyzing headers and footers."""
    
    def process(self, data: Dict[str, Any], base_name: str) -> Dict[str, Any]:
        """Process the header/footer analysis data.
        
        Args:
            data: Dictionary containing header/footer analysis results
            base_name: Base name for output files
            
        Returns:
            Processed data
        """
        # Save header/footer analysis results
        self.file_handler.save_json(data['header_footer_analysis'], base_name, "headers_footers")
        
        return data


class GenerateReportStage(PipelineStage):
    """Stage for generating the final report."""
    
    def process(self, data: Dict[str, Any], base_name: str) -> Dict[str, Any]:
        """Process the report data.
        
        Args:
            data: Dictionary containing report data
            base_name: Base name for output files
            
        Returns:
            Processed data
        """
        # Save consolidated report
        self.file_handler.save_json(data['consolidated_report'], base_name, "report")
        
        return data 