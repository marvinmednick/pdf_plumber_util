#!/usr/bin/env python3
"""
Focused testing for single-objective prompt optimization.

Tests each content type individually, then combinations, to find optimal wording
and measure performance scaling.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_focused_single_objective_test():
    """Test all single-objective templates on content page."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # Use the small content page for testing
    test_file = test_data_dir / "h264_content_page_305.json"

    if not test_file.exists():
        print(f"❌ Test data file not found: {test_file}")
        return

    # Single-objective templates to test
    single_objective_templates = [
        "headers_footers_only.txt",
        "section_headings_only.txt",
        "table_titles_only.txt",
        "figure_titles_only.txt",
        "toc_entries_only.txt",
        "equations_only.txt"
    ]

    print(f"🎯 FOCUSED SINGLE-OBJECTIVE TESTING")
    print(f"{'='*80}")
    print(f"Test data: {test_file.name} ({test_file.stat().st_size / 1024:.1f} KB)")
    print(f"Testing {len(single_objective_templates)} single-objective templates")

    # Initialize tester
    try:
        tester = PromptTester()
        print(f"✅ PromptTester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PromptTester: {e}")
        return

    results = []

    for template_name in single_objective_templates:
        template_file = template_dir / template_name

        if not template_file.exists():
            print(f"⚠️ Template not found: {template_name}")
            continue

        objective_name = template_name.replace('.txt', '').replace('_only', '')

        print(f"\n🔍 Testing: {objective_name}")
        print(f"   Template: {template_name}")

        try:
            start_time = time.time()
            result = tester.execute_test(template_file, test_file)
            end_time = time.time()

            if result.success:
                print(f"   ✅ SUCCESS in {end_time - start_time:.2f}s")
                print(f"   LLM Time: {result.execution_time:.2f}s")
                print(f"   Request: {result.request_size:,} bytes")
                print(f"   Response: {result.response_length:,} bytes")
                print(f"   Tokens: {result.token_count}")

                # Preview response (first 200 chars)
                preview = result.response_content[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")

                results.append({
                    'objective': objective_name,
                    'template': template_name,
                    'success': True,
                    'execution_time': result.execution_time,
                    'request_size': result.request_size,
                    'response_length': result.response_length,
                    'token_count': result.token_count
                })

            else:
                print(f"   ❌ FAILED in {end_time - start_time:.2f}s")
                print(f"   Error: {result.error_message}")

                results.append({
                    'objective': objective_name,
                    'template': template_name,
                    'success': False,
                    'error': result.error_message
                })

        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results.append({
                'objective': objective_name,
                'template': template_name,
                'success': False,
                'error': str(e)
            })

    # Save and analyze results
    results_file = results_dir / "single_objective_analysis.json"
    with open(results_file, 'w') as f:
        json.dump({
            'test_data': test_file.name,
            'data_size_kb': test_file.stat().st_size / 1024,
            'total_templates': len(single_objective_templates),
            'results': results
        }, f, indent=2)

    print(f"\n{'='*80}")
    print(f"SINGLE-OBJECTIVE ANALYSIS COMPLETE")
    print(f"{'='*80}")

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    print(f"✅ Successful: {len(successful_results)}/{len(results)}")
    print(f"❌ Failed: {len(failed_results)}")

    if successful_results:
        # Sort by performance
        successful_results.sort(key=lambda x: x['execution_time'])

        print(f"\n🏆 PERFORMANCE RANKING (fastest first):")
        for i, result in enumerate(successful_results, 1):
            print(f"{i}. {result['objective']:20} | {result['execution_time']:5.2f}s | {result['request_size']:6,} bytes")

        fastest = successful_results[0]
        slowest = successful_results[-1]
        print(f"\n📊 PERFORMANCE SPREAD:")
        print(f"Fastest: {fastest['objective']} ({fastest['execution_time']:.2f}s)")
        print(f"Slowest: {slowest['objective']} ({slowest['execution_time']:.2f}s)")
        print(f"Ratio: {slowest['execution_time'] / fastest['execution_time']:.1f}x difference")

    if failed_results:
        print(f"\n❌ FAILED OBJECTIVES:")
        for result in failed_results:
            print(f"   {result['objective']}: {result['error']}")

    print(f"\n💾 Detailed results saved to: {results_file}")

    return successful_results


if __name__ == "__main__":
    run_focused_single_objective_test()