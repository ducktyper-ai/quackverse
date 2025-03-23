# tests/test_plugins/pandoc/test_converter.py
"""
Tests for pandoc converter implementation.

This module tests the DocumentConverter class, which is responsible for
converting documents between formats using pandoc.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.converter import DocumentConverter
from quackcore.plugins.pandoc.models import (
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
    FileInfo,
)


class TestDocumentConverter:
    """Tests for the DocumentConverter class."""

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_initialization(self, mock_verify: MagicMock) -> None:
        """Test basic initialization of the converter."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        assert converter.config == config
        assert isinstance(converter.metrics, ConversionMetrics)
        assert converter.pandoc_version == "2.18"
        mock_verify.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_initialization_failure(self, mock_verify: MagicMock) -> None:
        """Test initialization failure when pandoc is not available."""
        mock_verify.side_effect = QuackIntegrationError("Pandoc not found")

        config = ConversionConfig()

        with pytest.raises(QuackIntegrationError) as exc_info:
            DocumentConverter(config)

        assert "Pandoc not found" in str(exc_info.value)
        mock_verify.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    @patch("quackcore.fs.service.create_directory")
    @patch("quackcore.plugins.pandoc.converter.convert_html_to_markdown")
    def test_convert_file_html_to_markdown(
        self,
        mock_convert: MagicMock,
        mock_create_dir: MagicMock,
        mock_get_info: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """Test converting a file from HTML to Markdown."""
        mock_verify.return_value = "2.18"

        # Mock file info
        mock_info = FileInfo(path=Path("test.html"), format="html", size=1000)
        mock_get_info.return_value = mock_info

        # Mock successful conversion
        expected_result = ConversionResult.success_result(
            Path("output.md"),
            "html",
            "markdown",
            1.5,
            500,
            1000,
            "Successfully converted",
        )
        mock_convert.return_value = expected_result

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(
            Path("test.html"), Path("output.md"), "markdown"
        )

        assert result == expected_result
        mock_get_info.assert_called_once_with(Path("test.html"))
        mock_create_dir.assert_called_once()
        mock_convert.assert_called_once_with(
            Path("test.html"), Path("output.md"), config, converter.metrics
        )

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    @patch("quackcore.fs.service.create_directory")
    @patch("quackcore.plugins.pandoc.converter.convert_markdown_to_docx")
    def test_convert_file_markdown_to_docx(
        self,
        mock_convert: MagicMock,
        mock_create_dir: MagicMock,
        mock_get_info: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """Test converting a file from Markdown to DOCX."""
        mock_verify.return_value = "2.18"

        # Mock file info
        mock_info = FileInfo(path=Path("test.md"), format="markdown", size=500)
        mock_get_info.return_value = mock_info

        # Mock successful conversion
        expected_result = ConversionResult.success_result(
            Path("output.docx"),
            "markdown",
            "docx",
            1.8,
            800,
            500,
            "Successfully converted",
        )
        mock_convert.return_value = expected_result

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(Path("test.md"), Path("output.docx"), "docx")

        assert result == expected_result
        mock_get_info.assert_called_once_with(Path("test.md"))
        mock_create_dir.assert_called_once()
        mock_convert.assert_called_once_with(
            Path("test.md"), Path("output.docx"), config, converter.metrics
        )

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    def test_convert_file_unsupported_conversion(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test converting between unsupported formats."""
        mock_verify.return_value = "2.18"

        # Mock file info for PDF file
        mock_info = FileInfo(path=Path("test.pdf"), format="pdf", size=1000)
        mock_get_info.return_value = mock_info

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(Path("test.pdf"), Path("output.docx"), "docx")

        assert result.success is False
        assert "Unsupported conversion" in result.error if result.error else ""
        assert result.source_format == "pdf"
        assert result.target_format == "docx"

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    def test_convert_file_file_not_found(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test conversion when input file is not found."""
        mock_verify.return_value = "2.18"

        # Mock file info error
        mock_get_info.side_effect = QuackIntegrationError("File not found")

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(
            Path("nonexistent.html"), Path("output.md"), "markdown"
        )

        assert result.success is False
        assert "File not found" in result.error if result.error else ""
        mock_get_info.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion of multiple files."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Set up mock for convert_file
        successful_result = ConversionResult.success_result(
            Path("output.md"),
            "html",
            "markdown",
            1.5,
            500,
            1000,
            "Successfully converted",
        )

        with patch.object(converter, "convert_file", return_value=successful_result):
            # Create test tasks
            task1 = ConversionTask(
                source=FileInfo(path=Path("file1.html"), format="html"),
                target_format="markdown",
                output_path=Path("file1.md"),
            )
            task2 = ConversionTask(
                source=FileInfo(path=Path("file2.html"), format="html"),
                target_format="markdown",
                output_path=Path("file2.md"),
            )

            tasks = [task1, task2]
            result = converter.convert_batch(tasks)

            assert result.success is True
            assert len(result.successful_files) == 2
            assert len(result.failed_files) == 0
            assert converter.metrics.successful_conversions == 2
            assert converter.metrics.failed_conversions == 0
            mock_create_dir.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_mixed_results(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion with mixed success and failure."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Set up mock for convert_file to return success for first file, failure for second
        successful_result = ConversionResult.success_result(
            Path("file1.md"),
            "html",
            "markdown",
            1.5,
            500,
            1000,
            "Successfully converted",
        )

        failed_result = ConversionResult.error_result(
            "Conversion failed",
            source_format="html",
            target_format="markdown",
        )

        # Create test tasks
        task1 = ConversionTask(
            source=FileInfo(path=Path("file1.html"), format="html"),
            target_format="markdown",
            output_path=Path("file1.md"),
        )
        task2 = ConversionTask(
            source=FileInfo(path=Path("file2.html"), format="html"),
            target_format="markdown",
            output_path=Path("file2.md"),
        )

        tasks = [task1, task2]

        with patch.object(
            converter, "convert_file", side_effect=[successful_result, failed_result]
        ):
            result = converter.convert_batch(tasks)

            assert result.success is True  # Partially successful
            assert len(result.successful_files) == 1
            assert len(result.failed_files) == 1
            assert converter.metrics.successful_conversions == 1
            assert converter.metrics.failed_conversions == 1
            assert "Partially successful" in result.message if result.message else ""

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_all_failed(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion with all failures."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Set up mock for convert_file to always fail
        failed_result = ConversionResult.error_result(
            "Conversion failed",
            source_format="html",
            target_format="markdown",
        )

        # Create test tasks
        task1 = ConversionTask(
            source=FileInfo(path=Path("file1.html"), format="html"),
            target_format="markdown",
            output_path=Path("file1.md"),
        )
        task2 = ConversionTask(
            source=FileInfo(path=Path("file2.html"), format="html"),
            target_format="markdown",
            output_path=Path("file2.md"),
        )

        tasks = [task1, task2]

        with patch.object(converter, "convert_file", return_value=failed_result):
            result = converter.convert_batch(tasks)

            assert result.success is False
            assert len(result.successful_files) == 0
            assert len(result.failed_files) == 2
            assert converter.metrics.successful_conversions == 0
            assert converter.metrics.failed_conversions == 2
            assert "Failed to convert any files" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.get_file_info")
    def test_validate_conversion_success(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test successful validation of converted file."""
        mock_verify.return_value = "2.18"

        # Mock file info for both input and output
        mock_input_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("test.html")),
            size=1000,
            modified=1609459200.0,
        )
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )

        mock_get_info.side_effect = [mock_input_info, mock_output_info]

        config = ConversionConfig()
        converter = DocumentConverter(config)

        with patch("pathlib.Path.read_text", return_value="# Converted content"):
            assert (
                converter.validate_conversion(Path("output.md"), Path("test.html"))
                is True
            )

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.get_file_info")
    def test_validate_conversion_missing_output(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test validation when output file is missing."""
        mock_verify.return_value = "2.18"

        # Mock file info for output file not existing
        mock_output_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("output.md")),
            size=0,
            modified=None,
            error="File not found",
        )

        mock_get_info.return_value = mock_output_info

        config = ConversionConfig()
        converter = DocumentConverter(config)

        assert (
            converter.validate_conversion(Path("output.md"), Path("test.html")) is False
        )

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.get_file_info")
    def test_validate_conversion_missing_input(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test validation when input file is missing."""
        mock_verify.return_value = "2.18"

        # Mock file info: output exists but input doesn't
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )
        mock_input_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("test.html")),
            size=0,
            modified=None,
            error="File not found",
        )

        mock_get_info.side_effect = [mock_output_info, mock_input_info]

        config = ConversionConfig()
        converter = DocumentConverter(config)

        assert (
            converter.validate_conversion(Path("output.md"), Path("test.html")) is False
        )

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.get_file_info")
    def test_validate_conversion_docx(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test validation of DOCX output."""
        mock_verify.return_value = "2.18"

        # Mock file info for both input and output
        mock_input_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("test.md")),
            size=500,
            modified=1609459200.0,
        )
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=800,
            modified=1609459300.0,
        )

        mock_get_info.side_effect = [mock_output_info, mock_input_info]

        config = ConversionConfig()
        converter = DocumentConverter(config)

        with patch(
            "quackcore.plugins.pandoc.operations.utils.validate_docx_structure"
        ) as mock_validate:
            mock_validate.return_value = (True, [])
            assert (
                converter.validate_conversion(Path("output.docx"), Path("test.md"))
                is True
            )
            mock_validate.assert_called_once()

    @given(
        st.integers(min_value=1, max_value=10), st.integers(min_value=0, max_value=10)
    )
    def test_convert_batch_property_based(
        self, success_count: int, failure_count: int
    ) -> None:
        """Property-based test for batch conversion with varying success/failure counts."""
        with patch("quackcore.plugins.pandoc.converter.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.18"

            config = ConversionConfig()
            converter = DocumentConverter(config)

            # Create tasks based on counts
            tasks = []
            for i in range(success_count + failure_count):
                tasks.append(
                    ConversionTask(
                        source=FileInfo(path=Path(f"file{i}.html"), format="html"),
                        target_format="markdown",
                        output_path=Path(f"file{i}.md"),
                    )
                )

            # Create mock results
            results = []
            for i in range(success_count):
                results.append(
                    ConversionResult.success_result(
                        Path(f"file{i}.md"),
                        "html",
                        "markdown",
                        1.0,
                        500,
                        1000,
                        "Success",
                    )
                )

            for i in range(failure_count):
                results.append(
                    ConversionResult.error_result(
                        "Failed",
                        source_format="html",
                        target_format="markdown",
                    )
                )

            with patch.object(converter, "convert_file", side_effect=results):
                with patch("quackcore.fs.service.create_directory"):
                    result = converter.convert_batch(tasks)

                    # Verify counts match expected values
                    assert len(result.successful_files) == success_count
                    assert len(result.failed_files) == failure_count
                    assert converter.metrics.successful_conversions == success_count
                    assert converter.metrics.failed_conversions == failure_count

                    # Check overall success/failure status
                    if success_count > 0 and failure_count == 0:
                        assert result.success is True
                        assert (
                            "Successfully converted" in result.message
                            if result.message
                            else ""
                        )
                    elif success_count > 0 and failure_count > 0:
                        assert result.success is True
                        assert (
                            "Partially successful" in result.message
                            if result.message
                            else ""
                        )
                    else:
                        assert result.success is False
                        assert (
                            "Failed to convert" in result.error if result.error else ""
                        )
