# src/quackcore/integrations/pandoc/operations/md_to_docx.py
"""
Markdown to DOCX conversion operations.

This module provides functions for converting Markdown documents to DOCX
using pandoc with optimized settings and error handling.
"""

import logging
import time
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionDetails, ConversionMetrics
from quackcore.integrations.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
)
from quackcore.integrations.core.results import IntegrationResult

logger = logging.getLogger(__name__)


def _validate_markdown_input(markdown_path: Path) -> int:
    """
    Validate the input Markdown file and return its size.

    Args:
        markdown_path: Path to the Markdown file.

    Returns:
        int: Size of the input Markdown file.

    Raises:
        QuackIntegrationError: If the input file is missing or empty.
    """
    file_info = fs.get_file_info(markdown_path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(
            f"Input file not found: {markdown_path}",
            {"path": str(markdown_path), "format": "markdown"},
        )
    original_size: int = file_info.size or 0

    try:
        markdown_content: str = markdown_path.read_text(encoding="utf-8")
        if not markdown_content.strip():
            raise QuackIntegrationError(
                f"Markdown file is empty: {markdown_path}",
                {"path": str(markdown_path)},
            )
    except Exception as e:
        if not isinstance(e, QuackIntegrationError):
            logger.warning(f"Could not validate markdown content: {str(e)}")
        else:
            raise
    return original_size


def _convert_markdown_to_docx_once(
    markdown_path: Path, output_path: Path, config: PandocConfig
) -> None:
    """
    Perform a single conversion attempt from Markdown to DOCX using pandoc.

    Args:
        markdown_path: Path to the Markdown file.
        output_path: Path to save the DOCX file.
        config: Conversion configuration.

    Raises:
        QuackIntegrationError: If pandoc conversion fails.
    """
    extra_args: list[str] = prepare_pandoc_args(
        config, "markdown", "docx", config.md_to_docx_extra_args
    )
    fs.create_directory(output_path.parent, exist_ok=True)
    logger.debug(f"Converting {markdown_path} to DOCX with args: {extra_args}")
    try:
        import pypandoc

        pypandoc.convert_file(
            str(markdown_path),
            "docx",
            format="markdown",
            outputfile=str(output_path),
            extra_args=extra_args,
        )
    except Exception as e:
        raise QuackIntegrationError(
            f"Pandoc conversion failed: {str(e)}",
            {"path": str(markdown_path), "format": "markdown"},
        ) from e


def _get_conversion_output(output_path: Path, start_time: float) -> tuple[float, int]:
    """
    Retrieve conversion timing and output file size.

    Args:
        output_path: Path to the output DOCX file.
        start_time: Timestamp when conversion attempt started.

    Returns:
        tuple: (conversion_time, output_size)

    Raises:
        QuackIntegrationError: If output file info cannot be retrieved.
    """
    conversion_time: float = time.time() - start_time
    output_info = fs.get_file_info(output_path)
    if not output_info.success:
        raise QuackIntegrationError(
            f"Failed to get info for converted file: {output_path}",
            {"path": str(output_path), "format": "docx"},
        )
    output_size: int = output_info.size or 0
    return conversion_time, output_size


def convert_markdown_to_docx(
    markdown_path: Path,
    output_path: Path,
    config: PandocConfig,
    metrics: ConversionMetrics | None = None,
) -> IntegrationResult[tuple[Path, ConversionDetails]]:
    """
    Convert a Markdown file to DOCX.

    Args:
        markdown_path: Path to the Markdown file.
        output_path: Path to save the DOCX file.
        config: Conversion configuration.
        metrics: Optional metrics tracker.

    Returns:
        IntegrationResult[tuple[Path, ConversionDetails]]: Result of the conversion.
    """
    filename: str = markdown_path.name
    original_size: int = _validate_markdown_input(markdown_path)
    max_retries: int = config.retry_mechanism.max_conversion_retries
    retry_count: int = 0
    start_time: float = time.time()

    while retry_count < max_retries:
        try:
            _convert_markdown_to_docx_once(markdown_path, output_path, config)
            conversion_time, output_size = _get_conversion_output(
                output_path, start_time
            )

            validation_errors: list[str] = validate_conversion(
                output_path, markdown_path, original_size, config
            )
            if validation_errors:
                error_str: str = "; ".join(validation_errors)
                logger.error(f"Conversion validation failed: {error_str}")
                raise QuackIntegrationError(error_str)

            if metrics:
                track_metrics(
                    filename, start_time, original_size, output_size, metrics, config
                )
                metrics.successful_conversions += 1

            # Create conversion details
            details = ConversionDetails(
                source_format="markdown",
                target_format="docx",
                conversion_time=conversion_time,
                output_size=output_size,
                input_size=original_size,
            )

            return IntegrationResult.success_result(
                (output_path, details),
                message=f"Successfully converted {markdown_path} to DOCX",
            )

        except Exception as e:
            retry_count += 1
            logger.warning(
                f"Markdown to DOCX conversion attempt {retry_count} failed: {str(e)}"
            )
            if retry_count >= max_retries:
                if metrics:
                    metrics.failed_conversions += 1
                    metrics.errors[str(markdown_path)] = str(e)
                error_msg: str = (
                    f"Integration error: {str(e)}"
                    if isinstance(e, QuackIntegrationError)
                    else f"Failed to convert Markdown to DOCX: {str(e)}"
                )
                return IntegrationResult.error_result(error_msg)
            time.sleep(config.retry_mechanism.conversion_retry_delay)

    return IntegrationResult.error_result("Conversion failed after maximum retries")


def validate_conversion(
    output_path: Path, input_path: Path, original_size: int, config: PandocConfig
) -> list[str]:
    """
    Validate the converted DOCX document.

    Args:
        output_path: Path to the output DOCX file.
        input_path: Path to the input Markdown file.
        original_size: Size of the original file.
        config: Conversion configuration.

    Returns:
        list[str]: List of validation error messages (empty if valid).
    """
    validation_errors: list[str] = []
    validation = config.validation

    output_info = fs.get_file_info(output_path)
    if not output_info.success or not output_info.exists:
        validation_errors.append(f"Output file does not exist: {output_path}")
        return validation_errors

    output_size: int = output_info.size or 0
    valid_size, size_errors = check_file_size(output_size, validation.min_file_size)
    if not valid_size:
        validation_errors.extend(size_errors)

    valid_ratio, ratio_errors = check_conversion_ratio(
        output_size, original_size, validation.conversion_ratio_threshold
    )
    if not valid_ratio:
        validation_errors.extend(ratio_errors)

    if validation.verify_structure and output_path.exists():
        is_valid, structure_errors = validate_docx_structure(
            output_path, validation.check_links
        )
        if not is_valid:
            validation_errors.extend(structure_errors)
        _check_docx_metadata(output_path, input_path, validation.check_links)

    return validation_errors


def _check_docx_metadata(docx_path: Path, source_path: Path, check_links: bool) -> None:
    """
    Check DOCX metadata for references to the source file.
    This function is separated to handle import errors cleanly.

    Args:
        docx_path: Path to the DOCX file.
        source_path: Path to the source file.
        check_links: Whether to check for links/references.
    """
    try:
        from docx import Document
    except ImportError:
        logger.debug("python-docx not available for detailed metadata check")
        return

    try:
        doc = Document(str(docx_path))
        source_filename = source_path.name
        source_found = False

        if hasattr(doc, "core_properties"):
            if (
                hasattr(doc.core_properties, "title")
                and doc.core_properties.title
                and source_filename in doc.core_properties.title
            ):
                source_found = True
            elif (
                hasattr(doc.core_properties, "comments")
                and doc.core_properties.comments
                and source_filename in doc.core_properties.comments
            ):
                source_found = True
            elif (
                hasattr(doc.core_properties, "subject")
                and doc.core_properties.subject
                and source_filename in doc.core_properties.subject
            ):
                source_found = True

            if not source_found and check_links:
                logger.debug(
                    f"Source file reference missing in "
                    f"document metadata: {source_filename}"
                )
    except Exception as e:
        logger.debug(f"Could not check document metadata: {str(e)}")
