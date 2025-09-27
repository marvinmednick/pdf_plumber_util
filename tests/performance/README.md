# Performance Tests

This directory contains performance tests for measuring LLM analysis accuracy and speed across different scenarios.

## TOC Extraction Performance Tests

The main performance test suite measures Table of Contents (TOC) extraction accuracy:

- **Single-page analysis**: Baseline performance test (should work well)
- **Multi-page analysis**: Regression test for performance degradation
- **Comparison analysis**: Measures efficiency ratio between single and multi-page

### Running Performance Tests

**Prerequisites:**
- Azure OpenAI API credentials configured (see main README.md)
- H.264 spec blocks data: `output/h264_100pages_blocks.json`

**Run all performance tests:**
```bash
uv run pytest tests/performance/ -v
```

**Run only performance tests (skip if no API credentials):**
```bash
uv run pytest -m performance -v
```

**Run a specific test:**
```bash
uv run pytest tests/performance/test_toc_extraction_performance.py::TestTOCExtractionPerformance::test_performance_comparison -v
```

### Expected Results

**Historical Baseline (before array format fix):**
- Single-page: 101.9% accuracy (55/54 TOC entries)
- Multi-page: 30.2% accuracy (35/116 TOC entries)
- Efficiency ratio: 29.7%

**Target with Array Format Fix:**
- Single-page: ≥90% accuracy
- Multi-page: ≥70% efficiency ratio vs single-page
- Overall improvement in multi-page parsing

### Test Output

The tests provide detailed performance metrics:

```
📊 Single-Page (Page 6): 45/55 (81.8%) in 12.3s
📊 Multi-Page (Pages 6-7): 89/117 (76.1%) in 18.7s
📊 Multi-page efficiency: 93% of single-page performance
✅ IMPROVEMENT: Multi-page efficiency meets target!
```

### Test Fixtures

Performance tests use standardized fixtures:
- `fixtures/h264_page_6_only.json`: Single-page test data
- `fixtures/h264_pages_6_7.json`: Multi-page test data

These are automatically generated from the main H.264 blocks data.

### Adding New Performance Tests

To add new performance scenarios:

1. Create test method in `TestTOCExtractionPerformance`
2. Use `TOCPerformanceTestSuite` for common functionality
3. Add `@pytest.mark.performance` decorator
4. Document expected baselines and targets

### Integration with CI

Performance tests are marked with `@pytest.mark.performance` and can be:
- **Included**: `pytest -m performance` (requires API credentials)
- **Excluded**: `pytest -m "not performance"` (default for CI without credentials)
- **Conditional**: Skip automatically if credentials not available

### Troubleshooting

**Test skipped due to missing credentials:**
- Ensure Azure OpenAI environment variables are set
- Check that API credentials are valid

**Test skipped due to missing H.264 data:**
- Generate blocks data: `uv run pdf-plumb process h264_spec.pdf --output-dir output`
- Ensure file exists: `output/h264_100pages_blocks.json`

**Performance degradation detected:**
- Compare results with historical baselines
- Check for prompt changes or format modifications
- Review LLM provider configuration changes