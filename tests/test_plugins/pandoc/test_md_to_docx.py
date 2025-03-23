# tests/test_plugins/pandoc/operations/test_md_to_docx.py
"""
Tests for Markdown to DOCX conversion operations.

This module tests the functions in the md_to_docx module that handle
converting Markdown documents to DOCX format.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import ConversionMetrics
from quackcore.plugins.pandoc.operations.md_to_docx import (
    convert_markdown_to_docx,
    validate_conversion,
    _validate_markdown_input,
    _convert_markdown_to_docx_once,
    _get_conversion_output,
    _check_docx_metadata,
)


class TestValidateMarkdownInput:
    """Tests for the _validate_markdown_input function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_valid_markdown(self, mock_get_info: MagicMock) -> None:
        """Test validation of valid Markdown file."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.md")),
            size=500,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock valid markdown content
        mock_content = "# Test Markdown\n\nThis is a paragraph."

        with patch("pathlib.Path.read_text", return_value=mock_content):
            size = _validate_markdown_input(Path("input.md"))

            assert size == 500
            mock_get_info.assert_called_once()

    @patch("quackcore.fs.service.get_file_info")
    def test_file_not_found(self, mock_get_info: MagicMock) -> None:
        """Test validation when Markdown file is not found."""
        # Mock file info for missing file
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("nonexistent.md")),
            size=0,
            modified=None,
            error="File not found",
        )
        mock_get_info.return_value = mock_file_info

        with pytest.raises(QuackIntegrationError) as exc_info:
            _validate_markdown_input(Path("nonexistent.md"))

        assert "Input file not found" in str(exc_info.value)
        mock_get_info.assert_called_once()

    @patch("quackcore.fs.service.get_file_info")
    def test_empty_markdown(self, mock_get_info: MagicMock) -> None:
        """Test validation of empty Markdown file."""
        # Mock file info for existing but empty file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("empty.md")),
            size=0,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock empty markdown content
        with patch("pathlib.Path.read_text", return_value=""):
            with pytest.raises(QuackIntegrationError) as exc_info:
                _validate_markdown_input(Path("empty.md"))

            assert "Markdown file is empty" in str(exc_info.value)
            mock_get_info.assert_called_once()


class TestConvertMarkdownToDocxOnce:
    """Tests for the _convert_markdown_to_docx_once function."""

    @patch("pypandoc.convert_file")
    @patch("quackcore.fs.service.create_directory")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.prepare_pandoc_args")
    def test_successful_conversion(
            self, mock_prepare_args: MagicMock, mock_create_dir: MagicMock,
            mock_convert: MagicMock
    ) -> None:
        """Test successful single conversion attempt."""
        # Mock prepare_pandoc_args
        mock_prepare_args.return_value = ["--standalone"]

        config = ConversionConfig()

        # Call function (should not raise any exceptions)
        _convert_markdown_to_docx_once(Path("input.md"), Path("output.docx"), config)

        # Verify function calls
        mock_prepare_args.assert_called_once()
        mock_create_dir.assert_called_once()
        mock_convert.assert_called_once_with(
            str(Path("input.md")),
            "docx",
            format="markdown",
            outputfile=str(Path("output.docx")),
            extra_args=["--standalone"],
        )

    @patch("pypandoc.convert_file")
    @patch("quackcore.fs.service.create_directory")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.prepare_pandoc_args")
    def test_conversion_failure(
            self, mock_prepare_args: MagicMock, mock_create_dir: MagicMock,
            mock_convert: MagicMock
    ) -> None:
        """Test conversion failure."""
        # Mock prepare_pandoc_args
        mock_prepare_args.return_value = ["--standalone"]

        # Mock convert_file to fail
        mock_convert.side_effect = Exception("Conversion failed")

        config = ConversionConfig()

        with pytest.raises(QuackIntegrationError) as exc_info:
            _convert_markdown_to_docx_once(Path("input.md"), Path("output.docx"),
                                           config)

        assert "Pandoc conversion failed" in str(exc_info.value)
        mock_prepare_args.assert_called_once()
        mock_create_dir.assert_called_once()
        mock_convert.assert_called_once()


class TestGetConversionOutput:
    """Tests for the _get_conversion_output function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_successful_output(self, mock_get_info: MagicMock) -> None:
        """Test getting successful conversion output."""
        # Mock file info for output file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=800,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_file_info

        start_time = time.time() - 2.0  # 2 seconds ago

        conversion_time, output_size = _get_conversion_output(Path("output.docx"),
                                                              start_time)

        assert conversion_time >= 1.9  # At least close to 2 seconds
        assert output_size == 800
        mock_get_info.assert_called_once()

    @patch("quackcore.fs.service.get_file_info")
    def test_output_file_info_failure(self, mock_get_info: MagicMock) -> None:
        """Test when getting output file info fails."""
        # Mock file info failure
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("output.docx")),
            size=0,
            modified=None,
            error="Failed to get file info",
        )
        mock_get_info.return_value = mock_file_info

        start_time = time.time()

        with pytest.raises(QuackIntegrationError) as exc_info:
            _get_conversion_output(Path("output.docx"), start_time)

        assert "Failed to get info for converted file" in str(exc_info.value)
        mock_get_info.assert_called_once()


