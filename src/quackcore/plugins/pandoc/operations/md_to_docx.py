# src/quackcore/plugins/pandoc/operations/md_to_docx.py
"""
Markdown to DOCX conversion operations.

This module provides functions for converting Markdown documents to DOCX
using pandoc with optimized settings.
"""

import logging
import time
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import ConversionMetrics, ConversionResult
from quackcore.plugins.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
)

logger = logging.getLogger(__name__)


def convert_markdown_to_docx(
        markdown_path: Path,
        output_path: Path,
        config: ConversionConfig,
        metrics: ConversionMetrics | None = None,
) -> ConversionResult:
    """
    Convert a Markdown file to DOCX.

    Args:
        markdown_path: Path to the Markdown file
        output_path: Path to save the DOCX file
        config: Conversion configuration
        metrics: Optional metrics tracker

    Returns:
        ConversionResult: Result of the conversion
    """
    import pypandoc

    filename = markdown_path.name
    start_time = time.time()

    # Ensure the input file exists
    file_info = fs.get_file_info(markdown_path)
    if not file_info.success or not file_info.exists:
        return ConversionResult.error_result(
            f"Input file not found: {markdown_path}",
            source_format="markdown",
            target_format="docx",
        )

    original_size = file_info.size or 0
    retry_count = 0

    while retry_count < config.retry_mechanism.max_conversion_retries:
        try:
            # Prepare pandoc arguments
            extra_args = prepare_pandoc_args(
                config, "markdown", "docx", config.md_to_docx_extra_args
            )

            # Ensure output directory exists
            fs.create_directory(output_path.parent, exist_ok=True)

            # Perform conversion directly to file
            logger.debug(f"Converting {markdown_path} to DOCX with args: {extra_args}")
            pypandoc.convert_file(
                str(markdown_path),
                "docx",
                format="markdown",
                outputfile=str(output_path),
                extra_args=extra_args,
            )

            # Calculate elapsed time
            conversion_time = time.time() - start_time

            # Get output file size
            output_info = fs.get_file_info(output_path)
            if not output_info.success:
                return ConversionResult.error_result(
                    f"Failed to get info for converted file: {output_path}",
                    source_format="markdown",
                    target_format="docx",
                )

            output_size = output_info.size or 0

            # Validate conversion
            validation_errors = validate_conversion(
                output_path, markdown_path, original_size, config
            )

            if validation_errors:
                error_str = "; ".join(validation_errors)
                logger.error(f"Conversion validation failed: {error_str}")

                retry_count += 1
                if retry_count >= config.retry_mechanism.max_conversion_retries:
                    return ConversionResult.error_result(
                        "Conversion validation failed after maximum retries",
                        validation_errors,
                        "markdown",
                        "docx",
                    )

                # Retry after delay
                time.sleep(config.retry_mechanism.conversion_retry_delay)
                continue

            # Track metrics if provided
            if metrics:
                track_metrics(
                    filename,
                    start_time,
                    original_size,
                    output_size,
                    metrics,
                    config,
                )
                metrics.successful_conversions += 1

            return ConversionResult.success_result(
                output_path,
                "markdown",
                "docx",
                conversion_time,
                output_size,
                original_size,
                f"Successfully converted {markdown_path} to DOCX",
            )

        except Exception as e:
            retry_count += 1
            logger.warning(
                f"Markdown to DOCX conversion attempt {retry_count} failed: {str(e)}")

            if retry_count >= config.retry_mechanism.max_conversion_retries:
                if metrics:
                    metrics.failed_conversions += 1
                    metrics.errors[str(markdown_path)] = str(e)

                return ConversionResult.error_result(
                    f"Failed to convert Markdown to DOCX: {str(e)}",
                    source_format="markdown",
                    target_format="docx",
                )

            time.sleep(config.retry_mechanism.conversion_retry_delay)

    # This should not happen, but just in case
    return ConversionResult.error_result(
        "Conversion failed after maximum retries",
        source_format="markdown",
        target_format="docx",
    )


def validate_conversion(
        output_path: Path, input_path: Path, original_size: int,
        config: ConversionConfig
) -> list[str]:
    """
    Validate the converted DOCX document.

    Args:
        output_path: Path to the output DOCX file
        input_path: Path to the input Markdown file
        original_size: Size of the original file
        config: Conversion configuration

    Returns:
        list[str]: List of validation error messages (empty if valid)
    """
    validation_errors = []
    validation = config.validation

    # Check if the output file exists
    output_info = fs.get_file_info(output_path)
    if not output_info.success or not output_info.exists:
        validation_errors.append(f"Output file does not exist: {output_path}")
        return validation_errors

    output_size = output_info.size or 0

    # Check file size
    valid_size, size_errors = check_file_size(output_size, validation.min_file_size)
    if not valid_size:
        validation_errors.extend(size_errors)

    # Check conversion ratio
    valid_ratio, ratio_errors = check_conversion_ratio(
        output_size, original_size, validation.conversion_ratio_threshold
    )
    if not valid_ratio:
        validation_errors.extend(ratio_errors)

    # Validate structure
    if validation.verify_structure and output_path.exists():
        is_valid, structure_errors = validate_docx_structure(
            output_path, validation.check_links
        )
        if not is_valid:
            validation_errors.extend(structure_errors)

    return validation_errors