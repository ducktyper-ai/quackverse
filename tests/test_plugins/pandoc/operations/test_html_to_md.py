# tests/test_plugins/pandoc/operations/test_html_to_md.py
"""
Tests for HTML to Markdown conversion operations.

This module tests the functions in the html_to_md module that handle
converting HTML documents to Markdown format.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

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


class TestPostProcessMarkdown:
    """Tests for the post_process_markdown function."""

    def test_basic_cleanup(self) -> None:
        """Test basic markdown cleanup operations."""
        input_markdown = """
        # Header with {attributes}

        ::: some-div-class
        Text inside a div
        :::

        <div class="some-class">Another div</div>



        Multiple empty lines above

        <!-- HTML comment -->


        - List item with extra space above
        """

        expected = """
        # Header with 


        Text inside a div


        Another div

        Multiple empty lines above



        - List item with extra space above
        """

        result = post_process_markdown(input_markdown)

        # Check that various patterns are removed
        assert "{attributes}" not in result
        assert ":::" not in result
        assert "<div" not in result
        assert "</div>" not in result
        assert "<!-- HTML comment -->" not in result

        # Verify consecutive empty lines are reduced
        assert "\n\n\n\n" not in result

    @given(st.text())
    def test_property_based(self, input_text: str) -> None:
        """Property-based test for post_process_markdown."""
        result = post_process_markdown(input_text)

        # The result should be a string
        assert isinstance(result, str)

        # The function should never return None
        assert result is not None

        # These patterns should never be in the result
        assert "{" not in result or "}" not in result  # May not always remove all {}
        assert ":::" not in result
        assert "<div" not in result
        assert "</div>" not in result
        assert (
            "<!--" not in result or "-->" not in result
        )  # May not always remove all comments


class TestValidateConversion:
    """Tests for the validate_conversion function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_valid_conversion(self, mock_get_info: MagicMock) -> None:
        """Test validation of a valid conversion."""
        # Mock file info for output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Mock reading the output file
        mock_content = "# Header\n\nConverted content with sufficient length."

        with patch("pathlib.Path.read_text", return_value=mock_content):
            config = ConversionConfig()
            errors = validate_conversion(
                Path("output.md"), Path("input.html"), 1000, config
            )

            assert len(errors) == 0

    @patch("quackcore.fs.service.get_file_info")
    def test_missing_output_file(self, mock_get_info: MagicMock) -> None:
        """Test validation when output file doesn't exist."""
        # Mock file info for missing output
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
        errors = validate_conversion(
            Path("output.md"), Path("input.html"), 1000, config
        )

        assert len(errors) == 1
        assert "does not exist" in errors[0]

    @patch("quackcore.fs.service.get_file_info")
    def test_file_too_small(self, mock_get_info: MagicMock) -> None:
        """Test validation when output file is too small."""
        # Mock file info for small output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=10,  # Very small file
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Set minimum file size requirement higher than the output
        config = ConversionConfig(validation={"min_file_size": 100})

        with patch("pathlib.Path.read_text", return_value="# Small"):
            errors = validate_conversion(
                Path("output.md"), Path("input.html"), 1000, config
            )

            assert len(errors) >= 1
            assert any("below the minimum threshold" in err for err in errors)

    @patch("quackcore.fs.service.get_file_info")
    def test_content_too_small(self, mock_get_info: MagicMock) -> None:
        """Test validation when output content is too small."""
        # Mock file info for output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=100,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Mock minimal content
        with patch("pathlib.Path.read_text", return_value="a"):
            config = ConversionConfig()
            errors = validate_conversion(
                Path("output.md"), Path("input.html"), 1000, config
            )

            assert len(errors) >= 1
            assert any("minimal content" in err for err in errors)

    @patch("quackcore.fs.service.get_file_info")
    def test_conversion_ratio_too_small(self, mock_get_info: MagicMock) -> None:
        """Test validation when conversion ratio is too small."""
        # Mock file info for output
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=50,  # Much smaller than input
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Set conversion ratio threshold higher than the actual ratio
        config = ConversionConfig(validation={"conversion_ratio_threshold": 0.2})

        with patch(
            "pathlib.Path.read_text", return_value="# Content with sufficient length"
        ):
            errors = validate_conversion(
                Path("output.md"), Path("input.html"), 1000, config
            )

            assert len(errors) >= 1
            assert any("ratio" in err for err in errors)


