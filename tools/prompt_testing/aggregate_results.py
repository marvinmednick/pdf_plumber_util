#!/usr/bin/env python3
"""
Aggregate multiple Phase 1 extraction results into a single dataset for Phase 2 pattern analysis.

This script combines extraction results from multiple test pages into a consolidated format
that can be analyzed to identify document structure patterns.

Usage:
    python aggregate_results.py result1.json result2.json result3.json > aggregated.json
    python aggregate_results.py results/comprehensive_*.json > aggregated_data.json
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def load_result_file(filepath: Path) -> Dict[str, Any]:
    """Load a single Phase 1 result file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def parse_response_content(response_content: Any) -> Dict[str, Any]:
    """
    Parse the response_content field which may be either a dict or a JSON string.

    Args:
        response_content: The response_content field from a result file

    Returns:
        Parsed dictionary containing the extracted content
    """
    if isinstance(response_content, dict):
        return response_content
    elif isinstance(response_content, str):
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse response_content as JSON", file=sys.stderr)
            return {}
    else:
        return {}


def aggregate_results(result_files: List[Path]) -> Dict[str, Any]:
    """
    Aggregate multiple Phase 1 result files into a single consolidated dataset.

    Args:
        result_files: List of paths to Phase 1 result JSON files

    Returns:
        Aggregated data structure containing all extracted content with metadata
    """
    aggregated = {
        "source_files": [],
        "total_pages_analyzed": 0,
        "aggregated_content": {
            "section_headings": [],
            "table_titles": [],
            "figure_titles": [],
            "equation_titles": [],
            "toc_entries": []
        },
        "metadata": {
            "total_execution_time": 0.0,
            "total_request_size": 0,
            "total_response_length": 0
        }
    }

    for filepath in result_files:
        try:
            result = load_result_file(filepath)

            # Track source file
            aggregated["source_files"].append({
                "filename": filepath.name,
                "template": result.get("template", "unknown"),
                "data_file": result.get("data_file", "unknown")
            })

            aggregated["total_pages_analyzed"] += 1

            # Parse the response content (handle both dict and JSON string formats)
            content = parse_response_content(result.get("response_content", {}))

            # Aggregate each content type with source file reference
            for content_type in ["section_headings", "table_titles", "figure_titles",
                                "equation_titles", "toc_entries"]:
                items = content.get(content_type, [])
                for item in items:
                    # Add source tracking to each item
                    item_with_source = item.copy()
                    item_with_source["_source_file"] = filepath.name
                    item_with_source["_source_data"] = result.get("data_file", "unknown")
                    aggregated["aggregated_content"][content_type].append(item_with_source)

            # Aggregate metadata
            aggregated["metadata"]["total_execution_time"] += result.get("execution_time", 0.0)
            aggregated["metadata"]["total_request_size"] += result.get("request_size", 0)
            aggregated["metadata"]["total_response_length"] += result.get("response_length", 0)

        except Exception as e:
            print(f"Error processing {filepath}: {e}", file=sys.stderr)
            continue

    # Add summary statistics
    aggregated["summary"] = {
        "section_headings_count": len(aggregated["aggregated_content"]["section_headings"]),
        "table_titles_count": len(aggregated["aggregated_content"]["table_titles"]),
        "figure_titles_count": len(aggregated["aggregated_content"]["figure_titles"]),
        "equation_titles_count": len(aggregated["aggregated_content"]["equation_titles"]),
        "toc_entries_count": len(aggregated["aggregated_content"]["toc_entries"]),
        "total_items": sum([
            len(aggregated["aggregated_content"]["section_headings"]),
            len(aggregated["aggregated_content"]["table_titles"]),
            len(aggregated["aggregated_content"]["figure_titles"]),
            len(aggregated["aggregated_content"]["equation_titles"]),
            len(aggregated["aggregated_content"]["toc_entries"])
        ])
    }

    return aggregated


def main():
    """Main entry point for the aggregation script."""
    if len(sys.argv) < 2:
        print("Usage: python aggregate_results.py result1.json result2.json ...", file=sys.stderr)
        print("       python aggregate_results.py results/comprehensive_*.json > aggregated.json", file=sys.stderr)
        sys.exit(1)

    # Collect all result file paths
    result_files = [Path(arg) for arg in sys.argv[1:]]

    # Validate files exist
    missing_files = [f for f in result_files if not f.exists()]
    if missing_files:
        print(f"Error: Files not found: {missing_files}", file=sys.stderr)
        sys.exit(1)

    # Aggregate the results
    aggregated = aggregate_results(result_files)

    # Output to stdout as JSON
    print(json.dumps(aggregated, indent=2))

    # Print summary to stderr for user visibility
    print(f"\n=== Aggregation Summary ===", file=sys.stderr)
    print(f"Files processed: {aggregated['total_pages_analyzed']}", file=sys.stderr)
    print(f"Section headings: {aggregated['summary']['section_headings_count']}", file=sys.stderr)
    print(f"Figure titles: {aggregated['summary']['figure_titles_count']}", file=sys.stderr)
    print(f"Table titles: {aggregated['summary']['table_titles_count']}", file=sys.stderr)
    print(f"Equation titles: {aggregated['summary']['equation_titles_count']}", file=sys.stderr)
    print(f"TOC entries: {aggregated['summary']['toc_entries_count']}", file=sys.stderr)
    print(f"Total items: {aggregated['summary']['total_items']}", file=sys.stderr)


if __name__ == "__main__":
    main()