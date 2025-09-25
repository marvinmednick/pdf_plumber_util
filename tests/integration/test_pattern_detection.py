#!/usr/bin/env python3
"""Test script for pattern detection components."""

import json
import sys
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf_plumb.core.pattern_manager import PatternSetManager
from pdf_plumb.core.document_scanner import DocumentScanner


def test_pattern_manager():
    """Test PatternSetManager functionality."""
    print("🔧 Testing PatternSetManager...")

    manager = PatternSetManager()

    # Test pattern loading
    all_patterns = manager.get_all_patterns()
    print(f"  ✓ Loaded {len(all_patterns)} patterns")

    # Test pattern sets
    section_patterns = manager.get_pattern_set('section_patterns')
    print(f"  ✓ Section patterns: {len(section_patterns)} patterns")

    toc_patterns = manager.get_pattern_set('toc_patterns')
    print(f"  ✓ TOC patterns: {len(toc_patterns)} patterns")

    # Test pattern validation
    errors = manager.validate_patterns()
    if errors:
        print(f"  ❌ Pattern validation errors: {errors}")
        return False
    else:
        print("  ✓ All patterns validate successfully")

    # Test statistics
    stats = manager.get_pattern_statistics()
    print(f"  ✓ Pattern statistics: {stats}")

    print("✅ PatternSetManager tests passed\n")


def test_document_scanner():
    """Test DocumentScanner with real document data."""
    print("🔍 Testing DocumentScanner...")

    # Load test document data
    test_file = Path("output/h264_pg305_10pgs_blocks.json")
    if not test_file.exists():
        print(f"  ❌ Test file not found: {test_file}")
        return False

    with open(test_file, 'r') as f:
        document_data = json.load(f)

    print(f"  📄 Loaded document with {len(document_data['pages'])} pages")

    # Initialize scanner
    manager = PatternSetManager()
    scanner = DocumentScanner(manager)

    # Perform full document scan
    print("  🔍 Performing full document scan...")
    scan_result = scanner.scan_full_document(document_data)

    # Display results
    print(f"  ✓ Scan completed: {scan_result.scan_statistics['total_matches']} total matches")
    print(f"  ✓ Patterns with matches: {scan_result.scan_statistics['patterns_with_matches']}")
    print(f"  ✓ Pages scanned: {scan_result.scan_statistics['pages_scanned']}")

    # Show ALL matches by type
    pattern_stats = scan_result.scan_statistics['pattern_statistics']
    for pattern_name, stats in pattern_stats.items():
        if stats['match_count'] > 0:
            print(f"    • {pattern_name}: {stats['match_count']} matches on {stats['pages_with_matches']} pages")

            # Show ALL matches for this pattern
            matches = scanner.get_matches_by_pattern(scan_result, pattern_name)
            print(f"      ALL MATCHES ({len(matches)} total):")
            for i, match in enumerate(matches):
                # Truncate long text but show the full match
                text_preview = match.text.strip()[:80]
                if len(match.text.strip()) > 80:
                    text_preview += "..."
                print(f"        [{match.page}:{match.line:2d}] '{text_preview}' → '{match.match}'")
            print()  # Add spacing between pattern types

    # Test font analysis
    font_analysis = scan_result.font_analysis
    print(f"  ✓ Font analysis - Body text: {font_analysis.get('body_text_font', 'Unknown')} {font_analysis.get('body_text_size', 'Unknown')}")
    print(f"  ✓ Total unique fonts: {font_analysis.get('total_unique_fonts', 0)}")

    # Test document context
    context = scan_result.document_context
    print(f"  ✓ Document context: {context['total_pages']} pages, {context['page_width']}x{context['page_height']}pt")

    # Test LLM format generation
    print("  📤 Testing LLM format generation...")
    llm_format = scanner.format_for_llm_analysis(scan_result)

    print(f"    • Section patterns: {len(llm_format.get('section_pattern_matches', {}))}")
    print(f"    • TOC patterns: {len(llm_format.get('toc_pattern_matches', {}))}")
    print(f"    • Figure/Table patterns: {len(llm_format.get('figure_table_pattern_matches', {}))}")

    print("✅ DocumentScanner tests passed\n")


def test_pattern_matching():
    """Test specific pattern matching examples."""
    print("🎯 Testing specific pattern matches...")

    manager = PatternSetManager()

    # Test section patterns
    decimal_pattern = manager.get_pattern('decimal_section')
    if decimal_pattern:
        test_texts = [
            "9.3.2.1 Initialization process",
            "Figure 9-11 – Flowchart of encoding",
            "Table 7-2: Motion vector prediction",
            "version 2.1 of the specification",
            "1 Introduction",
            "A.4.3 Reference pictures"
        ]

        print(f"  Testing pattern: {decimal_pattern.description}")
        for text in test_texts:
            match = decimal_pattern.compiled_regex.search(text)
            if match:
                print(f"    ✓ '{text}' → '{match.group(0)}'")
            else:
                print(f"    - '{text}' → No match")

    print("✅ Pattern matching tests completed\n")


def main():
    """Run all pattern detection tests."""
    print("🧪 Testing Pattern Detection Architecture Components\n")

    success = True

    # Test individual components
    success &= test_pattern_manager()
    success &= test_document_scanner()
    success &= test_pattern_matching()

    if success:
        print("🎉 All pattern detection tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())