#!/usr/bin/env python3
"""
Comprehensive testing of content detection on different page types.

Tests each template against appropriate page types to validate content detection
and measure performance for realistic combinations.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_comprehensive_content_test():
    """Test templates against appropriate page types."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # Define test scenarios: (template, data_file, description)
    test_scenarios = [
        # Single-objective tests on appropriate page types
        ("section_headings_only.txt", "h264_content_page_305.json", "Section headings on content page"),
        ("section_headings_only.txt", "h264_content_page_50.json", "Section headings on mid-document page"),

        ("table_titles_only.txt", "h264_content_page_50.json", "Table titles on content page"),
        ("table_titles_only.txt", "h264_list_of_tables_page19.json", "Table detection on List of Tables page"),

        ("figure_titles_only.txt", "h264_content_page_305.json", "Figure titles on content page"),
        ("figure_titles_only.txt", "h264_list_of_figures_page17.json", "Figure detection on List of Figures page"),

        ("toc_entries_only.txt", "h264_page_6_only.json", "TOC entries on TOC page"),

        # Specialized list detection
        ("list_of_figures_detection.txt", "h264_list_of_figures_page17.json", "List of Figures detection"),
        ("list_of_tables_detection.txt", "h264_list_of_tables_page19.json", "List of Tables detection"),

        # Multi-objective tests on rich content
        ("combo_2_headings_tables.txt", "h264_content_page_50.json", "2-objective on content page"),
        ("combo_3_headings_tables_figures.txt", "h264_content_page_305.json", "3-objective on content page"),
        ("combo_4_content_analysis.txt", "h264_content_page_50.json", "4-objective on content page"),
    ]

    print(f"🔍 COMPREHENSIVE CONTENT DETECTION TEST")
    print(f"{'='*80}")
    print(f"Testing {len(test_scenarios)} scenarios across different page types")

    # Initialize tester
    try:
        tester = PromptTester()
        print(f"✅ PromptTester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PromptTester: {e}")
        return

    results = []

    for scenario_idx, (template_name, data_name, description) in enumerate(test_scenarios, 1):
        template_file = template_dir / template_name
        data_file = test_data_dir / data_name

        if not template_file.exists():
            print(f"⚠️ Template not found: {template_name}")
            continue

        if not data_file.exists():
            print(f"⚠️ Data file not found: {data_name}")
            continue

        data_size_kb = data_file.stat().st_size / 1024

        print(f"\n📋 Scenario {scenario_idx}/{len(test_scenarios)}: {description}")
        print(f"   Template: {template_name}")
        print(f"   Data: {data_name} ({data_size_kb:.1f} KB)")

        try:
            start_time = time.time()
            result = tester.execute_test(template_file, data_file)
            end_time = time.time()

            if result.success:
                print(f"   ✅ SUCCESS in {end_time - start_time:.2f}s")
                print(f"   LLM Time: {result.execution_time:.2f}s")
                print(f"   Request: {result.request_size:,} bytes")
                print(f"   Response: {result.response_length:,} bytes")

                # Try to parse response to show what was found
                try:
                    response_json = json.loads(result.response_content)
                    found_items = []
                    for key, value in response_json.items():
                        if isinstance(value, list):
                            found_items.append(f"{len(value)} {key}")
                        elif isinstance(value, dict) and value:
                            found_items.append(f"1 {key}")

                    if found_items:
                        print(f"   Found: {', '.join(found_items)}")
                    else:
                        print(f"   Found: No items detected")

                except json.JSONDecodeError:
                    print(f"   Response: {result.response_content[:100]}...")

                # Save individual response to file for detailed analysis
                response_filename = f"response_{scenario_idx:02d}_{template_name.replace('.txt', '')}_{data_name.replace('.json', '')}.json"
                response_file = results_dir / response_filename
                with open(response_file, 'w') as f:
                    json.dump({
                        'scenario': description,
                        'template': template_name,
                        'data_file': data_name,
                        'response_content': result.response_content,
                        'execution_time': result.execution_time,
                        'request_size': result.request_size,
                        'response_length': result.response_length
                    }, f, indent=2)

                results.append({
                    'scenario': description,
                    'template': template_name,
                    'data_file': data_name,
                    'data_size_kb': data_size_kb,
                    'success': True,
                    'execution_time': result.execution_time,
                    'request_size': result.request_size,
                    'response_length': result.response_length,
                    'token_count': result.token_count,
                    'response_file': response_filename
                })

            else:
                print(f"   ❌ FAILED in {end_time - start_time:.2f}s")
                print(f"   Error: {result.error_message}")

                results.append({
                    'scenario': description,
                    'template': template_name,
                    'data_file': data_name,
                    'data_size_kb': data_size_kb,
                    'success': False,
                    'error': result.error_message
                })

        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results.append({
                'scenario': description,
                'template': template_name,
                'data_file': data_name,
                'data_size_kb': data_size_kb,
                'success': False,
                'error': str(e)
            })

    # Save and analyze results
    results_file = results_dir / "comprehensive_content_analysis.json"
    with open(results_file, 'w') as f:
        json.dump({
            'total_scenarios': len(test_scenarios),
            'results': results
        }, f, indent=2)

    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE CONTENT ANALYSIS")
    print(f"{'='*80}")

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    print(f"✅ Successful: {len(successful_results)}/{len(results)}")
    print(f"❌ Failed: {len(failed_results)}")

    if successful_results:
        print(f"\n📊 PERFORMANCE BY DATA SIZE:")

        # Group by data size ranges
        size_groups = {
            'Small (< 50 KB)': [r for r in successful_results if r['data_size_kb'] < 50],
            'Medium (50-150 KB)': [r for r in successful_results if 50 <= r['data_size_kb'] < 150],
            'Large (150+ KB)': [r for r in successful_results if r['data_size_kb'] >= 150]
        }

        for group_name, group_results in size_groups.items():
            if group_results:
                avg_time = sum(r['execution_time'] for r in group_results) / len(group_results)
                avg_size = sum(r['data_size_kb'] for r in group_results) / len(group_results)
                print(f"{group_name}: {len(group_results)} tests, avg {avg_time:.2f}s, avg {avg_size:.1f}KB")

        print(f"\n🏆 FASTEST TESTS:")
        successful_results.sort(key=lambda x: x['execution_time'])
        for i, result in enumerate(successful_results[:5], 1):
            print(f"{i}. {result['scenario'][:50]:50} | {result['execution_time']:5.2f}s")

        print(f"\n⚠️ SLOWEST TESTS:")
        for i, result in enumerate(successful_results[-3:], 1):
            print(f"{i}. {result['scenario'][:50]:50} | {result['execution_time']:5.2f}s")

    if failed_results:
        print(f"\n❌ FAILED SCENARIOS:")
        for result in failed_results:
            print(f"   {result['scenario']}: {result['error']}")

    print(f"\n💾 Detailed results saved to: {results_file}")

    return successful_results


if __name__ == "__main__":
    run_comprehensive_content_test()