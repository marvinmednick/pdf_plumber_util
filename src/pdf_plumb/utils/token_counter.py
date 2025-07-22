"""Token counting utilities for PDF document analysis with LLM integration.

This module provides accurate token counting for various LLM models to support
batch size planning and context management for document analysis.

Usage:
    from pdf_plumb.utils.token_counter import TokenCounter, DocumentTokenAnalyzer

    counter = TokenCounter('gpt-4.1')
    tokens = counter.count_tokens(text)

    analyzer = DocumentTokenAnalyzer('gpt-4.1')
    stats = analyzer.analyze_document('path/to/file.json')

Requirements:
    pip install tiktoken

Future Model Support:
    # For Google Gemini:
    # pip install google-generativeai
    # from google.generativeai import count_tokens

    # For Anthropic Claude:
    # pip install anthropic
    # Note: Claude token counting may require API calls or approximation
"""

import json
import random
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tiktoken

# Model configurations for token counting
MODEL_CONFIGS = {
    "gpt-4.1": {
        "encoder": "o200k_base",  # GPT-4.1 uses o200k encoding
        "context_limit": 1048576,  # 1M tokens for GPT-4.1
        "name": "GPT-4.1",
    },
    "gpt-4o": {
        "encoder": "o200k_base",  # GPT-4o uses o200k encoding
        "context_limit": 128000,
        "name": "GPT-4o",
    },
    "gpt-4": {
        "encoder": "cl100k_base",  # GPT-4 encoding
        "context_limit": 128000,
        "name": "GPT-4",
    },
    "gpt-4-turbo": {
        "encoder": "cl100k_base",
        "context_limit": 128000,
        "name": "GPT-4 Turbo",
    },
    "gpt-3.5-turbo": {
        "encoder": "cl100k_base",
        "context_limit": 16385,
        "name": "GPT-3.5 Turbo",
    },
}

# Alias for default model
DEFAULT_MODEL = "gpt-4.1"


