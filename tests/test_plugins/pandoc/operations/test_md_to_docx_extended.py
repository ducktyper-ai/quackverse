# tests/test_plugins/pandoc/operations/test_md_to_docx_extended.py
"""
Extended tests for Markdown to DOCX conversion operations.

This module provides additional tests for the md_to_docx module to increase
test coverage, focusing on previously untested code paths.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.operations.md_to_docx import (
    _check_docx_metadata,
    _convert_markdown_to_docx_once,
    _get_conversion_output,
    _validate_markdown_input,
    convert_markdown_to_docx,
    validate_conversion,
)


class TestValidateMarkdownInputExtended:
    """Extended tests for the _validate_markdown_input function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_read_error(self, mock_get_info: MagicMock) -> None:
        """Test handling of file read errors."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.md")),
            size=500,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock read_text to fail
        read_error = "Permission denied"
        with patch("pathlib.Path.read_text", side_effect=PermissionError(read_error)):
            # Should catch the error and check if it's a QuackIntegrationError
            # Since it's not, it should pass through to caller
            size = _validate_markdown_input(Path("input.md"))

            # Function should still return size as it catches non-QuackIntegrationErrors
            assert size == 500

    @patch("quackcore.fs.service.get_file_info")
    def test_empty_file_content(self, mock_get_info: MagicMock) -> None:
        """Test validation of file with whitespace-only content."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.md")),
            size=10,  # Size > 0 but content is just whitespace
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock empty markdown content (just whitespace)
        with patch("pathlib.Path.read_text", return_value="   \n\t   "):
            with pytest.raises(QuackIntegrationError) as exc_info:
                _validate_markdown_input(Path("input.md"))

            assert "Markdown file is empty" in str(exc_info.value)


class TestConvertMarkdownToDocxOnceExtended:
    """Extended tests for the _convert_markdown_to_docx_once function."""

    @patch("pypandoc.convert_file")
    @patch("quackcore.fs.service.create_directory")
    @patch("quackcore.plugins.pandoc.operations.md_to_docx.prepare_pandoc_args")
    def test_with_custom_args(
        self,
        mock_prepare_args: MagicMock,
        mock_create_dir: MagicMock,
        mock_convert: MagicMock,
    ) -> None:
        """Test conversion with custom arguments."""
        # Configure custom args
        custom_config = ConversionConfig()
        custom_config.md_to_docx_extra_args = [
            "--reference-doc=template.docx",
            "--custom-arg=value",
        ]

        # Mock prepare_pandoc_args
        mock_prepare_args.return_value = [
            "--standalone",
            "--reference-doc=template.docx",
            "--custom-arg=value",
        ]

        # Call function
        _convert_markdown_to_docx_once(
            Path("input.md"), Path("output.docx"), custom_config
        )

        # Verify args were passed to prepare_pandoc_args
        mock_prepare_args.assert_called_once_with(
            custom_config, "markdown", "docx", custom_config.md_to_docx_extra_args
        )

        # Verify convert_file was called with these args
        mock_convert.assert_called_once_with(
            str(Path("input.md")),
            "docx",
            format="markdown",
            outputfile=str(Path("output.docx")),
            extra_args=[
                "--standalone",
                "--reference-doc=template.docx",
                "--custom-arg=value",
            ],
        )

    @patch("pypandoc.convert_file")
    @patch("quackcore.fs.service.create_directory")
    def test_directory_creation_error(
        self, mock_create_dir: MagicMock, mock_convert: MagicMock
    ) -> None:
        """Test handling of directory creation errors."""
        # Mock create_directory to fail
        mock_create_dir.side_effect = PermissionError("Permission denied")

        config = ConversionConfig()

        # The function should let the exception propagate
        with pytest.raises(QuackIntegrationError) as exc_info:
            _convert_markdown_to_docx_once(
                Path("input.md"), Path("output.docx"), config
            )

        assert "Pandoc conversion failed" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)
        mock_convert.assert_not_called()


