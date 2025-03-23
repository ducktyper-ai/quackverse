# tests/test_plugins/pandoc/operations/test_operations_utils.py
"""
Tests for pandoc plugin operations utility functions.

This module tests the utility functions used by the pandoc operations modules,
for validation, metrics tracking, and other common operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from quackcore.errors import QuackIntegrationError
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import ConversionMetrics
from quackcore.plugins.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    get_file_info,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
    validate_html_structure,
    verify_pandoc,
)


class TestVerifyPandoc:
    """Tests for the verify_pandoc function."""

    def test_successful_verification(self) -> None:
        """Test successful verification of pandoc."""
        with patch("pypandoc.get_pandoc_version") as mock_get_version:
            mock_get_version.return_value = "2.18"

            version = verify_pandoc()
            assert version == "2.18"
            mock_get_version.assert_called_once()

    def test_pypandoc_not_installed(self) -> None:
        """Test when pypandoc is not installed."""
        with patch("pypandoc.get_pandoc_version",
                   side_effect=ImportError("No module named 'pypandoc'")):
            with pytest.raises(QuackIntegrationError) as exc_info:
                verify_pandoc()

            assert "pypandoc module is not installed" in str(exc_info.value)

    def test_pandoc_not_installed(self) -> None:
        """Test when pandoc is not installed."""
        with patch("pypandoc.get_pandoc_version",
                   side_effect=OSError("Pandoc not found")):
            with pytest.raises(QuackIntegrationError) as exc_info:
                verify_pandoc()

            assert "Pandoc is not installed" in str(exc_info.value)

    def test_other_exception(self) -> None:
        """Test when another exception occurs."""
        with patch("pypandoc.get_pandoc_version",
                   side_effect=Exception("Unexpected error")):
            with pytest.raises(QuackIntegrationError) as exc_info:
                verify_pandoc()

            assert "Error checking pandoc" in str(exc_info.value)


class TestPreparePandocArgs:
    """Tests for the prepare_pandoc_args function."""

    def test_base_arguments(self) -> None:
        """Test preparing base pandoc arguments."""
        config = ConversionConfig()

        args = prepare_pandoc_args(config, "html", "markdown")

        assert "--wrap=none" in args
        assert "--standalone" in args
        assert "--markdown-headings=atx" in args
        assert "--reference-links" not in args  # Default is False

    def test_resource_paths(self) -> None:
        """Test including resource paths."""
        config = ConversionConfig(
            pandoc_options={"resource_path": [Path("/path1"), Path("/path2")]}
        )

        args = prepare_pandoc_args(config, "html", "markdown")

        assert "--resource-path=/path1" in args
        assert "--resource-path=/path2" in args

    def test_html_to_markdown_extra_args(self) -> None:
        """Test html to markdown specific arguments."""
        config = ConversionConfig(
            html_to_md_extra_args=["--strip-comments", "--no-highlight"]
        )

        args = prepare_pandoc_args(config, "html", "markdown")

        assert "--strip-comments" in args
        assert "--no-highlight" in args

    def test_markdown_to_docx_extra_args(self) -> None:
        """Test markdown to docx specific arguments."""
        config = ConversionConfig(
            md_to_docx_extra_args=["--reference-doc=template.docx"]
        )

        args = prepare_pandoc_args(config, "markdown", "docx")

        assert "--reference-doc=template.docx" in args

    def test_additional_args(self) -> None:
        """Test adding additional arguments."""
        config = ConversionConfig()

        args = prepare_pandoc_args(
            config,
            "html",
            "markdown",
            extra_args=["--custom-arg", "--another-arg"]
        )

        assert "--custom-arg" in args
        assert "--another-arg" in args


class TestValidateHtmlStructure:
    """Tests for the validate_html_structure function."""

    def test_valid_html(self) -> None:
        """Test validating valid HTML content."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test.</p>
            <a href="https://example.com">Link</a>
        </body>
        </html>
        """

        is_valid, errors = validate_html_structure(html_content)

        assert is_valid is True
        assert errors == []

    def test_missing_body(self) -> None:
        """Test HTML without a body tag."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
        </head>
        </html>
        """

        is_valid, errors = validate_html_structure(html_content)

        assert is_valid is False
        assert "HTML document missing body tag" in errors[0]

    @patch("bs4.BeautifulSoup", side_effect=Exception("BeautifulSoup error"))
    def test_parsing_error(self, mock_bs4: MagicMock) -> None:
        """Test HTML that causes a parsing error."""
        html_content = "Invalid HTML"

        is_valid, errors = validate_html_structure(html_content)

        assert is_valid is False
        assert "HTML validation error" in errors[0]

    def test_check_links(self) -> None:
        """Test checking links in HTML."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <a href="https://example.com">Valid Link</a>
            <a href="">Empty Link</a>
            <a>Missing Link</a>
        </body>
        </html>
        """

        is_valid, errors = validate_html_structure(html_content, check_links=True)

        assert is_valid is False
        assert "empty links" in errors[0]


class TestValidateDocxStructure:
    """Tests for the validate_docx_structure function."""

    @patch("docx.Document")
    def test_valid_docx(self, mock_document: MagicMock) -> None:
        """Test validating valid DOCX document."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(), MagicMock()]  # Two paragraphs
        mock_doc.part = MagicMock()  # Has a part

        mock_document.return_value = mock_doc

        is_valid, errors = validate_docx_structure(Path("/path/to/doc.docx"))

        assert is_valid is True
        assert errors == []

    @patch("docx.Document")
    def test_empty_docx(self, mock_document: MagicMock) -> None:
        """Test validating empty DOCX document."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = []  # No paragraphs

        mock_document.return_value = mock_doc

        is_valid, errors = validate_docx_structure(Path("/path/to/doc.docx"))

        assert is_valid is False
        assert "DOCX document has no paragraphs" in errors[0]

    @patch("docx.Document")
    def test_check_links_incomplete(self, mock_document: MagicMock) -> None:
        """Test checking links in incomplete DOCX."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock()]  # One paragraph
        mock_doc.part = None  # Missing part

        mock_document.return_value = mock_doc

        is_valid, errors = validate_docx_structure(
            Path("/path/to/doc.docx"), check_links=True
        )

        assert is_valid is False
        assert "Document structure appears incomplete" in errors[0]

    @patch("docx.Document", side_effect=ImportError("No module named 'docx'"))
    def test_docx_module_missing(self, mock_document: MagicMock) -> None:
        """Test when python-docx module is not installed."""
        is_valid, errors = validate_docx_structure(Path("/path/to/doc.docx"))

        assert is_valid is False
        assert "python-docx module is not installed" in errors[0]

    @patch("docx.Document", side_effect=Exception("DOCX error"))
    def test_docx_error(self, mock_document: MagicMock) -> None:
        """Test when an error occurs during DOCX parsing."""
        is_valid, errors = validate_docx_structure(Path("/path/to/doc.docx"))

        assert is_valid is False
        assert "DOCX validation error" in errors[0]


