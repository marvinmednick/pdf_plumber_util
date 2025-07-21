#!/usr/bin/env python3
"""Analyze token reduction from reducing numerical precision in PDF data.

This script analyzes how much token reduction can be achieved by reducing
the precision of numerical values (coordinates, sizes, etc.) in PDF data files.

Usage:
    python precision_analysis.py <file_path> [options]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import argparse

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pdf_plumb.utils.token_counter import TokenCounter
except ImportError as e:
    print(f"Warning: Could not import TokenCounter: {e}")
    print("Precision analysis will use character count estimation.")
    TokenCounter = None

def round_numbers_in_dict(data: Any, precision: int = 3) -> Any:
    """Recursively round all numerical values in a data structure to specified precision.
    
    Args:
        data: Data structure to process
        precision: Number of decimal places to round to
        
    Returns:
        Data structure with rounded numbers
    """
    if isinstance(data, dict):
        return {key: round_numbers_in_dict(value, precision) for key, value in data.items()}
    elif isinstance(data, list):
        return [round_numbers_in_dict(item, precision) for item in data]
    elif isinstance(data, float):
        return round(data, precision)
    else:
        return data

def analyze_numerical_content(json_str: str) -> Dict[str, Any]:
    """Analyze numerical content in JSON string.
    
    Args:
        json_str: JSON string to analyze
        
    Returns:
        Dictionary with numerical content statistics
    """
    # Find all floating point numbers
    float_pattern = r'-?\d+\.\d+'
    floats = re.findall(float_pattern, json_str)
    
    # Analyze precision distribution
    precision_counts = {}
    total_float_chars = 0
    
    for float_str in floats:
        decimal_places = len(float_str.split('.')[1])
        precision_counts[decimal_places] = precision_counts.get(decimal_places, 0) + 1
        total_float_chars += len(float_str)
    
    # Find integers that could be affected by coordinate rounding
    int_pattern = r'-?\d{2,}'  # Multi-digit integers
    integers = re.findall(int_pattern, json_str)
    total_int_chars = sum(len(i) for i in integers)
    
    return {
        'total_floats': len(floats),
        'precision_distribution': precision_counts,
        'total_float_chars': total_float_chars,
        'total_integers': len(integers),
        'total_int_chars': total_int_chars,
        'total_number_chars': total_float_chars + total_int_chars,
        'example_floats': floats[:10]  # Sample for inspection
    }

def calculate_precision_reduction(original_data: Any, target_precision: int = 3) -> Tuple[str, str, Dict[str, Any]]:
    """Calculate token reduction from precision reduction.
    
    Args:
        original_data: Original data structure
        target_precision: Target decimal precision
        
    Returns:
        Tuple of (original_json, reduced_json, analysis_stats)
    """
    # Create reduced precision version
    reduced_data = round_numbers_in_dict(original_data, target_precision)
    
    # Convert to JSON strings
    original_json = json.dumps(original_data, separators=(',', ':'))
    reduced_json = json.dumps(reduced_data, separators=(',', ':'))
    
    # Analyze the changes
    original_analysis = analyze_numerical_content(original_json)
    reduced_analysis = analyze_numerical_content(reduced_json)
    
    char_reduction = len(original_json) - len(reduced_json)
    reduction_percentage = (char_reduction / len(original_json)) * 100
    
    analysis_stats = {
        'original_length': len(original_json),
        'reduced_length': len(reduced_json),
        'char_reduction': char_reduction,
        'reduction_percentage': reduction_percentage,
        'original_numerical_analysis': original_analysis,
        'reduced_numerical_analysis': reduced_analysis
    }
    
    return original_json, reduced_json, analysis_stats

def analyze_file_precision_reduction(file_path: str, target_precision: int = 3, sample_pages: int = 5) -> Dict[str, Any]:
    """Analyze precision reduction impact on a PDF data file.
    
    Args:
        file_path: Path to JSON file
        target_precision: Target decimal precision
        sample_pages: Number of pages to analyze
        
    Returns:
        Analysis results
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Handle different file structures
    if isinstance(data, list):
        pages = data[:sample_pages]
    elif 'pages' in data:
        pages = data['pages'][:sample_pages]
    else:
        pages = [data]  # Single page
    
    results = {
        'file_path': file_path,
        'target_precision': target_precision,
        'pages_analyzed': len(pages),
        'page_results': [],
        'aggregate_stats': {
            'total_original_chars': 0,
            'total_reduced_chars': 0,
            'total_char_reduction': 0,
            'avg_reduction_percentage': 0
        }
    }
    
    total_reduction = 0
    
    for i, page in enumerate(pages):
        original_json, reduced_json, stats = calculate_precision_reduction(page, target_precision)
        
        page_result = {
            'page_number': page.get('page', i+1),
            'original_chars': stats['original_length'],
            'reduced_chars': stats['reduced_length'],
            'char_reduction': stats['char_reduction'],
            'reduction_percentage': stats['reduction_percentage'],
            'numerical_stats': {
                'original_floats': stats['original_numerical_analysis']['total_floats'],
                'original_float_chars': stats['original_numerical_analysis']['total_float_chars'],
                'reduced_float_chars': stats['reduced_numerical_analysis']['total_float_chars'],
                'float_char_reduction': stats['original_numerical_analysis']['total_float_chars'] - stats['reduced_numerical_analysis']['total_float_chars']
            }
        }
        
        results['page_results'].append(page_result)
        
        # Aggregate stats
        results['aggregate_stats']['total_original_chars'] += stats['original_length']
        results['aggregate_stats']['total_reduced_chars'] += stats['reduced_length']
        results['aggregate_stats']['total_char_reduction'] += stats['char_reduction']
        total_reduction += stats['reduction_percentage']
    
    # Calculate averages
    results['aggregate_stats']['avg_reduction_percentage'] = total_reduction / len(pages)
    results['aggregate_stats']['overall_reduction_percentage'] = (
        results['aggregate_stats']['total_char_reduction'] / 
        results['aggregate_stats']['total_original_chars'] * 100
    )
    
    return results