class TestValidateConversion:
    """Tests for the validate_conversion function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_valid_conversion(self, mock_get_info: MagicMock) -> None:
        """Test validation of a valid conversion."""
        # Mock file info for output
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=800,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_file_info

        with patch(
                "quackcore.plugins.pandoc.operations.md_to_docx.validate_docx_structure") as mock_validate:
            mock_validate.return_value = (True, [])

            config = ConversionConfig()
            errors = validate_conversion(
                Path("output.docx"), Path("input.md"), 500, config
            )

            assert len(errors) == 0
            mock_validate.assert_called_once()

    @patch("quackcore.fs.service.get_file_info")
    def test_missing_output_file(self, mock_get_info: MagicMock) -> None:
        """Test validation when output file doesn't exist."""
        # Mock file info for missing output
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("output.docx")),
            size=0,
            modified=None,
            error="File not found",
        )
        mock_get_info.return_value = mock_file_info

        config = ConversionConfig()
        errors = validate_conversion(
            Path("output.docx"), Path("input.md"), 500, config
        )

        assert len(errors) == 1
        assert "does not exist" in errors[0]

    @patch("quackcore.fs.service.get_file_info")
    def test_file_too_small(self, mock_get_info: MagicMock) -> None:
        """Test validation when output file is too small."""
        # Mock file info for small output
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=10,  # Very small file
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_file_info

        # Set minimum file size requirement higher than the output
        config = ConversionConfig(
            validation={"min_file_size": 100}
        )

        errors = validate_conversion(
            Path("output.docx"), Path("input.md"), 500, config
        )

        assert len(errors) >= 1
        assert any("below the minimum threshold" in err for err in errors)

    @patch("quackcore.fs.service.get_file_info")
    def test_structure_validation_failure(self, mock_get_info: MagicMock) -> None:
        """Test validation when DOCX structure is invalid."""
        # Mock file info for output
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=500,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_file_info

        with patch(
                "quackcore.plugins.pandoc.operations.md_to_docx.validate_docx_structure") as mock_validate:
            mock_validate.return_value = (False, ["DOCX document has no paragraphs"])

            config = ConversionConfig()
            errors = validate_conversion(
                Path("output.docx"), Path("input.md"), 500, config
            )

            assert len(errors) >= 1
            assert "DOCX document has no paragraphs" in errors
            mock_validate.assert_called_once()


class TestCheckDocxMetadata:
    """Tests for the _check_docx_metadata function."""

    def test_with_docx_module_missing(self) -> None:
        """Test when python-docx module is not available."""
        with patch("builtins.__import__",
                   side_effect=ImportError("No module named 'docx'")):
            # Should not raise exception, just log warning
            _check_docx_metadata(Path("output.docx"), Path("input.md"), True)

    @patch("docx.Document")
    def test_with_source_reference_found(self, mock_document: MagicMock) -> None:
        """Test when source reference is found in metadata."""
        # Mock Document
        mock_doc = MagicMock()
        mock_doc.core_properties.title = "Generated from input.md"
        mock_document.return_value = mock_doc

        # Should not raise exception or log warning
        _check_docx_metadata(Path("output.docx"), Path("input.md"), True)
        mock_document.assert_called_once_with(str(Path("output.docx")))

    @patch("docx.Document")
    def test_with_source_reference_missing(self, mock_document: MagicMock) -> None:
        """Test when source reference is missing in metadata."""
        # Mock Document
        mock_doc = MagicMock()
        mock_doc.core_properties.title = "Some other title"
        mock_doc.core_properties.comments = ""
        mock_doc.core_properties.subject = ""
        mock_document.return_value = mock_doc

        # Should not raise exception, just log a debug message
        with patch(
                "quackcore.plugins.pandoc.operations.md_to_docx.logger.debug") as mock_debug:
            _check_docx_metadata(Path("output.docx"), Path("input.md"), True)
            mock_debug.assert_called_once()
            assert "Source file reference missing" in mock_debug.call_args[0][0]

        mock_document.assert_called_once_with(str(Path("output.docx")))