class TestGetConversionOutputExtended:
    """Extended tests for the _get_conversion_output function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_missing_output_file(self, mock_get_info: MagicMock) -> None:
        """Test when output file doesn't exist."""
        # Mock file info missing
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("output.docx")),
            size=0,
            modified=None,
            error="File not found",
        )
        mock_get_info.return_value = mock_file_info

        start_time = time.time()

        with pytest.raises(QuackIntegrationError) as exc_info:
            _get_conversion_output(Path("output.docx"), start_time)

        assert "Failed to get info for converted file" in str(exc_info.value)


class TestCheckDocxMetadataExtended:
    """Extended tests for the _check_docx_metadata function."""

    def test_core_properties_check(self) -> None:
        """Test detailed core properties checking."""
        # Create a mock with different metadata combinations
        with patch("docx.Document") as mock_document:
            # Case 1: Title contains source filename
            mock_doc1 = MagicMock()
            mock_doc1.core_properties.title = "Generated from source.md"
            mock_doc1.core_properties.comments = ""
            mock_doc1.core_properties.subject = ""

            # Case 2: Comments contain source filename
            mock_doc2 = MagicMock()
            mock_doc2.core_properties.title = "Some other title"
            mock_doc2.core_properties.comments = "Based on source.md"
            mock_doc2.core_properties.subject = ""

            # Case 3: Subject contains source filename
            mock_doc3 = MagicMock()
            mock_doc3.core_properties.title = "Some other title"
            mock_doc3.core_properties.comments = ""
            mock_doc3.core_properties.subject = "Converted from source.md"

            # Test each case
            mock_document.side_effect = [mock_doc1, mock_doc2, mock_doc3]

            for _ in range(3):
                # Should not raise exception
                _check_docx_metadata(Path("output.docx"), Path("source.md"), True)

            assert mock_document.call_count == 3

    @patch("docx.Document")
    def test_exception_handling(self, mock_document: MagicMock) -> None:
        """Test handling of exceptions during metadata check."""
        # Mock document to raise exception
        mock_document.side_effect = Exception("Document structure error")

        # Should not propagate the exception
        _check_docx_metadata(Path("output.docx"), Path("source.md"), True)

        mock_document.assert_called_once()

    def test_import_error_handling(self) -> None:
        """Test handling of import errors."""
        # Mock import error for docx module
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args: ImportError("No module named 'docx'")
            if name == "docx"
            else __import__(name, *args),
        ):
            # Should log a debug message but not raise exception
            _check_docx_metadata(Path("output.docx"), Path("source.md"), True)


class TestValidateConversionExtended:
    """Extended tests for the validate_conversion function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_validation_with_non_existent_output(
        self, mock_get_info: MagicMock
    ) -> None:
        """Test validation with a missing output file."""
        # Mock file info for missing output
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("output.docx")),
            size=0,
            modified=None,
            error="No such file",
        )
        mock_get_info.return_value = mock_file_info

        config = ConversionConfig()
        errors = validate_conversion(Path("output.docx"), Path("input.md"), 500, config)

        assert len(errors) == 1
        assert "does not exist" in errors[0]
        # Validation should stop after determining file doesn't exist

    @patch("quackcore.fs.service.get_file_info")
    def test_multiple_validation_failures(self, mock_get_info: MagicMock) -> None:
        """Test when multiple validation checks fail."""
        # Mock file info for small output
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.docx")),
            size=10,  # Very small file
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_file_info

        # Configure validation to generate multiple failures
        config = ConversionConfig(
            validation={
                "min_file_size": 1000,  # Much higher than our file size
                "conversion_ratio_threshold": 0.5,  # Much higher than our ratio
                "verify_structure": True,
            }
        )

        with patch(
            "quackcore.plugins.pandoc.operations.md_to_docx.validate_docx_structure"
        ) as mock_validate_docx:
            # Structure validation also fails
            mock_validate_docx.return_value = (
                False,
                ["DOCX missing required elements"],
            )

            errors = validate_conversion(
                Path("output.docx"), Path("input.md"), 500, config
            )

            # Should collect all validation errors
            assert len(errors) >= 3
            # Check for specific error messages
            assert any("below the minimum threshold" in err for err in errors)
            assert any("less than" in err for err in errors)
            assert "DOCX missing required elements" in errors
