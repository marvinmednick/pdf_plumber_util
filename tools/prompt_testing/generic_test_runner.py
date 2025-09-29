#!/usr/bin/env python3
"""
Generic test runner for prompt templates with command line arguments.
Usage: python generic_test_runner.py template_name.txt data1.json [data2.json ...]
"""

import argparse
import json
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_tests(template_name, data_files, template_dir, data_dir, results_dir, output_file=None, save_individual=True):
    """Run template on specified data files."""
    template_file = template_dir / template_name

    if not template_file.exists():
        print(f"❌ Template not found: {template_file}")
        return False

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False

    results_dir.mkdir(exist_ok=True)

    tester = PromptTester()

    print(f"🧪 Running template: {template_name}")
    print(f"📁 Template dir: {template_dir}")
    print(f"📁 Data dir: {data_dir}")
    print(f"📁 Results dir: {results_dir}")
    print(f"📄 Testing {len(data_files)} data file(s)")
    if output_file:
        print(f"📄 Summary will be saved to: {output_file}")
    if save_individual:
        print(f"💾 Individual results will be saved")
    else:
        print(f"🚫 Individual results will NOT be saved (--no-individual)")
    print()

    results = {}
    test_summary = {
        'template': template_name,
        'timestamp': time.time(),
        'total_tests': len(data_files),
        'test_results': {}
    }

    for data_name in data_files:
        data_file = data_dir / data_name

        if not data_file.exists():
            print(f"❌ Data file not found: {data_file}")
            error_result = {'success': False, 'error': 'File not found'}
            results[data_name] = error_result
            test_summary['test_results'][data_name] = error_result
            continue

        # Load and check data size
        with open(data_file, 'r') as f:
            data_content = f.read()
        data_size_kb = len(data_content.encode('utf-8')) / 1024

        print(f"🔍 Testing: {data_name}")
        print(f"   Size: {data_size_kb:.1f} KB")

        try:
            # Run the test
            start_time = time.time()
            result = tester.execute_test(template_file, data_file)
            elapsed_time = time.time() - start_time

            if result.success:
                print(f"   ✅ SUCCESS in {elapsed_time:.2f}s")
                print(f"   LLM Time: {result.execution_time:.2f}s")

                # Parse response for analysis
                content_summary = {}
                total_items = 0
                try:
                    response_data = json.loads(result.response_content)
                    print(f"   📄 Content Found:")

                    for content_type, items in response_data.items():
                        if items and len(items) > 0:
                            total_items += len(items)
                            content_summary[content_type] = len(items)
                            print(f"      {content_type}: {len(items)} items")
                            # Show first item as example
                            first_item = items[0]
                            text = first_item.get('text', 'N/A')
                            if len(text) > 60:
                                text = text[:57] + "..."
                            print(f"        Example: \"{text}\"")
                        else:
                            content_summary[content_type] = 0

                    if total_items == 0:
                        print(f"      No content found")
                    else:
                        print(f"      Total: {total_items} items")

                except json.JSONDecodeError:
                    print(f"      ⚠️ Could not parse response JSON")
                    response_data = None

                # Save individual result file if save_individual is True (default)
                if save_individual:
                    safe_template_name = template_name.replace('.txt', '')
                    safe_data_name = data_name.replace('.json', '')
                    result_filename = f"{safe_template_name}_{safe_data_name}_result.json"
                    result_file = results_dir / result_filename

                    # Parse the LLM response JSON for proper formatting
                    parsed_response = None
                    try:
                        parsed_response = json.loads(result.response_content)
                    except json.JSONDecodeError:
                        # If parsing fails, keep as string but note the issue
                        parsed_response = {
                            "parse_error": "Could not parse LLM response as JSON",
                            "raw_response": result.response_content
                        }

                    with open(result_file, 'w') as f:
                        json.dump({
                            'template': template_name,
                            'data_file': data_name,
                            'response_content': parsed_response,  # Now properly parsed JSON
                            'execution_time': result.execution_time,
                            'request_size': result.request_size,
                            'response_length': result.response_length,
                            'data_size_kb': data_size_kb,
                            'timestamp': time.time()
                        }, f, indent=2)

                    print(f"   💾 Individual result saved to: {result_filename}")

                # Store result for summary
                test_result = {
                    'success': True,
                    'execution_time': result.execution_time,
                    'request_size': result.request_size,
                    'response_length': result.response_length,
                    'data_size_kb': data_size_kb,
                    'total_items': total_items,
                    'content_summary': content_summary,
                    'response_content': parsed_response if not save_individual else None  # Include parsed response if not saving individually
                }
                results[data_name] = test_result
                test_summary['test_results'][data_name] = test_result

            else:
                print(f"   ❌ FAILED: {result.error_message}")
                error_result = {
                    'success': False,
                    'error': result.error_message,
                    'data_size_kb': data_size_kb
                }
                results[data_name] = error_result
                test_summary['test_results'][data_name] = error_result

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            error_result = {
                'success': False,
                'error': str(e),
                'data_size_kb': data_size_kb
            }
            results[data_name] = error_result
            test_summary['test_results'][data_name] = error_result

        print()  # Empty line between tests

    # Calculate summary statistics
    successful = sum(1 for r in results.values() if r.get('success', False))
    failed = len(data_files) - successful

    test_summary.update({
        'successful_tests': successful,
        'failed_tests': failed,
        'success_rate': successful / len(data_files) if data_files else 0
    })

    if successful > 0:
        avg_time = sum(r.get('execution_time', 0) for r in results.values() if r.get('success', False)) / successful
        total_items = sum(r.get('total_items', 0) for r in results.values() if r.get('success', False))
        test_summary.update({
            'average_execution_time': avg_time,
            'total_items_found': total_items
        })

    # Print summary
    print("📊 Summary:")
    print(f"   Total tests: {len(data_files)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")

    if successful > 0:
        print(f"   Average time: {test_summary['average_execution_time']:.2f}s")
        print(f"   Total items found: {test_summary['total_items_found']}")

    # Save summary file if requested
    if output_file:
        output_path = results_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(test_summary, f, indent=2)
        print(f"\n💾 Summary saved to: {output_file}")

    return successful == len(data_files)


