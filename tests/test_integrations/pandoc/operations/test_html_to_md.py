# tests/test_integrations/pandoc/operations/test_html_to_md.py
"""
Tests for HTML to Markdown conversion operations.
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import (
    FileInfoResult,
    OperationResult,
    ReadResult,
    WriteResult,
)
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionMetrics
from quackcore.integrations.pandoc.operations.html_to_md import (
    _attempt_conversion,
    _validate_input,
    _write_and_validate_output,
    convert_html_to_markdown,
    post_process_markdown,
    validate_conversion,
)


class TestHtmlToMarkdownOperations:
    """Tests for HTML to Markdown conversion operations."""

    @pytest.fixture
    def config(self):
        """Fixture to create a PandocConfig for testing."""
        return PandocConfig(
            output_dir=Path("/path/to/output"),
        )

    @pytest.fixture
    def metrics(self):
        """Fixture to create ConversionMetrics for testing."""
        return ConversionMetrics()

    @pytest.fixture
    def mock_fs(self):
        """Fixture to mock fs module."""
        with patch("quackcore.integrations.pandoc.operations.html_to_md.fs") as mock_fs:
            # Setup default behavior for file info checks
            file_info = FileInfoResult(
                success=True,
                path="/path/to/file.html",
                exists=True,
                is_file=True,
                size=1024,
            )
            mock_fs.service.get_file_info.return_value = file_info

            # Setup default behavior for directory creation
            dir_result = OperationResult(
                success=True,
                path="/path/to/output",
                message="Directory created",
            )
            mock_fs.create_directory.return_value = dir_result

            # Setup default behavior for read_text
            read_result = ReadResult(
                success=True,
                path="/path/to/file.html",
                content="<html><body><h1>Test</h1><p>Content</p></body></html>",
                encoding="utf-8",
            )
            mock_fs.service.read_text.return_value = read_result

            # Setup default behavior for write_text
            write_result = WriteResult(
                success=True,
                path="/path/to/output/file.md",
                bytes_written=100,
            )
            mock_fs.write_text.return_value = write_result

            yield mock_fs

    def test_validate_input(self, mock_fs):
        """Test validating HTML input file."""
        html_path = Path("/path/to/file.html")
        config = PandocConfig(validation={"verify_structure": True})

        # Test with valid input
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.validate_html_structure"
        ) as mock_validate:
            mock_validate.return_value = (True, [])

            original_size = _validate_input(html_path, config)

            assert original_size == 1024
            mock_fs.service.get_file_info.assert_called_with(html_path)
            mock_fs.service.read_text.assert_called_with(html_path)
            mock_validate.assert_called_once()

        # Test with invalid HTML structure
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.validate_html_structure"
        ) as mock_validate:
            mock_validate.return_value = (False, ["HTML document missing body tag"])

            with pytest.raises(QuackIntegrationError) as excinfo:
                _validate_input(html_path, config)

            assert "Invalid HTML structure" in str(excinfo.value)

        # Test with file not found
        mock_fs.service.get_file_info.return_value.exists = False

        with pytest.raises(QuackIntegrationError) as excinfo:
            _validate_input(html_path, config)

        assert "Input file not found" in str(excinfo.value)

        # Test with validation disabled
        mock_fs.service.get_file_info.return_value.exists = True
        config.validation.verify_structure = False

        original_size = _validate_input(html_path, config)

        assert original_size == 1024

    def test_attempt_conversion(self, config):
        """Test attempting HTML to Markdown conversion."""
        html_path = Path("/path/to/file.html")

        # Mock pypandoc to return markdown
        with patch("pypandoc.convert_file") as mock_convert:
            mock_convert.return_value = "# Test\n\nContent"

            # Test conversion
            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md.prepare_pandoc_args"
            ) as mock_args:
                mock_args.return_value = ["--strip-comments", "--no-highlight"]

                with patch(
                    "quackcore.integrations.pandoc.operations.html_to_md.post_process_markdown"
                ) as mock_post:
                    mock_post.return_value = "# Test\n\nContent"

                    result = _attempt_conversion(html_path, config)

                    assert result == "# Test\n\nContent"
                    mock_convert.assert_called_with(
                        str(html_path),
                        "markdown",
                        format="html",
                        extra_args=["--strip-comments", "--no-highlight"],
                    )
                    mock_post.assert_called_with("# Test\n\nContent")

        # Test with pandoc error
        with patch("pypandoc.convert_file") as mock_convert:
            mock_convert.side_effect = Exception("Pandoc error")

            with pytest.raises(QuackIntegrationError) as excinfo:
                _attempt_conversion(html_path, config)

            assert "Pandoc conversion failed" in str(excinfo.value)

    def test_post_process_markdown(self):
        """Test post-processing Markdown content."""
        # Test basic cleaning
        markdown = "{.class} Some content\n:::{.note}\nNote text\n:::\n<div>Content</div>\n\n\n\nMultiple empty lines\n<!-- Comment -->\n\n-List item"

        processed = post_process_markdown(markdown)

        # Check that various patterns are cleaned
        assert "{.class}" not in processed
        assert ":::{.note}" not in processed
        assert "<div>" not in processed
        assert "</div>" not in processed
        assert "<!-- Comment -->" not in processed
        assert "\n\n\n\n" not in processed  # Multiple newlines reduced
        assert "-List item" in processed  # List items preserved

    def test_write_and_validate_output(self, mock_fs, config):
        """Test writing and validating Markdown output."""
        cleaned_markdown = "# Test\n\nContent"
        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/file.html")
        original_size = 1024
        attempt_start = time.time() - 1  # 1 second ago

        # Test successful write and validation
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.validate_conversion"
        ) as mock_validate:
            mock_validate.return_value = []  # No validation errors

            conversion_time, output_size, validation_errors = (
                _write_and_validate_output(
                    cleaned_markdown,
                    output_path,
                    input_path,
                    original_size,
                    config,
                    attempt_start,
                )
            )

            assert conversion_time > 0
            assert output_size == 100  # From mock write_result.bytes_written
            assert len(validation_errors) == 0
            mock_fs.create_directory.assert_called_with(
                output_path.parent, exist_ok=True
            )
            mock_fs.write_text.assert_called_with(
                output_path, cleaned_markdown, encoding="utf-8"
            )
            mock_validate.assert_called_with(
                output_path, input_path, original_size, config
            )

        # Test directory creation failure
        mock_fs.create_directory.return_value.success = False
        mock_fs.create_directory.return_value.error = "Permission denied"

        with pytest.raises(QuackIntegrationError) as excinfo:
            _write_and_validate_output(
                cleaned_markdown,
                output_path,
                input_path,
                original_size,
                config,
                attempt_start,
            )

        assert "Failed to create output directory" in str(excinfo.value)

        # Test write failure
        mock_fs.create_directory.return_value.success = True
        mock_fs.write_text.return_value.success = False
        mock_fs.write_text.return_value.error = "Write error"

        with pytest.raises(QuackIntegrationError) as excinfo:
            _write_and_validate_output(
                cleaned_markdown,
                output_path,
                input_path,
                original_size,
                config,
                attempt_start,
            )

        assert "Failed to write output file" in str(excinfo.value)

        # Test with validation errors
        mock_fs.write_text.return_value.success = True

        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.validate_conversion"
        ) as mock_validate:
            mock_validate.return_value = ["Output file is empty"]

            conversion_time, output_size, validation_errors = (
                _write_and_validate_output(
                    cleaned_markdown,
                    output_path,
                    input_path,
                    original_size,
                    config,
                    attempt_start,
                )
            )

            assert len(validation_errors) == 1
            assert validation_errors[0] == "Output file is empty"

    def test_convert_html_to_markdown(self, config, metrics, mock_fs):
        """Test the main HTML to Markdown conversion function."""
        html_path = Path("/path/to/file.html")
        output_path = Path("/path/to/output/file.md")

        # Test successful conversion
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md._validate_input"
        ) as mock_validate:
            mock_validate.return_value = 1024  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md._attempt_conversion"
            ) as mock_attempt:
                mock_attempt.return_value = "# Test\n\nContent"

                with patch(
                    "quackcore.integrations.pandoc.operations.html_to_md._write_and_validate_output"
                ) as mock_write:
                    mock_write.return_value = (
                        1.0,
                        100,
                        [],
                    )  # (conversion_time, output_size, validation_errors)

                    with patch(
                        "quackcore.integrations.pandoc.operations.html_to_md.track_metrics"
                    ) as mock_track:
                        # Test successful conversion
                        result = convert_html_to_markdown(
                            html_path, output_path, config, metrics
                        )

                        assert result.success is True
                        assert result.content[0] == output_path
                        assert result.content[1].source_format == "html"
                        assert result.content[1].target_format == "markdown"
                        assert metrics.successful_conversions == 1
                        mock_validate.assert_called_once_with(html_path, config)
                        mock_attempt.assert_called_once_with(html_path, config)
                        mock_write.assert_called_once()
                        mock_track.assert_called_once()

        # Test with validation errors on first attempt but success on retry
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md._validate_input"
        ) as mock_validate:
            mock_validate.return_value = 1024  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md._attempt_conversion"
            ) as mock_attempt:
                mock_attempt.return_value = "# Test\n\nContent"

                with patch(
                    "quackcore.integrations.pandoc.operations.html_to_md._write_and_validate_output"
                ) as mock_write:
                    # First call returns validation errors, second call succeeds
                    mock_write.side_effect = [
                        (1.0, 100, ["Output file is empty"]),
                        (1.5, 200, []),
                    ]

                    with patch(
                        "quackcore.integrations.pandoc.operations.html_to_md.track_metrics"
                    ) as mock_track:
                        with patch(
                            "quackcore.integrations.pandoc.operations.html_to_md.time.sleep"
                        ) as mock_sleep:
                            # Test retry logic
                            result = convert_html_to_markdown(
                                html_path, output_path, config, metrics
                            )

                            assert result.success is True
                            assert mock_write.call_count == 2
                            assert mock_sleep.call_count == 1
                            assert mock_attempt.call_count == 2

        # Test with maximum retries exceeded
        metrics.successful_conversions = 0  # Reset for this test

        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md._validate_input"
        ) as mock_validate:
            mock_validate.return_value = 1024  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md._attempt_conversion"
            ) as mock_attempt:
                mock_attempt.return_value = "# Test\n\nContent"

                with patch(
                    "quackcore.integrations.pandoc.operations.html_to_md._write_and_validate_output"
                ) as mock_write:
                    # Always return validation errors
                    mock_write.return_value = (1.0, 100, ["Output file is empty"])

                    with patch(
                        "quackcore.integrations.pandoc.operations.html_to_md.time.sleep"
                    ) as mock_sleep:
                        # Test max retries (default is 3)
                        result = convert_html_to_markdown(
                            html_path, output_path, config, metrics
                        )

                        assert result.success is False
                        assert (
                            "Conversion validation failed after maximum retries"
                            in result.error
                        )
                        assert mock_write.call_count == 3
                        assert mock_sleep.call_count == 2
                        assert metrics.successful_conversions == 0
                        assert metrics.failed_conversions == 1
                        assert str(html_path) in metrics.errors

        # Test with exception
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md._validate_input"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")

            result = convert_html_to_markdown(html_path, output_path, config, metrics)

            assert result.success is False
            assert "Failed to convert HTML to Markdown" in result.error
            assert metrics.failed_conversions == 2

    def test_validate_conversion(self, mock_fs, config):
        """Test validating HTML to Markdown conversion."""
        output_path = Path("/path/to/output/file.md")
        input_path = Path("/path/to/file.html")
        original_size = 1024

        # Mock file info for output file
        output_info = FileInfoResult(
            success=True,
            path=str(output_path),
            exists=True,
            is_file=True,
            size=512,
        )
        mock_fs.service.get_file_info.return_value = output_info

        # Mock read_text to return content
        read_result = ReadResult(
            success=True,
            path=str(output_path),
            content="# Test\n\nThis is a markdown file with headers.\n\n## Section",
            encoding="utf-8",
        )
        mock_fs.service.read_text.return_value = read_result

        # Test valid conversion
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.check_file_size"
        ) as mock_size:
            mock_size.return_value = (True, [])

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (True, [])

                validation_errors = validate_conversion(
                    output_path, input_path, original_size, config
                )

                assert len(validation_errors) == 0
                mock_size.assert_called_with(
                    output_info.size, config.validation.min_file_size
                )
                mock_ratio.assert_called_with(
                    output_info.size,
                    original_size,
                    config.validation.conversion_ratio_threshold,
                )

        # Test with output file not found
        mock_fs.service.get_file_info.return_value.exists = False

        validation_errors = validate_conversion(
            output_path, input_path, original_size, config
        )

        assert len(validation_errors) == 1
        assert "Output file does not exist" in validation_errors[0]

        # Test with empty output content
        mock_fs.service.get_file_info.return_value.exists = True
        mock_fs.service.read_text.return_value.content = ""

        validation_errors = validate_conversion(
            output_path, input_path, original_size, config
        )

        assert len(validation_errors) == 1
        assert "Output file is empty" in validation_errors[0]

        # Test with minimal content
        mock_fs.service.read_text.return_value.content = "x"

        validation_errors = validate_conversion(
            output_path, input_path, original_size, config
        )

        assert len(validation_errors) == 1
        assert "Output file contains minimal content" in validation_errors[0]

        # Test with file size check failure
        mock_fs.service.read_text.return_value.content = "# Test\n\nContent"

        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.check_file_size"
        ) as mock_size:
            mock_size.return_value = (False, ["File size is below threshold"])

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (True, [])

                validation_errors = validate_conversion(
                    output_path, input_path, original_size, config
                )

                assert len(validation_errors) == 1
                assert "File size is below threshold" in validation_errors[0]

        # Test with conversion ratio check failure
        with patch(
            "quackcore.integrations.pandoc.operations.html_to_md.check_file_size"
        ) as mock_size:
            mock_size.return_value = (True, [])

            with patch(
                "quackcore.integrations.pandoc.operations.html_to_md.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (
                    False,
                    ["Conversion ratio is below threshold"],
                )

                validation_errors = validate_conversion(
                    output_path, input_path, original_size, config
                )

                assert len(validation_errors) == 1
                assert "Conversion ratio is below threshold" in validation_errors[0]

        # Test with read error
        mock_fs.service.read_text.return_value.success = False
        mock_fs.service.read_text.return_value.error = "Read error"

        validation_errors = validate_conversion(
            output_path, input_path, original_size, config
        )

        assert len(validation_errors) == 1
        assert "Error reading output file" in validation_errors[0]
