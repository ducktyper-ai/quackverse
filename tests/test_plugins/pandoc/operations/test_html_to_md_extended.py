# tests/test_plugins/pandoc/operations/test_html_to_md_extended.py
"""
Extended tests for HTML to Markdown conversion operations.

This module provides additional tests for the html_to_md module to increase
test coverage, focusing on previously untested code paths.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import ConversionMetrics
from quackcore.plugins.pandoc.operations.html_to_md import (
    _attempt_conversion,
    _validate_input,
    _write_and_validate_output,
    convert_html_to_markdown,
    post_process_markdown,
    validate_conversion,
)


class TestPostProcessMarkdownExtended:
    """Extended tests for the post_process_markdown function."""

    def test_remove_complex_attributes(self) -> None:
        """Test removal of complex attributes in curly braces."""
        input_markdown = """
        # Header {#id .class attr="value"}

        Paragraph {.with-class data-attr="test"}
        """

        result = post_process_markdown(input_markdown)

        assert '{#id .class attr="value"}' not in result
        assert '{.with-class data-attr="test"}' not in result

    def test_remove_div_containers(self) -> None:
        """Test removal of div containers from markdown."""
        input_markdown = """
        ::: container
        Content inside container
        :::

        ::: {.special-class #custom-id}
        Content with attributes
        :::
        """

        result = post_process_markdown(input_markdown)

        assert "::: container" not in result
        assert "::: {.special-class #custom-id}" not in result
        assert ":::" not in result
        assert "Content inside container" in result
        assert "Content with attributes" in result

    def test_remove_html_comments(self) -> None:
        """Test removal of HTML comments."""
        input_markdown = """
        # Title

        <!-- This is a comment that should be removed -->

        Text <!-- inline comment --> continues here.

        <!--
        Multi-line
        comment
        -->
        """

        result = post_process_markdown(input_markdown)

        assert "<!-- This is a comment that should be removed -->" not in result
        assert "<!-- inline comment -->" not in result
        assert "<!--\nMulti-line\ncomment\n-->" not in result
        assert "Text  continues here." in result

    def test_reduce_consecutive_empty_lines(self) -> None:
        """Test reduction of multiple consecutive empty lines."""
        input_markdown = """
        # Title




        Paragraph after many empty lines.
        """

        result = post_process_markdown(input_markdown)

        # Should have reduced multiple blank lines
        assert "\n\n\n\n" not in result
        assert "# Title" in result
        assert "Paragraph after many empty lines." in result


class TestValidateInputExtended:
    """Extended tests for the _validate_input function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_validation_disabled(self, mock_get_info: MagicMock) -> None:
        """Test when structure validation is disabled."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=1000,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Turn off structure validation
        config = ConversionConfig()
        config.validation.verify_structure = False

        # Call function - with validation disabled,
        # it shouldn't call read_text or validate_html_structure
        with (
            patch("pathlib.Path.read_text") as mock_read_text,
            patch(
                "quackcore.plugins.pandoc.operations.utils.validate_html_structure"
            ) as mock_validate,
        ):
            size = _validate_input(Path("input.html"), config)

            assert size == 1000
            mock_read_text.assert_not_called()
            mock_validate.assert_not_called()

    @patch("quackcore.fs.service.get_file_info")
    def test_html_read_error(self, mock_get_info: MagicMock) -> None:
        """Test when HTML file cannot be read."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=500,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock read_text to fail
        read_error = "Permission denied"
        with (
            patch("pathlib.Path.read_text", side_effect=PermissionError(read_error)),
            patch(
                "quackcore.plugins.pandoc.operations.utils.validate_html_structure"
            ) as mock_validate,
        ):
            config = ConversionConfig()

            # Call should log warning but not raise error
            size = _validate_input(Path("input.html"), config)

            assert size == 500
            mock_validate.assert_not_called()


class TestAttemptConversionExtended:
    """Extended tests for the _attempt_conversion function."""

    def test_conversion_with_custom_args(self) -> None:
        """Test conversion with custom arguments."""
        # Create config with custom HTML to MD args
        config = ConversionConfig()
        config.html_to_md_extra_args = ["--custom-arg", "--another-arg=value"]

        # Mock prepare_pandoc_args to verify our custom args are included
        with (
            patch(
                "quackcore.plugins.pandoc.operations.html_to_md.prepare_pandoc_args"
            ) as mock_prepare_args,
            patch("pypandoc.convert_file", return_value="# Output"),
            patch(
                "quackcore.plugins.pandoc.operations.html_to_md.post_process_markdown",
                return_value="# Cleaned output",
            ),
        ):
            # Call function
            _attempt_conversion(Path("input.html"), config)

            # Verify prepare_pandoc_args was called with our config
            mock_prepare_args.assert_called_once_with(
                config, "html", "markdown", config.html_to_md_extra_args
            )


class TestWriteAndValidateOutputExtended:
    """Extended tests for the _write_and_validate_output function."""

    @patch("quackcore.fs.service.write_text")
    def test_write_error_handling(self, mock_write: MagicMock) -> None:
        """Test handling of write errors."""
        # Mock write_text to fail with a specific error
        write_error = "Disk full"
        mock_write.return_value = MagicMock(success=False, error=write_error)

        config = ConversionConfig()
        start_time = time.time()

        with pytest.raises(QuackIntegrationError) as exc_info:
            _write_and_validate_output(
                "# Markdown Content",
                Path("output.md"),
                Path("input.html"),
                1000,
                config,
                start_time,
            )

        assert "Failed to write output file" in str(exc_info.value)
        assert write_error in str(exc_info.value)


class TestValidateConversionExtended:
    """Extended tests for the validate_conversion function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_validation_with_check_links(self, mock_get_info: MagicMock) -> None:
        """Test validation with link checking enabled."""
        # Mock file info for output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Create markdown content without source reference
        markdown_content = "# Title\n\nContent without source reference"

        with patch("pathlib.Path.read_text", return_value=markdown_content):
            config = ConversionConfig()
            config.validation.check_links = True

            errors = validate_conversion(
                Path("output.md"), Path("source_file.html"), 1000, config
            )

            # Should not add to errors list, but should log a debug message
            assert len(errors) == 0

    @patch("quackcore.fs.service.get_file_info")
    def test_file_read_error(self, mock_get_info: MagicMock) -> None:
        """Test validation when output file can't be read."""
        # Mock file info for output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Mock read_text to fail
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Permission denied")
        ):
            config = ConversionConfig()

            errors = validate_conversion(
                Path("output.md"), Path("input.html"), 1000, config
            )

            assert len(errors) == 1
            assert "Error reading output file" in errors[0]


