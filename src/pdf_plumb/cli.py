"""Modern Click-based CLI for PDF Plumb."""

import click
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables must be set manually
    pass

from rich.console import Console
from rich.panel import Panel

from .core.extractor import PDFExtractor
from .core.analyzer import DocumentAnalyzer
from .core.llm_analyzer import LLMDocumentAnalyzer
from .utils.helpers import ensure_output_dir, get_base_name
from .core.visualizer import SpacingVisualizer
from .config import get_config, update_config, apply_profile
from .core.exceptions import (
    PDFPlumbError,
    PDFExtractionError,
    PDFNotFoundError,
    PDFCorruptedError,
    PDFPermissionError,
    AnalysisError,
    VisualizationError,
    ConfigurationError,
    FileHandlingError
)

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
        
    except PDFNotFoundError as e:
        console.print(f"❌ [red]PDF Not Found:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except PDFCorruptedError as e:
        console.print(f"❌ [red]PDF Corrupted:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except PDFPermissionError as e:
        console.print(f"❌ [red]PDF Permission Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except PDFExtractionError as e:
        console.print(f"❌ [red]Extraction Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        if e.context:
            console.print(f"🔍 [blue]Context:[/blue] {e.context}")
        raise click.Abort()
    except VisualizationError as e:
        console.print(f"❌ [red]Visualization Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        console.print("📝 [dim]Note: Extraction completed successfully, only visualization failed[/dim]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Unexpected Error:[/red] {e}")
        console.print("🐛 [dim]This may be a bug. Please report it with the PDF file details.[/dim]")
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
    
    except AnalysisError as e:
        console.print(f"❌ [red]Analysis Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        if e.context:
            console.print(f"🔍 [blue]Context:[/blue] {e.context}")
        raise click.Abort()
    except FileHandlingError as e:
        console.print(f"❌ [red]File Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Unexpected Error:[/red] {e}")
        console.print("🐛 [dim]This may be a bug. Please report it with the lines file details.[/dim]")
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
        
    except PDFNotFoundError as e:
        console.print(f"❌ [red]PDF Not Found:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except PDFExtractionError as e:
        console.print(f"❌ [red]Extraction Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except AnalysisError as e:
        console.print(f"❌ [red]Analysis Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except VisualizationError as e:
        console.print(f"❌ [red]Visualization Failed:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        console.print("📝 [dim]Note: Extraction and analysis completed successfully[/dim]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Unexpected Error:[/red] {e}")
        console.print("🐛 [dim]This may be a bug. Please report it with the PDF file details.[/dim]")
        raise click.Abort()


@cli.command(name='llm-analyze')
@click.argument('document_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--focus',
    type=click.Choice(['headers-footers', 'sections', 'toc', 'multi-objective']),
    default='headers-footers',
    help='Analysis focus area (default: headers-footers)'
)
@click.option(
    '--provider',
    type=click.Choice(['azure']),
    default='azure',
    help='LLM provider to use (default: azure)'
)
@click.option(
    '-o', '--output-dir',
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=lambda: get_config().output_dir,
    help='Directory to save analysis results'
)
@click.option(
    '--estimate-cost',
    is_flag=True,
    help='Only estimate analysis cost without running'
)
@click.option(
    '--no-save',
    is_flag=True,
    help='Do not save results to files'
)
@click.option(
    '--show-status',
    is_flag=True,
    help='Show LLM provider configuration status'
)
def llm_analyze(document_file, focus, provider, output_dir, estimate_cost, no_save, show_status):
    """Analyze document structure using LLM.
    
    Performs LLM-enhanced analysis of PDF document structure, focusing on
    specific areas like headers/footers, section hierarchy, or table of contents.
    
    Requires Azure OpenAI configuration via environment variables:
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_API_KEY  
    - AZURE_OPENAI_DEPLOYMENT
    - AZURE_OPENAI_API_VERSION
    
    DOCUMENT_FILE should be a JSON file from 'extract' or 'process' commands,
    typically ending in '_blocks.json' or '_lines.json'.
    """
    try:
        # Initialize LLM analyzer
        console.print(f"🤖 Initializing {provider.upper()} LLM analyzer...")
        llm_analyzer = LLMDocumentAnalyzer(provider_name=provider)
        
        # Show status if requested
        if show_status:
            status = llm_analyzer.get_analysis_status()
            console.print("\n📊 [bold]LLM Configuration Status[/bold]")
            console.print(f"Provider: {status['provider']}")
            console.print(f"Configured: {'✅' if status['provider_configured'] else '❌'}")
            
            if not status['provider_configured']:
                console.print("\n❌ [red]LLM provider not configured![/red]")
                console.print("Required environment variables:")
                console.print("  • AZURE_OPENAI_ENDPOINT")
                console.print("  • AZURE_OPENAI_API_KEY")
                console.print("  • AZURE_OPENAI_DEPLOYMENT")
                console.print("  • AZURE_OPENAI_API_VERSION")
                raise click.Abort()
            
            console.print(f"LLM Enabled: ✅")
            console.print(f"Batch Size: {status['config']['batch_size']} pages")
            console.print("")
        
        # Load document data
        console.print(f"📄 Loading document: [bold]{document_file}[/bold]")
        
        if not document_file.exists():
            console.print(f"❌ [red]File not found:[/red] {document_file}")
            raise click.Abort()
        
        try:
            import json
            with open(document_file, 'r') as f:
                document_data = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"❌ [red]Invalid JSON file:[/red] {e}")
            raise click.Abort()
        except Exception as e:
            console.print(f"❌ [red]Failed to load document:[/red] {e}")
            raise click.Abort()
        
        # Validate document structure
        if isinstance(document_data, dict) and 'pages' in document_data:
            pages_count = len(document_data['pages'])
        elif isinstance(document_data, list):
            pages_count = len(document_data)
        else:
            console.print("❌ [red]Invalid document format![/red] Expected list of pages or dict with 'pages' key.")
            raise click.Abort()
        
        console.print(f"📄 Document loaded: {pages_count} pages")
        
        # Cost estimation
        if estimate_cost:
            console.print(f"💰 Estimating {focus} analysis cost...")
            try:
                cost_info = llm_analyzer.estimate_analysis_cost(document_data, focus)
                
                console.print("\n💰 [bold]Cost Estimation[/bold]")
                console.print(f"Input tokens: ~{cost_info['estimated_input_tokens']:,}")
                console.print(f"Output tokens: ~{cost_info['estimated_output_tokens']:,}")
                console.print(f"Total tokens: ~{cost_info['estimated_input_tokens'] + cost_info['estimated_output_tokens']:,}")
                console.print(f"Estimated cost: ${cost_info['estimated_cost_usd']:.4f} USD")
                console.print(f"[dim]{cost_info.get('note', '')}[/dim]")
                return
                
            except Exception as e:
                console.print(f"❌ [red]Cost estimation failed:[/red] {e}")
                raise click.Abort()
        
        # Perform analysis
        console.print(f"🔍 Starting [bold]{focus}[/bold] analysis...")
        
        try:
            if focus == 'headers-footers':
                results = llm_analyzer.analyze_headers_footers(
                    document_data,
                    save_results=not no_save,
                    output_dir=output_dir
                )
                
                # Display results summary
                console.print("\n✅ [bold green]Header/Footer Analysis Complete[/bold green]")
                console.print(f"Header confidence: {results.header_confidence.value}")
                console.print(f"Footer confidence: {results.footer_confidence.value}")
                
                boundaries = results.get_content_boundaries()
                console.print(f"Content area: Y {boundaries['start_after_y']:.1f} - {boundaries['end_before_y']:.1f}")
                
                pages_with_headers = len(results.get_pages_with_headers())
                pages_with_footers = len(results.get_pages_with_footers())
                total_analyzed = len(results.sampling_summary['page_indexes_analyzed'])
                
                console.print(f"Headers found: {pages_with_headers}/{total_analyzed} pages")
                console.print(f"Footers found: {pages_with_footers}/{total_analyzed} pages")
                
                if results.insights:
                    console.print("\n💡 [bold]Key Insights:[/bold]")
                    for insight in results.insights[:3]:  # Show top 3 insights
                        console.print(f"  • {insight}")
                
            else:
                console.print(f"❌ [red]Analysis type '{focus}' not yet implemented![/red]")
                console.print("Available: headers-footers")
                raise click.Abort()
            
            # Show token usage
            status = llm_analyzer.get_analysis_status()
            usage_summary = status['token_usage_summary']
            if usage_summary['total_tokens'] > 0:
                console.print(f"\n📊 Token usage: {usage_summary['total_tokens']:,} tokens")
                console.print(f"💰 Estimated cost: ${usage_summary['estimated_total_cost_usd']:.4f} USD")
            
            if not no_save:
                console.print(f"\n💾 Results saved to: [bold]{output_dir}[/bold]")
            
        except Exception as e:
            console.print(f"❌ [red]LLM Analysis Failed:[/red] {e}")
            console.print("🔧 [dim]Check your API configuration and document format[/dim]")
            raise click.Abort()
            
    except ConfigurationError as e:
        console.print(f"❌ [red]Configuration Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except AnalysisError as e:
        console.print(f"❌ [red]Analysis Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Unexpected Error:[/red] {e}")
        console.print("🐛 [dim]This may be a bug. Please report it with the document file details.[/dim]")
        raise click.Abort()


if __name__ == '__main__':
    cli()