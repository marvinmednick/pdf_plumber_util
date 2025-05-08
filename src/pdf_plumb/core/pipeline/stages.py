"""Pipeline stage implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path
import json
from ..utils.logging import LogManager, DebugManager
from .pipeline import PipelineConfig

class PipelineStage(ABC):
    """Base class for pipeline stages."""
    
    def __init__(self, name: str, config: PipelineConfig):
        self.name = name
        self.config = config
        self.logger = LogManager(config.debug_level)
        self.debugger = DebugManager(config.debug_level)
        
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process the input data."""
        pass
        
    def should_save(self) -> bool:
        """Determine if results should be saved."""
        return self.config.save_intermediate
        
    @abstractmethod
    def save_results(self, data: Any):
        """Save the stage results."""
        pass

class ExtractionStage(PipelineStage):
    """Handles PDF text extraction."""
    
    def process(self, pdf_path: str) -> Dict:
        """Process the PDF file and extract text."""
        self.logger.info(f"Starting PDF extraction: {pdf_path}")
        try:
            from ..extractor import PDFExtractor
            extractor = PDFExtractor(
                gap_rounding=self.config.gap_rounding
            )
            results = extractor.extract_from_pdf(pdf_path)
            self.logger.info("PDF extraction completed successfully")
            return results
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {str(e)}")
            raise
            
    def save_results(self, data: Dict):
        """Save extraction results."""
        output_dir = Path(self.config.output_dir)
        
        # Save full lines
        full_lines_path = output_dir / f"{self.config.base_name}_full_lines.json"
        with open(full_lines_path, 'w') as f:
            json.dump(data['lines_json_by_page'], f, indent=2)
            
        # Save processed lines
        lines_path = output_dir / f"{self.config.base_name}_lines.json"
        with open(lines_path, 'w') as f:
            json.dump(data['processed_lines'], f, indent=2)

class SpacingAnalysisStage(PipelineStage):
    """Analyzes line spacing patterns in the document."""
    
    def process(self, data: Dict) -> Dict:
        """Analyze line spacing patterns."""
        self.logger.info("Starting spacing analysis")
        try:
            from ..analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer()
            
            # Extract spacing analysis
            spacing_results = analyzer.analyze_spacing(
                data['processed_lines'],
                self.config.output_dir,
                self.config.base_name
            )
            
            self.logger.info("Spacing analysis completed successfully")
            return {
                'spacing_analysis': spacing_results,
                'processed_lines': data['processed_lines']  # Pass through for next stage
            }
        except Exception as e:
            self.logger.error(f"Spacing analysis failed: {str(e)}")
            raise
            
    def save_results(self, data: Dict):
        """Save spacing analysis results."""
        output_dir = Path(self.config.output_dir)
        spacing_path = output_dir / f"{self.config.base_name}_spacing_analysis.json"
        with open(spacing_path, 'w') as f:
            json.dump(data['spacing_analysis'], f, indent=2)

class HeaderFooterAnalysisStage(PipelineStage):
    """Analyzes header and footer patterns in the document."""
    
    def process(self, data: Dict) -> Dict:
        """Analyze header and footer patterns."""
        self.logger.info("Starting header/footer analysis")
        try:
            from ..analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer()
            
            # Extract header/footer analysis
            hf_results = analyzer.analyze_headers_footers(
                data['processed_lines'],
                self.config.output_dir,
                self.config.base_name
            )
            
            self.logger.info("Header/footer analysis completed successfully")
            return {
                'header_footer_analysis': hf_results,
                'processed_lines': data['processed_lines']  # Pass through for next stage
            }
        except Exception as e:
            self.logger.error(f"Header/footer analysis failed: {str(e)}")
            raise
            
    def save_results(self, data: Dict):
        """Save header/footer analysis results."""
        output_dir = Path(self.config.output_dir)
        hf_path = output_dir / f"{self.config.base_name}_header_footer_analysis.json"
        with open(hf_path, 'w') as f:
            json.dump(data['header_footer_analysis'], f, indent=2)

class ReportGenerationStage(PipelineStage):
    """Generates consolidated analysis reports."""
    
    def process(self, data: Dict) -> Dict:
        """Generate consolidated analysis report."""
        self.logger.info("Generating consolidated report")
        try:
            from ..analyzer import PDFAnalyzer
            analyzer = PDFAnalyzer()
            
            # Generate consolidated report
            report = analyzer.generate_consolidated_report(
                data['processed_lines'],
                data.get('spacing_analysis', {}),
                data.get('header_footer_analysis', {}),
                self.config.output_dir,
                self.config.base_name
            )
            
            self.logger.info("Report generation completed successfully")
            return {
                'consolidated_report': report,
                'all_analysis': data  # Include all previous analysis
            }
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise
            
    def save_results(self, data: Dict):
        """Save consolidated report."""
        output_dir = Path(self.config.output_dir)
        report_path = output_dir / f"{self.config.base_name}_analysis.json"
        with open(report_path, 'w') as f:
            json.dump(data['consolidated_report'], f, indent=2) 