# tests/test_plugins/pandoc/test_converter_extended.py
"""
Extended tests for pandoc converter implementation.

This module provides additional tests for the DocumentConverter class,
focusing on untested code paths to increase coverage.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.fs.results import FileInfoResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.converter import DocumentConverter, create_converter
from quackcore.plugins.pandoc.models import (
    ConversionResult,
    ConversionTask,
    FileInfo,
)


class TestDocumentConverterExtended:
    """Extended tests for the DocumentConverter class."""

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_create_converter_factory(self, mock_verify: MagicMock) -> None:
        """Test the create_converter factory function."""
        mock_verify.return_value = "2.19"

        config = ConversionConfig()
        converter = create_converter(config)

        assert isinstance(converter, DocumentConverter)
        assert converter.config == config
        assert converter.pandoc_version == "2.19"
        mock_verify.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    def test_convert_file_unsupported_source_format(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test convert_file with unsupported source format."""
        mock_verify.return_value = "2.18"

        # Mock file info for XML file (unsupported)
        mock_info = FileInfo(path=Path("test.xml"), format="xml", size=1000)
        mock_get_info.return_value = mock_info

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(Path("test.xml"), Path("output.docx"), "docx")

        assert result.success is False
        assert (
            "Unsupported conversion: xml to docx" in result.error
            if result.error
            else ""
        )
        assert result.source_format == "xml"
        assert result.target_format == "docx"
        mock_get_info.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.plugins.pandoc.converter.get_file_info")
    def test_convert_file_unexpected_error(
        self, mock_get_info: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test convert_file with an unexpected error."""
        mock_verify.return_value = "2.18"

        # Mock file info to raise unexpected error
        mock_get_info.side_effect = Exception("Unexpected error")

        config = ConversionConfig()
        converter = DocumentConverter(config)

        result = converter.convert_file(
            Path("test.html"), Path("output.md"), "markdown"
        )

        assert result.success is False
        assert (
            "Conversion error: Unexpected error" in result.error if result.error else ""
        )
        assert result.source_format is None
        assert result.target_format == "markdown"
        mock_get_info.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_empty_tasks(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion with empty task list."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Empty task list
        tasks = []
        result = converter.convert_batch(tasks)

        assert result.success is False
        assert "Failed to convert any files" in result.error if result.error else ""
        assert len(result.successful_files) == 0
        assert len(result.failed_files) == 0
        assert converter.metrics.successful_conversions == 0
        assert converter.metrics.failed_conversions == 0
        mock_create_dir.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_all_tasks_fail(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion where all tasks fail."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Create tasks
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

        # Mock convert_file to always fail
        failed_result = ConversionResult.error_result(
            "Conversion failed",
            source_format="html",
            target_format="markdown",
        )

        with patch.object(converter, "convert_file", return_value=failed_result):
            result = converter.convert_batch(tasks)

            assert result.success is False
            assert "Failed to convert any files" in result.error if result.error else ""
            assert len(result.successful_files) == 0
            assert len(result.failed_files) == 2
            assert converter.metrics.successful_conversions == 0
            assert converter.metrics.failed_conversions == 2
            assert Path("file1.html") in result.failed_files
            assert Path("file2.html") in result.failed_files
            mock_create_dir.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_mixed_results_with_exception(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion with mixed success, failure, and exception."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Create tasks
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
        task3 = ConversionTask(
            source=FileInfo(path=Path("file3.html"), format="html"),
            target_format="markdown",
            output_path=Path("file3.md"),
        )

        tasks = [task1, task2, task3]

        # Set up convert_file to return success for task1, fail for task2, and raise exception for task3
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

        def mock_convert_side_effect(input_path, output_path, format):
            if input_path == Path("file1.html"):
                return successful_result
            elif input_path == Path("file2.html"):
                return failed_result
            else:
                raise Exception("Unexpected test error")

        with patch.object(
            converter, "convert_file", side_effect=mock_convert_side_effect
        ):
            result = converter.convert_batch(tasks)

            assert result.success is True  # Partially successful
            assert "Partially successful" in result.message if result.message else ""
            assert len(result.successful_files) == 1
            assert len(result.failed_files) == 2
            assert converter.metrics.successful_conversions == 1
            assert converter.metrics.failed_conversions == 2
            assert Path("file1.md") in result.successful_files
            assert Path("file2.html") in result.failed_files
            assert Path("file3.html") in result.failed_files
            # The error for file3 should be recorded
            assert "file3.html" in converter.metrics.errors
            assert (
                "Unexpected test error"
                in converter.metrics.errors[str(Path("file3.html"))]
            )
            mock_create_dir.assert_called_once()

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_batch_with_output_dir_override(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test batch conversion with output directory override."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Create task with specific output path
        task = ConversionTask(
            source=FileInfo(path=Path("file1.html"), format="html"),
            target_format="markdown",
            output_path=Path("original/path/file1.md"),
        )

        tasks = [task]

        # Specify a different output directory
        override_output_dir = Path("/override/output/dir")

        # Mock convert_file to confirm the overridden path is used
        def mock_convert_file(input_path, output_path, output_format):
            assert output_path == override_output_dir / "file1.md"
            return ConversionResult.success_result(
                output_path, "html", "markdown", 1.0, 500, 1000
            )

        with patch.object(converter, "convert_file", side_effect=mock_convert_file):
            result = converter.convert_batch(tasks, override_output_dir)

            assert result.success is True
            assert len(result.successful_files) == 1
            mock_create_dir.assert_called_once_with(override_output_dir, exist_ok=True)

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_validate_conversion_markdown(self, mock_verify: MagicMock) -> None:
        """Test validation of Markdown conversion."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Mock file info
        input_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=1000,
            modified=1609459200.0,
        )

        output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )

        with (
            patch(
                "quackcore.fs.service.get_file_info",
                side_effect=[output_info, input_info],
            ),
            patch(
                "pathlib.Path.read_text",
                return_value="# Valid Markdown\n\nContent here",
            ),
        ):
            result = converter.validate_conversion(
                Path("output.md"), Path("input.html")
            )
            assert result is True

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_validate_conversion_empty_markdown(self, mock_verify: MagicMock) -> None:
        """Test validation of empty Markdown output."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Mock file info
        input_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=1000,
            modified=1609459200.0,
        )

        output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=0,  # Empty file
            modified=1609459300.0,
        )

        with (
            patch(
                "quackcore.fs.service.get_file_info",
                side_effect=[output_info, input_info],
            ),
            patch("pathlib.Path.read_text", return_value=""),
        ):
            result = converter.validate_conversion(
                Path("output.md"), Path("input.html")
            )
            assert result is False

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_validate_conversion_other_format(self, mock_verify: MagicMock) -> None:
        """Test validation of other format output."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Mock file info
        input_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=1000,
            modified=1609459200.0,
        )

        output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.pdf")),  # Non-docx, non-markdown
            size=2000,
            modified=1609459300.0,
        )

        with patch(
            "quackcore.fs.service.get_file_info", side_effect=[output_info, input_info]
        ):
            # For unknown formats, just check if the file exists with reasonable size
            result = converter.validate_conversion(
                Path("output.pdf"), Path("input.html")
            )
            assert result is True

    @patch("quackcore.plugins.pandoc.converter.verify_pandoc")
    def test_validate_conversion_error_handling(self, mock_verify: MagicMock) -> None:
        """Test error handling during validation."""
        mock_verify.return_value = "2.18"

        config = ConversionConfig()
        converter = DocumentConverter(config)

        # Mock an exception during validation
        with patch(
            "quackcore.fs.service.get_file_info",
            side_effect=Exception("Unexpected validation error"),
        ):
            result = converter.validate_conversion(
                Path("output.md"), Path("input.html")
            )
            assert (
                result is False
            )  # tests/test_plugins/pandoc/test_converter_extended.py
