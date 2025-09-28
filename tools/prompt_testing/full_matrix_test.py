#!/usr/bin/env python3
"""
Full matrix testing: Run every template against every page to validate robustness.

This tests whether templates correctly identify when content is NOT present,
and whether multi-objective detection changes accuracy on any page type.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_full_matrix_test():
    """Run every template against every test page."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # All single-objective templates to test
    single_objective_templates = [
        "section_headings_only.txt",
        "table_titles_only.txt",
        "figure_titles_only.txt",
        "toc_entries_only.txt",
        "headers_footers_only.txt",
        "equations_only.txt"
    ]

    # Multi-objective template
    multi_objective_template = "combo_4_content_analysis.txt"

    # All test data files to test against
    test_data_files = [
        "h264_content_page_305.json",      # Page 305 (figures)
        "h264_content_page_50.json",     # Page 50 (sections + tables)
        "h264_page_6_only.json",         # Page 6 (TOC)
        "h264_list_of_tables_page19.json",   # Page 19 (List of Tables)
        "h264_list_of_figures_page17.json"   # Page 17 (List of Figures)
    ]

    # Page descriptions for reporting
    page_descriptions = {
        "h264_content_page_305.json": "Page 305 (Figures content)",
        "h264_content_page_50.json": "Page 50 (Sections + Tables)",
        "h264_page_6_only.json": "Page 6 (Table of Contents)",
        "h264_list_of_tables_page19.json": "Page 19 (List of Tables)",
        "h264_list_of_figures_page17.json": "Page 17 (List of Figures)"
    }

    print(f"🔍 FULL MATRIX COMPREHENSIVE TEST")
    print(f"{'='*80}")
    print(f"Testing {len(single_objective_templates)} single-objective + 1 multi-objective template")
    print(f"Against {len(test_data_files)} different page types")
    print(f"Total tests: {(len(single_objective_templates) + 1) * len(test_data_files)} = {(len(single_objective_templates) + 1) * len(test_data_files)}")

    # Initialize tester
    try:
        tester = PromptTester()
        print(f"✅ PromptTester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PromptTester: {e}")
        return

    results = []
    test_counter = 0
    total_tests = (len(single_objective_templates) + 1) * len(test_data_files)

    # Test all single-objective templates against all pages
    for template_name in single_objective_templates:
        template_file = template_dir / template_name
        if not template_file.exists():
            print(f"⚠️ Template not found: {template_name}")
            continue

        for data_name in test_data_files:
            test_counter += 1
            data_file = test_data_dir / data_name
            if not data_file.exists():
                print(f"⚠️ Data file not found: {data_name}")
                continue

            run_single_test(tester, template_file, data_file, template_name, data_name,
                          page_descriptions[data_name], test_counter, total_tests, results, results_dir)

    # Test multi-objective template against all pages
    template_file = template_dir / multi_objective_template
    if template_file.exists():
        for data_name in test_data_files:
            test_counter += 1
            data_file = test_data_dir / data_name
            if not data_file.exists():
                continue

            run_single_test(tester, template_file, data_file, multi_objective_template, data_name,
                          page_descriptions[data_name], test_counter, total_tests, results, results_dir)

    # Save comprehensive results
    save_matrix_results(results, results_dir)

    # Analyze and display results
    analyze_matrix_results(results, single_objective_templates, test_data_files, page_descriptions)


def run_single_test(tester, template_file, data_file, template_name, data_name, page_desc,
                   test_num, total_tests, results, results_dir):
    """Run a single test and store results."""
    data_size_kb = data_file.stat().st_size / 1024
    content_type = template_name.replace('_only.txt', '').replace('.txt', '')

    print(f"\n📋 Test {test_num}/{total_tests}: {content_type} on {page_desc}")
    print(f"   Template: {template_name}")
    print(f"   Data: {data_name} ({data_size_kb:.1f} KB)")

    try:
        start_time = time.time()
        result = tester.execute_test(template_file, data_file)
        end_time = time.time()

        if result.success:
            print(f"   ✅ SUCCESS in {end_time - start_time:.2f}s")
            print(f"   LLM Time: {result.execution_time:.2f}s")

            # Parse response to count findings
            findings_summary = parse_findings(result.response_content)
            print(f"   Found: {findings_summary}")

            # Save individual response
            response_filename = f"matrix_{test_num:02d}_{content_type}_{data_name.replace('.json', '')}.json"
            response_file = results_dir / response_filename
            with open(response_file, 'w') as f:
                json.dump({
                    'test_number': test_num,
                    'template': template_name,
                    'content_type': content_type,
                    'data_file': data_name,
                    'page_description': page_desc,
                    'response_content': result.response_content,
                    'execution_time': result.execution_time,
                    'request_size': result.request_size,
                    'response_length': result.response_length,
                    'findings_summary': findings_summary
                }, f, indent=2)

            results.append({
                'test_number': test_num,
                'template': template_name,
                'content_type': content_type,
                'data_file': data_name,
                'page_description': page_desc,
                'data_size_kb': data_size_kb,
                'success': True,
                'execution_time': result.execution_time,
                'request_size': result.request_size,
                'response_length': result.response_length,
                'token_count': result.token_count,
                'findings_summary': findings_summary,
                'response_file': response_filename
            })

        else:
            print(f"   ❌ FAILED in {end_time - start_time:.2f}s")
            print(f"   Error: {result.error_message}")

            results.append({
                'test_number': test_num,
                'template': template_name,
                'content_type': content_type,
                'data_file': data_name,
                'page_description': page_desc,
                'data_size_kb': data_size_kb,
                'success': False,
                'error': result.error_message
            })

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        results.append({
            'test_number': test_num,
            'template': template_name,
            'content_type': content_type,
            'data_file': data_name,
            'page_description': page_desc,
            'data_size_kb': data_size_kb,
            'success': False,
            'error': str(e)
        })


