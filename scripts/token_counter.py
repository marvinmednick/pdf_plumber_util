#!/usr/bin/env python3
"""Token counting analysis for PDF document data with precise model-specific counting.

This script provides accurate token counting for LLM analysis planning, supporting
Azure GPT-4.x models initially with framework for adding other models.

Usage:
    python token_counter.py
    
Requirements:
    pip install tiktoken

Future Model Support:
    # For Google Gemini:
    # pip install google-generativeai
    # from google.generativeai import count_tokens
    
    # For Anthropic Claude:
    # pip install anthropic
    # from anthropic import count_tokens (when available)
    # Note: Claude token counting may require API calls or approximation
"""

import json
import random
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
import tiktoken

# Model configurations for token counting
MODEL_CONFIGS = {
    'gpt-4': {
        'encoder': 'cl100k_base',  # GPT-4 encoding
        'context_limit': 128000,
        'name': 'GPT-4'
    },
    'gpt-4-turbo': {
        'encoder': 'cl100k_base',
        'context_limit': 128000,
        'name': 'GPT-4 Turbo'
    },
    'gpt-4o': {
        'encoder': 'o200k_base',  # GPT-4o uses different encoding
        'context_limit': 128000,
        'name': 'GPT-4o'
    },
    'gpt-3.5-turbo': {
        'encoder': 'cl100k_base',
        'context_limit': 16385,
        'name': 'GPT-3.5 Turbo'
    }
}

class TokenCounter:
    """Precise token counting for various LLM models."""
    
    def __init__(self, model: str = 'gpt-4'):
        """Initialize token counter for specified model.
        
        Args:
            model: Model name (gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo)
        """
        self.model = model
        if model not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model}. Supported: {list(MODEL_CONFIGS.keys())}")
        
        self.config = MODEL_CONFIGS[model]
        self.encoder = tiktoken.get_encoding(self.config['encoder'])
        
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
        """
        if self.model.startswith('gpt'):
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

def count_page_tokens(page_data: Dict[str, Any], counter: TokenCounter) -> Dict[str, int]:
    """Count tokens for a single page's data."""
    # Convert page data to JSON string to get realistic representation
    page_json = json.dumps(page_data, indent=None)
    
    return {
        'total_tokens': counter.count_tokens(page_json),
        'raw_length': len(page_json),
        'block_count': len(page_data.get('lines', [])),
        'page_number': page_data.get('page', 'unknown')
    }

def analyze_document_tokens(file_path: str, model: str = 'gpt-4') -> Dict[str, Any]:
    """Analyze token requirements for document using specified model."""
    print(f"Loading document from: {file_path}")
    print(f"Using model: {MODEL_CONFIGS[model]['name']}")
    
    # Initialize token counter
    counter = TokenCounter(model)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Get all pages
    all_pages = data if isinstance(data, list) else data.get('pages', [])
    print(f"Total pages in document: {len(all_pages)}")
    
    # Select first 30 pages
    first_30 = all_pages[:30]
    print(f"Selected first {len(first_30)} pages")
    
    # Randomly select 10 from remaining pages (31-100)
    remaining_pages = all_pages[30:100] if len(all_pages) > 30 else []
    random_10 = random.sample(remaining_pages, min(10, len(remaining_pages))) if remaining_pages else []
    print(f"Randomly selected {len(random_10)} pages from remaining")
    
    # Show selected random pages for transparency
    if random_10:
        random_page_nums = [p.get('page', 'unknown') for p in random_10]
        print(f"Random pages selected: {sorted(random_page_nums)}")
    
    # Combine sample
    sample_pages = first_30 + random_10
    print(f"Total sample size: {len(sample_pages)} pages")
    
    # Count tokens for each page
    page_stats = []
    for i, page in enumerate(sample_pages):
        stats = count_page_tokens(page, counter)
        page_stats.append(stats)
        
        # Show progress for longer analysis
        if i % 10 == 0 or i == len(sample_pages) - 1:
            print(f"Processed {i+1}/{len(sample_pages)} pages...")
    
    # Calculate statistics
    token_counts = [p['total_tokens'] for p in page_stats]
    block_counts = [p['block_count'] for p in page_stats]
    
    results = {
        'model_used': model,
        'model_name': MODEL_CONFIGS[model]['name'],
        'sample_size': len(sample_pages),
        'token_stats': {
            'min': min(token_counts),
            'max': max(token_counts),
            'mean': statistics.mean(token_counts),
            'median': statistics.median(token_counts),
            'std_dev': statistics.stdev(token_counts) if len(token_counts) > 1 else 0,
            'total_sample': sum(token_counts)
        },
        'block_stats': {
            'min': min(block_counts),
            'max': max(block_counts),
            'mean': statistics.mean(block_counts),
            'median': statistics.median(block_counts)
        },
        'sample_pages': [p['page_number'] for p in page_stats],
        'detailed_stats': page_stats
    }
    
    return results

