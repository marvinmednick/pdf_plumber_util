#!/usr/bin/env python3
"""Generate LLM request for header/footer detection with random page sampling.

This script creates a structured LLM prompt for analyzing headers and footers
in PDF documents using strategic random sampling of pages.

Usage:
    python llm_header_footer_analysis.py <document_file> [options]
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse


def select_pages_for_analysis(total_pages: int, min_pages_required: int = 20) -> Optional[Dict[str, Any]]:
    """
    Select 3 groups of 4 pages + 4 individual pages for analysis.
    
    Args:
        total_pages: Total number of pages in document
        min_pages_required: Minimum pages needed for this sampling strategy
        
    Returns:
        Dictionary with selected pages or None if document too short
    """
    if total_pages < min_pages_required:
        return None
    
    selected_pages = set()
    groups = []
    individuals = []
    
    # Select 3 groups of 4 consecutive pages
    max_attempts = 100
    for group_num in range(3):
        for attempt in range(max_attempts):
            # Ensure we can fit 4 consecutive pages
            start_page = random.randint(1, total_pages - 3)
            group_pages = list(range(start_page, start_page + 4))
            
            # Check for overlap with existing selections
            if not any(p in selected_pages for p in group_pages):
                groups.append(group_pages)
                selected_pages.update(group_pages)
                break
        else:
            # If we couldn't find non-overlapping groups after max attempts
            raise RuntimeError(f"Could not find non-overlapping page groups after {max_attempts} attempts")
    
    # Select 4 individual pages from remaining pages
    available_pages = [p for p in range(1, total_pages + 1) if p not in selected_pages]
    if len(available_pages) < 4:
        raise RuntimeError("Not enough pages available for individual selection")
        
    individuals = random.sample(available_pages, 4)
    selected_pages.update(individuals)
    
    return {
        'groups': groups,
        'individuals': sorted(individuals),
        'total_pages_selected': len(selected_pages),
        'selected_pages': sorted(selected_pages)
    }


def extract_streamlined_blocks(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract streamlined block data for LLM analysis.
    
    Includes only essential information:
    - text: Content for pattern recognition  
    - bbox: Position for boundary detection
    - font: Style patterns (headers often different fonts)
    - size: Size patterns (headers often larger)
    - gap_before/gap_after: Spacing context
    """
    streamlined_blocks = []
    
    # Handle different block data structures
    blocks = page_data.get('blocks', [])
    if not blocks:
        # Try to get from lines if blocks not available
        blocks = page_data.get('lines', [])
    
    for block in blocks:
        # Extract bounding box with consistent format
        bbox = block.get('bbox', {})
        if isinstance(bbox, dict):
            bbox_formatted = {
                'x0': bbox.get('x0', 0),
                'top': bbox.get('top', 0),
                'x1': bbox.get('x1', 0), 
                'bottom': bbox.get('bottom', 0)
            }
        else:
            # Handle list format [x0, top, x1, bottom]
            bbox_formatted = {
                'x0': bbox[0] if len(bbox) > 0 else 0,
                'top': bbox[1] if len(bbox) > 1 else 0,
                'x1': bbox[2] if len(bbox) > 2 else 0,
                'bottom': bbox[3] if len(bbox) > 3 else 0
            }
        
        streamlined_block = {
            'text': block.get('text', '').strip(),
            'bbox': bbox_formatted,
            'font': block.get('predominant_font', block.get('font', '')),
            'size': block.get('predominant_size', block.get('size', 0)),
            'gap_before': block.get('gap_before', 0),
            'gap_after': block.get('gap_after', 0)
        }
        
        # Only include blocks with actual text content
        if streamlined_block['text']:
            streamlined_blocks.append(streamlined_block)
    
    return streamlined_blocks


