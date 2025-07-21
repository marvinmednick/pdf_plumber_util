#!/usr/bin/env python3
"""CLI utility for analyzing token counts in PDF document data files.

This script provides a command-line interface for analyzing token requirements
of PDF document data files for LLM processing planning.

Usage:
    python analyze_tokens.py <file_path> [options]
    
Examples:
    # Basic analysis with default model (GPT-4.1)
    python analyze_tokens.py output/h264_100pages_lines.json
    
    # Specify different model
    python analyze_tokens.py output/h264_100pages_blocks.json --model gpt-4o
    
    # Custom sampling parameters
    python analyze_tokens.py data.json --first-pages 20 --random-sample 15
    
    # Save results to specific file
    python analyze_tokens.py data.json --output results.json

Requirements:
    pip install tiktoken
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pdf_plumb.utils.token_counter import (
        DocumentTokenAnalyzer, 
        get_available_models, 
        get_default_model,
        get_model_info
    )
except ImportError as e:
    print(f"Error importing token counter utilities: {e}")
    print("Please ensure you're running from the project root directory.")
    sys.exit(1)

def print_detailed_results(stats: Dict[str, Any], recommendations: Dict[str, Any]):
    """Print comprehensive analysis results to console."""
    print(f"\n{'='*60}")
    print(f"PDF DOCUMENT TOKEN ANALYSIS - {stats['model_name']}")
    print(f"{'='*60}")
    
    print(f"\nFile Analysis:")
    print(f"  File: {Path(stats['file_analyzed']).name}")
    print(f"  Total pages in file: {stats['total_pages_in_file']}")
    print(f"  Pages analyzed: {stats['sample_size']}")
    
    sampling = stats['sampling_strategy']
    print(f"  Sampling strategy:")
    print(f"    - First {sampling['first_pages']} pages")
    print(f"    - {sampling['random_pages']} random pages (starting from page {sampling['random_start_page']})")
    
    if stats['sample_pages'][:10]:
        sample_preview = stats['sample_pages'][:10]
        if len(stats['sample_pages']) > 10:
            sample_preview_str = f"{sample_preview}... (+{len(stats['sample_pages'])-10} more)"
        else:
            sample_preview_str = str(sample_preview)
        print(f"    - Sample pages: {sample_preview_str}")
    
    print(f"\nToken Statistics (per page):")
    ts = stats['token_stats']
    print(f"  Mean: {ts['mean']:.1f} tokens")
    print(f"  Median: {ts['median']:.1f} tokens")
    print(f"  Range: {ts['min']:,} - {ts['max']:,} tokens")
    print(f"  Std Dev: {ts['std_dev']:.1f} tokens")
    print(f"  Total sample: {ts['total_sample']:,} tokens")
    
    print(f"\nContent Statistics (per page):")
    bs = stats['block_stats']
    print(f"  Mean blocks/lines: {bs['mean']:.1f}")
    print(f"  Range: {bs['min']} - {bs['max']} blocks/lines")
    
    print(f"\nModel Context Analysis:")
    print(f"  Model: {recommendations['model']}")
    print(f"  Context limit: {recommendations['context_limit']:,} tokens")
    print(f"  Available for data: {recommendations['available_tokens']:,} tokens")
    print(f"  Reserved overhead: {recommendations['overhead_reserved']:,} tokens")
    
    print(f"\nBatch Size Recommendations:")
    rec = recommendations['batch_recommendations']
    print(f"  Conservative: {rec['conservative_pages']} pages (using max tokens/page)")
    print(f"  Recommended: {rec['recommended_pages']} pages (using mean + 1σ)")
    print(f"  Optimistic: {rec['optimistic_pages']} pages (using mean tokens/page)")
    print(f"")
    print(f"  💡 Suggested initial batch: {rec['recommended_initial']} pages")
    print(f"  💡 Suggested incremental: {rec['recommended_incremental']} pages")
    
    print(f"\nSample Size Token Usage:")
    calc = recommendations['sample_calculations']
    print(f"  10 pages ≈ {calc['10_pages']:,} tokens")
    print(f"  15 pages ≈ {calc['15_pages']:,} tokens")
    print(f"  20 pages ≈ {calc['20_pages']:,} tokens")
    print(f"  50 pages ≈ {calc['50_pages']:,} tokens")

def print_summary(stats: Dict[str, Any], recommendations: Dict[str, Any]):
    """Print quick summary for planning."""
    print(f"\n{'='*60}")
    print(f"QUICK SUMMARY FOR PLANNING")
    print(f"{'='*60}")
    
    rec = recommendations['batch_recommendations']
    ts = stats['token_stats']
    
    print(f"📊 Model: {stats['model_name']}")
    print(f"📄 File: {Path(stats['file_analyzed']).name}")
    print(f"🔢 Avg tokens per page: {ts['mean']:.0f} ± {ts['std_dev']:.0f}")
    print(f"🚀 Recommended initial batch: {rec['recommended_initial']} pages")
    print(f"➕ Recommended incremental: {rec['recommended_incremental']} pages")
    print(f"📈 Max single batch: {rec['recommended_pages']} pages")

def save_results(stats: Dict[str, Any], recommendations: Dict[str, Any], output_path: str):
    """Save analysis results to JSON file."""
    results = {
        'analysis_metadata': {
            'cli_version': '1.0',
            'file_analyzed': stats['file_analyzed'],
            'model_used': stats['model_used']
        },
        'statistics': stats,
        'recommendations': recommendations
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_path}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Analyze token counts for PDF document data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {sys.argv[0]} output/h264_100pages_lines.json
  {sys.argv[0]} output/h264_100pages_blocks.json --model gpt-4o
  {sys.argv[0]} data.json --first-pages 20 --random-sample 15
  {sys.argv[0]} data.json --output custom_results.json --quiet

Available models: {', '.join(get_available_models())}
Default model: {get_default_model()}
        """
    )
    
    # Required arguments
    parser.add_argument(
        'file_path',
        help='Path to JSON file containing PDF document data'
    )
    
    # Optional arguments
    parser.add_argument(
        '--model', '-m',
        choices=get_available_models(),
        default=get_default_model(),
        help=f'Model to use for token counting (default: {get_default_model()})'
    )
    
    parser.add_argument(
        '--first-pages', '-f',
        type=int,
        default=30,
        help='Number of initial pages to analyze (default: 30)'
    )
    
    parser.add_argument(
        '--random-sample', '-r',
        type=int,
        default=10,
        help='Number of random pages to sample (default: 10)'
    )
    
    parser.add_argument(
        '--random-start', '-s',
        type=int,
        default=31,
        help='Starting page for random sampling (default: 31)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for detailed results (default: auto-generated based on input file)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Show only summary, skip detailed output'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible sampling (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.file_path)
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return 1
    
    if not input_path.suffix.lower() == '.json':
        print(f"⚠️  Warning: File doesn't have .json extension: {input_path}")
    
    # Generate output path if not provided
    if args.output:
        output_path = args.output
    else:
        output_dir = input_path.parent
        base_name = input_path.stem
        output_path = output_dir / f"{base_name}_token_analysis.json"
    
    # Display model info
    if not args.quiet:
        model_info = get_model_info(args.model)
        print(f"🤖 Using model: {model_info['name']}")
        print(f"📊 Context limit: {model_info['context_limit']:,} tokens")
        print(f"🔄 Processing file: {input_path}")
    
    try:
        # Initialize analyzer
        analyzer = DocumentTokenAnalyzer(
            model=args.model,
            random_seed=args.seed
        )
        
        # Perform analysis
        stats = analyzer.analyze_document(
            str(input_path),
            first_n_pages=args.first_pages,
            random_sample_size=args.random_sample,
            random_start_page=args.random_start
        )
        
        # Generate recommendations
        recommendations = analyzer.recommend_batch_sizes(stats)
        
        # Display results
        if args.quiet:
            print_summary(stats, recommendations)
        else:
            print_detailed_results(stats, recommendations)
            print_summary(stats, recommendations)
        
        # Save results
        save_results(stats, recommendations, output_path)
        
        return 0
        
    except ImportError as e:
        print(f"❌ Error: Missing required package. Please install tiktoken:")
        print(f"   uv add tiktoken")
        print(f"   Error details: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"❌ Error: File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())