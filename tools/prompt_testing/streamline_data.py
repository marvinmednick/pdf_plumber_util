#!/usr/bin/env python3
"""
Streamline PDF extraction data for LLM analysis.

This utility converts raw PDF extraction data (with verbose text_segments, spacing metadata, etc.)
into a streamlined format optimized for LLM consumption, removing unnecessary details while
preserving essential information for content detection.

Usage:
    python streamline_data.py input.json > streamlined_output.json
    python streamline_data.py input1.json input2.json --output-dir streamlined_data/
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse


def extract_streamlined_blocks(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract streamlined blocks from page data.

    Args:
        page_data: Raw page extraction data with blocks or doc_blocks

    Returns:
        List of streamlined blocks with essential information only
    """
    streamlined_blocks = []

    # Handle different block formats
    blocks_key = 'blocks' if 'blocks' in page_data else 'doc_blocks' if 'doc_blocks' in page_data else None

    if not blocks_key:
        return streamlined_blocks

    for block in page_data[blocks_key]:
        # Extract text lines - handle different formats
        text_lines = []

        if 'text_segments' in block:
            # Format 1: text_segments array
            for segment in block['text_segments']:
                if 'text' in segment:
                    text_lines.append(segment['text'])
        elif 'lines' in block:
            # Format 2: lines array - extract text from line objects
            for line in block['lines']:
                if isinstance(line, dict) and 'text' in line:
                    text_lines.append(line['text'])
                elif isinstance(line, str):
                    text_lines.append(line)
        elif 'text' in block:
            # Format 3: single text field
            text_lines = [block['text']]

        # Extract position from bbox if available
        bbox = block.get('bbox', {})
        y0 = bbox.get('y0', block.get('y0', 0.0))
        x0 = bbox.get('x0', block.get('x0', 0.0))

        # Create streamlined block with only essential info
        streamlined_block = {
            'text_lines': text_lines,
            'font_name': block.get('predominant_font', block.get('font_name', 'Unknown')),
            'font_size': block.get('predominant_size', block.get('font_size', 0.0)),
            'y0': y0,
            'x0': x0
        }

        streamlined_blocks.append(streamlined_block)

    return streamlined_blocks


def convert_to_streamlined_format(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert raw PDF extraction data to streamlined LLM format.

    This removes heavy text_segments, spacing metadata, and other verbose
    data while preserving essential information for content detection.

    Args:
        raw_data: Raw extraction data from PDF processing

    Returns:
        Streamlined data optimized for LLM analysis
    """
    if 'pages' in raw_data:
        # Handle multi-page format
        streamlined_pages = []
        for page_data in raw_data['pages']:
            streamlined_blocks = extract_streamlined_blocks(page_data)
            streamlined_pages.append({
                'page_index': page_data.get('page', 1),
                'blocks': streamlined_blocks,
                'block_count': len(streamlined_blocks)
            })
        return {'pages': streamlined_pages}
    else:
        # Handle single page format - assume it's page data directly
        streamlined_blocks = extract_streamlined_blocks(raw_data)
        return {
            'page_index': raw_data.get('page', 1),
            'blocks': streamlined_blocks,
            'block_count': len(streamlined_blocks)
        }


def streamline_file(input_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Streamline a single data file.

    Args:
        input_path: Path to input JSON file
        output_path: Optional path to output file. If None, returns data without saving

    Returns:
        Streamlined data
    """
    # Load raw data
    with open(input_path, 'r') as f:
        raw_data = json.load(f)

    # Convert to streamlined format
    streamlined_data = convert_to_streamlined_format(raw_data)

    # Calculate statistics
    if 'pages' in streamlined_data:
        total_blocks = sum(page['block_count'] for page in streamlined_data['pages'])
        page_count = len(streamlined_data['pages'])
    else:
        total_blocks = streamlined_data['block_count']
        page_count = 1

    # Add metadata
    result = {
        'source_file': input_path.name,
        'streamlined_data': streamlined_data,
        'metadata': {
            'page_count': page_count,
            'total_blocks': total_blocks
        }
    }

    # Save to output file if specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Streamlined: {input_path.name} → {output_path.name} ({total_blocks} blocks, {page_count} pages)",
              file=sys.stderr)

    return result


def main():
    """Main entry point for the streamlining utility."""
    parser = argparse.ArgumentParser(
        description='Streamline PDF extraction data for LLM analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Streamline single file to stdout
  python streamline_data.py h264_content_page_50.json > streamlined_page50.json

  # Streamline multiple files to output directory
  python streamline_data.py test_data/*.json --output-dir streamlined_data/

  # Streamline with custom output naming
  python streamline_data.py h264_content_page_50.json --output streamlined_page50.json
        '''
    )

    parser.add_argument('input_files', nargs='+', type=Path,
                       help='Input JSON file(s) to streamline')
    parser.add_argument('--output-dir', '-d', type=Path,
                       help='Output directory for streamlined files (default: stdout for single file)')
    parser.add_argument('--output', '-o', type=Path,
                       help='Output file path (only for single input file)')
    parser.add_argument('--prefix', '-p', default='streamlined_',
                       help='Prefix for output filenames when using --output-dir (default: streamlined_)')

    args = parser.parse_args()

    input_files = args.input_files

    # Validate input files exist
    missing_files = [f for f in input_files if not f.exists()]
    if missing_files:
        print(f"❌ Error: Files not found: {missing_files}", file=sys.stderr)
        sys.exit(1)

    # Handle single file with --output flag or stdout
    if len(input_files) == 1 and not args.output_dir:
        input_file = input_files[0]

        if args.output:
            # Save to specified output file
            streamline_file(input_file, args.output)
        else:
            # Output to stdout
            result = streamline_file(input_file)
            print(json.dumps(result, indent=2))

        return

    # Handle multiple files or --output-dir specified
    if not args.output_dir:
        print("❌ Error: --output-dir required for multiple input files", file=sys.stderr)
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔄 Streamlining {len(input_files)} file(s)...", file=sys.stderr)

    for input_file in input_files:
        output_filename = f"{args.prefix}{input_file.stem}.json"
        output_path = args.output_dir / output_filename
        streamline_file(input_file, output_path)

    print(f"\n✅ Streamlined {len(input_files)} file(s) to {args.output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()