def build_header_footer_prompt(
    total_pages: int,
    group_ranges: List[str], 
    individual_pages: List[int],
    selected_page_indexes: List[int],
    page_data: List[Dict[str, Any]],
    page_width: float = 612,
    page_height: float = 792,
    footer_boundary: Optional[float] = None
) -> str:
    """Build the complete LLM prompt for header/footer analysis."""
    
    system_prompt = """You are a document structure analyst specializing in technical specifications. Your task is to analyze PDF document pages and identify header/footer boundaries to distinguish main content areas from page margins.

You will receive contextual block data from randomly sampled pages with spacing, font, and position metadata. Focus on identifying patterns that consistently appear at page tops/bottoms across the sample.

Important: Headers/footers may be absent on some pages or vary by document section. Provide specific text identification for each page."""

    footer_boundary_text = f"- Current programmatic footer boundary: {footer_boundary}pt" if footer_boundary else ""
    
    user_prompt = f"""Analyze these 16 randomly sampled pages from a {total_pages}-page technical document to identify header/footer patterns:

**IMPORTANT**: Page numbers refer to document position (page index), NOT printed page numbers on the page.
- Document has pages indexed 1-{total_pages}
- Printed page numbers may be different: roman numerals (i, ii, iii), missing, or offset
- When you identify page numbers in footers, note both the page index AND the printed page number

**Sampling Strategy**: 
- 3 groups of 4 consecutive pages: {', '.join(group_ranges)}
- 4 individual pages: {', '.join(map(str, individual_pages))}
- Selected page indexes: {', '.join(map(str, selected_page_indexes))}

**Analysis Objective**: Distinguish main content area from header/footer margins
**Document Info**:
- Total pages: {total_pages}
- Page dimensions: {page_width} x {page_height} pts
{footer_boundary_text}

**Key Guidelines**:
- Headers/footers may be ABSENT on some pages (title pages, chapter starts, etc.)
- Patterns may be INCONSISTENT across document sections
- Some pages may have headers but no footers, or vice versa
- Identify the actual TEXT content of headers/footers for each page

**Pages Data**:
{json.dumps(page_data, indent=2)}

For each page index, analyze the blocks and identify:
1. Specific header text (or "NONE" if absent)
2. Specific footer text (or "NONE" if absent)
3. **If footer contains page numbering**: Note both the page index and printed page number
4. Main content boundaries
5. Cross-page pattern consistency

**Response Format**:
```json
{{
  "sampling_summary": {{
    "page_indexes_analyzed": {selected_page_indexes},
    "group_ranges": {group_ranges},
    "individual_pages": {individual_pages}
  }},
  "per_page_analysis": [
    {{
      "page_index": 1,
      "header": {{"detected": true, "text": "Document Title", "y_position": 52}},
      "footer": {{"detected": true, "text": "Page 1", "y_position": 748, "printed_page_number": "1"}}
    }}
  ],
  "header_pattern": {{
    "consistent_pattern": true,
    "pages_with_headers": [1, 2, 3],
    "pages_without_headers": [4, 5],
    "typical_content": ["Document Title", "Chapter Name"],
    "y_boundary_typical": 55,
    "confidence": "High|Medium|Low",
    "reasoning": "explanation"
  }},
  "footer_pattern": {{
    "consistent_pattern": true,
    "pages_with_footers": [1, 2, 3, 4, 5],
    "pages_without_footers": [],
    "typical_content": ["Page X", "© Copyright"],
    "y_boundary_typical": 748,
    "confidence": "High|Medium|Low", 
    "reasoning": "explanation"
  }},
  "page_numbering_analysis": {{
    "numbering_system_detected": "arabic|roman|mixed|none",
    "patterns": [
      {{"page_indexes": [1, 2], "format": "arabic", "examples": ["1", "2"]}},
      {{"page_indexes": [3, 4], "format": "roman", "examples": ["iii", "iv"]}}
    ],
    "missing_page_numbers": [],
    "offset_detected": {{"offset": 0, "explanation": "page numbers match indexes"}}
  }},
  "content_area_boundaries": {{
    "main_content_starts_after_y": 65,
    "main_content_ends_before_y": 735,
    "confidence": "High|Medium|Low"
  }},
  "insights": [
    "Key observations about header/footer patterns",
    "Notable exceptions or variations"
  ]
}}
```

Provide structured analysis with confidence scores and specific reasoning for your determinations."""

    return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"


def estimate_prompt_tokens(prompt: str) -> int:
    """Rough estimate of token count for prompt."""
    # Rough approximation: 1 token ≈ 3.5 characters for technical content
    return len(prompt) // 3


