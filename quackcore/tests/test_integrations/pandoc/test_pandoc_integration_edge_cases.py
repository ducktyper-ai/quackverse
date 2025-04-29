# quackcore/tests/test_integrations/pandoc/test_pandoc_integration_edge_cases.py
"""
Additional tests for edge cases in the pandoc integration.

This module tests edge cases and error handling in the pandoc integration
to ensure robust behavior in all situations.
"""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc import (
    ConversionMetrics,
    DocumentConverter,
    FileInfo,
    PandocConfig,
    PandocIntegration,
)
from quackcore.integrations.pandoc.service import PandocIntegration

# --- Tests for PandocIntegration edge cases ---

def test_integration_with_custom_config_path(monkeypatch):
    """Test PandocIntegration with custom config path."""
    # Mock config provider
    mock_config_provider = MagicMock()
    mock_config_provider.load_config.return_value = {"output_dir": "/custom/path"}

    with patch('quackcore.integrations.pandoc.config.PandocConfigProvider',
               return_value=mock_config_provider):
        integration = PandocIntegration(config_path="/path/to/config.yaml")

        # Initialize to trigger config loading
        with patch('quackcore.integrations.pandoc.service.verify_pandoc',
                   return_value="2.11.0"):
            integration.initialize()

            # Verify config was loaded from the custom path
            mock_config_provider.load_config.assert_called_once_with(
                "/path/to/config.yaml")


def test_integration_with_custom_output_dir(monkeypatch):
    """Test PandocIntegration with custom output directory."""
    integration = PandocIntegration(output_dir="/custom/output")

    # Initialize
    with patch('quackcore.integrations.pandoc.service.verify_pandoc',
               return_value="2.11.0"):
        # Mock super().initialize()
        with patch.object(PandocIntegration, 'initialize',
                          return_value=IntegrationResult.success_result()):
            integration.initialize()

            # Check if output_dir was set correctly in config
            assert integration.output_dir == "/custom/output"
            if integration.converter and integration.converter.config:
                assert integration.converter.config.output_dir == "/custom/output"


def test_integration_initialize_with_invalid_config(monkeypatch):
    """Test initialization with invalid configuration."""
    integration = PandocIntegration()

    # Set invalid config
    integration.config = {"invalid_key": "value"}

    # Initialize - should fail on config validation
    result = integration.initialize()

    assert not result.success
    assert "Invalid configuration" in result.error


def test_integration_directory_conversion_edge_cases(fs_stub):
    """Test directory conversion edge cases."""
    integration = PandocIntegration()

    # Initialize
    with patch('quackcore.integrations.pandoc.service.verify_pandoc',
               return_value="2.11.0"):
        integration.initialize()

    # Test with input directory not existing
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists="input_dir" not in path, is_dir=False
    )

    result = integration.convert_directory("input_dir", "markdown")
    assert not result.success
    assert "directory does not exist" in result.error

    # Test with no matching files
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, is_dir=True
    )
    fs_stub.find_files = lambda dir_path, pattern, recursive: SimpleNamespace(
        success=True, files=[]
    )

    result = integration.convert_directory("input_dir", "markdown")
    assert not result.success
    assert "No matching files found" in result.error

    # Test with find_files operation failing
    fs_stub.find_files = lambda dir_path, pattern, recursive: SimpleNamespace(
        success=False, error="Find operation failed"
    )

    result = integration.convert_directory("input_dir", "markdown")
    assert not result.success
    assert "Failed to find files" in result.error

    # Test with unsupported output format
    fs_stub.find_files = lambda dir_path, pattern, recursive: SimpleNamespace(
        success=True, files=["file1.html"]
    )

    result = integration.convert_directory("input_dir", "pdf")  # Unsupported format
    assert not result.success
    assert "Unsupported output format" in result.error


def test_integration_determine_conversion_params():
    """Test the _determine_conversion_params method."""
    integration = PandocIntegration()

    # Test supported formats
    markdown_params = integration._determine_conversion_params("markdown", None)
    assert markdown_params == ("html", "*.html")

    docx_params = integration._determine_conversion_params("docx", None)
    assert docx_params == ("markdown", "*.md")

    # Test with custom file pattern
    custom_params = integration._determine_conversion_params("markdown", "*.htm")
    assert custom_params == ("html", "*.htm")

    # Test unsupported format
    unsupported = integration._determine_conversion_params("pdf", None)
    assert unsupported is None


