"""Modern Click-based CLI for PDF Plumb."""

import click
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from .core.extractor import PDFExtractor
from .core.analyzer import DocumentAnalyzer
from .utils.helpers import ensure_output_dir, get_base_name
from .core.visualizer import SpacingVisualizer
from .config import get_config, update_config, apply_profile

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    '--profile',
    type=click.Choice(['technical', 'academic', 'manual', 'dense']),
    help='Document type profile to use'
)
@click.option(
    '--config-file',
    type=click.Path(exists=True),
    help='Path to configuration file'
)
@click.option(
    '--version',
    is_flag=True,
    help='Show version information'
)
@click.pass_context
def cli(ctx, profile, config_file, version):
    """PDF Plumb - Modern PDF text extraction and analysis tool.
    
    A comprehensive tool for extracting and analyzing text from PDF documents
    with advanced structure detection and visualization capabilities.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    if version:
        console.print(Panel("PDF Plumb v0.1.0", title="Version"))
        return
    
    # Apply profile if specified
    if profile:
        try:
            apply_profile(profile)
            console.print(f"✅ Applied [bold]{profile}[/bold] document profile")
        except ValueError as e:
            console.print(f"❌ Error applying profile: {e}")
            raise click.Abort()
    
    # Store configuration in context
    ctx.obj['config'] = get_config()
    
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Common options that are shared across commands
def common_options(f):
    """Decorator to add common options to commands."""
    f = click.option(
        '-o', '--output-dir',
        type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
        default=lambda: get_config().output_dir,
        help='Directory to save output files'
    )(f)
    f = click.option(
        '-b', '--basename',
        help='Base name for output files (default: PDF filename without extension)'
    )(f)
    f = click.option(
        '-y', '--y-tolerance',
        type=float,
        default=lambda: get_config().y_tolerance,
        help='Y-axis tolerance for word alignment'
    )(f)
    f = click.option(
        '-x', '--x-tolerance',
        type=float,
        default=lambda: get_config().x_tolerance,
        help='X-axis tolerance for word alignment'
    )(f)
    f = click.option(
        '--debug-level',
        type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
        default=lambda: get_config().log_level,
        help='Set the logging level'
    )(f)
    return f


def visualization_options(f):
    """Decorator to add visualization options to commands."""
    f = click.option(
        '--visualize-spacing',
        is_flag=True,
        help='Generate a visualization PDF with lines showing vertical spacing'
    )(f)
    f = click.option(
        '--spacing-sizes',
        help='Comma-separated list of spacing sizes to visualize'
    )(f)
    f = click.option(
        '--spacing-colors',
        help='Comma-separated list of colors for each spacing size'
    )(f)
    f = click.option(
        '--spacing-patterns',
        help='Comma-separated list of line patterns for each spacing size'
    )(f)
    return f


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@common_options
@visualization_options
def extract(pdf_file, output_dir, basename, y_tolerance, x_tolerance, debug_level,
           visualize_spacing, spacing_sizes, spacing_colors, spacing_patterns):
    """Extract text from PDF file using multiple methods.
    
    Extracts text from a PDF file using three different methods:
    - Raw text extraction
    - Text line extraction 
    - Word-based extraction with manual alignment
    
    Results are saved as JSON files with rich metadata for analysis.
    """
    try:
        # Update config with CLI arguments
        update_config(
            y_tolerance=y_tolerance,
            x_tolerance=x_tolerance,
            log_level=debug_level,
            output_dir=output_dir
        )
        
        # Ensure output directory exists
        output_dir = ensure_output_dir(str(output_dir))
        
        # Get base name for output files
        basename = get_base_name(str(pdf_file), basename)
        
        # Initialize extractor
        extractor = PDFExtractor()
        
        # Extract text with progress indication
        console.print(f"📄 Extracting text from [bold]{pdf_file}[/bold]...")
        results = extractor.extract_from_pdf(str(pdf_file))
        
        # Save results
        console.print(f"💾 Saving results to [bold]{output_dir}[/bold]...")
        extractor.save_results(results, output_dir, basename)
        
        # Handle visualization if requested
        if visualize_spacing:
            visualizer = SpacingVisualizer()
            
            # Parse spacing sizes
            spacing_sizes_parsed = visualizer.parse_spacing_sizes(spacing_sizes)
            if not spacing_sizes_parsed:
                console.print("ℹ️  No spacing sizes specified, using all found sizes")
                # Extract all unique spacing sizes from results
                spacing_sizes_parsed = sorted(set(
                    line.get('spacing', 0)
                    for page in results['lines_json_by_page']
                    for line in page['lines']
                    if line.get('spacing') is not None
                ))
            
            # Parse colors and patterns
            spacing_colors_parsed = visualizer.parse_colors(spacing_colors)
            spacing_patterns_parsed = visualizer.parse_patterns(spacing_patterns)
            
            # Create visualization
            output_pdf = Path(output_dir) / f"{basename}_visualized.pdf"
            console.print(f"🎨 Creating visualization in [bold]{output_pdf}[/bold]...")
            visualizer.create_visualization(
                str(pdf_file),
                str(output_pdf),
                spacing_sizes_parsed,
                spacing_colors_parsed,
                spacing_patterns_parsed,
                results['lines_json_by_page']
            )
            console.print("✅ Visualization complete")
        
        # Success message
        lines_file = Path(output_dir) / f"{basename}_lines.json"
        console.print(f"✅ Extraction complete! Lines file: [bold]{lines_file}[/bold]")
        
    except Exception as e:
        console.print(f"❌ Error during extraction: {e}")
        raise click.Abort()


@cli.command()
@click.argument('lines_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '-f', '--output-file',
    type=click.Path(path_type=Path),
    help='Path to save the analysis output'
)
@click.option(
    '--show-output',
    is_flag=True,
    help='Show analysis output on stdout in addition to saving to file'
)
def analyze(lines_file, output_file, show_output):
    """Analyze extracted text data to determine document structure.
    
    Analyzes extracted text data to identify:
    - Font usage and distribution
    - Text size analysis
    - Line spacing patterns
    - Header and footer boundaries
    - Document structure
    """
    try:
        # Initialize analyzer
        analyzer = DocumentAnalyzer()
        
        # Analyze document
        console.print(f"🔍 Analyzing [bold]{lines_file}[/bold]...")
        results = analyzer.analyze_document(str(lines_file))
        
        if results:
            # Print analysis results
            analyzer.print_analysis(results, str(output_file) if output_file else None, show_output)
            
            if output_file:
                console.print(f"✅ Analysis complete! Results saved to [bold]{output_file}[/bold]")
            else:
                console.print("✅ Analysis complete!")
        else:
            console.print("❌ No analysis results to display")
            raise click.Abort()
    
    except Exception as e:
        console.print(f"❌ Error during analysis: {e}")
        raise click.Abort()


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@common_options
@visualization_options
@click.option(
    '-f', '--output-file',
    type=click.Path(path_type=Path),
    help='Path to save the analysis output'
)
@click.option(
    '--show-output',
    is_flag=True,
    help='Show analysis output on stdout in addition to saving to file'
)
def process(pdf_file, output_dir, basename, y_tolerance, x_tolerance, debug_level,
           visualize_spacing, spacing_sizes, spacing_colors, spacing_patterns,
           output_file, show_output):
    """Extract and analyze PDF in one step.
    
    Combines extraction and analysis into a single command for convenience.
    First extracts text using multiple methods, then analyzes the results
    to determine document structure and characteristics.
    """
    try:
        # Update config with CLI arguments
        update_config(
            y_tolerance=y_tolerance,
            x_tolerance=x_tolerance,
            log_level=debug_level,
            output_dir=output_dir
        )
        
        # Initialize components
        extractor = PDFExtractor()
        analyzer = DocumentAnalyzer()
        visualizer = SpacingVisualizer()
        
        # Extract text and metadata
        console.print(f"📄 Extracting text from [bold]{pdf_file}[/bold]...")
        results = extractor.extract_from_pdf(str(pdf_file))
        
        # Save intermediate results
        base_name = get_base_name(str(pdf_file), basename)
        output_dir_path = ensure_output_dir(str(output_dir))
        extractor.save_results(results, output_dir_path, base_name)
        
        # Analyze document structure
        console.print("🔍 Analyzing document structure...")
        analysis_results = analyzer.analyze_document_data(results['lines_json_by_page'], base_name)
        
        # Print analysis results
        output_file_path = output_file or Path(output_dir_path) / f"{base_name}_analysis.txt"
        analyzer.print_analysis(analysis_results, str(output_file_path), show_output)
        
        # Handle visualization if requested
        if visualize_spacing:
            # Parse spacing options
            spacing_sizes_parsed = visualizer.parse_spacing_sizes(spacing_sizes)
            spacing_colors_parsed = visualizer.parse_colors(spacing_colors)
            spacing_patterns_parsed = visualizer.parse_patterns(spacing_patterns)
            
            # Create main visualization
            output_pdf = Path(output_dir_path) / f"{base_name}_visualized.pdf"
            console.print(f"🎨 Creating visualization in [bold]{output_pdf}[/bold]...")
            visualizer.create_visualization(
                str(pdf_file),
                str(output_pdf),
                spacing_sizes_parsed,
                spacing_colors_parsed,
                spacing_patterns_parsed,
                results['lines_json_by_page']
            )
            console.print("✅ Visualization complete")
        
        console.print("✅ Processing complete!")
        
    except Exception as e:
        console.print(f"❌ Error during processing: {e}")
        raise click.Abort()


if __name__ == '__main__':
    cli()