def generate_llm_header_footer_request(
    document_file: str, 
    output_file: Optional[str] = None,
    seed: Optional[int] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate LLM request for header/footer detection with random page sampling.
    
    Args:
        document_file: Path to JSON file containing PDF document data
        output_file: Optional path to save the generated request
        seed: Optional random seed for reproducible page selection
        
    Returns:
        Tuple of (prompt_string, selection_metadata)
    """
    
    if seed is not None:
        random.seed(seed)
    
    # Load document data
    document_path = Path(document_file)
    if not document_path.exists():
        raise FileNotFoundError(f"Document file not found: {document_file}")
    
    print(f"📖 Loading document: {document_path.name}")
    
    with open(document_file, 'r') as f:
        doc_data = json.load(f)
    
    # Handle different JSON structures
    if 'pages' in doc_data:
        pages = doc_data['pages'] 
        print(f"📄 Found {len(pages)} pages in document")
    elif isinstance(doc_data, list):
        pages = doc_data
        print(f"📄 Found {len(pages)} pages in document")
    else:
        raise ValueError("Cannot determine page structure in JSON. Expected 'pages' key or list of pages.")
    
    total_pages = len(pages)
    
    # Select pages using our sampling strategy
    print(f"🎲 Selecting random page sample...")
    selection = select_pages_for_analysis(total_pages)
    if not selection:
        raise ValueError(f"Document too short ({total_pages} pages). Need at least 20 pages for this sampling strategy.")
    
    print(f"✅ Selected {selection['total_pages_selected']} pages:")
    print(f"   Groups: {[f'{group[0]}-{group[-1]}' for group in selection['groups']]}")
    print(f"   Individual: {selection['individuals']}")
    
    # Build page data for LLM with clear indexing
    page_data_for_llm = []
    
    for page_idx in selection['selected_pages']:
        # Convert to 0-based index for array access
        array_idx = page_idx - 1
        
        if array_idx >= len(pages):
            raise IndexError(f"Page index {page_idx} out of range (document has {len(pages)} pages)")
            
        page = pages[array_idx]
        
        # Extract streamlined block data
        streamlined_blocks = extract_streamlined_blocks(page)
        
        page_data_for_llm.append({
            'page_index': page_idx,
            'blocks': streamlined_blocks,
            'block_count': len(streamlined_blocks)
        })
        
        print(f"   Page {page_idx}: {len(streamlined_blocks)} blocks")
    
    # Get document metadata
    page_width = pages[0].get('page_width', pages[0].get('width', 612))
    page_height = pages[0].get('page_height', pages[0].get('height', 792))
    footer_boundary = None
    
    # Try to find programmatic footer boundary from analysis
    if 'analysis' in pages[0]:
        footer_boundary = pages[0]['analysis'].get('footer_boundary')
    
    # Format group ranges for prompt
    group_ranges = [f"{group[0]}-{group[-1]}" for group in selection['groups']]
    
    # Build the complete LLM request
    prompt = build_header_footer_prompt(
        total_pages=total_pages,
        group_ranges=group_ranges,
        individual_pages=selection['individuals'], 
        selected_page_indexes=selection['selected_pages'],
        page_data=page_data_for_llm,
        page_width=page_width,
        page_height=page_height,
        footer_boundary=footer_boundary
    )
    
    # Estimate token usage
    estimated_tokens = estimate_prompt_tokens(prompt)
    print(f"📊 Estimated tokens: ~{estimated_tokens:,}")
    
    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        request_data = {
            'prompt': prompt,
            'selection_metadata': selection,
            'document_metadata': {
                'source_file': str(document_path),
                'total_pages': total_pages,
                'page_dimensions': {'width': page_width, 'height': page_height},
                'footer_boundary': footer_boundary
            },
            'estimated_tokens': estimated_tokens,
            'generation_params': {
                'seed': seed,
                'timestamp': json.dumps(None, default=str)  # Will be current time when serialized
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(request_data, f, indent=2)
        
        print(f"💾 LLM request saved to: {output_file}")
    
    return prompt, selection


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description='Generate LLM request for header/footer detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llm_header_footer_analysis.py output/h264_100pages_blocks.json
  python llm_header_footer_analysis.py doc.json --output llm_requests/header_analysis.json --seed 42
        """
    )
    
    parser.add_argument(
        'document_file',
        help='Path to JSON file containing PDF document data'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Save LLM request to JSON file'
    )
    
    parser.add_argument(
        '--seed', '-s',
        type=int,
        help='Random seed for reproducible page selection'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    try:
        # Generate the LLM request
        prompt, selection = generate_llm_header_footer_request(
            args.document_file,
            args.output,
            args.seed
        )
        
        if not args.quiet:
            print(f"\n🎯 LLM Request Generated Successfully")
            print(f"Selected pages: {selection['selected_pages']}")
            
            if not args.output:
                print("\n" + "="*80)
                print("LLM PROMPT:")
                print("="*80)
                print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
                print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())