#!/usr/bin/env python3
"""Quick script to run TOC extraction performance tests."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run performance tests with proper environment setup."""

    print("🚀 Running TOC Extraction Performance Tests")
    print("="*50)

    # Check if H.264 data exists
    h264_data = Path("output/h264_100pages_blocks.json")
    if not h264_data.exists():
        print(f"❌ H.264 blocks data not found: {h264_data}")
        print("💡 Generate with: uv run pdf-plumb process h264_spec.pdf --output-dir output")
        return 1

    # Run the performance tests
    cmd = [
        "uv", "run", "pytest",
        "tests/performance/test_toc_extraction_performance.py::TestTOCExtractionPerformance::test_performance_comparison",
        "-v", "--tb=short"
    ]

    print(f"🔧 Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())