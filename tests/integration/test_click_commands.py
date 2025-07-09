"""Integration tests for Click CLI commands."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.pdf_plumb.cli_click import cli


@pytest.mark.integration
class TestClickCLICommands:
    """Test Click CLI command integration."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "PDF Plumb - Modern PDF text extraction and analysis tool" in result.output
        assert "extract" in result.output
        assert "analyze" in result.output
        assert "process" in result.output
    
    def test_cli_version(self):
        """Test version flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "PDF Plumb v0.1.0" in result.output
    
    def test_profile_application(self):
        """Test profile application."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--profile', 'technical'])
        
        assert result.exit_code == 0
        assert "Applied technical document profile" in result.output
    
    def test_invalid_profile(self):
        """Test invalid profile handling."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--profile', 'invalid'])
        
        assert result.exit_code != 0
        assert "Invalid value for '--profile'" in result.output
    
    def test_extract_help(self):
        """Test extract command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', '--help'])
        
        assert result.exit_code == 0
        assert "Extract text from PDF file using multiple methods" in result.output
        assert "--y-tolerance" in result.output
        assert "--x-tolerance" in result.output
        assert "--visualize-spacing" in result.output
    
    def test_analyze_help(self):
        """Test analyze command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert "Analyze extracted text data to determine document structure" in result.output
        assert "--output-file" in result.output
        assert "--show-output" in result.output
    
    def test_process_help(self):
        """Test process command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['process', '--help'])
        
        assert result.exit_code == 0
        assert "Extract and analyze PDF in one step" in result.output
        assert "--visualize-spacing" in result.output
        assert "--show-output" in result.output
    
    @patch('src.pdf_plumb.cli_click.PDFExtractor')
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
        
        # Create test PDF file
        test_pdf = temp_output_dir / "test.pdf"
        test_pdf.write_text("dummy content")
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(test_pdf),
            '--output-dir', str(temp_output_dir),
            '--basename', 'test'
        ])
        
        assert result.exit_code == 0
        assert "Extracting text from" in result.output
        assert "Saving results to" in result.output
        assert "Extraction complete" in result.output
        
        # Should have called extractor methods
        mock_instance.extract_from_pdf.assert_called_once_with(str(test_pdf))
        mock_instance.save_results.assert_called_once()
    
    @patch('src.pdf_plumb.cli_click.DocumentAnalyzer')
    def test_analyze_command_basic(self, mock_analyzer, sample_lines_file, temp_output_dir):
        """Test basic analyze command functionality."""
        # Mock the analyzer
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.analyze_document.return_value = {
            'fonts': ['Arial'],
            'sizes': [12.0],
            'spacing': [6.0]
        }
        
        output_file = temp_output_dir / "test_analysis.txt"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'analyze',
            str(sample_lines_file),
            '--output-file', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "Analyzing" in result.output
        assert "Analysis complete" in result.output
        
        # Should have called analyzer methods
        mock_instance.analyze_document.assert_called_once_with(str(sample_lines_file))
        mock_instance.print_analysis.assert_called_once()
    
    def test_missing_pdf_file(self):
        """Test error handling for missing PDF file."""
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', 'nonexistent.pdf'])
        
        assert result.exit_code == 2  # Click error code for invalid argument
        assert "does not exist" in result.output
    
    def test_extract_with_profile(self):
        """Test extract command with profile."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--profile', 'technical',
            'extract', '--help'
        ])
        
        assert result.exit_code == 0
        assert "Applied technical document profile" in result.output