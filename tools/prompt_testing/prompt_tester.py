#!/usr/bin/env python3
"""
Prompt Testing Utility for Systematic LLM Experimentation

This utility enables rapid testing of different prompt templates against various data inputs
to optimize LLM analysis architecture through systematic experimentation.
"""

import json
import time
import argparse
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Import from main project
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from pdf_plumb.llm.providers import AzureOpenAIProvider
from pdf_plumb.config import PDFPlumbConfig


@dataclass
class TestResult:
    """Results from a single prompt test execution."""
    template_name: str
    data_file: str
    success: bool
    execution_time: float  # Pure LLM processing time in seconds
    token_count: Optional[int]
    request_size: int
    response_length: int
    response_content: str
    error_message: Optional[str] = None
    start_timestamp: Optional[str] = None  # ISO timestamp when LLM request started
    end_timestamp: Optional[str] = None    # ISO timestamp when LLM request completed


@dataclass
class TestSummary:
    """Summary of all test results."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_execution_time: float
    avg_token_count: float
    results: List[TestResult]


class PromptTester:
    """Systematic prompt testing utility."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize prompt tester with configuration."""
        self.config = PDFPlumbConfig()

        # Configure Azure OpenAI from environment variables
        azure_config = {
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        }

        # Validate required environment variables
        missing_vars = []
        for key, value in azure_config.items():
            if not value and key in ['endpoint', 'api_key']:
                missing_vars.append(f'AZURE_OPENAI_{key.upper()}')

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please set them in your .env file."
            )

        print(f"Using Azure OpenAI endpoint: {azure_config['endpoint']}")
        print(f"Using deployment: {azure_config['deployment']}")

        self.llm_provider = AzureOpenAIProvider(azure_config)
        self.results: List[TestResult] = []

    def load_template(self, template_path: Path) -> str:
        """Load prompt template from file."""
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, 'r') as f:
            return f.read()

    def load_test_data(self, data_path: Path) -> Dict[str, Any]:
        """Load test data from JSON file."""
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        with open(data_path, 'r') as f:
            return json.load(f)

    def _extract_streamlined_blocks(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract streamlined block data for LLM analysis.

        Creates an optimized format that reduces context usage while preserving
        essential information for document structure analysis. Uses text_lines
        array instead of concatenated text to improve LLM parsing accuracy.

        This matches the format used in the main LLM implementation.
        """
        streamlined_blocks = []

        # Handle different block data structures
        blocks = page_data.get('blocks', [])
        if not blocks:
            # Try to get from lines if blocks not available
            blocks = page_data.get('lines', [])

        for block in blocks:
            # Prefer text_lines array over concatenated text
            text_lines = block.get('text_lines', [])
            if not text_lines:
                # Fallback to old format for backward compatibility
                text = block.get('text', '').strip()
                if not text:
                    continue
                text_lines = [line.strip() for line in text.split('\n') if line.strip()]

            # Skip empty blocks
            if not text_lines:
                continue

            # Extract essential positioning (simplified)
            y_position = None
            x_position = None

            # Handle different bbox formats
            bbox = block.get('bbox', {})
            if isinstance(bbox, dict):
                y_position = bbox.get('top', bbox.get('y0', 0))
                x_position = bbox.get('x0', 0)
            elif isinstance(bbox, list) and len(bbox) >= 2:
                x_position = bbox[0]
                y_position = bbox[1]
            else:
                # Fallback to direct position attributes
                y_position = block.get('y0', block.get('top', 0))
                x_position = block.get('x0', 0)

            # Extract font information (critical for hierarchy)
            font_name = block.get('predominant_font', block.get('font_name', block.get('font', '')))
            font_size = block.get('predominant_size', block.get('font_size', block.get('size', 0)))

            # Create optimized block structure with line array
            streamlined_block = {
                'text_lines': text_lines,
                'y0': y_position,
                'x0': x_position,
                'font_name': font_name,
                'font_size': font_size
            }

            streamlined_blocks.append(streamlined_block)

        return streamlined_blocks

    def convert_to_streamlined_format(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw PDF extraction data to streamlined LLM format.

        This removes heavy text_segments, spacing metadata, and other verbose
        data while preserving essential information for content detection.
        """
        if 'pages' in raw_data:
            # Handle multi-page format
            streamlined_pages = []
            for page_data in raw_data['pages']:
                streamlined_blocks = self._extract_streamlined_blocks(page_data)
                streamlined_pages.append({
                    'page_index': page_data.get('page', 1),
                    'blocks': streamlined_blocks,
                    'block_count': len(streamlined_blocks)
                })
            return {'pages': streamlined_pages}
        else:
            # Handle single page format - assume it's page data directly
            streamlined_blocks = self._extract_streamlined_blocks(raw_data)
            return {
                'page_index': raw_data.get('page', 1),
                'blocks': streamlined_blocks,
                'block_count': len(streamlined_blocks)
            }

    def substitute_template(self, template: str, data: Dict[str, Any], **kwargs) -> str:
        """Substitute template variables with actual values."""
        # Convert to streamlined format for LLM efficiency
        streamlined_data = self.convert_to_streamlined_format(data)

        # Default format explanation for streamlined format
        default_format_explanation = """Input data format: Optimized format with 'blocks' arrays. Each block has:
- 'text_lines': Array of text lines in the block
- 'font_name': Font family (e.g., 'TimesNewRomanPSMT', 'Arial-Bold')
- 'font_size': Font size in points (e.g., 12.0)
- 'y0': Vertical position on page (higher = closer to top)
- 'x0': Horizontal position on page

Example block structure:
{
  'text_lines': ['This is line 1', 'This is line 2'],
  'font_name': 'TimesNewRomanPSMT',
  'font_size': 12.0,
  'y0': 150.0,
  'x0': 72.0
}"""

        # Prepare substitution variables
        substitutions = {
            'data': json.dumps(streamlined_data, indent=2),
            'format_explanation': default_format_explanation,
            'objective': kwargs.get('objective', 'Find table of contents entries'),
            'output_format': kwargs.get('output_format', 'JSON format with extracted entries'),
            **kwargs
        }

        # Perform substitutions
        result = template
        for key, value in substitutions.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        return result

    def execute_test(
        self,
        template_path: Path,
        data_path: Path,
        **template_kwargs
    ) -> TestResult:
        """Execute a single prompt test."""
        template_name = template_path.stem
        data_file = data_path.name

        try:
            # Load template and data
            template = self.load_template(template_path)
            test_data = self.load_test_data(data_path)

            # Substitute template variables
            prompt = self.substitute_template(template, test_data, **template_kwargs)

            # Calculate request size
            request_size = len(prompt.encode('utf-8'))

            # Execute LLM request - measure pure LLM processing time
            print(f"  Starting LLM request for {template_name} + {data_file} (request size: {request_size:,} bytes)")
            llm_start_time = time.time()
            start_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(llm_start_time))

            # Call LLM provider (note: not all providers may be async)
            response = self.llm_provider.analyze_document_structure(prompt)
            if hasattr(response, 'content'):
                response = response.content
            else:
                response = str(response)

            llm_end_time = time.time()
            end_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(llm_end_time))
            execution_time = llm_end_time - llm_start_time
            print(f"  ✅ LLM request completed in {execution_time:.2f}s")

            # Calculate response metrics
            response_length = len(response.encode('utf-8'))
            token_count = self.estimate_token_count(prompt + response)

            return TestResult(
                template_name=template_name,
                data_file=data_file,
                success=True,
                execution_time=execution_time,
                token_count=token_count,
                request_size=request_size,
                response_length=response_length,
                response_content=response,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp
            )

        except Exception as e:
            return TestResult(
                template_name=template_name,
                data_file=data_file,
                success=False,
                execution_time=0.0,
                token_count=None,
                request_size=0,
                response_length=0,
                response_content="",
                error_message=str(e)
            )

    def estimate_token_count(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: ~4 characters per token for English text
        return len(text) // 4

    def run_test_matrix(
        self,
        template_dir: Path,
        data_dir: Path,
        template_kwargs: Optional[Dict[str, Any]] = None
    ) -> TestSummary:
        """Run tests for all template/data combinations."""
        if template_kwargs is None:
            template_kwargs = {}

        # Find all templates and data files
        template_files = list(template_dir.glob("*.txt"))
        data_files = list(data_dir.glob("*.json"))

        if not template_files:
            raise ValueError(f"No template files (*.txt) found in {template_dir}")
        if not data_files:
            raise ValueError(f"No data files (*.json) found in {data_dir}")

        # Run all combinations
        results = []
        for template_file in template_files:
            for data_file in data_files:
                result = self.execute_test(template_file, data_file, **template_kwargs)
                results.append(result)
        self.results.extend(results)

        # Calculate summary
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests

        successful_results = [r for r in results if r.success]
        avg_execution_time = sum(r.execution_time for r in successful_results) / len(successful_results) if successful_results else 0
        avg_token_count = sum(r.token_count or 0 for r in successful_results) / len(successful_results) if successful_results else 0

        return TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            avg_execution_time=avg_execution_time,
            avg_token_count=avg_token_count,
            results=results
        )

    def save_results(self, summary: TestSummary, output_path: Path) -> None:
        """Save test results to JSON file."""
        output_data = asdict(summary)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

    def print_summary(self, summary: TestSummary) -> None:
        """Print test summary to console."""
        print(f"\n{'='*60}")
        print(f"PROMPT TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {summary.total_tests}")
        print(f"Successful: {summary.successful_tests}")
        print(f"Failed: {summary.failed_tests}")
        print(f"Success rate: {summary.successful_tests/summary.total_tests*100:.1f}%")
        print(f"Avg execution time: {summary.avg_execution_time:.2f}s")
        print(f"Avg token count: {summary.avg_token_count:.0f}")

        print(f"\n{'='*60}")
        print(f"DETAILED RESULTS")
        print(f"{'='*60}")

        for result in summary.results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"\n{status} | {result.template_name} + {result.data_file}")
            if result.success:
                print(f"  LLM Time: {result.execution_time:.2f}s | Tokens: {result.token_count} | Request: {result.request_size:,} bytes")
                if result.start_timestamp and result.end_timestamp:
                    print(f"  Started: {result.start_timestamp} | Ended: {result.end_timestamp}")
            else:
                print(f"  Error: {result.error_message}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Systematic prompt testing utility")
    parser.add_argument("template_dir", type=Path, help="Directory containing prompt templates (*.txt)")
    parser.add_argument("data_dir", type=Path, help="Directory containing test data (*.json)")
    parser.add_argument("--output", "-o", type=Path, help="Output file for results (JSON)")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--objective", help="Override default objective for templates")
    parser.add_argument("--output-format", help="Override default output format for templates")

    args = parser.parse_args()

    # Initialize tester
    tester = PromptTester(args.config)

    # Prepare template kwargs
    template_kwargs = {}
    if args.objective:
        template_kwargs['objective'] = args.objective
    if args.output_format:
        template_kwargs['output_format'] = args.output_format

    # Run tests
    print(f"Running prompt tests...")
    print(f"Templates: {args.template_dir}")
    print(f"Data: {args.data_dir}")

    summary = tester.run_test_matrix(args.template_dir, args.data_dir, template_kwargs)

    # Print results
    tester.print_summary(summary)

    # Save results if requested
    if args.output:
        tester.save_results(summary, args.output)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()