def recommend_batch_sizes(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Recommend batch sizes based on token analysis."""
    model = stats['model_used']
    config = MODEL_CONFIGS[model]
    
    avg_tokens = stats['token_stats']['mean']
    max_tokens = stats['token_stats']['max']
    std_dev = stats['token_stats']['std_dev']
    
    # Conservative estimate: mean + 1 std dev (covers ~84% of pages)
    conservative_estimate = avg_tokens + std_dev
    
    # Reserve tokens for prompting and response
    context_limit = config['context_limit']
    overhead_tokens = 5000  # Prompt + response buffer
    available_tokens = context_limit - overhead_tokens
    
    # Calculate batch sizes
    conservative_pages = int(available_tokens // max_tokens)
    optimistic_pages = int(available_tokens // avg_tokens)
    recommended_pages = int(available_tokens // conservative_estimate)
    
    # Practical limits
    recommended_initial = min(15, recommended_pages)
    recommended_incremental = min(5, recommended_pages // 3)
    
    return {
        'model': config['name'],
        'context_limit': context_limit,
        'available_tokens': available_tokens,
        'overhead_reserved': overhead_tokens,
        'token_estimates': {
            'avg_per_page': round(avg_tokens, 1),
            'max_per_page': max_tokens,
            'conservative_per_page': round(conservative_estimate, 1)
        },
        'batch_recommendations': {
            'conservative_pages': conservative_pages,
            'optimistic_pages': optimistic_pages,
            'recommended_pages': recommended_pages,
            'recommended_initial': recommended_initial,
            'recommended_incremental': recommended_incremental
        },
        'sample_calculations': {
            '10_pages': round(10 * avg_tokens),
            '15_pages': round(15 * avg_tokens),
            '20_pages': round(20 * avg_tokens)
        }
    }

def print_detailed_results(stats: Dict[str, Any], recommendations: Dict[str, Any]):
    """Print comprehensive analysis results."""
    print(f"\n{'='*50}")
    print(f"PDF DOCUMENT TOKEN ANALYSIS - {stats['model_name']}")
    print(f"{'='*50}")
    
    print(f"\nSample Analysis:")
    print(f"  Pages analyzed: {stats['sample_size']}")
    print(f"  Sample pages: {stats['sample_pages'][:10]}{'...' if len(stats['sample_pages']) > 10 else ''}")
    
    print(f"\nToken Statistics (per page):")
    print(f"  Mean: {stats['token_stats']['mean']:.1f} tokens")
    print(f"  Median: {stats['token_stats']['median']:.1f} tokens")
    print(f"  Range: {stats['token_stats']['min']} - {stats['token_stats']['max']} tokens")
    print(f"  Std Dev: {stats['token_stats']['std_dev']:.1f} tokens")
    print(f"  Total sample: {stats['token_stats']['total_sample']:,} tokens")
    
    print(f"\nBlock Statistics (per page):")
    print(f"  Mean: {stats['block_stats']['mean']:.1f} blocks")
    print(f"  Range: {stats['block_stats']['min']} - {stats['block_stats']['max']} blocks")
    
    print(f"\nModel Context Analysis:")
    print(f"  Model: {recommendations['model']}")
    print(f"  Context limit: {recommendations['context_limit']:,} tokens")
    print(f"  Available for data: {recommendations['available_tokens']:,} tokens")
    print(f"  Reserved overhead: {recommendations['overhead_reserved']:,} tokens")
    
    print(f"\nBatch Size Recommendations:")
    rec = recommendations['batch_recommendations']
    print(f"  Conservative: {rec['conservative_pages']} pages (using max tokens/page)")
    print(f"  Recommended: {rec['recommended_pages']} pages (using mean + 1σ)")
    print(f"  Optimistic: {rec['optimistic_pages']} pages (using mean tokens/page)")
    print(f"  ")
    print(f"  Suggested initial batch: {rec['recommended_initial']} pages")
    print(f"  Suggested incremental: {rec['recommended_incremental']} pages")
    
    print(f"\nSample Size Token Usage:")
    calc = recommendations['sample_calculations']
    print(f"  10 pages ≈ {calc['10_pages']:,} tokens")
    print(f"  15 pages ≈ {calc['15_pages']:,} tokens")
    print(f"  20 pages ≈ {calc['20_pages']:,} tokens")

def main():
    """Main analysis function."""
    # Set random seed for reproducible results
    random.seed(42)
    
    # Analyze the h264 100-page document
    file_path = "/home/mmednick/Development/pdf/pdf_plumb/output/h264_100pages_lines.json"
    
    # Default to GPT-4, but can be changed
    model = 'gpt-4'  # Options: gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo
    
    try:
        # Check if file exists
        if not Path(file_path).exists():
            print(f"Error: File not found: {file_path}")
            print("Please ensure the h264_100pages_lines.json file exists in the output directory.")
            return 1
        
        # Perform analysis
        stats = analyze_document_tokens(file_path, model)
        recommendations = recommend_batch_sizes(stats)
        
        # Print results
        print_detailed_results(stats, recommendations)
        
        # Save detailed results
        output_file = "/home/mmednick/Development/pdf/pdf_plumb/output/token_analysis.json"
        with open(output_file, 'w') as f:
            json.dump({
                'analysis_metadata': {
                    'file_analyzed': file_path,
                    'analysis_date': None,  # Could add datetime.now().isoformat()
                    'random_seed': 42
                },
                'statistics': stats,
                'recommendations': recommendations
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # Quick summary for planning
        print(f"\n{'='*50}")
        print(f"QUICK SUMMARY FOR PLANNING")
        print(f"{'='*50}")
        print(f"Recommended initial batch: {recommendations['batch_recommendations']['recommended_initial']} pages")
        print(f"Recommended incremental: {recommendations['batch_recommendations']['recommended_incremental']} pages")
        print(f"Estimated tokens per page: {recommendations['token_estimates']['avg_per_page']:.0f} ± {stats['token_stats']['std_dev']:.0f}")
        
    except ImportError as e:
        print(f"Error: Missing required package. Please install tiktoken:")
        print(f"pip install tiktoken")
        print(f"Error details: {e}")
        return 1
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())