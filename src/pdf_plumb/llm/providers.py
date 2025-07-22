"""LLM provider implementations for PDF document analysis."""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AzureOpenAI = None

from ..config import get_config
from ..core.exceptions import ConfigurationError, AnalysisError


@dataclass
class LLMResponse:
    """Standard LLM response format."""
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def analyze_document_structure(self, prompt: str, **kwargs) -> LLMResponse:
        """Analyze document structure using the LLM."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt: str) -> Dict[str, Union[float, int]]:
        """Estimate the cost of the request."""
        pass


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider for document analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Azure OpenAI provider.
        
        Args:
            config: Optional config override. If None, uses global config.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.config = config or {}
        self._client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup the Azure OpenAI client."""
        global_config = get_config()
        
        # Use provided config or fall back to global config
        endpoint = self.config.get('endpoint') or global_config.azure_openai_endpoint
        api_key = self.config.get('api_key') or global_config.azure_openai_api_key
        api_version = self.config.get('api_version') or global_config.azure_openai_api_version
        
        if not all([endpoint, api_key, api_version]):
            missing = []
            if not endpoint: missing.append("endpoint")
            if not api_key: missing.append("api_key") 
            if not api_version: missing.append("api_version")
            raise ConfigurationError(
                f"Azure OpenAI configuration incomplete. Missing: {', '.join(missing)}. "
                "Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_API_VERSION "
                "environment variables."
            )
        
        try:
            self._client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Azure OpenAI client: {e}")
    
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        try:
            global_config = get_config()
            return all([
                global_config.azure_openai_endpoint,
                global_config.azure_openai_api_key,
                global_config.azure_openai_api_version,
                global_config.azure_openai_deployment
            ])
        except Exception:
            return False
    
    def analyze_document_structure(
        self, 
        prompt: str, 
        deployment: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Analyze document structure using Azure OpenAI.
        
        Args:
            prompt: The analysis prompt
            deployment: Azure OpenAI deployment name (overrides config)
            temperature: Sampling temperature (default: 0.1 for consistent analysis)
            max_tokens: Maximum response tokens
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            LLMResponse with analysis results
        """
        if not self._client:
            raise AnalysisError("Azure OpenAI client not initialized")
        
        global_config = get_config()
        deployment_name = deployment or global_config.azure_openai_deployment
        
        if not deployment_name:
            raise ConfigurationError(
                "No Azure OpenAI deployment specified. Set AZURE_OPENAI_DEPLOYMENT "
                "environment variable."
            )
        
        try:
            # Split system and user prompts if provided together
            if "SYSTEM:" in prompt and "USER:" in prompt:
                parts = prompt.split("USER:", 1)
                system_content = parts[0].replace("SYSTEM:", "").strip()
                user_content = parts[1].strip()
                
                messages = [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            response = self._client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            raise AnalysisError(f"Azure OpenAI API request failed: {e}")
    
    def estimate_cost(self, prompt: str) -> Dict[str, Union[float, int]]:
        """Estimate the cost of analyzing the prompt.
        
        Note: This is a rough estimate. Actual costs may vary.
        Azure OpenAI pricing varies by model and region.
        """
        # Rough token estimation (4 chars = 1 token average)
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = 1000  # Typical response length
        
        # GPT-4 pricing (approximate, varies by region)
        input_cost_per_1k = 0.03  # USD per 1K input tokens
        output_cost_per_1k = 0.06  # USD per 1K output tokens
        
        estimated_cost = (
            (estimated_input_tokens / 1000) * input_cost_per_1k +
            (estimated_output_tokens / 1000) * output_cost_per_1k
        )
        
        return {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "currency": "USD",
            "note": "Estimate only - actual costs may vary by model and region"
        }


def get_llm_provider(provider_name: str = "azure", **config_overrides) -> LLMProvider:
    """Factory function to get an LLM provider.
    
    Args:
        provider_name: Name of the provider ("azure")
        **config_overrides: Configuration overrides
        
    Returns:
        Configured LLM provider instance
    """
    providers = {
        "azure": AzureOpenAIProvider
    }
    
    if provider_name not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(f"Unknown LLM provider '{provider_name}'. Available: {available}")
    
    provider_class = providers[provider_name]
    return provider_class(config_overrides if config_overrides else {})