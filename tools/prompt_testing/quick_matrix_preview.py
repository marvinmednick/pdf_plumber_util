#!/usr/bin/env python3
"""
Quick matrix preview: Test a few key scenarios to check for false positives.
"""

import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def quick_matrix_preview():
    """Quick test of key false positive scenarios."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"

    print("🔍 QUICK MATRIX PREVIEW - Testing for False Positives")
    print("="*60)

    # Key tests that should reveal false positives
    test_scenarios = [
        # Should find NOTHING (testing false positives)
        ("section_headings_only.txt", "h264_page_6_only.json", "Sections on TOC page"),
        ("figure_titles_only.txt", "h264_page_6_only.json", "Figures on TOC page"),
        ("toc_entries_only.txt", "h264_content_page_50.json", "TOC on content page"),

        # Should find SOMETHING (testing false negatives)
        ("section_headings_only.txt", "h264_content_page_50.json", "Sections on content page"),
        ("figure_titles_only.txt", "h264_content_page_305.json", "Figures on figure page"),

        # Multi-objective consistency check
        ("combo_4_content_analysis.txt", "h264_page_6_only.json", "4-objective on TOC page"),
    ]

    try:
        tester = PromptTester()
        print("✅ PromptTester initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    results = []

    for i, (template_name, data_name, description) in enumerate(test_scenarios, 1):
        template_file = template_dir / template_name
        data_file = test_data_dir / data_name

        print(f"\n📋 Test {i}/{len(test_scenarios)}: {description}")
        print(f"   Template: {template_name}")
        print(f"   Data: {data_name}")

        if not template_file.exists() or not data_file.exists():
            print(f"   ⚠️ Files not found")
            continue

        try:
            result = tester.execute_test(template_file, data_file)

            if result.success:
                # Parse findings
                try:
                    response_json = json.loads(result.response_content)
                    total_items = 0
                    findings = []

                    for key, value in response_json.items():
                        if isinstance(value, list):
                            count = len(value)
                            total_items += count
                            if count > 0:
                                findings.append(f"{count} {key}")

                    findings_text = ", ".join(findings) if findings else "Nothing found"

                    print(f"   ✅ SUCCESS: {findings_text}")
                    print(f"   Time: {result.execution_time:.2f}s")

                    # Analyze result
                    expected_empty = any(x in description.lower() for x in ["on toc", "toc on content"])
                    found_something = total_items > 0

                    if expected_empty and found_something:
                        print(f"   🚨 FALSE POSITIVE detected!")
                    elif expected_empty and not found_something:
                        print(f"   ✅ Correct negative")
                    elif not expected_empty and found_something:
                        print(f"   ✅ Correct positive")
                    elif not expected_empty and not found_something:
                        print(f"   ⚠️ Possible false negative")

                except json.JSONDecodeError:
                    print(f"   ⚠️ Parse error")

            else:
                print(f"   ❌ FAILED: {result.error_message}")

        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")

    print(f"\n{'='*60}")
    print("QUICK PREVIEW COMPLETE")
    print("This gives a snapshot of potential false positive/negative issues.")
    print("Full matrix test will provide comprehensive validation.")


if __name__ == "__main__":
    quick_matrix_preview()