# src/quackcore/integrations/pandoc/operations/utils.py
"""
Utility functions for pandoc operations.

This module provides helper functions for pandoc conversion operations,
such as validation, metrics tracking, and pandoc installation verification.
"""

import logging
import time
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import ConversionMetrics, FileInfo

logger = logging.getLogger(__name__)


def verify_pandoc() -> str:
    """
    Verify pandoc installation and version.

    Returns:
        str: Pandoc version string

    Raises:
        QuackIntegrationError: If pandoc is not installed
    """
    try:
        import pypandoc

        version = pypandoc.get_pandoc_version()
        logger.info(f"Found pandoc version: {version}")
        return version
    except ImportError:
        msg = "pypandoc module is not installed"
        logger.error(msg)
        raise QuackIntegrationError(msg, {"module": "pypandoc"})
    except OSError as err:
        msg = "Pandoc is not installed. Please install pandoc first."
        logger.error(msg)
        raise QuackIntegrationError(msg, {"original_error": str(err)})
    except Exception as e:
        msg = f"Error checking pandoc: {str(e)}"
        logger.error(msg)
        raise QuackIntegrationError(msg, {"original_error": str(e)})


def prepare_pandoc_args(
        config: ConversionConfig,
        source_format: str,
        target_format: str,
        extra_args: list[str] | None = None,
) -> list[str]:
    """
    Prepare pandoc conversion arguments.

    Args:
        config: Conversion configuration
        source_format: Source format
        target_format: Target format
        extra_args: Additional arguments

    Returns:
        list[str]: List of pandoc arguments
    """
    # Base arguments from configuration
    pandoc_opts = config.pandoc_options
    args = [
        f"--wrap={pandoc_opts.wrap}",
        "--standalone" if pandoc_opts.standalone else None,
        f"--markdown-headings={pandoc_opts.markdown_headings}",
        "--reference-links" if pandoc_opts.reference_links else None,
    ]

    # Add resource paths
    for path in pandoc_opts.resource_path:
        args.append(f"--resource-path={path}")

    # Format-specific arguments
    if source_format == "html" and target_format == "markdown":
        args.extend(config.html_to_md_extra_args)
    elif source_format == "markdown" and target_format == "docx":
        args.extend(config.md_to_docx_extra_args)

    # Add additional arguments
    if extra_args:
        args.extend(extra_args)

    # Filter out None values
    return [arg for arg in args if arg is not None]


def validate_html_structure(content: str, check_links: bool = False) -> tuple[
    bool, list[str]]:
    """
    Validate HTML document structure.

    Args:
        content: HTML content
        check_links: Whether to check links

    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        # Check for basic HTML structure
        if not soup.find("body"):
            errors.append("HTML document missing body tag")
            return False, errors

        # Validate links if configured
        if check_links:
            links = soup.find_all("a")
            empty_links = []
            for link in links:
                href = link.get("href")
                if href is None or href.strip() == "":
                    empty_links.append(str(link))

            if empty_links:
                errors.append(f"Found {len(empty_links)} empty links in document")

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"HTML validation error: {str(e)}")
        return False, errors


def validate_docx_structure(docx_path: Path, check_links: bool = False) -> tuple[
    bool, list[str]]:
    """
    Validate DOCX document structure.

    Args:
        docx_path: Path to DOCX file
        check_links: Whether to check links

    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []

    try:
        from docx import Document

        doc = Document(str(docx_path))

        # Check if document has content
        if len(doc.paragraphs) == 0:
            errors.append("DOCX document has no paragraphs")
            return False, errors

        # Validate links if configured
        if check_links:
            # In python-docx, hyperlinks are part of the relationships
            if not doc.part:
                errors.append("Document structure appears incomplete")
                return False, errors

        return len(errors) == 0, errors

    except ImportError:
        errors.append("python-docx module is not installed")
        return False, errors
    except Exception as e:
        errors.append(f"DOCX validation error: {str(e)}")
        return False, errors


def track_metrics(
        filename: str,
        start_time: float,
        original_size: int,
        converted_size: int,
        metrics: ConversionMetrics,
        config: ConversionConfig,
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

        logger.info(
            f"File size change for {filename}: "
            f"{original_size / 1024:.2f}KB -> {converted_size / 1024:.2f}KB"
        )


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
    file_info = fs.get_file_info(path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(f"File not found: {path}")

    # Determine format from file extension if not provided
    if format_hint:
        format_name = format_hint
    else:
        extension = path.suffix.lower().lstrip(".")
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
    errors = []

    if validation_min_size > 0 and converted_size < validation_min_size:
        errors.append(
            f"Converted file size ({converted_size} bytes) "
            f"is below the minimum threshold "
            f"({validation_min_size} bytes)"
        )
        return False, errors

    return True, errors


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
    errors = []

    if original_size > 0:
        conversion_ratio = converted_size / original_size
        if conversion_ratio < threshold:
            errors.append(
                f"Conversion error: Converted file size "
                f"({converted_size} bytes) is less than "
                f"{threshold * 100:.0f}% of the original file size "
                f"({original_size} bytes) (ratio: {conversion_ratio:.2f})."
            )
            return False, errors

    return True, errors