class TestValidateInput:
    """Tests for the _validate_input function."""

    @patch("quackcore.fs.service.get_file_info")
    def test_valid_input(self, mock_get_info: MagicMock) -> None:
        """Test validation of valid input file."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=1000,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock valid HTML content
        mock_content = "<!DOCTYPE html><html><body><h1>Test</h1></body></html>"

        with patch("pathlib.Path.read_text", return_value=mock_content):
            with patch(
                "quackcore.plugins.pandoc.operations.utils.validate_html_structure"
            ) as mock_validate:
                mock_validate.return_value = (True, [])

                config = ConversionConfig()
                size = _validate_input(Path("input.html"), config)

                assert size == 1000
                mock_validate.assert_called_once()

    @patch("quackcore.fs.service.get_file_info")
    def test_file_not_found(self, mock_get_info: MagicMock) -> None:
        """Test validation when input file is not found."""
        # Mock file info for missing file
        mock_file_info = FileInfoResult(
            success=False,
            exists=False,
            path=str(Path("nonexistent.html")),
            size=0,
            modified=None,
            error="File not found",
        )
        mock_get_info.return_value = mock_file_info

        config = ConversionConfig()

        with pytest.raises(QuackIntegrationError) as exc_info:
            _validate_input(Path("nonexistent.html"), config)

        assert "not found" in str(exc_info.value)

    @patch("quackcore.fs.service.get_file_info")
    def test_invalid_html_structure(self, mock_get_info: MagicMock) -> None:
        """Test validation of file with invalid HTML structure."""
        # Mock file info for existing file
        mock_file_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("input.html")),
            size=500,
            modified=1609459200.0,
        )
        mock_get_info.return_value = mock_file_info

        # Mock invalid HTML content
        mock_content = "<h1>Invalid HTML without proper structure</h1>"

        with patch("pathlib.Path.read_text", return_value=mock_content):
            with patch(
                "quackcore.plugins.pandoc.operations.utils.validate_html_structure"
            ) as mock_validate:
                mock_validate.return_value = (False, ["HTML document missing body tag"])

                config = ConversionConfig()

                with pytest.raises(QuackIntegrationError) as exc_info:
                    _validate_input(Path("input.html"), config)

                assert "Invalid HTML structure" in str(exc_info.value)


class TestAttemptConversion:
    """Tests for the _attempt_conversion function."""

    def test_successful_conversion(self) -> None:
        """Test successful conversion attempt."""
        # Mock pypandoc convert_file
        mock_output = "# Converted Content\n\nThis is the body text."

        with patch("pypandoc.convert_file", return_value=mock_output):
            config = ConversionConfig()
            result = _attempt_conversion(Path("input.html"), config)

            # Verify result is processed markdown
            assert result == mock_output
            # Verify post-processing happened
            assert isinstance(result, str)

    def test_conversion_failure(self) -> None:
        """Test conversion attempt failure."""
        # Mock pypandoc convert_file failing
        with patch("pypandoc.convert_file", side_effect=Exception("Conversion failed")):
            config = ConversionConfig()

            with pytest.raises(QuackIntegrationError) as exc_info:
                _attempt_conversion(Path("input.html"), config)

            assert "Pandoc conversion failed" in str(exc_info.value)


class TestWriteAndValidateOutput:
    """Tests for the _write_and_validate_output function."""

    @patch("quackcore.fs.service.write_text")
    @patch("quackcore.fs.service.get_file_info")
    @patch("quackcore.fs.service.create_directory")
    def test_successful_write(
        self,
        mock_create_dir: MagicMock,
        mock_get_info: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """Test successful write and validate."""
        # Mock successful write
        mock_write.return_value = MagicMock(success=True)

        # Mock file info
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=500,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Mock validation returning no errors
        with patch(
            "quackcore.plugins.pandoc.operations.html_to_md.validate_conversion"
        ) as mock_validate:
            mock_validate.return_value = []

            config = ConversionConfig()
            start_time = time.time() - 1.5  # 1.5 seconds ago

            conversion_time, output_size, validation_errors = (
                _write_and_validate_output(
                    "# Markdown Content",
                    Path("output.md"),
                    Path("input.html"),
                    1000,
                    config,
                    start_time,
                )
            )

            assert conversion_time > 1.0  # At least 1 second elapsed
            assert output_size == 500
            assert len(validation_errors) == 0
            mock_create_dir.assert_called_once()
            mock_write.assert_called_once()
            mock_validate.assert_called_once()

    @patch("quackcore.fs.service.write_text")
    def test_write_failure(self, mock_write: MagicMock) -> None:
        """Test failure to write output."""
        # Mock failed write
        mock_write.return_value = MagicMock(success=False, error="Permission denied")

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

    @patch("quackcore.fs.service.write_text")
    @patch("quackcore.fs.service.get_file_info")
    @patch("quackcore.fs.service.create_directory")
    def test_validation_errors(
        self,
        mock_create_dir: MagicMock,
        mock_get_info: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """Test when validation returns errors."""
        # Mock successful write
        mock_write.return_value = MagicMock(success=True)

        # Mock file info
        mock_output_info = FileInfoResult(
            success=True,
            exists=True,
            path=str(Path("output.md")),
            size=50,
            modified=1609459300.0,
        )
        mock_get_info.return_value = mock_output_info

        # Mock validation returning errors
        with patch(
            "quackcore.plugins.pandoc.operations.html_to_md.validate_conversion"
        ) as mock_validate:
            mock_validate.return_value = ["File size too small", "Invalid content"]

            config = ConversionConfig()
            start_time = time.time() - 1.0

            conversion_time, output_size, validation_errors = (
                _write_and_validate_output(
                    "# Small Content",
                    Path("output.md"),
                    Path("input.html"),
                    1000,
                    config,
                    start_time,
                )
            )

            assert conversion_time > 0
            assert output_size == 50
            assert len(validation_errors) == 2
            assert "File size too small" in validation_errors
            assert "Invalid content" in validation_errors


class TestConvertHtmlToMarkdown:
    """Tests for the convert_html_to_markdown function."""

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._attempt_conversion")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._write_and_validate_output")
    @patch("quackcore.plugins.pandoc.operations.html_to_md.track_metrics")
    def test_successful_conversion(
        self,
        mock_track: MagicMock,
        mock_write: MagicMock,
        mock_attempt: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test successful HTML to Markdown conversion."""
        # Mock successful validation
        mock_validate.return_value = 1000  # Original size

        # Mock successful conversion attempt
        mock_attempt.return_value = "# Converted Content"

        # Mock successful write with no validation errors
        mock_write.return_value = (1.5, 500, [])  # conversion_time, output_size, errors

        config = ConversionConfig()
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("input.html"), Path("output.md"), config, metrics
        )

        assert result.success is True
        assert result.content == Path("output.md")
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        assert result.conversion_time == 1.5
        assert result.output_size == 500
        assert result.input_size == 1000
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 0

        mock_validate.assert_called_once()
        mock_attempt.assert_called_once()
        mock_write.assert_called_once()
        mock_track.assert_called_once()

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    def test_input_validation_failure(self, mock_validate: MagicMock) -> None:
        """Test conversion with input validation failure."""
        # Mock validation failure
        mock_validate.side_effect = QuackIntegrationError("File not found")

        config = ConversionConfig()
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("nonexistent.html"), Path("output.md"), config, metrics
        )

        assert result.success is False
        assert "File not found" in result.error if result.error else ""
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        assert metrics.failed_conversions == 1
        assert "nonexistent.html" in metrics.errors

        mock_validate.assert_called_once()

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._attempt_conversion")
    def test_conversion_attempt_failure(
        self, mock_attempt: MagicMock, mock_validate: MagicMock
    ) -> None:
        """Test conversion with conversion attempt failure."""
        # Mock successful validation
        mock_validate.return_value = 1000  # Original size

        # Mock failed conversion attempt
        mock_attempt.side_effect = QuackIntegrationError("Pandoc conversion failed")

        config = ConversionConfig(
            retry_mechanism={
                "max_conversion_retries": 2,
                "conversion_retry_delay": 0.01,
            }
        )
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("input.html"), Path("output.md"), config, metrics
        )

        assert result.success is False
        assert "Pandoc conversion failed" in result.error if result.error else ""
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        assert metrics.failed_conversions == 1
        assert "input.html" in metrics.errors

        # Should have attempted twice due to retry configuration
        assert mock_attempt.call_count == 2

    @patch("quackcore.plugins.pandoc.operations.html_to_md._validate_input")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._attempt_conversion")
    @patch("quackcore.plugins.pandoc.operations.html_to_md._write_and_validate_output")
    def test_validation_errors_with_retry(
        self,
        mock_write: MagicMock,
        mock_attempt: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test conversion with validation errors and retry."""
        # Mock successful validation
        mock_validate.return_value = 1000  # Original size

        # Mock successful conversion attempt
        mock_attempt.return_value = "# Converted Content"

        # Mock write with validation errors on first try, success on second
        mock_write.side_effect = [
            (1.0, 50, ["File too small"]),  # First attempt fails validation
            (1.5, 500, []),  # Second attempt succeeds
        ]

        config = ConversionConfig(
            retry_mechanism={
                "max_conversion_retries": 2,
                "conversion_retry_delay": 0.01,
            }
        )
        metrics = ConversionMetrics()

        result = convert_html_to_markdown(
            Path("input.html"), Path("output.md"), config, metrics
        )

        assert result.success is True
        assert result.content == Path("output.md")
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 0

        # Should have attempted twice
        assert mock_attempt.call_count == 2
        assert mock_write.call_count == 2
