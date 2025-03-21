# src/quackcore/plugins/pandoc/operations/html_to_md.py
"""
HTML to Markdown conversion operations.

This module provides functions for converting HTML documents to Markdown
using pandoc with optimized settings.
"""

import re
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
    validate_html_structure,
)

logger = logging.getLogger(__name__)


def convert_html_to_markdown(
        html_path: Path,
        output_path: Path,
        config: ConversionConfig,
        metrics: ConversionMetrics | None = None,
) -> ConversionResult:
    """
    Convert an HTML file to Markdown.

    Args:
        html_path: Path to the HTML file
        output_path: Path to save the Markdown file
        config: Conversion configuration
        metrics: Optional metrics tracker

    Returns:
        ConversionResult: Result of the conversion
    """
    import pypandoc

    filename = html_path.name
    start_time = time.time()

    # Ensure the input file exists
    file_info = fs.get_file_info(html_path)
    if not file_info.success or not file_info.exists:
        return ConversionResult.error_result(
            f"Input file not found: {html_path}",
            source_format="html",
            target_format="markdown",
        )

    original_size = file_info.size or 0
    retry_count = 0

    while retry_count < config.retry_mechanism.max_conversion_retries:
        try:
            # Prepare pandoc arguments
            extra_args = prepare_pandoc_args(
                config, "html", "markdown", config.html_to_md_extra_args
            )

            # Perform conversion
            logger.debug(f"Converting {html_path} to Markdown with args: {extra_args}")
            output = pypandoc.convert_file(
                str(html_path),
                "markdown",
                format="html",
                extra_args=extra_args,
            )

            # Post-process cleanup
            cleaned = post_process_markdown(output)

            # Ensure output directory exists
            fs.create_directory(output_path.parent, exist_ok=True)

            # Write output
            write_result = fs.write_text(output_path, cleaned, encoding="utf-8")
            if not write_result.success:
                return ConversionResult.error_result(
                    f"Failed to write output file: {write_result.error}",
                    source_format="html",
                    target_format="markdown",
                )

            # Calculate elapsed time
            conversion_time = time.time() - start_time

            # Get output file size
            output_info = fs.get_file_info(output_path)
            if not output_info.success:
                return ConversionResult.error_result(
                    f"Failed to get info for converted file: {output_path}",
                    source_format="html",
                    target_format="markdown",
                )

            output_size = output_info.size or 0

            # Validate conversion
            validation_errors = validate_conversion(
                output_path, html_path, original_size, config
            )

            if validation_errors:
                error_str = "; ".join(validation_errors)
                logger.error(f"Conversion validation failed: {error_str}")

                retry_count += 1
                if retry_count >= config.retry_mechanism.max_conversion_retries:
                    return ConversionResult.error_result(
                        "Conversion validation failed after maximum retries",
                        validation_errors,
                        "html",
                        "markdown",
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
                "html",
                "markdown",
                conversion_time,
                output_size,
                original_size,
                f"Successfully converted {html_path} to Markdown",
            )

        except Exception as e:
            retry_count += 1
            logger.warning(
                f"HTML to Markdown conversion attempt {retry_count} failed: {str(e)}")

            if retry_count >= config.retry_mechanism.max_conversion_retries:
                if metrics:
                    metrics.failed_conversions += 1
                    metrics.errors[str(html_path)] = str(e)

                return ConversionResult.error_result(
                    f"Failed to convert HTML to Markdown: {str(e)}",
                    source_format="html",
                    target_format="markdown",
                )

            time.sleep(config.retry_mechanism.conversion_retry_delay)

    # This should not happen, but just in case
    return ConversionResult.error_result(
        "Conversion failed after maximum retries",
        source_format="html",
        target_format="markdown",
    )


def post_process_markdown(markdown_content: str) -> str:
    """
    Post-process markdown content for cleaner output.

    Args:
        markdown_content: Raw markdown content from pandoc

    Returns:
        str: Cleaned markdown content
    """
    # Remove all class/style attributes
    cleaned = re.sub(r'{[^}]*}', '', markdown_content)

    # Remove div containers
    cleaned = re.sub(r':::+\s*[^\n]*\n', '', cleaned)

    # Remove div tags
    cleaned = re.sub(r'<div[^>]*>|</div>', '', cleaned)

    # Normalize whitespace
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

    # Remove HTML comments
    cleaned = re.sub(r'<!--[^>]*-->', '', cleaned)

    # Fix bullet lists that might have been affected by div removal
    cleaned = re.sub(r'\n\s*\n-', '\n-', cleaned)

    return cleaned


def validate_conversion(
        output_path: Path, input_path: Path, original_size: int,
        config: ConversionConfig
) -> list[str]:
    """
    Validate the converted markdown document.

    Args:
        output_path: Path to the output markdown file
        input_path: Path to the input HTML file
        original_size: Size of the original file
        config: Conversion configuration

    Returns:
        list[str]: List of validation error messages (empty if valid)
    """
    validation_errors: list[str] = []
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

    # Validate content
    if not output_path.exists():
        validation_errors.append(f"Output file does not exist: {output_path}")
    else:
        # Check if the file contains actual markdown content
        try:
            content = output_path.read_text(encoding="utf-8")
            if not content.strip():
                validation_errors.append("Output file is empty")
            elif len(content.strip()) < 10:  # Arbitrary small content check
                validation_errors.append("Output file contains minimal content")

            # Check for basic markdown features (headers, paragraphs)
            if "# " not in content and "## " not in content:
                # It's possible to have valid markdown without headers,
                # but most documents should have at least one
                logger.warning(f"No headers found in converted markdown: {output_path}")
        except Exception as e:
            validation_errors.append(f"Error reading output file: {str(e)}")

    return validation_errors