#!/usr/bin/env python3
"""Test comprehensive pattern detection across different document types."""

import sys
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf_plumb.core.pattern_manager import PatternSetManager


def test_document_types():
    """Test patterns against different document type examples."""
    manager = PatternSetManager()

    # Simulate different document types
    document_types = {
        'Academic Paper': [
            '1 Introduction',
            '2 Related Work',
            '2.1 Background',
            '2.2 Previous Studies',
            '3 Methodology',
            '3.1 Data Collection',
            '3.2 Analysis Framework',
            '4 Results',
            '5 Discussion',
            '6 Conclusion',
        ],

        'Technical Standard (like H.264)': [
            '9.3.4.6Byte stuffing process',
            'Annex A',
            'A.1Requirements on video decoder',
            'A.2Profiles',
            'A.2.1Baseline profile',
            'Figure 9-11 – Flowchart',
            'Table 7-2: Motion vectors',
        ],

        'Legal Document': [
            'I. Definitions',
            'II. Terms and Conditions',
            'III. Liability',
            'A. General Provisions',
            'B. Specific Terms',
            '1. Scope of Agreement',
            '2. Payment Terms',
            'a. Due dates',
            'b. Late fees',
            '(i) First violation',
            '(ii) Subsequent violations',
        ],

        'Manual/Guide': [
            'Chapter 1: Getting Started',
            'Chapter 2: Basic Operations',
            'Section 2.1 Installation',
            'Section 2.2 Configuration',
            'Appendix A: Troubleshooting',
            'Appendix B: Reference',
        ],

        'Research Report': [
            'Part I: Executive Summary',
            'Part II: Detailed Findings',
            '1. Introduction',
            '1.1 Background',
            '1.2 Objectives',
            'i. Primary goals',
            'ii. Secondary objectives',
            'a. Short-term targets',
            'b. Long-term vision',
        ]
    }

    section_patterns = manager.get_pattern_set('section_patterns')

    print("🔍 Comprehensive Pattern Detection Test Across Document Types\n")

    for doc_type, examples in document_types.items():
        print(f"📄 {doc_type}:")

        # Track which patterns work for this document type
        working_patterns = set()
        total_matches = 0

        for text in examples:
            matches_found = []
            for pattern in section_patterns:
                match = pattern.compiled_regex.search(text)
                if match:
                    matches_found.append((pattern.name, match.group(1)))
                    working_patterns.add(pattern.name)
                    total_matches += 1

            # Show the best match (first one found)
            if matches_found:
                best_pattern, best_match = matches_found[0]
                print(f"  ✓ '{text}' → {best_pattern}: '{best_match}'")
            else:
                print(f"  ❌ '{text}' → No pattern match")

        print(f"  📊 Summary: {total_matches} matches using {len(working_patterns)} different pattern types")
        if working_patterns:
            print(f"  🎯 Effective patterns: {', '.join(sorted(working_patterns))}")
        print()


def test_pattern_coverage():
    """Test coverage of all pattern types."""
    manager = PatternSetManager()
    section_patterns = manager.get_pattern_set('section_patterns')

    print("📊 Pattern Coverage Analysis:")
    print(f"Total section patterns available: {len(section_patterns)}\n")

    # Test each pattern individually
    for pattern in section_patterns:
        print(f"🔧 {pattern.name}:")
        print(f"   Description: {pattern.description}")
        print(f"   Regex: {pattern.regex}")
        print(f"   Type: {pattern.pattern_type}")
        print()


def main():
    """Run comprehensive pattern tests."""
    print("🧪 Comprehensive Pattern Detection Analysis\n")

    test_document_types()
    print("\n" + "="*80 + "\n")
    test_pattern_coverage()

    return 0


if __name__ == "__main__":
    sys.exit(main())