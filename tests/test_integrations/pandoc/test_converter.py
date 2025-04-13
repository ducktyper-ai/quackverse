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
from quackcore.fs.results import FileInfoResult, OperationResult, ReadResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import (
    ConversionMetrics,
    ConversionTask,
    FileInfo,
)


class TestDocumentConverter:
    """Tests for the DocumentConverter class."""

    @pytest.fixture
    def config(self):
        """Fixture to create a PandocConfig for testing."""
        return PandocConfig(
            output_dir=Path("/path/to/output"),
        )

    @pytest.fixture
    def converter(self, config):
        """Fixture to create a DocumentConverter instance for testing."""
        # Make sure we use our mock, not the real pandoc
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ):
            converter = DocumentConverter(config)
            return converter

    def test_init(self, config):
        """Test initialization of the DocumentConverter."""
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ) as mock_verify:
            converter = DocumentConverter(config)

            assert converter.config == config
            assert isinstance(converter.metrics, ConversionMetrics)
            assert converter.pandoc_version == "2.11.4"
            mock_verify.assert_called_once()

    def test_init_pandoc_not_available(self, config):
        """Test initialization when pandoc is not available."""
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            side_effect=QuackIntegrationError("Pandoc not found"),
        ) as mock_verify:
            with pytest.raises(QuackIntegrationError) as excinfo:
                DocumentConverter(config)

            assert "Pandoc not found" in str(excinfo.value)

    def test_convert_file_html_to_markdown(self, converter):
        """Test converting an HTML file to Markdown."""
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup directory creation response
                mock_fs.create_directory.return_value = OperationResult(
                    success=True,
                    path="/path/to/output",
                    message="Directory created",
                )

                # Setup FileInfo for both direct and service calls
                file_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=1024,
                )
                mock_fs.get_file_info.return_value = file_info

                # Setup service mock
                service_mock = MagicMock()
                service_mock.get_file_info.return_value = file_info
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

                # Also patch the operations.utils.get_file_info
                with patch(
                    "quackcore.integrations.pandoc.operations.utils.get_file_info"
                ) as mock_get_info:
                    # Return a proper FileInfo object
                    mock_get_info.return_value = FileInfo(
                        path=input_path,
                        format="html",
                        size=1024,
                    )

                    # Mock the convert_html_to_markdown function
                    with patch(
                        "quackcore.integrations.pandoc.converter.convert_html_to_markdown"
                    ) as mock_convert:
                        mock_convert.return_value = IntegrationResult.success_result(
                            (output_path, None),
                            message="Successfully converted HTML to Markdown",
                        )

                        # Test the conversion
                        result = converter.convert_file(
                            input_path, output_path, "markdown"
                        )

                        # Assertions
                        assert result.success is True
                        assert result.content == output_path
                        assert "Successfully converted" in result.message
                        mock_convert.assert_called_once()

    def test_convert_file_markdown_to_docx(self, converter):
        """Test converting a Markdown file to DOCX."""
        input_path = Path("/path/to/input.md")
        output_path = Path("/path/to/output/output.docx")

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup directory creation response
                mock_fs.create_directory.return_value = OperationResult(
                    success=True,
                    path="/path/to/output",
                    message="Directory created",
                )

                # Setup FileInfo for both direct and service calls
                file_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=512,
                )
                mock_fs.get_file_info.return_value = file_info

                # Setup service mock
                service_mock = MagicMock()
                service_mock.get_file_info.return_value = file_info
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

                # Mock the operations.utils.get_file_info function
                with patch(
                    "quackcore.integrations.pandoc.operations.utils.get_file_info"
                ) as mock_get_info:
                    # Return a proper FileInfo object
                    mock_get_info.return_value = FileInfo(
                        path=input_path,
                        format="markdown",
                        size=512,
                    )

                    # Mock the convert_markdown_to_docx function
                    with patch(
                        "quackcore.integrations.pandoc.converter.convert_markdown_to_docx"
                    ) as mock_convert:
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
                        mock_convert.assert_called_once()

    def test_convert_file_unsupported_format(self, converter):
        """Test converting to an unsupported format."""
        input_path = Path("/path/to/input.md")
        output_path = Path("/path/to/output/output.pdf")

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup FileInfo for both direct and service calls
                file_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=512,
                )
                mock_fs.get_file_info.return_value = file_info

                # Setup service mock
                service_mock = MagicMock()
                service_mock.get_file_info.return_value = file_info
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

                # Mock the operations.utils.get_file_info function
                with patch(
                    "quackcore.integrations.pandoc.operations.utils.get_file_info"
                ) as mock_get_info:
                    # Return a proper FileInfo object
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
                    mock_get_info.assert_called_with(input_path)

    def test_convert_file_directory_creation_failure(self, converter):
        """Test conversion when directory creation fails."""
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup directory creation to fail
                mock_fs.create_directory.return_value = OperationResult(
                    success=False,
                    path="/path/to/output",
                    error="Permission denied",
                )

                # Setup FileInfo for both direct and service calls
                file_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=1024,
                )
                mock_fs.get_file_info.return_value = file_info

                # Setup service mock
                service_mock = MagicMock()
                service_mock.get_file_info.return_value = file_info
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

                # Mock the operations.utils.get_file_info function
                with patch(
                    "quackcore.integrations.pandoc.operations.utils.get_file_info"
                ) as mock_get_info:
                    # Return a proper FileInfo object
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
                    mock_fs.create_directory.assert_called_once_with(
                        output_path.parent, exist_ok=True
                    )

    def test_convert_file_integration_error(self, converter):
        """Test conversion when an integration error occurs."""
        input_path = Path("/path/to/input.html")
        output_path = Path("/path/to/output/output.md")

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup FileInfo for both direct and service calls
                file_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=1024,
                )
                mock_fs.get_file_info.return_value = file_info

                # Setup service mock
                service_mock = MagicMock()
                service_mock.get_file_info.return_value = file_info
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

                # Mock the operations.utils.get_file_info function to raise an error
                with patch(
                    "quackcore.integrations.pandoc.operations.utils.get_file_info"
                ) as mock_get_info:
                    mock_get_info.side_effect = QuackIntegrationError("File not found")

                    # Test the conversion
                    result = converter.convert_file(input_path, output_path, "markdown")

                    # Assertions
                    assert result.success is False
                    assert "File not found" in result.error

    def test_convert_batch(self, converter):
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

        # Patch the fs object to mock file operations
        with patch("quackcore.fs.service.path_exists", return_value=True):
            # Mock the converter's fs module
            with patch("quackcore.integrations.pandoc.converter.fs") as mock_fs:
                # Setup directory creation
                mock_fs.create_directory.return_value = OperationResult(
                    success=True,
                    path="/path/to/output",
                    message="Directory created",
                )

                # Setup service mock
                service_mock = MagicMock()
                service_mock.path_exists.return_value = True
                mock_fs.service = service_mock

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

    def test_validate_conversion_markdown(self):
        """Test validation of a converted Markdown file."""
        # Create a fresh converter
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ):
            converter = DocumentConverter(PandocConfig())

        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file system operations at the service level
        with patch("quackcore.fs.service.path_exists", return_value=True):
            with patch("quackcore.fs.service.get_file_info") as mock_service_get_info:
                # Setup output and input file mocks for service calls
                output_info = FileInfoResult(
                    success=True,
                    path=str(output_path),
                    exists=True,
                    is_file=True,
                    size=512,
                )
                input_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=1024,
                )
                # Side effect for different calls
                mock_service_get_info.side_effect = [output_info, input_info]

                # Mock read_text
                with patch("quackcore.fs.service.read_text") as mock_read_text:
                    read_result = ReadResult(
                        success=True,
                        path=str(output_path),
                        content="# Test\n\nContent",
                        encoding="utf-8",
                    )
                    mock_read_text.return_value = read_result

                    # Mock fs.get_extension
                    with patch("quackcore.fs.get_extension") as mock_get_extension:
                        mock_get_extension.return_value = "md"

                        # Test validation
                        result = converter.validate_conversion(output_path, input_path)

                        # Assertions
                        assert result is True
                        # Make sure get_file_info was called twice - once for output, once for input
                        assert mock_service_get_info.call_count == 2

    def test_validate_conversion_docx(self):
        """Test validation of a converted DOCX file."""
        # Create a fresh converter
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ):
            converter = DocumentConverter(PandocConfig())

        output_path = Path("/path/to/output/file.docx")
        input_path = Path("/path/to/input.md")

        # Mock file system operations at the service level
        with patch("quackcore.fs.service.path_exists", return_value=True):
            with patch("quackcore.fs.service.get_file_info") as mock_service_get_info:
                # Setup output and input file mocks for service calls
                output_info = FileInfoResult(
                    success=True,
                    path=str(output_path),
                    exists=True,
                    is_file=True,
                    size=10240,
                )
                input_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=True,
                    is_file=True,
                    size=512,
                )
                # Side effect for different calls
                mock_service_get_info.side_effect = [output_info, input_info]

                # Mock fs.get_extension
                with patch("quackcore.fs.get_extension") as mock_get_extension:
                    mock_get_extension.return_value = "docx"

                    # Mock validate_docx_structure
                    with patch(
                        "quackcore.integrations.pandoc.operations.utils.validate_docx_structure"
                    ) as mock_validate_docx:
                        mock_validate_docx.return_value = (True, [])

                        # Test validation
                        result = converter.validate_conversion(output_path, input_path)

                        # Assertions
                        assert result is True
                        assert mock_service_get_info.call_count == 2
                        mock_validate_docx.assert_called_with(
                            output_path, converter.config.validation.check_links
                        )

    def test_validate_conversion_output_not_exists(self):
        """Test validation when output file doesn't exist."""
        # Create a fresh converter
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ):
            converter = DocumentConverter(PandocConfig())

        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file system operations at the service level
        with patch("quackcore.fs.service.path_exists") as mock_path_exists:
            # Let path_exists return False for output path, True for any other path
            mock_path_exists.side_effect = lambda p: str(p) != str(output_path)

            with patch("quackcore.fs.service.get_file_info") as mock_service_get_info:
                # Setup output file mock to indicate it doesn't exist
                output_info = FileInfoResult(
                    success=True,
                    path=str(output_path),
                    exists=False,
                    is_file=False,
                )
                mock_service_get_info.return_value = output_info

                # Test validation
                result = converter.validate_conversion(output_path, input_path)

                # Assertions
                assert result is False
                mock_service_get_info.assert_called_with(output_path)

    def test_validate_conversion_input_not_exists(self):
        """Test validation when input file doesn't exist."""
        # Create a fresh converter
        with patch(
            "quackcore.integrations.pandoc.converter.verify_pandoc",
            return_value="2.11.4",
        ):
            converter = DocumentConverter(PandocConfig())

        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/input.html")

        # Mock file system operations to control which files exist
        with patch("quackcore.fs.service.path_exists") as mock_path_exists:
            # Let path_exists return False for input path, True for any other path
            mock_path_exists.side_effect = lambda p: str(p) != str(input_path)

            with patch("quackcore.fs.service.get_file_info") as mock_service_get_info:
                # Setup output and input file mocks
                output_info = FileInfoResult(
                    success=True,
                    path=str(output_path),
                    exists=True,
                    is_file=True,
                    size=100,
                )
                input_info = FileInfoResult(
                    success=True,
                    path=str(input_path),
                    exists=False,
                    is_file=False,
                )
                # First call for output, second for input
                mock_service_get_info.side_effect = [output_info, input_info]

                # Test validation
                result = converter.validate_conversion(output_path, input_path)

                # Assertions
                assert result is False
                assert mock_service_get_info.call_count == 2
