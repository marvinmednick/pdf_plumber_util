#!/usr/bin/env python3
"""Create TOC fixture from H.264 100 pages data."""

import json
from pathlib import Path

def create_toc_fixture():
    """Extract pages 5-10 from H.264 100 pages data to create TOC fixture."""

    # Load source data
    source_file = Path("output/h264_100pages_blocks.json")
    if not source_file.exists():
        print(f"Error: Source file {source_file} not found")
        return

    print(f"Loading source data from {source_file}")
    with open(source_file, 'r') as f:
        source_data = json.load(f)

    # Extract pages 5-10 (contains TOC starting on page 6)
    pages_to_extract = [5, 6, 7, 8, 9, 10]
    extracted_pages = []

    for page_data in source_data['pages']:
        if page_data['page'] in pages_to_extract:
            extracted_pages.append(page_data)
            print(f"Extracted page {page_data['page']}")

    if len(extracted_pages) != 6:
        print(f"Warning: Expected 6 pages, got {len(extracted_pages)}")

    # Create fixture structure
    fixture_data = {
        "test_info": {
            "description": "H.264 specification pages 5-10 containing Table of Contents for positive TOC detection testing",
            "source_document": "h264_100pages_blocks.json",
            "extracted_pages": pages_to_extract,
            "total_pages": len(extracted_pages),
            "created_by": "create_toc_fixture.py",
            "toc_content": {
                "page_5": "Pre-TOC content (should detect no TOC)",
                "pages_6_10": "Comprehensive TOC structure with hierarchical sections",
                "expected_toc_detected": True,
                "expected_toc_pages": [6, 7, 8, 9, 10]
            }
        },
        "document_info": {
            "original_total_pages": 100,
            "page_dimensions": {},
            "extraction_method": "word-based with blocks"
        },
        "pages": extracted_pages
    }

    # Save fixture
    output_file = Path("tests/fixtures/test_document_with_toc.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(fixture_data, f, indent=2)

    print(f"✅ Created TOC fixture: {output_file}")
    print(f"📊 Contains {len(extracted_pages)} pages: {pages_to_extract}")
    print(f"📝 TOC should be detected on pages 6-10")

    return output_file

if __name__ == "__main__":
    create_toc_fixture()