def parse_findings(response_content):
    """Parse LLM response to summarize findings."""
    try:
        response_json = json.loads(response_content)
        findings = []
        total_items = 0

        for key, value in response_json.items():
            if isinstance(value, list):
                count = len(value)
                total_items += count
                if count > 0:
                    findings.append(f"{count} {key}")
            elif isinstance(value, dict) and value:
                findings.append(f"1 {key}")
                total_items += 1

        if total_items == 0:
            return "Nothing found"
        elif findings:
            return ", ".join(findings)
        else:
            return f"{total_items} items"

    except json.JSONDecodeError:
        return "Parse error"


def save_matrix_results(results, results_dir):
    """Save comprehensive matrix results."""
    matrix_file = results_dir / "full_matrix_analysis.json"
    with open(matrix_file, 'w') as f:
        json.dump({
            'test_type': 'full_matrix_comprehensive',
            'total_tests': len(results),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        }, f, indent=2)
    print(f"\n💾 Matrix results saved to: {matrix_file}")


def analyze_matrix_results(results, templates, data_files, page_descriptions):
    """Analyze and display matrix test results."""
    print(f"\n{'='*80}")
    print("FULL MATRIX ANALYSIS")
    print(f"{'='*80}")

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    print(f"✅ Successful: {len(successful_results)}/{len(results)}")
    print(f"❌ Failed: {len(failed_results)}")

    if failed_results:
        print(f"\n❌ FAILED TESTS:")
        for result in failed_results:
            print(f"   {result['content_type']} on {result['page_description']}: {result.get('error', 'Unknown error')}")

    # Analyze false positives/negatives by content type
    print(f"\n🔍 FALSE POSITIVE/NEGATIVE ANALYSIS:")

    expected_findings = {
        # What we SHOULD find on each page type
        "h264_content_page_305.json": ["figure_titles"],  # Page 305 has figures
        "h264_content_page_50.json": ["section_headings", "table_titles"],  # Page 50 has sections + tables
        "h264_page_6_only.json": ["toc_entries"],  # Page 6 is TOC
        "h264_list_of_tables_page19.json": ["table_titles"],  # Page 19 is List of Tables
        "h264_list_of_figures_page17.json": ["figure_titles"]  # Page 17 is List of Figures
    }

    for data_file, expected_content in expected_findings.items():
        page_desc = page_descriptions[data_file]
        print(f"\n📄 {page_desc}:")

        page_results = [r for r in successful_results if r['data_file'] == data_file]

        for template in templates + ["combo_4_content_analysis"]:
            content_type = template.replace('_only.txt', '').replace('.txt', '')
            test_result = next((r for r in page_results if r['template'] == template), None)

            if test_result:
                findings = test_result['findings_summary']
                should_find = any(expected in content_type for expected in expected_content)
                found_something = findings != "Nothing found"

                if should_find and found_something:
                    print(f"   ✅ {content_type}: {findings} (correct positive)")
                elif not should_find and not found_something:
                    print(f"   ✅ {content_type}: {findings} (correct negative)")
                elif should_find and not found_something:
                    print(f"   ⚠️ {content_type}: {findings} (false negative - should have found content)")
                elif not should_find and found_something:
                    print(f"   🚨 {content_type}: {findings} (FALSE POSITIVE - found content that shouldn't be there)")

    print(f"\n🎯 MULTI-OBJECTIVE CONSISTENCY CHECK:")
    multi_results = [r for r in successful_results if 'combo_4' in r['template']]
    for result in multi_results:
        print(f"   {result['page_description']}: {result['findings_summary']}")


if __name__ == "__main__":
    run_full_matrix_test()