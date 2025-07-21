#!/usr/bin/env python3
"""Analyze token reduction from field name shortening in PDF data.

This script analyzes how much token reduction can be achieved by shortening
JSON field names in PDF document data files.

Usage:
    python field_analysis.py <file_path> [options]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Set
import argparse
from collections import Counter

def analyze_field_usage(data: Any, field_counter: Counter = None) -> Counter:
    """Recursively count field name usage in data structure.
    
    Args:
        data: Data structure to analyze
        field_counter: Counter to accumulate results
        
    Returns:
        Counter with field name usage counts
    """
    if field_counter is None:
        field_counter = Counter()
    
    if isinstance(data, dict):
        for key, value in data.items():
            field_counter[key] += 1
            analyze_field_usage(value, field_counter)
    elif isinstance(data, list):
        for item in data:
            analyze_field_usage(item, field_counter)
    
    return field_counter

def create_field_mapping(field_counter: Counter, min_usage: int = 2) -> Dict[str, str]:
    """Create mapping from long field names to short ones.
    
    Args:
        field_counter: Field usage statistics
        min_usage: Minimum usage count to consider for shortening
        
    Returns:
        Dictionary mapping original field names to shortened versions
    """
    # Common PDF document field mappings
    standard_mappings = {
        # Coordinate fields (very high frequency)
        'bbox': 'b',
        'x0': 'x',
        'x1': 'X', 
        'top': 't',
        'bottom': 'B',
        
        # Text and content fields
        'text': 'T',
        'text_segments': 'ts',
        'line_number': 'ln',
        'lines': 'L',
        'blocks': 'bl',
        
        # Font fields
        'font': 'f',
        'predominant_font': 'pf',
        'predominant_size': 'ps',
        'reported_size': 'rs',
        'rounded_size': 'rz',
        'predominant_font_coverage': 'pfc',
        'predominant_size_coverage': 'psc',
        'direction': 'd',
        
        # Spacing fields
        'gap_before': 'gb',
        'gap_after': 'ga',
        'spacing': 's',
        
        # Page fields
        'page': 'p',
        'page_width': 'pw',
        'page_height': 'ph',
        'pages': 'P',
        
        # Coverage and statistics
        'size_coverage': 'sc',
        'font_coverage': 'fc'
    }
    
    # Calculate savings for each mapping
    mapping_with_savings = {}
    for original, short in standard_mappings.items():
        if original in field_counter and field_counter[original] >= min_usage:
            usage_count = field_counter[original]
            chars_saved = (len(original) - len(short)) * usage_count
            mapping_with_savings[original] = {
                'short': short,
                'usage_count': usage_count,
                'chars_saved': chars_saved,
                'original_chars': len(original) * usage_count,
                'new_chars': len(short) * usage_count
            }
    
    return mapping_with_savings

def apply_field_mapping(data: Any, field_mapping: Dict[str, str]) -> Any:
    """Apply field name mapping to data structure.
    
    Args:
        data: Data structure to transform
        field_mapping: Dictionary mapping old field names to new ones
        
    Returns:
        Transformed data structure with shortened field names
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            new_dict[new_key] = apply_field_mapping(value, field_mapping)
        return new_dict
    elif isinstance(data, list):
        return [apply_field_mapping(item, field_mapping) for item in data]
    else:
        return data

def analyze_field_reduction(original_data: Any, sample_pages: int = 5) -> Dict[str, Any]:
    """Analyze field name reduction impact.
    
    Args:
        original_data: Original data structure
        sample_pages: Number of pages to analyze
        
    Returns:
        Analysis results
    """
    # Handle different file structures
    if isinstance(original_data, list):
        pages = original_data[:sample_pages]
        full_data = pages
    elif 'pages' in original_data:
        pages = original_data['pages'][:sample_pages]
        full_data = {'pages': pages}
    else:
        pages = [original_data]
        full_data = original_data
    
    # Analyze field usage
    field_counter = analyze_field_usage(full_data)
    
    # Create field mapping
    field_mapping_details = create_field_mapping(field_counter)
    
    # Extract just the mapping for transformation
    field_mapping = {k: v['short'] for k, v in field_mapping_details.items()}
    
    # Apply mapping
    reduced_data = apply_field_mapping(full_data, field_mapping)
    
    # Convert to JSON for size comparison
    original_json = json.dumps(full_data, separators=(',', ':'))
    reduced_json = json.dumps(reduced_data, separators=(',', ':'))
    
    # Calculate savings
    char_reduction = len(original_json) - len(reduced_json)
    reduction_percentage = (char_reduction / len(original_json)) * 100
    
    # Calculate field-specific savings
    total_field_chars_saved = sum(v['chars_saved'] for v in field_mapping_details.values())
    total_original_field_chars = sum(v['original_chars'] for v in field_mapping_details.values())
    
    return {
        'pages_analyzed': len(pages),
        'field_usage_stats': dict(field_counter.most_common(20)),
        'field_mapping_details': field_mapping_details,
        'applied_mapping': field_mapping,
        'size_analysis': {
            'original_length': len(original_json),
            'reduced_length': len(reduced_json),
            'char_reduction': char_reduction,
            'reduction_percentage': reduction_percentage
        },
        'field_specific_savings': {
            'total_field_chars_saved': total_field_chars_saved,
            'total_original_field_chars': total_original_field_chars,
            'field_reduction_percentage': (total_field_chars_saved / total_original_field_chars * 100) if total_original_field_chars > 0 else 0
        }
    }

