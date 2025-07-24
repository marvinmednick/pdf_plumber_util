"""Integration tests for CLI commands."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.pdf_plumb.cli import cli


@pytest.mark.integration
class TestCLICommands:
    """Test CLI command integration."""
    
    def test_cli_help(self):
        """Test the main CLI help command displays complete command overview and available subcommands.
        
        Test setup:
        - Uses CliRunner to invoke CLI with --help flag
        - No additional arguments or configuration needed
        - Tests basic CLI framework functionality without dependencies
        
        What it verifies:
        - CLI exits successfully (exit_code == 0) without errors
        - Main description "PDF Plumb - Modern PDF text extraction and analysis tool" appears
        - All primary subcommands are listed: extract, analyze, process
        - Help text is properly formatted and accessible
        
        Test limitation:
        - Only tests help text content, not actual command functionality
        - Doesn't verify help text formatting or completeness
        - Basic string matching rather than comprehensive help validation
        
        Key insight: Validates that CLI framework is properly configured and main commands are registered.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "PDF Plumb - Modern PDF text extraction and analysis tool" in result.output
        assert "extract" in result.output
        assert "analyze" in result.output
        assert "process" in result.output
    
    def test_cli_version(self):
        """Test the --version flag returns correct version information.
        
        Test setup:
        - Uses CliRunner to invoke CLI with --version flag
        - Tests version display functionality independent of other commands
        
        What it verifies:
        - Version command executes successfully (exit_code == 0)
        - Version string "PDF Plumb v0.1.0" appears in output
        - Version information is properly accessible via standard --version flag
        
        Test limitation:
        - Hardcoded version string check may become outdated
        - Doesn't validate version format or semantic versioning
        - Only tests string presence, not version accuracy
        
        Key insight: Ensures version information is properly configured in CLI framework.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "PDF Plumb v0.1.0" in result.output
    
    def test_profile_application(self):
        """Test the --profile flag successfully applies predefined document type configurations.
        
        Test setup:
        - Uses CliRunner to invoke CLI with --profile technical flag
        - Tests profile system without requiring PDF files or additional commands
        - Uses 'technical' profile which should be predefined in configuration
        
        What it verifies:
        - Profile application executes successfully (exit_code == 0)
        - Success message "Applied technical document profile" appears in output
        - Profile system is accessible and properly configured
        - Technical profile exists and can be applied
        
        Test limitation:
        - Only tests success message, not actual profile configuration changes
        - Doesn't verify that profile settings are actually applied
        - Limited to testing one profile type (technical)
        
        Key insight: Validates that document type profile system is working and technical profile is properly configured.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--profile', 'technical'])
        
        assert result.exit_code == 0
        assert "Applied technical document profile" in result.output
    
    def test_invalid_profile(self):
        """Test CLI error handling when an invalid profile name is provided.
        
        Test setup:
        - Uses CliRunner to invoke CLI with --profile invalid flag
        - Tests error handling for profile names that don't exist in configuration
        - Uses 'invalid' as a profile name that should not be defined
        
        What it verifies:
        - CLI exits with error code (exit_code != 0) for invalid profile
        - Error message "Invalid value for '--profile'" appears in output
        - Profile validation properly rejects undefined profile names
        - Click framework error handling works for invalid choices
        
        Test limitation:
        - Only tests one invalid profile name ('invalid')
        - Doesn't test other types of profile validation errors
        - Relies on Click's built-in choice validation rather than custom logic
        
        Key insight: Ensures profile system has proper validation and provides clear error messages for invalid choices.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--profile', 'invalid'])
        
        assert result.exit_code != 0
        assert "Invalid value for '--profile'" in result.output
    
    def test_extract_help(self):
        """Test extract subcommand help displays all available options and parameters."""
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', '--help'])
        
        assert result.exit_code == 0
        assert "Extract text from PDF file using multiple methods" in result.output
        assert "--y-tolerance" in result.output
        assert "--x-tolerance" in result.output
        assert "--visualize-spacing" in result.output
    
    def test_analyze_help(self):
        """Test analyze subcommand help displays description and key options."""
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', '--help'])
        
        assert result.exit_code == 0
        assert "Analyze extracted text data to determine document structure" in result.output
        assert "--output-file" in result.output
        assert "--show-output" in result.output
    
    def test_process_help(self):
        """Test process subcommand help shows combined extraction and analysis options."""
        runner = CliRunner()
        result = runner.invoke(cli, ['process', '--help'])
        
        assert result.exit_code == 0
        assert "Extract and analyze PDF in one step" in result.output
        assert "--visualize-spacing" in result.output
        assert "--show-output" in result.output
    
    @patch('src.pdf_plumb.cli.PDFExtractor')
    def test_extract_command_basic(self, mock_extractor, temp_output_dir):
        """Test the CLI extract command's ability to orchestrate PDF extraction through the command interface.
        
        Test setup:
        - Mocks PDFExtractor to return structured test data (lines, words, comparison)
        - Creates temporary PDF file with dummy content for CLI testing
        - Uses CliRunner to invoke extract command with output directory and basename options

        What it verifies:
        - CLI command executes successfully (exit_code == 0)
        - Success messages appear in command output ("Extracting text", "Extraction complete")
        - PDFExtractor.extract_from_pdf() called with correct file path
        - PDFExtractor.save_results() called exactly once

        Test limitation:
        - Uses mocked extractor, doesn't test actual PDF processing logic
        - Temporary PDF contains dummy text, not real PDF structure
        - Doesn't validate output file contents or data accuracy

        Key insight: Confirms CLI command orchestration works correctly but doesn't validate core PDF extraction functionality.
        """
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
    
    @patch('src.pdf_plumb.cli.DocumentAnalyzer')
    def test_analyze_command_basic(self, mock_analyzer, sample_lines_file, temp_output_dir):
        """Test the CLI analyze command's ability to orchestrate document analysis through the command interface.
        
        Test setup:
        - Mocks DocumentAnalyzer to return structured test data (fonts, sizes, spacing)
        - Uses sample_lines_file fixture containing JSON line data for analysis
        - Creates temporary output file path for analysis results
        - Uses CliRunner to invoke analyze command with file and output options
        
        What it verifies:
        - CLI command executes successfully (exit_code == 0)
        - Progress messages appear in output ("Analyzing", "Analysis complete")
        - DocumentAnalyzer.analyze_document() called with correct file path
        - DocumentAnalyzer.print_analysis() called exactly once
        
        Test limitation:
        - Uses mocked analyzer, doesn't test actual document analysis logic
        - Sample file may not represent real extracted line data structure
        - Doesn't validate output file contents or analysis accuracy
        
        Key insight: Confirms CLI command orchestration works correctly but doesn't validate core analysis functionality.
        """
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
        """Test CLI error handling when extract command is given a nonexistent PDF file path.
        
        Test setup:
        - Uses CliRunner to invoke extract command with nonexistent.pdf file path
        - File path intentionally doesn't exist to trigger error condition
        - Tests Click framework's built-in file existence validation
        
        What it verifies:
        - CLI exits with Click's standard error code 2 for invalid arguments
        - Error message contains "does not exist" indicating file validation failed
        - File existence validation occurs before attempting PDF processing
        - Clear error messaging for common user mistake (wrong file path)
        
        Test limitation:
        - Only tests one type of file error (nonexistent file)
        - Doesn't test other file issues like permissions or invalid format
        - Relies on Click's built-in validation rather than custom error handling
        
        Key insight: Ensures CLI provides clear feedback when users specify incorrect file paths.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', 'nonexistent.pdf'])
        
        assert result.exit_code == 2  # Click error code for invalid argument
        assert "does not exist" in result.output
    
    def test_extract_with_profile(self):
        """Test combining global --profile flag with extract subcommand help to verify profile application.
        
        Test setup:
        - Uses CliRunner to invoke CLI with --profile technical followed by extract --help
        - Tests interaction between global profile option and subcommand
        - Uses help command to avoid needing actual PDF files for testing
        
        What it verifies:
        - Profile application works when combined with subcommands (exit_code == 0)
        - Profile success message "Applied technical document profile" appears
        - Global options are processed before subcommand execution
        - Profile system integrates properly with CLI command structure
        
        Test limitation:
        - Only tests profile application message, not actual configuration changes
        - Uses help subcommand rather than testing profile effects on extraction
        - Limited to testing one profile type with one subcommand
        
        Key insight: Validates that global profile options work correctly with all subcommands.
        """
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--profile', 'technical',
            'extract', '--help'
        ])
        
        assert result.exit_code == 0
        assert "Applied technical document profile" in result.output