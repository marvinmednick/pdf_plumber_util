"""Main CLI for PDF Plumb."""

import sys
import argparse
from pathlib import Path
from core.pipeline import ProcessingPipeline, PipelineConfig
from core.pipeline.stages import (
    ExtractionStage,
    SpacingAnalysisStage,
    HeaderFooterAnalysisStage,
    ReportGenerationStage
)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process PDF documents for text analysis.')
    parser.add_argument('pdf_file', help='Path to the PDF file to process')
    parser.add_argument('-o', '--output-dir', default='output',
                      help='Directory to save output files (default: output)')
    parser.add_argument('-d', '--debug', action='store_true',
                      help='Enable debug logging')
    parser.add_argument('--no-save-intermediate', action='store_true',
                      help='Disable saving intermediate results')
    parser.add_argument('--gap-rounding', type=float, default=0.5,
                      help='Amount to round gap values to (default: 0.5)')
    
    # Analysis options
    analysis_group = parser.add_argument_group('Analysis Options')
    analysis_group.add_argument('--skip-spacing', action='store_true',
                              help='Skip spacing analysis')
    analysis_group.add_argument('--skip-headers-footers', action='store_true',
                              help='Skip header/footer analysis')
    analysis_group.add_argument('--skip-report', action='store_true',
                              help='Skip consolidated report generation')
    
    return parser.parse_args()

def main():
    """Main entry point for PDF Plumb."""
    args = parse_args()
    
    # Create pipeline configuration
    config = PipelineConfig(
        save_intermediate=not args.no_save_intermediate,
        debug_level='DEBUG' if args.debug else 'INFO',
        output_dir=args.output_dir,
        base_name=Path(args.pdf_file).stem,
        gap_rounding=args.gap_rounding
    )
    
    # Create pipeline
    pipeline = ProcessingPipeline(config)
    
    # Add stages
    pipeline.add_stage(ExtractionStage('extraction', config))
    
    # Add analysis stages based on options
    if not args.skip_spacing:
        pipeline.add_stage(SpacingAnalysisStage('spacing_analysis', config))
        
    if not args.skip_headers_footers:
        pipeline.add_stage(HeaderFooterAnalysisStage('header_footer_analysis', config))
        
    if not args.skip_report:
        pipeline.add_stage(ReportGenerationStage('report_generation', config))
    
    # Run pipeline
    try:
        results = pipeline.run(args.pdf_file)
        print(f"Processing completed successfully. Results saved to {args.output_dir}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 