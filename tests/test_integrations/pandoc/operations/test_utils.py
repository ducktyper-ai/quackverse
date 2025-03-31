# tests/test_integrations/pandoc/operations/test_utils.py
"""
Tests for Pandoc utility functions.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore import fs
from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult, OperationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionMetrics, FileInfo
from quackcore.integrations.pandoc.operations import utils, verify_pandoc


class TestPandocUtilities:
    """Tests for Pandoc utility functions."""

    def test_verify_pandoc_success(self):
        """Test verifying Pandoc availability successfully."""
        with patch("pypandoc.get_pandoc_version") as mock_get_version:
            mock_get_version.return_value = "2.11.4"

            version = verify_pandoc()

            assert version == "2.11.4"
            mock_get_version.assert_called_once()

    def test_verify_pandoc_import_error(self):
        """Test verifying Pandoc when pypandoc is not installed."""
        with patch("pypandoc.get_pandoc_version") as mock_get_version:
            mock_get_version.side_effect = ImportError("No module named 'pypandoc'")

            with pytest.raises(QuackIntegrationError) as excinfo:
                verify_pandoc()

            assert "pypandoc module is not installed" in str(excinfo.value)

    def test_verify_pandoc_os_error(self):
        """Test verifying Pandoc when pandoc executable is not found."""
        with patch("pypandoc.get_pandoc_version") as mock_get_version:
            mock_get_version.side_effect = OSError("Pandoc not found")

            with pytest.raises(QuackIntegrationError) as excinfo:
                verify_pandoc()

            assert "Pandoc is not installed" in str(excinfo.value)

    def test_prepare_pandoc_args(self):
        """Test preparing pandoc arguments based on configuration."""
        config = PandocConfig(
            pandoc_options={
                "wrap": "auto",
                "standalone": True,
                "markdown_headings": "atx",
                "reference_links": True,
                "resource_path": [Path("/path/to/resources")],
            },
            html_to_md_extra_args=["--strip-comments", "--no-highlight"],
            md_to_docx_extra_args=["--reference-doc=template.docx"],
        )

        # Test HTML to Markdown arguments
        args = utils.prepare_pandoc_args(config, "html", "markdown")
        assert "--wrap=auto" in args
        assert "--standalone" in args
        assert "--markdown-headings=atx" in args
        assert "--reference-links" in args
        assert "--resource-path=/path/to/resources" in args
        assert "--strip-comments" in args
        assert "--no-highlight" in args

        # Test Markdown to DOCX arguments
        args = utils.prepare_pandoc_args(config, "markdown", "docx")
        assert "--wrap=auto" in args
        assert "--standalone" in args
        assert "--markdown-headings=atx" in args
        assert "--reference-links" in args
        assert "--resource-path=/path/to/resources" in args
        assert "--reference-doc=template.docx" in args

        # Test with additional arguments
        extra_args = ["--toc", "--toc-depth=2"]
        args = utils.prepare_pandoc_args(config, "html", "markdown", extra_args)
        assert "--toc" in args
        assert "--toc-depth=2" in args

    # src/quackcore/integrations/pandoc/operations/utils.py

    # Fix get_file_info function
    def get_file_info(path: Path, format_hint: str | None = None) -> FileInfo:
        """
        Get file information for conversion.

        Args:
            path: Path to the file
            format_hint: Hint about the file format

        Returns:
            FileInfo: File information

        Raises:
            QuackIntegrationError: If the file does not exist
        """
        # Changed from fs.service.get_file_info to fs.get_file_info
        file_info = fs.get_file_info(path)
        if not file_info.success or not file_info.exists:
            raise QuackIntegrationError(f"File not found: {path}")

        # Determine format from file extension if not provided
        if format_hint:
            format_name = format_hint
        else:
            extension = fs.get_extension(path)
            format_mapping = {
                "md": "markdown",
                "markdown": "markdown",
                "html": "html",
                "htm": "html",
                "docx": "docx",
                "doc": "docx",
                "pdf": "pdf",
                "txt": "plain",
            }
            format_name = format_mapping.get(extension, extension)

        return FileInfo(
            path=path,
            format=format_name,
            size=file_info.size or 0,
            modified=file_info.modified,
        )

    # Fix check_file_size function
    def check_file_size(
        converted_size: int, validation_min_size: int
    ) -> tuple[bool, list[str]]:
        """
        Check if the converted file meets the minimum file size.

        Args:
            converted_size: Size of the converted file
            validation_min_size: Minimum file size threshold

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors: list[str] = []

        if validation_min_size > 0 and converted_size < validation_min_size:
            # Changed from fs.service.get_file_size_str to fs.get_file_size_str
            converted_size_str = fs.get_file_size_str(converted_size)
            min_size_str = fs.get_file_size_str(validation_min_size)

            errors.append(
                f"Converted file size ({converted_size_str}) "
                f"is below the minimum threshold "
                f"({min_size_str})"
            )
            return False, errors

        return True, errors

    # Fix check_conversion_ratio function
    def check_conversion_ratio(
        converted_size: int, original_size: int, threshold: float
    ) -> tuple[bool, list[str]]:
        """
        Check if the converted file size is not drastically smaller than the original.

        Args:
            converted_size: Size of the converted file
            original_size: Size of the original file
            threshold: Minimum ratio threshold

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors: list[str] = []

        if original_size > 0:
            conversion_ratio = converted_size / original_size
            if conversion_ratio < threshold:
                # Changed from fs.service.get_file_size_str to fs.get_file_size_str
                converted_size_str = fs.get_file_size_str(converted_size)
                original_size_str = fs.get_file_size_str(original_size)

                errors.append(
                    f"Conversion error: Converted file size "
                    f"({converted_size_str}) is less than "
                    f"{threshold * 100:.0f}% of the original file size "
                    f"({original_size_str}) (ratio: {conversion_ratio:.2f})."
                )
                return False, errors

        return True, errors

    # Fix track_metrics function
    def track_metrics(
        filename: str,
        start_time: float,
        original_size: int,
        converted_size: int,
        metrics: ConversionMetrics,
        config: PandocConfig,
    ) -> None:
        """
        Track conversion metrics.

        Args:
            filename: Name of the file
            start_time: Start time of conversion
            original_size: Size of the original file
            converted_size: Size of the converted file
            metrics: Metrics tracker
            config: Configuration object
        """
        # Track conversion time
        if config.metrics.track_conversion_time:
            end_time = time.time()
            duration = end_time - start_time

            metrics.conversion_times[filename] = {"start": start_time, "end": end_time}

            logger.info(f"Conversion time for {filename}: {duration:.2f} seconds")

        # Track file size changes
        if config.metrics.track_file_sizes:
            metrics.file_sizes[filename] = {
                "original": original_size,
                "converted": converted_size,
                "ratio": converted_size / original_size if original_size > 0 else 0,
            }

            # Use fs module's utility for formatting file sizes
            # Changed from fs.service.get_file_size_str to fs.get_file_size_str
            original_size_str = fs.get_file_size_str(original_size)
            converted_size_str = fs.get_file_size_str(converted_size)

            logger.info(
                f"File size change for {filename}: "
                f"{original_size_str} -> {converted_size_str}"
            )

    def test_get_file_info_file_not_found(self):
        """Test getting file information for a file that doesn't exist."""
        path = Path("/path/to/nonexistent.md")

        # Mock fs service to return file not found
        with patch("quackcore.fs.service.get_file_info") as mock_get_info:
            file_info_result = FileInfoResult(
                success=True,
                path=str(path),
                exists=False,
            )
            mock_get_info.return_value = file_info_result

            with pytest.raises(QuackIntegrationError) as excinfo:
                utils.get_file_info(path)

            assert "File not found" in str(excinfo.value)

    def test_validate_html_structure(self):
        """Test validating HTML structure."""
        # Test valid HTML
        valid_html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        is_valid, errors = utils.validate_html_structure(valid_html)
        assert is_valid is True
        assert len(errors) == 0

        # Test HTML missing body tag
        invalid_html = "<html><h1>Title</h1><p>Content</p></html>"
        is_valid, errors = utils.validate_html_structure(invalid_html)
        assert is_valid is False
        assert len(errors) == 1
        assert "HTML document missing body tag" in errors[0]

        # Test with links check enabled
        html_with_links = """
        <html><body>
            <a href="">Empty link</a>
            <a href="https://example.com">Valid link</a>
            <a>No href</a>
        </body></html>
        """
        is_valid, errors = utils.validate_html_structure(
            html_with_links, check_links=True
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "Found 2 empty links in document" in errors[0]

        # Test with invalid HTML structure causing parsing error
        with patch("bs4.BeautifulSoup") as mock_soup:
            mock_soup.side_effect = Exception("Parsing error")
            is_valid, errors = utils.validate_html_structure("<invalid>")
            assert is_valid is False
            assert len(errors) == 1
            assert "HTML validation error" in errors[0]

    def test_validate_docx_structure(self):
        """Test validating DOCX structure."""
        from docx.document import Document as DocxDocument

        # Mock a document with paragraphs
        mock_doc = MagicMock(spec=DocxDocument)
        mock_doc.paragraphs = [MagicMock(), MagicMock()]

        # Mock docx.Document to return our mock document
        with patch("docx.Document", return_value=mock_doc):
            # Test valid DOCX
            docx_path = Path("/path/to/valid.docx")
            is_valid, errors = utils.validate_docx_structure(docx_path)
            assert is_valid is True
            assert len(errors) == 0

            # Test empty DOCX
            mock_doc.paragraphs = []
            is_valid, errors = utils.validate_docx_structure(docx_path)
            assert is_valid is False
            assert len(errors) == 1
            assert "DOCX document has no paragraphs" in errors[0]

            # Test with links check and incomplete document
            mock_doc.paragraphs = [MagicMock()]
            mock_doc.part = None
            is_valid, errors = utils.validate_docx_structure(
                docx_path, check_links=True
            )
            assert is_valid is False
            assert len(errors) == 1
            assert "Document structure appears incomplete" in errors[0]

        # Test with ImportError (python-docx not installed)
        with patch("docx.Document", side_effect=ImportError("No module named 'docx'")):
            docx_path = Path("/path/to/valid.docx")
            is_valid, errors = utils.validate_docx_structure(docx_path)
            assert (
                is_valid is True
            )  # Shouldn't fail validation if module isn't installed
            assert len(errors) == 0

        # Test with other exceptions
        with patch("docx.Document", side_effect=Exception("DOCX error")):
            docx_path = Path("/path/to/valid.docx")
            is_valid, errors = utils.validate_docx_structure(docx_path)
            assert is_valid is False
            assert len(errors) == 1
            assert "DOCX validation error" in errors[0]

    def test_track_metrics(self):
        """Test tracking conversion metrics."""
        metrics = ConversionMetrics()
        config = PandocConfig(
            metrics={"track_conversion_time": True, "track_file_sizes": True},
        )

        start_time = time.time() - 5  # 5 seconds ago
        original_size = 1024
        converted_size = 512

        # Test with all tracking enabled
        utils.track_metrics(
            "test.html",
            start_time,
            original_size,
            converted_size,
            metrics,
            config,
        )

        assert "test.html" in metrics.conversion_times
        assert metrics.conversion_times["test.html"]["start"] == start_time
        assert "end" in metrics.conversion_times["test.html"]

        assert "test.html" in metrics.file_sizes
        assert metrics.file_sizes["test.html"]["original"] == original_size
        assert metrics.file_sizes["test.html"]["converted"] == converted_size
        assert metrics.file_sizes["test.html"]["ratio"] == 0.5  # 512/1024

        # Test with time tracking disabled
        metrics = ConversionMetrics()
        config.metrics.track_conversion_time = False

        utils.track_metrics(
            "test.html",
            start_time,
            original_size,
            converted_size,
            metrics,
            config,
        )

        assert "test.html" not in metrics.conversion_times
        assert "test.html" in metrics.file_sizes

        # Test with file size tracking disabled
        metrics = ConversionMetrics()
        config.metrics.track_conversion_time = True
        config.metrics.track_file_sizes = False

        utils.track_metrics(
            "test.html",
            start_time,
            original_size,
            converted_size,
            metrics,
            config,
        )

        assert "test.html" in metrics.conversion_times
        assert "test.html" not in metrics.file_sizes

    def test_check_file_size(self):
        """Test checking file size against threshold."""
        # Test file size above threshold
        converted_size = 1024
        min_size = 100

        is_valid, errors = utils.check_file_size(converted_size, min_size)
        assert is_valid is True
        assert len(errors) == 0

        # Test file size below threshold
        converted_size = 10
        min_size = 100

        is_valid, errors = utils.check_file_size(converted_size, min_size)
        assert is_valid is False
        assert len(errors) == 1
        assert "below the minimum threshold" in errors[0]

        # Test with zero threshold (validation disabled)
        converted_size = 10
        min_size = 0

        is_valid, errors = utils.check_file_size(converted_size, min_size)
        assert is_valid is True
        assert len(errors) == 0

    def test_check_conversion_ratio(self):
        """Test checking conversion ratio against threshold."""
        # Test with ratio above threshold
        converted_size = 900
        original_size = 1000
        threshold = 0.1  # 10%

        is_valid, errors = utils.check_conversion_ratio(
            converted_size, original_size, threshold
        )
        assert is_valid is True
        assert len(errors) == 0

        # Test with ratio below threshold
        converted_size = 50
        original_size = 1000
        threshold = 0.1  # 10%

        is_valid, errors = utils.check_conversion_ratio(
            converted_size, original_size, threshold
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "less than 10% of the original file size" in errors[0]

        # Test with zero original size (should avoid division by zero)
        converted_size = 50
        original_size = 0
        threshold = 0.1

        is_valid, errors = utils.check_conversion_ratio(
            converted_size, original_size, threshold
        )
        assert is_valid is True
        assert len(errors) == 0