class TestTrackMetrics:
    """Tests for the track_metrics function."""

    def test_track_conversion_time(self) -> None:
        """Test tracking conversion time."""
        metrics = ConversionMetrics()
        config = ConversionConfig(metrics={"track_conversion_time": True})

        start_time = 1000.0  # seconds since epoch
        original_size = 1000
        converted_size = 500

        with patch("time.time", return_value=1005.0):  # 5 seconds elapsed
            track_metrics(
                "file.html",
                start_time,
                original_size,
                converted_size,
                metrics,
                config
            )

        assert "file.html" in metrics.conversion_times
        assert metrics.conversion_times["file.html"]["start"] == 1000.0
        assert metrics.conversion_times["file.html"]["end"] == 1005.0

    def test_track_file_sizes(self) -> None:
        """Test tracking file sizes."""
        metrics = ConversionMetrics()
        config = ConversionConfig(
            metrics={"track_conversion_time": False, "track_file_sizes": True}
        )

        start_time = 1000.0
        original_size = 1000
        converted_size = 500

        track_metrics(
            "file.html",
            start_time,
            original_size,
            converted_size,
            metrics,
            config
        )

        assert "file.html" in metrics.file_sizes
        assert metrics.file_sizes["file.html"]["original"] == 1000
        assert metrics.file_sizes["file.html"]["converted"] == 500
        assert metrics.file_sizes["file.html"]["ratio"] == 0.5

    def test_metrics_disabled(self) -> None:
        """Test when metrics tracking is disabled."""
        metrics = ConversionMetrics()
        config = ConversionConfig(
            metrics={"track_conversion_time": False, "track_file_sizes": False}
        )

        start_time = 1000.0
        original_size = 1000
        converted_size = 500

        track_metrics(
            "file.html",
            start_time,
            original_size,
            converted_size,
            metrics,
            config
        )

        assert "file.html" not in metrics.conversion_times
        assert "file.html" not in metrics.file_sizes