def test_integration_create_conversion_tasks(fs_stub):
    """Test the _create_conversion_tasks method."""
    integration = PandocIntegration()

    # Mock get_file_info to return valid info
    with patch(
            'quackcore.integrations.pandoc.operations.get_file_info') as mock_get_info:
        mock_get_info.return_value = FileInfo(
            path="file.html", format="html", size=100, modified=None, extra_args=[]
        )

        # Test task creation for HTML to Markdown
        tasks = integration._create_conversion_tasks(
            ["file1.html", "file2.html"],
            "html",
            "markdown",
            "/output/dir"
        )

        assert len(tasks) == 2
        assert tasks[0].source.path == "file1.html"
        assert tasks[0].target_format == "markdown"
        assert tasks[0].output_path == os.path.join("/output/dir", "file1.md")

        # Test task creation for Markdown to DOCX
        tasks = integration._create_conversion_tasks(
            ["file1.md", "file2.md"],
            "markdown",
            "docx",
            "/output/dir"
        )

        assert len(tasks) == 2
        assert tasks[0].source.path == "file1.md"
        assert tasks[0].target_format == "docx"
        assert tasks[0].output_path == os.path.join("/output/dir", "file1.docx")

        # Test with get_file_info raising an exception
        mock_get_info.side_effect = Exception("File info error")

        tasks = integration._create_conversion_tasks(
            ["file1.html", "file2.html"],
            "html",
            "markdown",
            "/output/dir"
        )

        # Should skip files with errors
        assert len(tasks) == 0


def test_integration_get_metrics():
    """Test the get_metrics method."""
    integration = PandocIntegration()

    # Without initialization
    metrics = integration.get_metrics()
    assert isinstance(metrics, ConversionMetrics)
    assert metrics.successful_conversions == 0

    # After initialization
    with patch('quackcore.integrations.pandoc.service.verify_pandoc',
               return_value="2.11.0"):
        integration.initialize()

        # Simulate some conversion metrics
        if integration.converter:
            integration.converter.metrics.successful_conversions = 5
            integration.converter.metrics.failed_conversions = 2

        metrics = integration.get_metrics()
        assert metrics.successful_conversions == 5
        assert metrics.failed_conversions == 2


# --- Tests for DocumentConverter edge cases ---

def test_document_converter_validate_conversion_edge_cases(fs_stub):
    """Test edge cases for the validate_conversion method."""
    config = PandocConfig()
    converter = DocumentConverter(config)

    # Test with output file not existing
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists="output" not in path
    )

    result = converter.validate_conversion("output.md", "input.html")
    assert not result

    # Test with input file not existing
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists="input" not in path
    )

    result = converter.validate_conversion("output.md", "input.html")
    assert not result

    # Test with Markdown file reading error
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, size=100
    )
    fs_stub.get_extension = lambda path: SimpleNamespace(data="md")
    fs_stub.read_text = lambda path, encoding=None: SimpleNamespace(
        success=False, error="Read error"
    )

    result = converter.validate_conversion("output.md", "input.html")
    assert not result

    # Test with exception during validation
    fs_stub.read_text = lambda path, encoding=None: (_ for _ in ()).throw(
        Exception("Test error"))

    result = converter.validate_conversion("output.md", "input.html")
    assert not result


def test_document_converter_validate_docx():
    """Test validation of DOCX files in the converter."""
    config = PandocConfig()
    converter = DocumentConverter(config)

    # Mock fs and validate_docx_structure
    with patch('quackcore.fs.service.standalone.get_file_info') as mock_get_info, \
            patch('quackcore.fs.service.standalone.get_extension') as mock_get_ext, \
            patch(
                'quackcore.integrations.pandoc.operations.utils.validate_docx_structure') as mock_validate:
        mock_get_info.return_value = SimpleNamespace(success=True, exists=True,
                                                     size=100)
        mock_get_ext.return_value = SimpleNamespace(data="docx")
        mock_validate.return_value = (True, [])  # Valid DOCX

        result = converter.validate_conversion("output.docx", "input.md")
        assert result

        # Test invalid DOCX
        mock_validate.return_value = (False, ["Invalid DOCX structure"])

        result = converter.validate_conversion("output.docx", "input.md")
        assert not result


# --- Tests for mocked service functionality ---

def test_mock_services_integration():
    """Test integration with mocked services."""
    # Mock fs, path and pypandoc
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch('quackcore.paths.service') as mock_paths, \
            patch.dict('sys.modules', {'pypandoc': MagicMock()}):
        # Setup mocks
        mock_fs.normalize_path.return_value = SimpleNamespace(success=True,
                                                              path="/resolved/path")
        mock_fs.get_file_info.return_value = SimpleNamespace(success=True, exists=True,
                                                             size=100)
        mock_fs.create_directory.return_value = SimpleNamespace(success=True)
        mock_fs.join_path = os.path.join
        mock_fs.read_text.return_value = SimpleNamespace(success=True,
                                                         content="HTML content")

        mock_paths.resolve_project_path = lambda p: p

        # Create and initialize integration
        integration = PandocIntegration()

        with patch('quackcore.integrations.pandoc.service.verify_pandoc',
                   return_value="2.11.0"):
            init_result = integration.initialize()
            assert init_result.success

        # Mock converter methods
        if integration.converter:
            integration.converter.convert_file = MagicMock(
                return_value=IntegrationResult.success_result("output.md"))

        # Test HTML to Markdown conversion
        result = integration.html_to_markdown("input.html")
        assert result.success
