# src/quackcore/integrations/pandoc/operations/html_to_md.py
"""
HTML to Markdown conversion operations.

This module provides functions for converting HTML documents to Markdown
using pandoc with optimized settings and error handling.
"""

import re
import time
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionDetails, ConversionMetrics
from quackcore.integrations.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    prepare_pandoc_args,
    track_metrics,
    validate_html_structure,
)
from quackcore.logging import get_logger

logger = get_logger(__name__)


def _validate_input(html_path: Path, config: PandocConfig) -> int:
    """
    Validate the input HTML file and return its size.

    Args:
        html_path: Path to the HTML file.
        config: Conversion configuration.

    Returns:
        int: Size of the input HTML file.

    Raises:
        QuackIntegrationError: If the input file is missing or has invalid structure.
    """
    file_info = fs.service.get_file_info(html_path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(f"Input file not found: {html_path}")

    original_size: int = file_info.size or 0

    if config.validation.verify_structure:
        try:
            read_result = fs.service.read_text(html_path)
            if not read_result.success:
                raise QuackIntegrationError(
                    f"Could not read HTML file: {read_result.error}"
                )

            html_content = read_result.content
            is_valid, html_errors = validate_html_structure(
                html_content, config.validation.check_links
            )
            if not is_valid:
                error_msg: str = "; ".join(html_errors)
                raise QuackIntegrationError(
                    f"Invalid HTML structure in {html_path}: {error_msg}"
                )
        except Exception as e:
            if not isinstance(e, QuackIntegrationError):
                logger.warning(f"Could not validate HTML structure: {str(e)}")
            else:
                raise

    return original_size


def _attempt_conversion(html_path: Path, config: PandocConfig) -> str:
    """
    Perform a single attempt to convert an HTML file to Markdown using pandoc.

    Args:
        html_path: Path to the HTML file.
        config: Conversion configuration.

    Returns:
        str: Cleaned Markdown content.

    Raises:
        QuackIntegrationError: If the pandoc conversion fails.
    """
    import pypandoc

    extra_args: list[str] = prepare_pandoc_args(
        config, "html", "markdown", config.html_to_md_extra_args
    )
    logger.debug(f"Converting {html_path} to Markdown with args: {extra_args}")
    try:
        output: str = pypandoc.convert_file(
            str(html_path),
            "markdown",
            format="html",
            extra_args=extra_args,
        )
    except Exception as e:
        raise QuackIntegrationError(f"Pandoc conversion failed: {str(e)}") from e

    return post_process_markdown(output)


def _write_and_validate_output(
    cleaned_markdown: str,
    output_path: Path,
    input_path: Path,
    original_size: int,
    config: PandocConfig,
    attempt_start: float,
) -> tuple[float, int, list[str]]:
    """
    Write the converted markdown to the output file and validate the conversion.

    Args:
        cleaned_markdown: The cleaned markdown content.
        output_path: Path to save the Markdown file.
        input_path: Path to the original HTML file.
        original_size: Size of the original HTML file.
        config: Conversion configuration.
        attempt_start: Timestamp when the attempt started.

    Returns:
        tuple: (conversion_time, output_size, validation_errors)
    """
    # Create output directory if it doesn't exist
    dir_result = fs.service.create_directory(output_path.parent, exist_ok=True)
    if not dir_result.success:
        raise QuackIntegrationError(
            f"Failed to create output directory: {dir_result.error}"
        )

    # Write the content
    write_result = fs.service.write_text(
        output_path, cleaned_markdown, encoding="utf-8"
    )
    if not write_result.success:
        raise QuackIntegrationError(
            f"Failed to write output file: {write_result.error}"
        )

    conversion_time: float = time.time() - attempt_start

    # Get output file info
    output_info = fs.service.get_file_info(output_path)
    if not output_info.success:
        raise QuackIntegrationError(
            f"Failed to get info for converted file: {output_path}"
        )
    output_size: int = output_info.size or 0

    # Validate the conversion
    validation_errors: list[str] = validate_conversion(
        output_path, input_path, original_size, config
    )

    return conversion_time, output_size, validation_errors


def convert_html_to_markdown(
    html_path: Path,
    output_path: Path,
    config: PandocConfig,
    metrics: ConversionMetrics | None = None,
) -> IntegrationResult[tuple[Path, ConversionDetails]]:
    """
    Convert an HTML file to Markdown.

    Args:
        html_path: Path to the HTML file.
        output_path: Path to save the Markdown file.
        config: Conversion configuration.
        metrics: Optional metrics tracker.

    Returns:
        IntegrationResult[tuple[Path, ConversionDetails]]: Result of the conversion.
    """
    filename: str = html_path.name

    # Validate input file and get its size.
    original_size: int = _validate_input(html_path, config)

    max_retries: int = config.retry_mechanism.max_conversion_retries
    for attempt in range(1, max_retries + 1):
        attempt_start: float = time.time()
        try:
            cleaned_markdown: str = _attempt_conversion(html_path, config)
            conversion_time, output_size, validation_errors = (
                _write_and_validate_output(
                    cleaned_markdown,
                    output_path,
                    html_path,
                    original_size,
                    config,
                    attempt_start,
                )
            )

            if validation_errors:
                error_str: str = "; ".join(validation_errors)
                logger.error(
                    f"Conversion validation failed on attempt {attempt}: {error_str}"
                )
                if attempt == max_retries:
                    if metrics:
                        metrics.failed_conversions += 1
                        metrics.errors[str(html_path)] = error_str
                    return IntegrationResult.error_result(
                        "Conversion validation "
                        "failed after maximum retries: " + error_str
                    )
                time.sleep(config.retry_mechanism.conversion_retry_delay)
                continue

            if metrics:
                track_metrics(
                    filename, attempt_start, original_size, output_size, metrics, config
                )
                metrics.successful_conversions += 1

            # Create conversion details
            details = ConversionDetails(
                source_format="html",
                target_format="markdown",
                conversion_time=conversion_time,
                output_size=output_size,
                input_size=original_size,
            )

            return IntegrationResult.success_result(
                (output_path, details),
                message=f"Successfully converted {html_path} to Markdown",
            )

        except Exception as e:
            error_msg: str = (
                f"Integration error: {str(e)}"
                if isinstance(e, QuackIntegrationError)
                else f"Failed to convert HTML to Markdown: {str(e)}"
            )
            logger.warning(
                f"HTML to Markdown conversion attempt {attempt} failed: {str(e)}"
            )
            if attempt == max_retries:
                if metrics:
                    metrics.failed_conversions += 1
                    metrics.errors[str(html_path)] = str(e)
                return IntegrationResult.error_result(error_msg)
            time.sleep(config.retry_mechanism.conversion_retry_delay)

    return IntegrationResult.error_result("Conversion failed after maximum retries")


def post_process_markdown(markdown_content: str) -> str:
    """
    Post-process markdown content for cleaner output.

    Args:
        markdown_content: Raw markdown content from pandoc.

    Returns:
        str: Cleaned markdown content.
    """
    cleaned: str = re.sub(r"{[^}]*}", "", markdown_content)
    cleaned = re.sub(r":::+\s*[^\n]*\n", "", cleaned)
    cleaned = re.sub(r"<div[^>]*>|</div>", "", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"<!--[^>]*-->", "", cleaned)
    cleaned = re.sub(r"\n\s*\n-", "\n-", cleaned)
    return cleaned


def validate_conversion(
    output_path: Path,
    input_path: Path,
    original_size: int,
    config: PandocConfig,
) -> list[str]:
    """
    Validate the converted markdown document.

    Args:
        output_path: Path to the output markdown file.
        input_path: Path to the input HTML file.
        original_size: Size of the original file.
        config: Conversion configuration.

    Returns:
        list[str]: List of validation error messages (empty if valid).
    """
    validation_errors: list[str] = []

    # Get info about output file
    output_info = fs.service.get_file_info(output_path)
    if not output_info.success or not output_info.exists:
        validation_errors.append(f"Output file does not exist: {output_path}")
        return validation_errors

    output_size: int = output_info.size or 0

    # Check file size
    valid_size, size_errors = check_file_size(
        output_size, config.validation.min_file_size
    )
    if not valid_size:
        validation_errors.extend(size_errors)

    # Check conversion ratio
    valid_ratio, ratio_errors = check_conversion_ratio(
        output_size, original_size, config.validation.conversion_ratio_threshold
    )
    if not valid_ratio:
        validation_errors.extend(ratio_errors)

    # Check content
    try:
        read_result = fs.service.read_text(output_path, encoding="utf-8")
        if not read_result.success:
            validation_errors.append(f"Error reading output file: {read_result.error}")
            return validation_errors

        content = read_result.content
        if not content.strip():
            validation_errors.append("Output file is empty")
        elif len(content.strip()) < 10:
            validation_errors.append("Output file contains minimal content")

        if "# " not in content and "## " not in content:
            logger.warning(f"No headers found in converted markdown: {output_path}")

        source_file_name: str = input_path.name
        if config.validation.check_links and source_file_name not in content:
            logger.debug(
                f"Source file reference missing in markdown output: {source_file_name}"
            )
    except Exception as e:
        validation_errors.append(f"Error reading output file: {str(e)}")

    return validation_errors