class TestGetFileInfo:
    """Tests for the get_file_info function."""

    def test_existing_file(self) -> None:
        """Test getting info for an existing file."""
        path = Path("/path/to/file.html")

        mock_file_info = MagicMock()
        mock_file_info.success = True
        mock_file_info.exists = True
        mock_file_info.size = 1000
        mock_file_info.modified = 1609459200.0  # 2021-01-01

        with patch("quackcore.fs.service.get_file_info", return_value=mock_file_info):
            info = get_file_info(path)

            assert info.path == path
            assert info.format == "html"  # Determined from extension
            assert info.size == 1000
            assert info.modified == 1609459200.0

    def test_nonexistent_file(self) -> None:
        """Test getting info for a nonexistent file."""
        path = Path("/path/to/nonexistent.html")

        mock_file_info = MagicMock()
        mock_file_info.success = False
        mock_file_info.exists = False

        with patch("quackcore.fs.service.get_file_info", return_value=mock_file_info):
            with pytest.raises(QuackIntegrationError) as exc_info:
                get_file_info(path)

            assert f"File not found: {path}" in str(exc_info.value)

    def test_with_format_hint(self) -> None:
        """Test getting info with a format hint."""
        path = Path("/path/to/file.txt")

        mock_file_info = MagicMock()
        mock_file_info.success = True
        mock_file_info.exists = True
        mock_file_info.size = 500

        with patch("quackcore.fs.service.get_file_info", return_value=mock_file_info):
            info = get_file_info(path, format_hint="markdown")

            assert info.path == path
            assert info.format == "markdown"  # Used hint instead of extension

    def test_format_mapping(self) -> None:
        """Test format mapping from file extensions."""
        formats = {
            "md": "markdown",
            "markdown": "markdown",
            "html": "html",
            "htm": "html",
            "docx": "docx",
            "pdf": "pdf",
            "txt": "plain",
            "unknown": "unknown",  # Default to extension
        }

        mock_file_info = MagicMock()
        mock_file_info.success = True
        mock_file_info.exists = True

        with patch("quackcore.fs.service.get_file_info", return_value=mock_file_info):
            for ext, expected_format in formats.items():
                path = Path(f"/path/to/file.{ext}")
                info = get_file_info(path)
                assert info.format == expected_format


class TestCheckFileSize:
    """Tests for the check_file_size function."""

    def test_valid_size(self) -> None:
        """Test valid file size."""
        converted_size = 100
        min_size = 50

        is_valid, errors = check_file_size(converted_size, min_size)

        assert is_valid is True
        assert errors == []

    def test_size_too_small(self) -> None:
        """Test file size below threshold."""
        converted_size = 25
        min_size = 50

        is_valid, errors = check_file_size(converted_size, min_size)

        assert is_valid is False
        assert len(errors) == 1
        assert "below the minimum threshold" in errors[0]

    def test_min_size_zero(self) -> None:
        """Test when min_size is zero (validation disabled)."""
        converted_size = 0
        min_size = 0

        is_valid, errors = check_file_size(converted_size, min_size)

        assert is_valid is True
        assert errors == []

    @given(
        st.integers(min_value=0),
        st.integers(min_value=0)
    )
    def test_property_based(self, converted_size: int, min_size: int) -> None:
        """Property-based test for check_file_size."""
        is_valid, _ = check_file_size(converted_size, min_size)

        # Should be valid if size is >= min_size or min_size is 0
        expected_valid = converted_size >= min_size or min_size == 0
        assert is_valid is expected_valid


class TestCheckConversionRatio:
    """Tests for the check_conversion_ratio function."""

    def test_valid_ratio(self) -> None:
        """Test valid conversion ratio."""
        converted_size = 800
        original_size = 1000
        threshold = 0.5

        is_valid, errors = check_conversion_ratio(converted_size, original_size,
                                                  threshold)

        assert is_valid is True
        assert errors == []

    def test_ratio_too_small(self) -> None:
        """Test conversion ratio below threshold."""
        converted_size = 400
        original_size = 1000
        threshold = 0.5

        is_valid, errors = check_conversion_ratio(converted_size, original_size,
                                                  threshold)

        assert is_valid is False
        assert len(errors) == 1
        assert "less than" in errors[0]
        assert "50%" in errors[0]  # 0.5 * 100

    def test_zero_original_size(self) -> None:
        """Test when original_size is zero."""
        converted_size = 100
        original_size = 0
        threshold = 0.1

        is_valid, errors = check_conversion_ratio(converted_size, original_size,
                                                  threshold)

        assert is_valid is True
        assert errors == []

    @given(
        st.integers(min_value=0),
        st.integers(min_value=0),
        st.floats(min_value=0, max_value=1)
    )
    def test_property_based(
            self,
            converted_size: int,
            original_size: int,
            threshold: float
    ) -> None:
        """Property-based test for check_conversion_ratio."""
        is_valid, _ = check_conversion_ratio(converted_size, original_size, threshold)

        # Should be valid if original_size is 0 or ratio >= threshold
        if original_size == 0:
            expected_valid = True
        else:
            ratio = converted_size / original_size
            expected_valid = ratio >= threshold

        assert is_valid is expected_valid