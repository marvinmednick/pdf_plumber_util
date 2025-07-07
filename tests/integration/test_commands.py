"""Integration tests for CLI commands."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.pdf_plumb.cli import extract_pdf, analyze_lines


@pytest.mark.integration  
class TestCLICommands:
    """Test CLI command integration."""
    
    @patch('src.pdf_plumb.cli.PDFExtractor')
    def test_extract_command_basic(self, mock_extractor, temp_output_dir):
        """Test basic extract command functionality."""
        # Mock the extractor
        mock_instance = MagicMock()
        mock_extractor.return_value = mock_instance
        mock_instance.extract_from_pdf.return_value = {
            'lines_json_by_page': [{'page': 1, 'lines': []}],
            'raw_words_by_page': [{'page': 1, 'words': []}],
            'comparison': []
        }
        
        # Create mock args
        args = MagicMock()
        args.pdf_file = "test.pdf"
        args.output_dir = str(temp_output_dir)
        args.basename = None
        args.y_tolerance = 3.0
        args.x_tolerance = 3.0
        args.debug_level = 'INFO'
        args.visualize_spacing = False
        
        # Run extract
        result = extract_pdf(args)
        
        # Should return path to lines file
        assert result is not None
        assert result.endswith("_lines.json")
        
        # Should have called extractor methods
        mock_instance.extract_from_pdf.assert_called_once_with("test.pdf")
        mock_instance.save_results.assert_called_once()
    
    def test_analyze_command_with_sample_data(self, sample_lines_file, temp_output_dir):
        """Test analyze command with real sample data."""
        output_file = temp_output_dir / "test_analysis.txt"
        
        # Run analysis
        analyze_lines(str(sample_lines_file), str(output_file), show_output=False)
        
        # Should create analysis file
        assert output_file.exists()
        
        # Should contain analysis content
        content = output_file.read_text()
        assert "Analysis Results" in content
        assert "Font Usage Analysis" in content
        assert "Font Size Analysis" in content