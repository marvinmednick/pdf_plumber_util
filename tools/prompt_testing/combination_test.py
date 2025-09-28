#!/usr/bin/env python3
"""
Test multi-objective combinations to measure performance scaling.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_combination_scaling_test():
    """Test how performance scales as we combine objectives."""
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

    # Multi-objective templates in order of complexity
    combination_templates = [
        ("1_baseline", "section_headings_only.txt", 1),
        ("2_objectives", "combo_2_headings_tables.txt", 2),
        ("3_objectives", "combo_3_headings_tables_figures.txt", 3),
        ("4_objectives", "combo_4_content_analysis.txt", 4),
        ("6_objectives", "multi_objective_single_page.txt", 6)
    ]

    print(f"📈 MULTI-OBJECTIVE SCALING TEST")
    print(f"{'='*80}")
    print(f"Test data: {test_file.name} ({test_file.stat().st_size / 1024:.1f} KB)")
    print(f"Testing {len(combination_templates)} combinations from 1 to 6 objectives")

    # Initialize tester
    try:
        tester = PromptTester()
        print(f"✅ PromptTester initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PromptTester: {e}")
        return

    results = []

    for combo_name, template_name, num_objectives in combination_templates:
        template_file = template_dir / template_name

        if not template_file.exists():
            print(f"⚠️ Template not found: {template_name}")
            continue

        print(f"\n📊 Testing: {combo_name}")
        print(f"   Template: {template_name}")
        print(f"   Objectives: {num_objectives}")

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

                # Calculate efficiency metrics
                time_per_objective = result.execution_time / num_objectives
                bytes_per_objective = result.request_size / num_objectives

                print(f"   Efficiency: {time_per_objective:.2f}s per objective, {bytes_per_objective:,.0f} bytes per objective")

                results.append({
                    'combination': combo_name,
                    'template': template_name,
                    'num_objectives': num_objectives,
                    'success': True,
                    'execution_time': result.execution_time,
                    'request_size': result.request_size,
                    'response_length': result.response_length,
                    'token_count': result.token_count,
                    'time_per_objective': time_per_objective,
                    'bytes_per_objective': bytes_per_objective
                })

            else:
                print(f"   ❌ FAILED in {end_time - start_time:.2f}s")
                print(f"   Error: {result.error_message}")

                results.append({
                    'combination': combo_name,
                    'template': template_name,
                    'num_objectives': num_objectives,
                    'success': False,
                    'error': result.error_message
                })

        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results.append({
                'combination': combo_name,
                'template': template_name,
                'num_objectives': num_objectives,
                'success': False,
                'error': str(e)
            })

    # Save and analyze results
    results_file = results_dir / "combination_scaling_analysis.json"
    with open(results_file, 'w') as f:
        json.dump({
            'test_data': test_file.name,
            'data_size_kb': test_file.stat().st_size / 1024,
            'total_combinations': len(combination_templates),
            'results': results
        }, f, indent=2)

    print(f"\n{'='*80}")
    print(f"COMBINATION SCALING ANALYSIS")
    print(f"{'='*80}")

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    print(f"✅ Successful: {len(successful_results)}/{len(results)}")
    print(f"❌ Failed: {len(failed_results)}")

    if successful_results:
        print(f"\n📈 SCALING ANALYSIS:")
        print(f"{'Objectives':>10} | {'Time (s)':>8} | {'Request (KB)':>12} | {'Time/Obj':>10} | {'Efficiency':>12}")
        print(f"{'-'*70}")

        baseline_time = successful_results[0]['execution_time'] if successful_results else 1.0

        for result in successful_results:
            efficiency_score = baseline_time / result['execution_time'] * result['num_objectives']
            print(f"{result['num_objectives']:>10} | {result['execution_time']:>8.2f} | {result['request_size']/1024:>12.1f} | {result['time_per_objective']:>10.2f} | {efficiency_score:>12.2f}")

        # Calculate scaling factors
        if len(successful_results) > 1:
            first = successful_results[0]
            last = successful_results[-1]
            time_scaling = last['execution_time'] / first['execution_time']
            obj_scaling = last['num_objectives'] / first['num_objectives']

            print(f"\n📊 SCALING FACTORS:")
            print(f"Objectives: {first['num_objectives']} → {last['num_objectives']} ({obj_scaling:.1f}x increase)")
            print(f"Time: {first['execution_time']:.2f}s → {last['execution_time']:.2f}s ({time_scaling:.1f}x increase)")
            print(f"Efficiency: {time_scaling/obj_scaling:.2f} (1.0 = linear scaling, <1.0 = better than linear)")

    if failed_results:
        print(f"\n❌ FAILED COMBINATIONS:")
        for result in failed_results:
            print(f"   {result['combination']} ({result['num_objectives']} objectives): {result['error']}")

    print(f"\n💾 Detailed results saved to: {results_file}")

    return successful_results


if __name__ == "__main__":
    run_combination_scaling_test()