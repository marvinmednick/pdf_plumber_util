#!/usr/bin/env python3
"""
Incremental prompt testing to identify exact failure points.

This script tests one template+data combination at a time, saving results immediately,
to determine exactly where the timeout occurs.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_incremental_tests():
    """Run tests incrementally, one at a time, starting with smallest data."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # Get all templates and data files
    template_files = sorted(list(template_dir.glob("*.txt")))
    data_files = sorted(list(test_data_dir.glob("*.json")), key=lambda x: x.stat().st_size)  # Sort by size

    print(f"Found {len(template_files)} templates and {len(data_files)} data files")
    print("\nData files (sorted by size):")
    for data_file in data_files:
        size_kb = data_file.stat().st_size / 1024
        print(f"  {data_file.name}: {size_kb:.1f} KB")

    print(f"\nTemplate files:")
    for template_file in template_files:
        print(f"  {template_file.name}")

    # Initialize tester
    try:
        tester = PromptTester()
        print(f"\n✅ PromptTester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PromptTester: {e}")
        return

    # Test each combination, starting with smallest data
    test_number = 0
    successful_tests = 0
    failed_tests = 0

    for data_file in data_files:  # Smallest first
        for template_file in template_files:
            test_number += 1
            test_name = f"{template_file.stem}_{data_file.stem}"

            print(f"\n{'='*80}")
            print(f"TEST {test_number}/16: {test_name}")
            print(f"Template: {template_file.name}")
            print(f"Data: {data_file.name} ({data_file.stat().st_size / 1024:.1f} KB)")
            print(f"{'='*80}")

            try:
                # Run single test
                start_time = time.time()
                result = tester.execute_test(template_file, data_file)
                end_time = time.time()

                if result.success:
                    successful_tests += 1
                    print(f"✅ SUCCESS in {end_time - start_time:.2f}s")
                    print(f"   LLM Time: {result.execution_time:.2f}s")
                    print(f"   Request: {result.request_size:,} bytes")
                    print(f"   Response: {result.response_length:,} bytes")
                    print(f"   Tokens: {result.token_count}")
                else:
                    failed_tests += 1
                    print(f"❌ FAILED in {end_time - start_time:.2f}s")
                    print(f"   Error: {result.error_message}")

                # Save individual result immediately
                individual_result_file = results_dir / f"{test_name}_result.json"
                with open(individual_result_file, 'w') as f:
                    json.dump({
                        'test_name': test_name,
                        'template': template_file.name,
                        'data_file': data_file.name,
                        'data_size_kb': data_file.stat().st_size / 1024,
                        'result': {
                            'success': result.success,
                            'execution_time': result.execution_time,
                            'request_size': result.request_size,
                            'response_length': result.response_length,
                            'token_count': result.token_count,
                            'start_timestamp': result.start_timestamp,
                            'end_timestamp': result.end_timestamp,
                            'error_message': result.error_message
                        }
                    }, f, indent=2)

                print(f"💾 Result saved to: {individual_result_file.name}")

            except KeyboardInterrupt:
                print(f"\n⚠️ Test interrupted by user")
                break
            except Exception as e:
                failed_tests += 1
                print(f"❌ UNEXPECTED ERROR: {e}")

                # Save error result
                error_result_file = results_dir / f"{test_name}_error.json"
                with open(error_result_file, 'w') as f:
                    json.dump({
                        'test_name': test_name,
                        'template': template_file.name,
                        'data_file': data_file.name,
                        'data_size_kb': data_file.stat().st_size / 1024,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }, f, indent=2)

            # Progress summary
            print(f"\nPROGRESS: {test_number}/16 tests completed")
            print(f"✅ Successful: {successful_tests}")
            print(f"❌ Failed: {failed_tests}")

        # Stop if we've had failures, don't continue to larger data
        if failed_tests > 0:
            print(f"\n⚠️ Stopping after first failures to analyze results")
            break

    # Final summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests attempted: {test_number}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")

    if successful_tests > 0:
        print(f"\n✅ Some tests succeeded - check individual result files")
    if failed_tests > 0:
        print(f"\n❌ Some tests failed - check error files for details")

    print(f"\nAll results saved in: {results_dir}")


if __name__ == "__main__":
    run_incremental_tests()