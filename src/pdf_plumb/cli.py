"""Main CLI entry point for PDF Plumb."""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from .core.extractor import PDFExtractor
from .core.analyzer import DocumentAnalyzer
from .utils.helpers import ensure_output_dir, get_base_name
from .core.visualizer import SpacingVisualizer
from .config import get_config, update_config


def add_extraction_args(parser: argparse.ArgumentParser) -> None:
    """Add common extraction arguments to a parser."""
    config = get_config()
    
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file to process",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=str(config.output_dir),
        help=f"Directory to save output files (default: {config.output_dir})",
    )
    parser.add_argument(
        "-b", "--basename",
        type=str,
        help="Base name for output files (default: PDF filename without extension)",
    )
    parser.add_argument(
        "-y", "--y-tolerance",
        type=float,
        default=config.y_tolerance,
        help=f"Y-axis tolerance for word alignment (default: {config.y_tolerance})",
    )
    parser.add_argument(
        "-x", "--x-tolerance",
        type=float,
        default=config.x_tolerance,
        help=f"X-axis tolerance for word alignment (default: {config.x_tolerance})",
    )
    parser.add_argument(
        "--debug-level",
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.log_level,
        help=f"Set the logging level (default: {config.log_level})",
    )
    # Add visualization arguments
    parser.add_argument(
        "--visualize-spacing",
        action="store_true",
        help="Generate a visualization PDF with lines showing vertical spacing",
    )
    parser.add_argument(
        "--spacing-sizes",
        type=str,
        help="Comma-separated list of spacing sizes to visualize. Each item can be:\n"
             "- A single value (e.g. '2.0')\n"
             "- A range (e.g. '2.0-4.0')\n"
             "- Less than or equal (e.g. '-4.0')\n"
             "- Greater than or equal (e.g. '2.0-')",
    )
    parser.add_argument(
        "--spacing-colors",
        type=str,
        help="Comma-separated list of colors for each spacing size (e.g. 'red,blue,green')",
    )
    parser.add_argument(
        "--spacing-patterns",
        type=str,
        help="Comma-separated list of line patterns for each spacing size (e.g. 'solid,dashed,dotted')",
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PDF Plumb - PDF text extraction and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract text from PDF file",
        description="Extract text from a PDF file using multiple methods and save results as JSON.",
    )
    add_extraction_args(extract_parser)

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze extracted text data",
        description="Analyze extracted text data to determine document structure, fonts, and spacing.",
    )
    analyze_parser.add_argument(
        "lines_file",
        type=str,
        help="Path to the lines JSON file to analyze",
    )
    analyze_parser.add_argument(
        "-f", "--output-file",
        type=str,
        help="Path to save the analysis output (default: <basename>_analysis.txt in output directory)",
    )
    analyze_parser.add_argument(
        "--show-output",
        action="store_true",
        help="Show analysis output on stdout in addition to saving to file",
    )

    # Process command (extract + analyze)
    process_parser = subparsers.add_parser(
        "process",
        help="Extract and analyze PDF in one step",
        description="Extract text from PDF and analyze the results in one step.",
    )
    add_extraction_args(process_parser)
    process_parser.add_argument(
        "-f", "--output-file",
        type=str,
        help="Path to save the analysis output (default: <basename>_analysis.txt in output directory)",
    )
    process_parser.add_argument(
        "--show-output",
        action="store_true",
        help="Show analysis output on stdout in addition to saving to file",
    )

    return parser.parse_args()


def extract_pdf(args) -> Optional[str]:
    """Extract text from PDF file."""
    try:
        # Ensure output directory exists
        output_dir = ensure_output_dir(args.output_dir)
        
        # Get base name for output files
        basename = get_base_name(args.pdf_file, args.basename)
        
        # Initialize extractor
        # Update config with CLI arguments
        update_config(
            y_tolerance=args.y_tolerance,
            x_tolerance=args.x_tolerance,
            log_level=args.debug_level
        )
        
        extractor = PDFExtractor()
        
        # Extract text
        print(f"Extracting text from {args.pdf_file}...")
        results = extractor.extract_from_pdf(args.pdf_file)
        
        # Save results
        print(f"Saving results to {output_dir}...")
        extractor.save_results(results, output_dir, basename)
        
        # Handle visualization if requested
        if args.visualize_spacing:
            visualizer = SpacingVisualizer()
            
            # Parse spacing sizes
            spacing_sizes = visualizer.parse_spacing_sizes(args.spacing_sizes)
            if not spacing_sizes:
                print("No spacing sizes specified for visualization. Using all found sizes.")
                # Extract all unique spacing sizes from results
                spacing_sizes = sorted(set(
                    line.get('spacing', 0)
                    for page in results['lines_json_by_page']
                    for line in page['lines']
                    if line.get('spacing') is not None
                ))
            
            # Parse colors and patterns
            spacing_colors = visualizer.parse_colors(args.spacing_colors)
            spacing_patterns = visualizer.parse_patterns(args.spacing_patterns)
            
            # Create visualization
            output_pdf = str(Path(output_dir) / f"{basename}_visualized.pdf")
            print(f"Creating visualization in {output_pdf}...")
            visualizer.create_visualization(
                args.pdf_file,
                output_pdf,
                spacing_sizes,
                spacing_colors,
                spacing_patterns,
                results['lines_json_by_page']
            )
            print("Visualization complete.")
        
        # Return path to lines file for analysis
        return str(Path(output_dir) / f"{basename}_lines.json")
    
    except Exception as e:
        print(f"Error during extraction: {e}", file=sys.stderr)
        return None


