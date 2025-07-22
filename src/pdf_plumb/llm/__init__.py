"""LLM integration module for PDF Plumb.

This module provides LLM-enhanced document analysis capabilities including:
- Header/footer detection with content understanding
- Section hierarchy identification  
- Table of contents mapping
- Cross-reference validation

Supported providers:
- Azure OpenAI
"""

from .providers import AzureOpenAIProvider, LLMProvider
from .sampling import PageSampler
from .prompts import PromptTemplates
from .responses import ResponseParser

__all__ = [
    'AzureOpenAIProvider',
    'LLMProvider', 
    'PageSampler',
    'PromptTemplates',
    'ResponseParser'
]