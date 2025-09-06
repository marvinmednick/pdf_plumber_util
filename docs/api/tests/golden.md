# Golden Document Tests

This section documents golden document tests that use real LLM API calls to validate analysis capabilities.

## Overview

Golden document tests serve as:
- **Regression tests** for LLM prompt effectiveness
- **Integration validation** with real Azure OpenAI API responses  
- **End-to-end testing** of enhanced capabilities like TOC detection
- **Reference validation** against known correct results

## Golden Test Requirements

**CRITICAL**: Golden tests **must fail** (not skip) when API credentials are missing. This ensures:
- Tests cannot pass without real validation
- Missing credentials are caught as failures, not hidden as skips
- CI/CD pipelines detect missing configuration immediately
- No false sense of security from "passing" tests that didn't run

**To run golden tests**: Ensure Azure OpenAI credentials are configured in `.env`
**To avoid golden tests**: Use `pytest -m "not golden"` to exclude them entirely

## Test Structure

::: tests.golden.test_llm_golden_document
    options:
      heading_level: 3

## Test Fixtures and Reference Results

### test_table_titles_not_section_headings.json

**Source Document**: H.264 specification pages 97-99  
**Purpose**: Validates LLM prompt fix for double categorization issue  
**Expected Results** (based on `docs/status.md:40`):
- **Table 7-2, 7-3, 7-4** appear ONLY in `table_titles` category
- **Table 7-2, 7-3, 7-4** do NOT appear in `section_headings` category  
- **TOC detection** identifies any table of contents patterns
- **Header/footer validation** confirms consistency with previous analysis

### Running Golden Tests

**Run golden tests** (fails if no API credentials):
```bash
uv run pytest tests/golden/ -v
```

**Run only golden tests**:
```bash  
uv run pytest -m golden -v
```

**Exclude golden tests** (to avoid API calls):
```bash
uv run pytest -m "not golden" -v
```

**Required Environment Variables** (in `.env` file):
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`  
- `AZURE_OPENAI_DEPLOYMENT`

## Test Validation

Golden tests validate:

1. **Regression Prevention**: Ensures prompt changes don't break existing functionality
2. **Enhanced Capabilities**: Validates new features like TOC detection work with real LLM responses
3. **API Integration**: Confirms actual Azure OpenAI integration works correctly
4. **Result Structure**: Validates LLM response parsing and state machine compatibility

## Cost Considerations

Golden tests make real API calls and incur costs:
- **H.264 pages 97-99**: ~3 pages analyzed per test run
- **Token usage**: Varies based on document content and LLM response length
- **Frequency**: Should be run before releases and after prompt changes
- **CI/CD**: Can be disabled in environments without API access

## Adding New Golden Tests

When adding new golden tests:

1. **Create test fixture** using `scripts/create_llm_test_fixture.py`
2. **Document expected results** in test docstring and this documentation  
3. **Add markers** `@pytest.mark.golden` and `@pytest.mark.external`
4. **Include skip conditions** for missing API credentials
5. **Validate reference results** manually before committing test