class TestConvertMarkdownToDocx:
    """Tests for the convert_markdown_to_docx function."""

    @patch("quackcore.plugins.pandoc.operations.md_to_docx._validate_markdown_input")
    @patch(
        "quackcore.plugins.pandoc.operations.md_to_docx._convert_markdown_to_docx_once")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx._get_conversion_output")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.validate_conversion")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.track_metrics")
    def test_successful_conversion(
            self,
            mock_track: MagicMock,
            mock_validate: MagicMock,
            mock_get_output: MagicMock,
            mock_convert: MagicMock,
            mock_validate_input: MagicMock,
    ) -> None:
        """Test successful Markdown to DOCX conversion."""
        # Mock successful validation
        mock_validate_input.return_value = 500  # Original size

        # Mock successful output
        mock_get_output.return_value = (1.5, 800)  # conversion_time, output_size

        # Mock successful validation
        mock_validate.return_value = []  # No errors

        config = ConversionConfig()
        metrics = ConversionMetrics()

        result = convert_markdown_to_docx(
            Path("input.md"),
            Path("output.docx"),
            config,
            metrics
        )

        assert result.success is True
        assert result.content == Path("output.docx")
        assert result.source_format == "markdown"
        assert result.target_format == "docx"
        assert result.conversion_time == 1.5
        assert result.output_size == 800
        assert result.input_size == 500
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 0

        mock_validate_input.assert_called_once()
        mock_convert.assert_called_once()
        mock_get_output.assert_called_once()
        mock_validate.assert_called_once()
        mock_track.assert_called_once()

    @patch("quackcore.plugins.pandoc.operations.md_to_docx._validate_markdown_input")
    def test_input_validation_failure(self, mock_validate_input: MagicMock) -> None:
        """Test conversion with input validation failure."""
        # Mock validation failure
        mock_validate_input.side_effect = QuackIntegrationError("File not found")

        config = ConversionConfig()
        metrics = ConversionMetrics()

        result = convert_markdown_to_docx(
            Path("nonexistent.md"),
            Path("output.docx"),
            config,
            metrics
        )

        assert result.success is False
        assert "File not found" in result.error if result.error else ""
        assert result.source_format == "markdown"
        assert result.target_format == "docx"
        assert metrics.failed_conversions == 1
        assert "nonexistent.md" in metrics.errors

        mock_validate_input.assert_called_once()

    @patch("quackcore.plugins.pandoc.operations.md_to_docx._validate_markdown_input")
    @patch(
        "quackcore.plugins.pandoc.operations.md_to_docx._convert_markdown_to_docx_once")
    def test_conversion_failure(
            self, mock_convert: MagicMock, mock_validate_input: MagicMock
    ) -> None:
        """Test when conversion fails."""
        # Mock successful validation
        mock_validate_input.return_value = 500  # Original size

        # Mock conversion failure
        mock_convert.side_effect = QuackIntegrationError("Pandoc conversion failed")

        config = ConversionConfig(
            retry_mechanism={"max_conversion_retries": 2,
                             "conversion_retry_delay": 0.01}
        )
        metrics = ConversionMetrics()

        result = convert_markdown_to_docx(
            Path("input.md"),
            Path("output.docx"),
            config,
            metrics
        )

        assert result.success is False
        assert "Pandoc conversion failed" in result.error if result.error else ""
        assert result.source_format == "markdown"
        assert result.target_format == "docx"
        assert metrics.failed_conversions == 1
        assert "input.md" in metrics.errors

        # Should have attempted twice due to retry configuration
        assert mock_convert.call_count == 2

    @patch("quackcore.plugins.pandoc.operations.md_to_docx._validate_markdown_input")
    @patch(
        "quackcore.plugins.pandoc.operations.md_to_docx._convert_markdown_to_docx_once")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx._get_conversion_output")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.validate_conversion")
    def test_validation_errors(
            self,
            mock_validate: MagicMock,
            mock_get_output: MagicMock,
            mock_convert: MagicMock,
            mock_validate_input: MagicMock,
    ) -> None:
        """Test when conversion succeeds but validation fails."""
        # Mock successful validation
        mock_validate_input.return_value = 500  # Original size

        # Mock successful output
        mock_get_output.return_value = (1.5, 100)  # conversion_time, output_size

        # Mock validation errors
        mock_validate.return_value = ["File size too small"]

        config = ConversionConfig(
            retry_mechanism={"max_conversion_retries": 2,
                             "conversion_retry_delay": 0.01}
        )
        metrics = ConversionMetrics()

        result = convert_markdown_to_docx(
            Path("input.md"),
            Path("output.docx"),
            config,
            metrics
        )

        assert result.success is False
        assert "File size too small" in result.error if result.error else ""
        assert result.source_format == "markdown"
        assert result.target_format == "docx"
        assert metrics.failed_conversions == 1
        assert "input.md" in metrics.errors

        mock_validate_input.assert_called_once()
        mock_convert.assert_called_once()
        mock_get_output.assert_called_once()
        mock_validate.assert_called_once()