def analyze_lines(lines_file: str, output_file: Optional[str] = None, show_output: bool = False) -> None:
    """Analyze extracted text data."""
    try:
        # Initialize analyzer
        analyzer = DocumentAnalyzer()
        
        # Analyze document
        print(f"Analyzing {lines_file}...")
        results = analyzer.analyze_document(lines_file)
        
        if results:
            # Print analysis results
            analyzer.print_analysis(results, output_file, show_output)
        else:
            print("No analysis results to display.", file=sys.stderr)
    
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)


def process_pdf(args) -> None:
    """Process a PDF file through the extraction and analysis pipeline."""
    try:
        # Update config with CLI arguments
        update_config(
            y_tolerance=args.y_tolerance,
            x_tolerance=args.x_tolerance,
            log_level=args.debug_level,
            output_dir=Path(args.output_dir)
        )
        
        # Initialize components
        extractor = PDFExtractor()
        analyzer = DocumentAnalyzer()
        visualizer = SpacingVisualizer()
        
        # Extract text and metadata
        print(f"\nExtracting text from {args.pdf_file}...")
        results = extractor.extract_from_pdf(args.pdf_file)
        
        # Save intermediate results
        base_name = get_base_name(args.pdf_file)
        extractor.save_results(results, args.output_dir, base_name)
        
        # Analyze document structure
        print("\nAnalyzing document structure...")
        analysis_results = analyzer.analyze_document_data(results['lines_json_by_page'], base_name)
        
        # Print analysis results
        output_file = args.output_file or os.path.join(args.output_dir, f"{base_name}_analysis.txt")
        analyzer.print_analysis(analysis_results, output_file=output_file, show_output=args.show_output)
        
        # Handle visualization if requested
        if args.visualize_spacing:
            # Parse spacing sizes
            spacing_sizes = visualizer.parse_spacing_sizes(args.spacing_sizes)
            if not spacing_sizes:
                print("No spacing sizes specified for visualization. Using all found sizes.")
                # Extract all unique spacing sizes from results
                spacing_sizes = sorted(set(
                    line.get('spacing', 0)
                    for page in results['lines_json_by_page']
                    for line in page['lines']
                    if line.get('spacing') is not None
                ))
            
            # Parse colors and patterns
            spacing_colors = visualizer.parse_colors(args.spacing_colors)
            spacing_patterns = visualizer.parse_patterns(args.spacing_patterns)
            
            # Create main visualization (like extract command)
            output_pdf = os.path.join(args.output_dir, f"{base_name}_visualized.pdf")
            print(f"Creating visualization in {output_pdf}...")
            visualizer.create_visualization(
                args.pdf_file,
                output_pdf,
                spacing_sizes,
                spacing_colors,
                spacing_patterns,
                results['lines_json_by_page']
            )
            print("Visualization complete.")
            
            # Create line spacing visualization
            print("\nCreating line spacing visualization...")
            visualizer.create_visualization(
                input_pdf=args.pdf_file,
                output_pdf=os.path.join(args.output_dir, f"{base_name}_spacing.pdf"),
                spacing_ranges=spacing_sizes,
                spacing_colors=spacing_colors,
                spacing_patterns=spacing_patterns,
                lines_data=results['lines_json_by_page']
            )
            
            # Create block spacing visualization
            print("\nCreating block spacing visualization...")
            visualizer.create_block_visualization(
                input_pdf=args.pdf_file,
                output_pdf=os.path.join(args.output_dir, f"{base_name}_block_spacing.pdf"),
                spacing_ranges=spacing_sizes,
                spacing_colors=spacing_colors,
                spacing_patterns=spacing_patterns,
                blocks_data=analysis_results['blocks']
            )
        
        print(f"\nProcessing complete. Results saved to {args.output_dir}")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        if args.debug_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with CLI selection."""
    # Check for new CLI flag
    if "--click" in sys.argv:
        sys.argv.remove("--click")
        from .cli_click import cli
        cli()
        return
    
    # Check for legacy CLI flag (explicit)
    if "--legacy" in sys.argv:
        sys.argv.remove("--legacy")
    
    # Default to legacy argparse CLI for now
    args = parse_args()
    
    if args.command == "extract":
        extract_pdf(args)
    
    elif args.command == "analyze":
        # If no output file specified, use default path
        if not args.output_file:
            basename = get_base_name(args.lines_file)
            args.output_file = str(Path("output") / f"{basename}_analysis.txt")
        analyze_lines(args.lines_file, args.output_file, args.show_output)
    
    elif args.command == "process":
        process_pdf(args)
    
    else:
        print("Please specify a command: extract, analyze, or process")
        sys.exit(1)


if __name__ == "__main__":
    main() 