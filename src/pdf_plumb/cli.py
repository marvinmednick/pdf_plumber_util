"""Main CLI entry point for PDF Plumb."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core.extractor import PDFExtractor
from .core.analyzer import DocumentAnalyzer
from .utils.helpers import ensure_output_dir, get_base_name


def add_extraction_args(parser: argparse.ArgumentParser) -> None:
    """Add common extraction arguments to a parser."""
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file to process",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="output",
        help="Directory to save output files (default: output)",
    )
    parser.add_argument(
        "-b", "--basename",
        type=str,
        help="Base name for output files (default: PDF filename without extension)",
    )
    parser.add_argument(
        "-y", "--y-tolerance",
        type=float,
        default=3.0,
        help="Y-axis tolerance for word alignment (default: 3.0)",
    )
    parser.add_argument(
        "-x", "--x-tolerance",
        type=float,
        default=3.0,
        help="X-axis tolerance for word alignment (default: 3.0)",
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
        help="Comma-separated list of spacing sizes to visualize (e.g. '2.0,2.5,5.0') or range (e.g. '>2.0,<8.5')",
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

    # Process command (extract + analyze)
    process_parser = subparsers.add_parser(
        "process",
        help="Extract and analyze PDF in one step",
        description="Extract text from PDF and analyze the results in one step.",
    )
    add_extraction_args(process_parser)

    return parser.parse_args()


def extract_pdf(args) -> Optional[str]:
    """Extract text from PDF file."""
    try:
        # Ensure output directory exists
        output_dir = ensure_output_dir(args.output_dir)
        
        # Get base name for output files
        basename = get_base_name(args.pdf_file, args.basename)
        
        # Initialize extractor
        extractor = PDFExtractor(
            y_tolerance=args.y_tolerance,
            x_tolerance=args.x_tolerance,
        )
        
        # Extract text
        print(f"Extracting text from {args.pdf_file}...")
        results = extractor.extract_from_pdf(args.pdf_file)
        
        # Save results
        print(f"Saving results to {output_dir}...")
        extractor.save_results(results, output_dir, basename)
        
        # Handle visualization if requested
        if args.visualize_spacing:
            from .core.visualizer import SpacingVisualizer
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


def analyze_lines(lines_file: str) -> None:
    """Analyze extracted text data."""
    try:
        # Initialize analyzer
        analyzer = DocumentAnalyzer()
        
        # Analyze document
        print(f"Analyzing {lines_file}...")
        results = analyzer.analyze_document(lines_file)
        
        if results:
            # Print analysis results
            analyzer.print_analysis(results)
        else:
            print("No analysis results to display.", file=sys.stderr)
    
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "extract":
        extract_pdf(args)
    
    elif args.command == "analyze":
        analyze_lines(args.lines_file)
    
    elif args.command == "process":
        lines_file = extract_pdf(args)
        if lines_file:
            analyze_lines(lines_file)
    
    else:
        print("Please specify a command: extract, analyze, or process")
        sys.exit(1)


if __name__ == "__main__":
    main() 