def main():
    script_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(
        description='Run prompt template on one or more data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generic_test_runner.py comprehensive_content_analysis.txt h264_content_page_1.json
  python generic_test_runner.py section_headings_only.txt h264_content_page_1.json h264_content_page_50.json
  python generic_test_runner.py comprehensive_content_analysis.txt h264_*.json --output summary.json
  python generic_test_runner.py toc_entries_only.txt h264_page_6_only.json --no-individual
  python generic_test_runner.py my_template.txt data.json --template-dir ../other_templates --data-dir ../other_data
        '''
    )

    parser.add_argument('template', help='Template file name')
    parser.add_argument('data_files', nargs='+', help='Data file name(s)')
    parser.add_argument('--template-dir', '-t', type=Path, default=script_dir / "templates",
                        help='Directory containing template files (default: templates/)')
    parser.add_argument('--data-dir', '-d', type=Path, default=script_dir / "test_data",
                        help='Directory containing data files (default: test_data/)')
    parser.add_argument('--results-dir', '-r', type=Path, default=script_dir / "results",
                        help='Directory to save results (default: results/)')
    parser.add_argument('--output', '-o', help='Save test summary to specified file (saved in results directory)')
    parser.add_argument('--no-individual', action='store_true',
                        help='Don\'t save individual result files (default: saves individual files)')

    args = parser.parse_args()

    success = run_tests(
        args.template,
        args.data_files,
        template_dir=args.template_dir,
        data_dir=args.data_dir,
        results_dir=args.results_dir,
        output_file=args.output,
        save_individual=not args.no_individual  # Default True, False only if --no-individual flag set
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()