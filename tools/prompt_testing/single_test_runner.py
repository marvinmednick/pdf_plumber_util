#!/usr/bin/env python3
"""
Quick single test runner to get specific LLM response content.
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from prompt_tester import PromptTester


def run_single_test(template_name, data_name, description):
    """Run a single test and save the response."""
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    template_file = template_dir / template_name
    data_file = test_data_dir / data_name

    if not template_file.exists():
        print(f"❌ Template not found: {template_name}")
        return None

    if not data_file.exists():
        print(f"❌ Data file not found: {data_name}")
        return None

    data_size_kb = data_file.stat().st_size / 1024

    print(f"🔍 Running: {description}")
    print(f"   Template: {template_name}")
    print(f"   Data: {data_name} ({data_size_kb:.1f} KB)")

    try:
        tester = PromptTester()
        start_time = time.time()
        result = tester.execute_test(template_file, data_file)
        end_time = time.time()

        if result.success:
            print(f"   ✅ SUCCESS in {end_time - start_time:.2f}s")
            print(f"   LLM Time: {result.execution_time:.2f}s")

            # Save response to file
            response_filename = f"single_test_{template_name.replace('.txt', '')}_{data_name.replace('.json', '')}.json"
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

            print(f"   💾 Response saved to: {response_filename}")

            # Show parsed response
            try:
                response_json = json.loads(result.response_content)
                print(f"   📄 Parsed Response:")
                for key, value in response_json.items():
                    if isinstance(value, list):
                        print(f"      {key}: {len(value)} items")
                        for i, item in enumerate(value[:3]):  # Show first 3 items
                            print(f"        {i+1}. {item}")
                        if len(value) > 3:
                            print(f"        ... and {len(value) - 3} more")
                    else:
                        print(f"      {key}: {value}")
            except json.JSONDecodeError:
                print(f"   📄 Raw Response: {result.response_content}")

            return response_file
        else:
            print(f"   ❌ FAILED: {result.error_message}")
            return None

    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return None


if __name__ == "__main__":
    # Test the section headings on page 50 to get the actual response
    run_single_test(
        "section_headings_only.txt",
        "h264_content_page_50.json",
        "Section headings on content page 50"
    )