def analyze_file_field_reduction(file_path: str, sample_pages: int = 10) -> Dict[str, Any]:
    """Analyze field reduction impact on a PDF data file.
    
    Args:
        file_path: Path to JSON file
        sample_pages: Number of pages to analyze
        
    Returns:
        Analysis results
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    results = analyze_field_reduction(data, sample_pages)
    results['file_path'] = file_path
    
    return results

def print_field_analysis_results(results: Dict[str, Any]):
    """Print comprehensive field analysis results."""
    print(f"\n{'='*60}")
    print(f"FIELD NAME REDUCTION ANALYSIS")
    print(f"{'='*60}")
    
    print(f"\nFile: {Path(results['file_path']).name}")
    print(f"Pages Analyzed: {results['pages_analyzed']}")
    
    # Overall results
    size = results['size_analysis']
    print(f"\n{'='*40}")
    print(f"OVERALL RESULTS")
    print(f"{'='*40}")
    print(f"Character Reduction: {size['char_reduction']:,} chars")
    print(f"Reduction Percentage: {size['reduction_percentage']:.2f}%")
    print(f"Original Size: {size['original_length']:,} chars")
    print(f"Reduced Size: {size['reduced_length']:,} chars")
    
    # Field-specific analysis
    field_savings = results['field_specific_savings']
    print(f"\n{'='*40}")
    print(f"FIELD-SPECIFIC ANALYSIS")
    print(f"{'='*40}")
    print(f"Total Field Characters Saved: {field_savings['total_field_chars_saved']:,}")
    print(f"Field-Only Reduction: {field_savings['field_reduction_percentage']:.1f}%")
    
    # Top field mappings by savings
    print(f"\n{'='*40}")
    print(f"TOP FIELD MAPPINGS (by chars saved)")
    print(f"{'='*40}")
    
    mappings = results['field_mapping_details']
    sorted_mappings = sorted(mappings.items(), key=lambda x: x[1]['chars_saved'], reverse=True)
    
    print(f"{'Original':<20} {'Short':<6} {'Usage':<8} {'Saved':<8} {'%':<6}")
    print(f"{'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*6}")
    
    for field, details in sorted_mappings[:15]:
        reduction_pct = (details['chars_saved'] / details['original_chars']) * 100
        print(f"{field:<20} {details['short']:<6} {details['usage_count']:<8} "
              f"{details['chars_saved']:<8} {reduction_pct:<6.1f}%")
    
    # Most frequent fields
    print(f"\n{'='*40}")
    print(f"MOST FREQUENT FIELDS")
    print(f"{'='*40}")
    
    usage = results['field_usage_stats']
    print(f"{'Field Name':<20} {'Usage Count':<12} {'Mapped?':<8}")
    print(f"{'-'*20} {'-'*12} {'-'*8}")
    
    applied = results['applied_mapping']
    for field, count in list(usage.items())[:15]:
        mapped = "Yes" if field in applied else "No"
        print(f"{field:<20} {count:<12} {mapped:<8}")
    
    # Estimate token reduction
    print(f"\n{'='*40}")
    print(f"ESTIMATED TOKEN REDUCTION")
    print(f"{'='*40}")
    
    char_reduction = size['char_reduction']
    original_chars = size['original_length']
    
    # Token estimates
    estimates = {
        'conservative': char_reduction / 4.0,
        'average': char_reduction / 3.5,
        'optimistic': char_reduction / 3.0
    }
    
    for method, token_reduction in estimates.items():
        original_tokens = original_chars / (4.0 if method == 'conservative' else 3.5 if method == 'average' else 3.0)
        token_percentage = (token_reduction / original_tokens) * 100
        
        print(f"{method.capitalize():>12}: {token_reduction:,.0f} tokens ({token_percentage:.2f}%)")

def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(
        description='Analyze token reduction from field name shortening',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python field_analysis.py output/h264_100pages_lines.json
  python field_analysis.py output/h264_100pages_blocks.json --pages 15
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to JSON file containing PDF document data'
    )
    
    parser.add_argument(
        '--pages', '-p',
        type=int,
        default=10,
        help='Number of pages to analyze (default: 10)'
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
        results = analyze_file_field_reduction(
            str(input_path),
            sample_pages=args.pages
        )
        
        # Print results
        print_field_analysis_results(results)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Detailed results saved to: {args.output}")
        
        # Quick summary
        reduction = results['size_analysis']['reduction_percentage']
        print(f"\n🎯 SUMMARY: {reduction:.1f}% total reduction from field name shortening")
        print(f"   Combined with precision reduction: ~{reduction + 12:.1f}% total savings")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())