def estimate_token_reduction(char_reduction: int, original_chars: int) -> Dict[str, float]:
    """Estimate token reduction from character reduction.
    
    Args:
        char_reduction: Number of characters reduced
        original_chars: Original character count
        
    Returns:
        Token reduction estimates
    """
    # Different estimation methods
    char_per_token_estimates = {
        'conservative': 4.0,  # 4 chars per token
        'average': 3.5,       # 3.5 chars per token  
        'optimistic': 3.0     # 3 chars per token
    }
    
    estimates = {}
    for method, ratio in char_per_token_estimates.items():
        original_tokens = original_chars / ratio
        reduced_tokens = char_reduction / ratio
        token_reduction_pct = (reduced_tokens / original_tokens) * 100
        
        estimates[method] = {
            'original_tokens': original_tokens,
            'token_reduction': reduced_tokens,
            'token_reduction_percentage': token_reduction_pct
        }
    
    return estimates

def print_analysis_results(results: Dict[str, Any], show_token_estimates: bool = True):
    """Print comprehensive analysis results."""
    print(f"\n{'='*60}")
    print(f"PRECISION REDUCTION ANALYSIS")
    print(f"{'='*60}")
    
    print(f"\nFile: {Path(results['file_path']).name}")
    print(f"Target Precision: {results['target_precision']} decimal places")
    print(f"Pages Analyzed: {results['pages_analyzed']}")
    
    print(f"\n{'='*40}")
    print(f"AGGREGATE RESULTS")
    print(f"{'='*40}")
    
    agg = results['aggregate_stats']
    print(f"Total Character Reduction: {agg['total_char_reduction']:,} chars")
    print(f"Overall Reduction: {agg['overall_reduction_percentage']:.2f}%")
    print(f"Average Page Reduction: {agg['avg_reduction_percentage']:.2f}%")
    
    # Character breakdown
    print(f"\nCharacter Analysis:")
    print(f"  Original: {agg['total_original_chars']:,} chars")
    print(f"  Reduced:  {agg['total_reduced_chars']:,} chars")
    print(f"  Saved:    {agg['total_char_reduction']:,} chars")
    
    if show_token_estimates:
        print(f"\n{'='*40}")
        print(f"ESTIMATED TOKEN REDUCTION")
        print(f"{'='*40}")
        
        token_estimates = estimate_token_reduction(
            agg['total_char_reduction'], 
            agg['total_original_chars']
        )
        
        for method, estimate in token_estimates.items():
            print(f"\n{method.capitalize()} Estimate (assuming {3.0 if method == 'optimistic' else 3.5 if method == 'average' else 4.0} chars/token):")
            print(f"  Original tokens: {estimate['original_tokens']:,.0f}")
            print(f"  Token reduction: {estimate['token_reduction']:,.0f} tokens")
            print(f"  Percentage: {estimate['token_reduction_percentage']:.2f}%")
    
    print(f"\n{'='*40}")
    print(f"PER-PAGE BREAKDOWN")
    print(f"{'='*40}")
    
    print(f"{'Page':<6} {'Original':<10} {'Reduced':<10} {'Saved':<8} {'%':<6} {'Floats':<8}")
    print(f"{'-'*6} {'-'*10} {'-'*10} {'-'*8} {'-'*6} {'-'*8}")
    
    for page in results['page_results']:
        print(f"{page['page_number']:<6} "
              f"{page['original_chars']:<10,} "
              f"{page['reduced_chars']:<10,} "
              f"{page['char_reduction']:<8,} "
              f"{page['reduction_percentage']:<6.1f}% "
              f"{page['numerical_stats']['original_floats']:<8}")
    
    # Show examples of high-impact pages
    sorted_pages = sorted(results['page_results'], key=lambda x: x['reduction_percentage'], reverse=True)
    print(f"\nHighest Reduction Pages:")
    for page in sorted_pages[:3]:
        print(f"  Page {page['page_number']}: {page['reduction_percentage']:.1f}% "
              f"({page['char_reduction']:,} chars saved)")

def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(
        description='Analyze token reduction from numerical precision reduction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python precision_analysis.py output/h264_100pages_lines.json
  python precision_analysis.py output/h264_100pages_blocks.json --precision 2
  python precision_analysis.py data.json --pages 10 --no-tokens
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to JSON file containing PDF document data'
    )
    
    parser.add_argument(
        '--precision', '-p',
        type=int,
        default=3,
        help='Target decimal precision (default: 3)'
    )
    
    parser.add_argument(
        '--pages', '-n',
        type=int,
        default=5,
        help='Number of pages to analyze (default: 5)'
    )
    
    parser.add_argument(
        '--no-tokens',
        action='store_true',
        help='Skip token reduction estimates'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Save detailed results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.file_path)
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return 1
    
    try:
        # Perform analysis
        results = analyze_file_precision_reduction(
            str(input_path),
            target_precision=args.precision,
            sample_pages=args.pages
        )
        
        # Print results
        print_analysis_results(results, show_token_estimates=not args.no_tokens)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Detailed results saved to: {args.output}")
        
        # Quick summary
        reduction = results['aggregate_stats']['overall_reduction_percentage']
        print(f"\n🎯 SUMMARY: {reduction:.1f}% character reduction achievable")
        print(f"   Estimated token reduction: {reduction * 0.8:.1f}% - {reduction * 1.2:.1f}%")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())