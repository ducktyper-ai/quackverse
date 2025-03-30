# tests/test_integrations/pandoc/test_converter.py
"""
Tests for the Pandoc document converter.

This module tests the DocumentConverter class that implements the document
conversion functionality using Pandoc.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult, OperationResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import ConversionMetrics, ConversionTask, \
    FileInfo


class TestDocumentConverter:
    """Tests for the DocumentConverter class."""

    @pytest.fixture
    def mock_fs(self):
        """Fixture to mock fs service."""
        with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
            # Setup default behavior for directory creation
            mock_fs.service.create_directory.return_value = OperationResult(
                success=True,
                path="/path/to/output",
                message="Directory created",
            )

            # Setup default behavior for file existence check
            file_info = FileInfoResult(
                success=True,
                path="/path/to/file",
                exists=True,
                is_file=True,
            )
            mock_fs.service.get_file_info.return_value = file_info

            yield mock_fs

    @pytest.fixture
    def config(self):
        """Fixture to create a PandocConfig for testing."""
        return PandocConfig(
            output_dir=Path("/path/to/output"),
        )

    @pytest.fixture
    def converter(self, config, mock_fs):
        """Fixture to create a DocumentConverter instance for testing."""
        with patch(
                "quackcore.integrations.pandoc.converter.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.11.4"

            converter = DocumentConverter(config)
            return converter

    def test_init(self, config, mock_fs):
        """Test initialization of the DocumentConverter."""
        with patch(
                "quackcore.integrations.pandoc.converter.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.11.4"

            converter = DocumentConverter(config)

            assert converter.config == config
            assert isinstance(converter.metrics, ConversionMetrics)
            assert converter.pandoc_version == "2.11.4"
            mock_verify.assert_called_once()

    def test_init_pandoc_not_available(self, config):
        """Test initialization when pandoc is not available."""
        with patch(
                "quackcore.integrations.pandoc.converter.verify_pandoc") as mock_verify:
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")

            with pytest.raises(QuackIntegrationError) as excinfo:
                DocumentConverter(config)

            assert "Pandoc not found" in str(excinfo.value)

    def test_convert_file_html_to_markdown(self, converter, mock_fs):
        """Test converting an HTML file to Markdown."""
        # Set up mocks for file info
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Mock the get_file_info function to handle the input file
        with patch(
                "quackcore.integrations.pandoc.operations.get_file_info") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                path=input_path,
                format="html",
                size=1024,
            )

            # Mock the convert_html_to_markdown function
            with patch(
                    "quackcore.integrations.pandoc.converter.convert_html_to_markdown") as mock_convert:
                mock_convert.return_value = IntegrationResult.success_result(
                    (output_path, None),
                    message="Successfully converted HTML to Markdown",
                )

                # Test the conversion
                result = converter.convert_file(input_path, output_path, "markdown")

                # Assertions
                assert result.success is True
                assert result.content == output_path
                assert "Successfully converted" in result.message
                mock_get_info.assert_called_once_with(input_path)
                mock_convert.assert_called_once()
                mock_fs.service.create_directory.assert_called_once_with(
                    output_path.parent, exist_ok=True)

    def test_convert_file_markdown_to_docx(self, converter, mock_fs):
        """Test converting a Markdown file to DOCX."""
        # Set up mocks for file info
        input_path = Path("/path/to/input.md")
        output_path = Path("/path/to/output/output.docx")

        # Mock the get_file_info function to handle the input file
        with patch(
                "quackcore.integrations.pandoc.operations.get_file_info") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                path=input_path,
                format="markdown",
                size=512,
            )

            # Mock the convert_markdown_to_docx function
            with patch(
                    "quackcore.integrations.pandoc.converter.convert_markdown_to_docx") as mock_convert:
                mock_convert.return_value = IntegrationResult.success_result(
                    (output_path, None),
                    message="Successfully converted Markdown to DOCX",
                )

                # Test the conversion
                result = converter.convert_file(input_path, output_path, "docx")

                # Assertions
                assert result.success is True
                assert result.content == output_path
                assert "Successfully converted" in result.message
                mock_get_info.assert_called_once_with(input_path)
                mock_convert.assert_called_once()
                mock_fs.service.create_directory.assert_called_once_with(
                    output_path.parent, exist_ok=True)

    def test_convert_file_unsupported_format(self, converter, mock_fs):
        """Test converting to an unsupported format."""
        # Set up mocks for file info
        input_path = Path("/path/to/input.md")
        output_path = Path("/path/to/output/output.pdf")

        # Mock the get_file_info function to handle the input file
        with patch(
                "quackcore.integrations.pandoc.operations.get_file_info") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                path=input_path,
                format="markdown",
                size=512,
            )

            # Test the conversion
            result = converter.convert_file(input_path, output_path, "pdf")

            # Assertions
            assert result.success is False
            assert "Unsupported conversion" in result.error
            mock_get_info.assert_called_once_with(input_path)

    def test_convert_file_directory_creation_failure(self, converter, mock_fs):
        """Test conversion when directory creation fails."""
        # Set up mocks for file info
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Mock directory creation to fail
        mock_fs.service.create_directory.return_value = OperationResult(
            success=False,
            path="/path/to/output",
            error="Permission denied",
        )

        # Mock the get_file_info function to handle the input file
        with patch(
                "quackcore.integrations.pandoc.operations.get_file_info") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                path=input_path,
                format="html",
                size=1024,
            )

            # Test the conversion
            result = converter.convert_file(input_path, output_path, "markdown")

            # Assertions
            assert result.success is False
            assert "Failed to create output directory" in result.error
            mock_get_info.assert_called_once_with(input_path)
            mock_fs.service.create_directory.assert_called_once_with(output_path.parent,
                                                                     exist_ok=True)

    def test_convert_file_integration_error(self, converter, mock_fs):
        """Test conversion when an integration error occurs."""
        # Set up mocks for file info
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Mock the get_file_info function to raise an error
        with patch(
                "quackcore.integrations.pandoc.operations.get_file_info") as mock_get_info:
            mock_get_info.side_effect = QuackIntegrationError("File not found")

            # Test the conversion
            result = converter.convert_file(input_path, output_path, "markdown")

            # Assertions
            assert result.success is False
            assert "File not found" in result.error

    def test_convert_batch(self, converter, mock_fs):
        """Test batch conversion of files."""
        # Create test tasks
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file1.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file1.md"),
            ),
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file2.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file2.md"),
            ),
        ]

        # Mock the convert_file method to return successful results
        with patch.object(converter, "convert_file") as mock_convert:
            mock_convert.side_effect = [
                IntegrationResult.success_result(
                    Path("/path/to/output/file1.md"),
                    message="Successfully converted file1.html",
                ),
                IntegrationResult.success_result(
                    Path("/path/to/output/file2.md"),
                    message="Successfully converted file2.html",
                ),
            ]

            # Test batch conversion
            result = converter.convert_batch(tasks)

            # Assertions
            assert result.success is True
            assert len(result.content) == 2
            assert result.content[0] == Path("/path/to/output/file1.md")
            assert result.content[1] == Path("/path/to/output/file2.md")
            assert "Successfully converted 2 files" in result.message
            assert mock_convert.call_count == 2
            assert converter.metrics.successful_conversions == 2
            assert converter.metrics.failed_conversions == 0

    def test_convert_batch_with_output_dir(self, converter, mock_fs):
        """Test batch conversion with explicit output directory."""
        # Create test tasks without output paths
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file1.html"), format="html"),
                target_format="markdown",
            ),
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file2.html"), format="html"),
                target_format="markdown",
            ),
        ]

        output_dir = Path("/custom/output")

        # Mock directory creation for the custom output directory
        mock_fs.service.create_directory.return_value = OperationResult(
            success=True,
            path="/custom/output",
            message="Directory created",
        )

        # Mock the convert_file method to return successful results
        with patch.object(converter, "convert_file") as mock_convert:
            mock_convert.side_effect = [
                IntegrationResult.success_result(
                    Path("/custom/output/file1.md"),
                    message="Successfully converted file1.html",
                ),
                IntegrationResult.success_result(
                    Path("/custom/output/file2.md"),
                    message="Successfully converted file2.html",
                ),
            ]

            # Test batch conversion
            result = converter.convert_batch(tasks, output_dir)

            # Assertions
            assert result.success is True
            assert len(result.content) == 2
            assert mock_convert.call_count == 2
            mock_fs.service.create_directory.assert_called_with(output_dir,
                                                                exist_ok=True)

    def test_convert_batch_partial_success(self, converter, mock_fs):
        """Test batch conversion with partial success."""
        # Create test tasks
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file1.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file1.md"),
            ),
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file2.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file2.md"),
            ),
        ]

        # Mock the convert_file method to return mixed results
        with patch.object(converter, "convert_file") as mock_convert:
            mock_convert.side_effect = [
                IntegrationResult.success_result(
                    Path("/path/to/output/file1.md"),
                    message="Successfully converted file1.html",
                ),
                IntegrationResult.error_result(
                    "Failed to convert file2.html",
                ),
            ]

            # Test batch conversion
            result = converter.convert_batch(tasks)

            # Assertions
            assert result.success is True  # Still successful overall
            assert len(result.content) == 1
            assert result.content[0] == Path("/path/to/output/file1.md")
            assert "Partially successful" in result.message
            assert "converted 1 files" in result.message
            assert "failed to convert 1 files" in result.message
            assert mock_convert.call_count == 2
            assert converter.metrics.successful_conversions == 1
            assert converter.metrics.failed_conversions == 1

    def test_convert_batch_all_failed(self, converter, mock_fs):
        """Test batch conversion when all tasks fail."""
        # Create test tasks
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file1.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file1.md"),
            ),
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file2.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file2.md"),
            ),
        ]

        # Mock the convert_file method to return failure results
        with patch.object(converter, "convert_file") as mock_convert:
            mock_convert.side_effect = [
                IntegrationResult.error_result("Failed to convert file1.html"),
                IntegrationResult.error_result("Failed to convert file2.html"),
            ]

            # Test batch conversion
            result = converter.convert_batch(tasks)

            # Assertions
            assert result.success is False
            assert "Failed to convert any files" in result.error
            assert "All 2 conversion tasks failed" in result.message
            assert mock_convert.call_count == 2
            assert converter.metrics.successful_conversions == 0
            assert converter.metrics.failed_conversions == 2

    def test_convert_batch_exception(self, converter, mock_fs):
        """Test batch conversion when an exception occurs."""
        # Create test tasks
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file1.html"), format="html"),
                target_format="markdown",
                output_path=Path("/path/to/output/file1.md"),
            ),
        ]

        # Mock the convert_file method to raise an exception
        with patch.object(converter, "convert_file") as mock_convert:
            mock_convert.side_effect = Exception("Unexpected error")

            # Test batch conversion
            result = converter.convert_batch(tasks)

            # Assertions
            assert result.success is False
            assert "All 1 conversion tasks failed" in result.message
            assert converter.metrics.successful_conversions == 0
            assert converter.metrics.failed_conversions == 0  # Not incremented for unexpected errors
            assert "file1.html" in converter.metrics.errors

    def test_validate_conversion_markdown(self, converter, mock_fs):
        """Test validation of a converted Markdown file."""
        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file info for the output file
        output_info = FileInfoResult(
            success=True,
            path="/path/to/output/file.md",
            exists=True,
            is_file=True,
            size=512,
        )
        mock_fs.service.get_file_info.return_value = output_info

        # Mock read_text to return content for the Markdown file
        mock_fs.service.read_text.return_value.success = True
        mock_fs.service.read_text.return_value.content = "# Sample Markdown\n\nThis is a sample markdown file."

        # Get the extension
        mock_fs.get_extension.return_value = "md"

        # Test validation
        result = converter.validate_conversion(output_path, input_path)

        # Assertions
        assert result is True
        mock_fs.service.get_file_info.assert_called_with(output_path)
        mock_fs.service.read_text.assert_called_with(output_path, encoding="utf-8")

    def test_validate_conversion_docx(self, converter, mock_fs):
        """Test validation of a converted DOCX file."""
        output_path = Path("/path/to/output/file.docx")
        input_path = Path("/path/to/input.md")

        # Mock file info for the output file
        output_info = FileInfoResult(
            success=True,
            path="/path/to/output/file.docx",
            exists=True,
            is_file=True,
            size=10240,
        )
        mock_fs.service.get_file_info.return_value = output_info

        # Get the extension
        mock_fs.get_extension.return_value = "docx"

        # Mock validate_docx_structure
        with patch(
                "quackcore.integrations.pandoc.operations.utils.validate_docx_structure") as mock_validate:
            mock_validate.return_value = (True, [])

            # Test validation
            result = converter.validate_conversion(output_path, input_path)

            # Assertions
            assert result is True
            mock_fs.service.get_file_info.assert_called_with(output_path)
            mock_validate.assert_called_once_with(output_path,
                                                  converter.config.validation.check_links)

    def test_validate_conversion_output_not_exists(self, converter, mock_fs):
        """Test validation when output file doesn't exist."""
        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file info for the output file to show it doesn't exist
        output_info = FileInfoResult(
            success=True,
            path="/path/to/output/file.md",
            exists=False,
        )
        mock_fs.service.get_file_info.return_value = output_info

        # Test validation
        result = converter.validate_conversion(output_path, input_path)

        # Assertions
        assert result is False
        mock_fs.service.get_file_info.assert_called_with(output_path)

    def test_validate_conversion_input_not_exists(self, converter, mock_fs):
        """Test validation when input file doesn't exist."""
        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file info for the output file to show it exists
        output_info = FileInfoResult(
            success=True,
            path="/path/to/output/file.md",
            exists=True,
            is_file=True,
            size=512,
        )
        # Mock file info for the input file to show it doesn't exist
        input_info = FileInfoResult(
            success=True,
            path="/path/to/input.html",
            exists=False,
        )

        # Setup mock to return different results for input and output
        mock_fs.service.get_file_info.side_effect = [output_info, input_info]

        # Test validation
        result = converter.validate_conversion(output_path, input_path)

        # Assertions
        assert result is False
        assert mock_fs.service.get_file_info.call_count == 2