"""Golden document tests using real LLM API calls.

This module contains tests that validate LLM analysis capabilities using
prepared test fixtures and actual API calls to Azure OpenAI. These tests
are automatically skipped when API credentials are not available.

Tests in this module:
- Validate LLM prompt effectiveness with real API responses
- Serve as regression tests for prompt changes
- Use prepared JSON fixtures from tests/fixtures/
- Test enhanced capabilities like TOC detection

Usage:
    # Run all tests (golden tests skipped if no API credentials)
    pytest tests/golden/
    
    # Skip golden tests explicitly
    SKIP_LLM_TESTS=1 pytest tests/golden/
    
    # Run only golden tests (will skip if no credentials)
    pytest tests/golden/ -v
"""