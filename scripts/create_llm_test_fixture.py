#!/usr/bin/env python3
"""
Create LLM test fixtures from existing document JSON data.

This script extracts specific pages from a full document JSON file to create
focused test cases for LLM analysis validation.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def extract_pages_from_json(
    json_file: Path, 
    pages: List[int], 
    output_file: Path,
    test_description: str = ""
) -> None:
    """Extract specific pages from document JSON to create test fixture.
    
    Args:
        json_file: Path to full document JSON file
        pages: List of page numbers to extract (1-based indexing) 
        output_file: Path for output test fixture
        test_description: Description of what this test case validates
    """
    
    # Load full document data
    print(f"Loading document data from {json_file}")
    with open(json_file, 'r') as f:
        doc_data = json.load(f)
    
    # Validate we have pages data
    if 'pages' not in doc_data:
        raise ValueError("JSON file must contain 'pages' array")
    
    all_pages = doc_data['pages']
    total_pages = len(all_pages)
    
    print(f"Document has {total_pages} pages")
    
    # Validate requested pages exist
    invalid_pages = [p for p in pages if p < 1 or p > total_pages]
    if invalid_pages:
        raise ValueError(f"Invalid page numbers: {invalid_pages}. Document has pages 1-{total_pages}")
    
    # Extract requested pages (convert to 0-based indexing)
    extracted_pages = []
    for page_num in sorted(pages):
        page_index = page_num - 1
        page_data = all_pages[page_index]
        
        # Ensure page has the expected structure
        if 'page_number' not in page_data:
            page_data['page_number'] = page_num
            
        extracted_pages.append(page_data)
        print(f"Extracted page {page_num}: {len(page_data.get('blocks', []))} blocks")
    
    # Create test fixture structure
    test_fixture = {
        "test_info": {
            "description": test_description,
            "source_document": str(json_file.name),
            "extracted_pages": pages,
            "total_pages": len(pages),
            "created_by": "create_llm_test_fixture.py"
        },
        "document_info": {
            "original_total_pages": total_pages,
            "page_dimensions": doc_data.get('page_dimensions', {}),
            "extraction_method": doc_data.get('extraction_method', 'unknown')
        },
        "pages": extracted_pages
    }
    
    # Save test fixture
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(test_fixture, f, indent=2)
    
    print(f"Created test fixture: {output_file}")
    print(f"Test fixture contains {len(extracted_pages)} pages with {sum(len(p.get('blocks', [])) for p in extracted_pages)} total blocks")


def main():
    parser = argparse.ArgumentParser(
        description="Extract specific pages from document JSON to create LLM test fixtures"
    )
    parser.add_argument(
        "json_file", 
        type=Path,
        help="Path to full document JSON file"
    )
    parser.add_argument(
        "--pages",
        type=str,
        required=True,
        help="Comma-separated list of page numbers to extract (e.g., '97,98,99')"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for test fixture JSON file"
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Description of what this test case validates"
    )
    
    args = parser.parse_args()
    
    # Parse page numbers
    try:
        pages = [int(p.strip()) for p in args.pages.split(',')]
    except ValueError as e:
        print(f"Error parsing page numbers: {e}")
        print("Pages must be comma-separated integers (e.g., '97,98,99')")
        return 1
    
    try:
        extract_pages_from_json(
            json_file=args.json_file,
            pages=pages,
            output_file=args.output,
            test_description=args.description
        )
        return 0
        
    except Exception as e:
        print(f"Error creating test fixture: {e}")
        return 1


if __name__ == "__main__":
    exit(main())