class TokenCounter:
    """Precise token counting for various LLM models."""

    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize token counter for specified model.

        Args:
            model: Model name (gpt-4.1, gpt-4o, gpt-4, gpt-4-turbo, gpt-3.5-turbo)

        Raises:
            ValueError: If model is not supported
        """
        self.model = model
        if model not in MODEL_CONFIGS:
            available = ", ".join(MODEL_CONFIGS.keys())
            raise ValueError(f"Unsupported model: {model}. Available: {available}")

        self.config = MODEL_CONFIGS[model]
        self.encoder = tiktoken.get_encoding(self.config["encoder"])

        # Future model support framework
        # self._setup_additional_models()

    def _setup_additional_models(self):
        """Framework for adding support for additional models.

        To add Gemini support:
            import google.generativeai as genai
            self.gemini_model = genai.GenerativeModel('gemini-pro')

        To add Claude support:
            import anthropic
            self.claude_client = anthropic.Anthropic()
            # Note: Claude token counting may require API estimation
        """
        pass

    def count_tokens(self, text: str) -> int:
        """Count tokens for the configured model.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Raises:
            ValueError: If token counting not implemented for model
        """
        if self.model.startswith("gpt"):
            return len(self.encoder.encode(text))

        # Future model implementations:
        # elif self.model.startswith('gemini'):
        #     return self._count_gemini_tokens(text)
        # elif self.model.startswith('claude'):
        #     return self._count_claude_tokens(text)

        else:
            raise ValueError(f"Token counting not implemented for model: {self.model}")

    def _count_gemini_tokens(self, text: str) -> int:
        """Count tokens for Gemini models.

        Example implementation for future use:

        import google.generativeai as genai

        response = genai.count_tokens(
            model='models/gemini-pro',
            contents=[text]
        )
        return response.total_tokens
        """
        raise NotImplementedError("Gemini token counting not yet implemented")

    def _count_claude_tokens(self, text: str) -> int:
        """Count tokens for Claude models.

        Example implementation for future use:

        # Claude may not have direct token counting API
        # Options:
        # 1. Use Anthropic's tokenizer when available
        # 2. Use API call with max_tokens=1 to get estimate
        # 3. Use approximation based on character count

        # Approximation method:
        return len(text) // 3.5  # Claude typically ~3.5 chars/token
        """
        raise NotImplementedError("Claude token counting not yet implemented")

    @property
    def context_limit(self) -> int:
        """Get context limit for the current model."""
        return self.config["context_limit"]

    @property
    def model_name(self) -> str:
        """Get display name for the current model."""
        return self.config["name"]


class DocumentTokenAnalyzer:
    """Analyze token requirements for PDF document data."""

    def __init__(self, model: str = DEFAULT_MODEL, random_seed: int = 42):
        """Initialize document token analyzer.

        Args:
            model: Model name for token counting
            random_seed: Seed for reproducible random sampling
        """
        self.counter = TokenCounter(model)
        self.random_seed = random_seed

    def count_page_tokens(self, page_data: Dict[str, Any]) -> Dict[str, int]:
        """Count tokens for a single page's data.

        Args:
            page_data: Page data dictionary

        Returns:
            Dictionary with token counts and metadata
        """
        # Convert page data to JSON string to get realistic representation
        page_json = json.dumps(page_data, indent=None)

        return {
            "total_tokens": self.counter.count_tokens(page_json),
            "raw_length": len(page_json),
            "block_count": len(
                page_data.get("lines", [])
            ),  # 'lines' for lines file, 'blocks' for blocks file
            "page_number": page_data.get("page", "unknown"),
        }

    def analyze_document(
        self,
        file_path: str,
        first_n_pages: int = 30,
        random_sample_size: int = 10,
        random_start_page: int = 31,
    ) -> Dict[str, Any]:
        """Analyze token requirements for document.

        Args:
            file_path: Path to JSON file containing document data
            first_n_pages: Number of initial pages to analyze
            random_sample_size: Number of random pages to sample
            random_start_page: Starting page for random sampling

        Returns:
            Dictionary containing analysis results
        """
        # Set random seed for reproducible results
        random.seed(self.random_seed)

        with open(file_path, "r") as f:
            data = json.load(f)

        # Get all pages - handle both direct list and nested structure
        if isinstance(data, list):
            all_pages = data
        elif "pages" in data:
            all_pages = data["pages"]
        else:
            # If it's a single page, wrap in list
            all_pages = [data]

        total_pages = len(all_pages)

        # Select first N pages
        first_pages = all_pages[:first_n_pages]

        # Randomly select from remaining pages
        remaining_pages = (
            all_pages[random_start_page - 1 :]
            if total_pages > random_start_page - 1
            else []
        )
        random_pages = (
            random.sample(
                remaining_pages, min(random_sample_size, len(remaining_pages))
            )
            if remaining_pages
            else []
        )

        # Combine sample
        sample_pages = first_pages + random_pages

        # Count tokens for each page
        page_stats = []
        for page in sample_pages:
            stats = self.count_page_tokens(page)
            page_stats.append(stats)

        # Calculate statistics
        token_counts = [p["total_tokens"] for p in page_stats]
        block_counts = [p["block_count"] for p in page_stats]

        results = {
            "model_used": self.counter.model,
            "model_name": self.counter.model_name,
            "file_analyzed": file_path,
            "total_pages_in_file": total_pages,
            "sample_size": len(sample_pages),
            "sampling_strategy": {
                "first_pages": len(first_pages),
                "random_pages": len(random_pages),
                "random_start_page": random_start_page,
            },
            "token_stats": {
                "min": min(token_counts) if token_counts else 0,
                "max": max(token_counts) if token_counts else 0,
                "mean": statistics.mean(token_counts) if token_counts else 0,
                "median": statistics.median(token_counts) if token_counts else 0,
                "std_dev": statistics.stdev(token_counts)
                if len(token_counts) > 1
                else 0,
                "total_sample": sum(token_counts),
            },
            "block_stats": {
                "min": min(block_counts) if block_counts else 0,
                "max": max(block_counts) if block_counts else 0,
                "mean": statistics.mean(block_counts) if block_counts else 0,
                "median": statistics.median(block_counts) if block_counts else 0,
            },
            "sample_pages": [p["page_number"] for p in page_stats],
            "detailed_stats": page_stats,
        }

        return results

    def recommend_batch_sizes(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend batch sizes based on token analysis.

        Args:
            stats: Results from analyze_document()

        Returns:
            Dictionary with batch size recommendations
        """
        avg_tokens = stats["token_stats"]["mean"]
        max_tokens = stats["token_stats"]["max"]
        std_dev = stats["token_stats"]["std_dev"]

        # Conservative estimate: mean + 1 std dev (covers ~84% of pages)
        conservative_estimate = avg_tokens + std_dev

        # Reserve tokens for prompting and response
        context_limit = self.counter.context_limit
        overhead_tokens = 10000  # Prompt + response buffer (larger for GPT-4.1)
        available_tokens = context_limit - overhead_tokens

        # Calculate batch sizes
        conservative_pages = (
            int(available_tokens // max_tokens) if max_tokens > 0 else 0
        )
        optimistic_pages = int(available_tokens // avg_tokens) if avg_tokens > 0 else 0
        recommended_pages = (
            int(available_tokens // conservative_estimate)
            if conservative_estimate > 0
            else 0
        )

        # Practical limits and suggestions
        recommended_initial = min(20, recommended_pages)  # Higher limit for GPT-4.1
        recommended_incremental = min(
            8, recommended_pages // 3
        )  # Higher incremental for GPT-4.1

        return {
            "model": self.counter.model_name,
            "context_limit": context_limit,
            "available_tokens": available_tokens,
            "overhead_reserved": overhead_tokens,
            "token_estimates": {
                "avg_per_page": round(avg_tokens, 1),
                "max_per_page": max_tokens,
                "conservative_per_page": round(conservative_estimate, 1),
            },
            "batch_recommendations": {
                "conservative_pages": conservative_pages,
                "optimistic_pages": optimistic_pages,
                "recommended_pages": recommended_pages,
                "recommended_initial": recommended_initial,
                "recommended_incremental": recommended_incremental,
            },
            "sample_calculations": {
                "10_pages": round(10 * avg_tokens) if avg_tokens else 0,
                "15_pages": round(15 * avg_tokens) if avg_tokens else 0,
                "20_pages": round(20 * avg_tokens) if avg_tokens else 0,
                "50_pages": round(50 * avg_tokens) if avg_tokens else 0,
            },
        }


def get_available_models() -> List[str]:
    """Get list of available models for token counting."""
    return list(MODEL_CONFIGS.keys())


def get_default_model() -> str:
    """Get the default model name."""
    return DEFAULT_MODEL


def get_model_info(model: str) -> Dict[str, Any]:
    """Get information about a specific model.

    Args:
        model: Model name

    Returns:
        Dictionary with model information

    Raises:
        ValueError: If model is not supported
    """
    if model not in MODEL_CONFIGS:
        available = ", ".join(MODEL_CONFIGS.keys())
        raise ValueError(f"Unsupported model: {model}. Available: {available}")

    return MODEL_CONFIGS[model].copy()

