"""Azure OpenAI API connectivity tests.

These tests verify basic Azure OpenAI API connectivity and functionality
using minimal requests. Tests FAIL if API credentials are not configured.
"""

import pytest
from pdf_plumb.llm.providers import AzureOpenAIProvider
from pdf_plumb.core.exceptions import ConfigurationError, AnalysisError


class TestAzureOpenAIConnectivity:
    """Basic connectivity tests for Azure OpenAI API."""

    def setup_method(self):
        """Set up test environment."""
        self.provider = AzureOpenAIProvider()

    @pytest.mark.integration
    def test_azure_openai_basic_connectivity(self):
        """Test basic Azure OpenAI connectivity with simple reading comprehension.

        Uses a minimal reading comprehension task with one-shot example to verify:
        - API authentication works
        - Network connectivity is functional
        - Basic request/response cycle completes
        - Response parsing works correctly

        This test should complete quickly (<30 seconds) and use minimal tokens.

        FAILS if credentials are not configured - this is a connectivity test.
        """

        # Verify configuration first - should fail if not set up
        assert self.provider.is_configured(), "Azure OpenAI credentials must be configured for connectivity test"

        # One-shot example with simple reading comprehension
        prompt = """Example:
Context: The girl placed the book on the blue table.
Question: What color is the table?
Answer: Blue

Now answer this question:
Context: The boy put the toy in the red box.
Question: What color is the box?
Answer:"""

        try:
            # Send minimal request with low token limit
            response = self.provider.analyze_document_structure(
                prompt=prompt,
                max_tokens=10,  # Just need one word response
                temperature=0.0  # Most deterministic response
            )

            # Basic response validation
            assert response is not None, "Should receive a response object"
            assert response.content is not None, "Response should have content"
            assert len(response.content.strip()) > 0, "Response content should not be empty"

            # Validate correct answer
            response_text = response.content.strip().lower()
            assert "red" in response_text, f"Response should contain 'red', got: '{response.content}'"

            # Validate usage tracking (if available)
            if response.usage:
                assert response.usage.get('total_tokens', 0) > 0, "Should track token usage"

            print(f"✅ Connectivity test passed. Response: '{response.content.strip()}'")

        except Exception as e:
            # Provide clear diagnostic information
            error_type = type(e).__name__
            error_msg = str(e)

            print(f"❌ Connectivity test failed with {error_type}: {error_msg}")

            # Re-raise with context for pytest
            pytest.fail(f"Azure OpenAI connectivity test failed: {error_type} - {error_msg}")

    @pytest.mark.integration
    def test_azure_openai_configuration_status(self):
        """Test that Azure OpenAI provider reports correct configuration status.

        FAILS if not configured - this verifies the configuration is working.
        """

        # Should be configured - fail if not
        assert self.provider.is_configured(), "Azure OpenAI provider must be configured"

        # Should be able to access client
        assert hasattr(self.provider, '_client'), "Provider should have client"
        assert self.provider._client is not None, "Client should be initialized"

        print("✅ Configuration status check passed")


@pytest.mark.integration
def test_connectivity_with_error_handling():
    """Test connectivity with various error scenarios for diagnostic purposes.

    FAILS if not configured - this is a connectivity diagnostic test.
    """

    provider = AzureOpenAIProvider()

    # Must be configured for connectivity test
    assert provider.is_configured(), "Azure OpenAI must be configured for connectivity diagnostics"

    # Test with different prompt formats to isolate issues
    simple_prompt = "What color is red?"

    try:
        response = provider.analyze_document_structure(
            prompt=simple_prompt,
            max_tokens=5,
            temperature=0.0
        )

        assert response.content is not None
        print(f"✅ Simple prompt test passed: '{response.content.strip()}'")

    except Exception as e:
        print(f"❌ Simple prompt failed: {type(e).__name__} - {str(e)}")
        raise