# Prompt Testing Utility

Systematic testing framework for optimizing LLM prompt architecture through empirical experimentation.

## Overview

This utility enables rapid testing of different prompt templates against various data inputs to identify optimal LLM analysis approaches before scaling to full document processing.

## Quick Start

```bash
# Run quick test with default settings
cd tools/prompt_testing
python run_tests.py --quick
```

## Architecture

### Components

- **`prompt_tester.py`**: Core testing engine with template substitution and performance tracking
- **`run_tests.py`**: CLI wrapper for convenient testing workflows
- **`templates/`**: Prompt template files with variable placeholders
- **`test_data/`**: JSON test data files (automatically populated from performance fixtures)
- **`results/`**: Test output and analysis results

### Template System

Templates use placeholder substitution for reusable prompt components:

```
{format_explanation}  # Generic data structure explanation
{data}               # JSON test data
{objective}          # Task description
{output_format}      # Expected response format
```

## Prototype Matrix

The utility includes 4 core prototype templates for systematic testing:

1. **`single_objective_single_page.txt`**: Find TOC entries on one page
2. **`single_objective_multi_page.txt`**: Find TOC entries across multiple pages
3. **`multi_objective_single_page.txt`**: Find TOC entries + section headings on one page
4. **`multi_objective_multi_page.txt`**: Find TOC entries + section headings across multiple pages

## Usage

### Quick Testing
```bash
python run_tests.py --quick
```

### Custom Testing
```bash
python run_tests.py --templates /path/to/templates --data /path/to/data --output results.json
```

### Advanced Usage
```bash
python prompt_tester.py templates/ test_data/ --objective "Find table headings" --output detailed_results.json
```

## Metrics Tracked

- **Execution time**: Time to complete LLM request
- **Token count**: Estimated tokens used (request + response)
- **Request size**: Byte size of prompt payload
- **Response length**: Byte size of LLM response
- **Success rate**: Percentage of successful vs failed requests
- **Error analysis**: Detailed error messages for failures

## Test Data

Test data is automatically populated from existing performance test fixtures:

- **Single-page data**: `h264_page_6_only.json` (extracted from multi-page fixture)
- **Multi-page data**: `h264_pages_6_7.json` (from performance test suite)

## Results Analysis

The utility provides:

- **Summary statistics**: Success rates, average times, token usage
- **Detailed results**: Per-test metrics and response content
- **Quick analysis**: Identification of fastest/most efficient approaches
- **Timeout detection**: Flagging of potentially problematic long-running tests

## Integration

This testing framework supports the empirical pattern discovery methodology:

1. **Prototype different prompt architectures** using the 4-variant matrix
2. **Identify optimal approaches** through systematic performance comparison
3. **Scale successful patterns** to full document processing pipeline

## Example Output

```
============================================================
PROMPT TESTING SUMMARY
============================================================
Total tests: 8
Successful: 6
Failed: 2
Success rate: 75.0%
Avg execution time: 12.34s
Avg token count: 1,234

============================================================
DETAILED RESULTS
============================================================

✅ SUCCESS | single_objective_single_page + h264_page_6_only.json
  Time: 8.45s | Tokens: 987 | Request: 12,345 bytes

❌ FAILED | multi_objective_multi_page + h264_pages_6_7.json
  Error: Request timeout after 240 seconds
```

This systematic approach ensures optimal prompt architecture is identified through empirical testing before implementing the full pattern discovery pipeline.