class TestConvertHtmlToMarkdownExtended:
    """Extended tests for the convert_html_to_markdown function."""

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._attempt_conversion")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._write_and_validate_output")
    def test_partial_success_then_failure(
        self,
        mock_write: MagicMock,
        mock_attempt: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test when initial attempts succeed but validation fails repeatedly."""
        # Mock successful validation
        mock_validate.return_value = 1000  # Original size

        # Mock successful conversion attempt
        mock_attempt.return_value = "# Converted Content"

        # First call returns validation errors, second call succeeds
        mock_write.side_effect = [
            (1.0, 200, ["Validation error 1"]),  # First try: has errors
            (1.5, 250, ["Validation error 2"]),  # Second try: still has errors
            (2.0, 300, ["Validation error 3"]),  # Third try: still has errors
        ]

        config = ConversionConfig(
            retry_mechanism={
                "max_conversion_retries": 3,
                "conversion_retry_delay": 0.01,
            }
        )
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("input.html"), Path("output.md"), config, metrics
        )

        # Should fail after 3 attempts
        assert result.success is False
        assert (
            "Conversion validation failed after maximum retries" in result.error
            if result.error
            else ""
        )
        assert mock_attempt.call_count == 3
        assert mock_write.call_count == 3
        assert metrics.failed_conversions == 1

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._attempt_conversion")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._write_and_validate_output")
    def test_failure_then_success(
        self,
        mock_write: MagicMock,
        mock_attempt: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test when first conversion attempt fails but second one succeeds."""
        # Mock successful validation
        mock_validate.return_value = 1000  # Original size

        # First attempt fails, second succeeds
        mock_attempt.side_effect = [
            QuackIntegrationError("First attempt failed"),
            "# Successful conversion",
        ]

        # Mock successful write with no validation errors
        mock_write.return_value = (1.5, 500, [])

        config = ConversionConfig(
            retry_mechanism={
                "max_conversion_retries": 3,
                "conversion_retry_delay": 0.01,
            }
        )
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("input.html"), Path("output.md"), config, metrics
        )

        assert result.success is True
        assert result.content == Path("output.md")
        assert mock_attempt.call_count == 2
        assert mock_write.call_count == 1
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 0
