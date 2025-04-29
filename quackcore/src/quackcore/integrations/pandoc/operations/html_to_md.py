# quackcore/src/quackcore/integrations/pandoc/operations/html_to_md.py
"""
HTML to Markdown conversion _operations.

This module provides functions for converting HTML documents to Markdown
using pandoc with optimized settings and error handling.
All file paths are represented as strings. Filesystem interactions are delegated
to the quackcore.fs service functions.
"""

import os
import re
import time

from quackcore.errors import QuackIntegrationError
from quackcore.fs.service import standalone
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

fs = standalone

def _validate_input(html_path: str, config: PandocConfig) -> int:
    """
    Validate the input HTML file and return its size.

    Args:
        html_path: Path to the HTML file as a string.
        config: Conversion configuration.

    Returns:
        int: Size of the input HTML file.

    Raises:
        QuackIntegrationError: If the input file is missing or has invalid structure.
    """
    file_info = fs.get_file_info(html_path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(f"Input file not found: {html_path}")

    try:
        if hasattr(file_info.size, "__int__"):
            original_size = int(file_info.size)
        elif file_info.size is not None:
            original_size = int(str(file_info.size))
        else:
            original_size = 0
    except (TypeError, ValueError):
        logger.warning(
            f"Could not convert file size to integer: {file_info.size}, using default size"
        )
        original_size = 1024

    if not config.validation.verify_structure:
        return original_size

    try:
        read_result = fs.read_text(html_path)
        if not read_result.success:
            raise QuackIntegrationError(
                f"Could not read HTML file: {read_result.error}"
            )
        html_content = read_result.content
        if not isinstance(html_content, str):
            logger.warning(
                f"HTML content is not a string, skipping validation: {type(html_content)}"
            )
            return original_size
        is_valid, html_errors = validate_html_structure(
            html_content, config.validation.check_links
        )
        if not is_valid:
            error_msg = "; ".join(html_errors)
            raise QuackIntegrationError(
                f"Invalid HTML structure in {html_path}: {error_msg}"
            )
    except Exception as e:
        if isinstance(e, QuackIntegrationError):
            raise
        logger.warning(f"Could not validate HTML structure: {str(e)}")

    return original_size


def _attempt_conversion(html_path: str, config: PandocConfig) -> str:
    """
    Perform a single attempt to convert an HTML file to Markdown using pandoc.

    Args:
        html_path: Path to the HTML file as a string.
        config: Conversion configuration.

    Returns:
        str: Cleaned Markdown content.

    Raises:
        QuackIntegrationError: If the pandoc conversion fails.
    """
    import pypandoc

    extra_args = prepare_pandoc_args(
        config, "html", "markdown", config.html_to_md_extra_args
    )
    logger.debug(f"Converting {html_path} to Markdown with args: {extra_args}")
    try:
        output = pypandoc.convert_file(
            html_path, "markdown", format="html", extra_args=extra_args
        )
    except Exception as e:
        raise QuackIntegrationError(f"Pandoc conversion failed: {str(e)}") from e

    return post_process_markdown(output)


def _write_and_validate_output(
    cleaned_markdown: str,
    output_path: str,
    input_path: str,
    original_size: int,
    config: PandocConfig,
    attempt_start: float,
) -> tuple[float, int, list[str]]:
    """
    Write the converted markdown to the output file and validate the conversion.

    Args:
        cleaned_markdown: The cleaned markdown content.
        output_path: Path to save the Markdown file as a string.
        input_path: Path to the original HTML file as a string.
        original_size: Size of the original HTML file.
        config: Conversion configuration.
        attempt_start: Timestamp when the attempt started.

    Returns:
        tuple: (conversion_time, output_size, validation_errors)
    """
    output_dir = os.path.dirname(output_path)
    dir_result = fs.create_directory(output_dir, exist_ok=True)
    if not dir_result.success:
        raise QuackIntegrationError(
            f"Failed to create output directory: {dir_result.error}"
        )

    write_result = fs.write_text(output_path, cleaned_markdown, encoding="utf-8")
    if not write_result.success:
        raise QuackIntegrationError(
            f"Failed to write output file: {write_result.error}"
        )

    conversion_time = time.time() - attempt_start

    output_info = fs.get_file_info(output_path)
    if not output_info.success:
        raise QuackIntegrationError(
            f"Failed to get info for converted file: {output_path}"
        )

    output_size = 0
    if (
        hasattr(write_result, "bytes_written")
        and write_result.bytes_written is not None
    ):
        try:
            output_size = int(write_result.bytes_written)
        except (TypeError, ValueError):
            logger.warning(
                f"Could not convert bytes_written to integer: {write_result.bytes_written}"
            )

    if output_size == 0 and output_info.size is not None:
        try:
            output_size = int(output_info.size)
        except (TypeError, ValueError):
            logger.warning(
                f"Could not convert file size to integer: {output_info.size}"
            )

    validation_errors = validate_conversion(
        output_path, input_path, original_size, config
    )

    return conversion_time, output_size, validation_errors


def convert_html_to_markdown(
    html_path: str,
    output_path: str,
    config: PandocConfig,
    metrics: ConversionMetrics | None = None,
) -> IntegrationResult[tuple[str, ConversionDetails]]:
    """
    Convert an HTML file to Markdown.

    Args:
        html_path: Path to the HTML file as a string.
        output_path: Path to save the Markdown file as a string.
        config: Conversion configuration.
        metrics: Optional metrics tracker.

    Returns:
        IntegrationResult containing a tuple of (output_path, ConversionDetails).
    """
    filename = os.path.basename(html_path)

    if metrics is None:
        metrics = ConversionMetrics()

    try:
        original_size = _validate_input(html_path, config)
        max_retries = config.retry_mechanism.max_conversion_retries
        for attempt in range(1, max_retries + 1):
            attempt_start = time.time()
            try:
                cleaned_markdown = _attempt_conversion(html_path, config)
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
                    error_msg = "; ".join(validation_errors)
                    logger.error(
                        f"Conversion validation failed on attempt {attempt}: {error_msg}"
                    )
                    if attempt == max_retries:
                        metrics.failed_conversions += 1
                        metrics.errors[html_path] = error_msg
                        return IntegrationResult.error_result(
                            "Conversion validation failed after maximum retries: "
                            + error_msg
                        )
                    time.sleep(config.retry_mechanism.conversion_retry_delay)
                    continue

                track_metrics(
                    filename, attempt_start, original_size, output_size, metrics, config
                )
                metrics.successful_conversions += 1

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
                error_msg = (
                    f"Integration error: {str(e)}"
                    if isinstance(e, QuackIntegrationError)
                    else f"Failed to convert HTML to Markdown: {str(e)}"
                )
                logger.warning(
                    f"HTML to Markdown conversion attempt {attempt} failed: {str(e)}"
                )
                if attempt == max_retries:
                    metrics.failed_conversions += 1
                    metrics.errors[html_path] = str(e)
                    return IntegrationResult.error_result(error_msg)
                time.sleep(config.retry_mechanism.conversion_retry_delay)

        return IntegrationResult.error_result("Conversion failed after maximum retries")
    except Exception as e:
        metrics.failed_conversions += 1
        metrics.errors[html_path] = str(e)
        return IntegrationResult.error_result(
            f"Failed to convert HTML to Markdown: {str(e)}"
        )


def post_process_markdown(markdown_content: str) -> str:
    """
    Post-process markdown content for cleaner output.

    Args:
        markdown_content: Raw markdown content from pandoc.

    Returns:
        Cleaned markdown content.
    """
    cleaned = re.sub(r"{[^}]*}", "", markdown_content)
    cleaned = re.sub(r":::+\s*[^\n]*\n", "", cleaned)
    cleaned = re.sub(r"<div[^>]*>|</div>", "", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"<!--[^>]*-->", "", cleaned)
    cleaned = re.sub(r"\n\s*\n-", "\n-", cleaned)
    return cleaned


def validate_conversion(
    output_path: str, input_path: str, original_size: int, config: PandocConfig
) -> list[str]:
    """
    Validate the converted markdown document.

    Args:
        output_path: Path to the output markdown file as a string.
        input_path: Path to the input HTML file as a string.
        original_size: Size of the original file.
        config: Conversion configuration.

    Returns:
        List of validation error messages (empty if valid).
    """
    validation_errors = []
    output_info = fs.get_file_info(output_path)
    if not output_info.success or not output_info.exists:
        validation_errors.append(f"Output file does not exist: {output_path}")
        return validation_errors

    try:
        output_size = int(output_info.size) if output_info.size is not None else 0
    except (TypeError, ValueError):
        logger.warning(
            f"Could not convert output size to integer: {output_info.size}, using 0"
        )
        output_size = 0

    valid_size, size_errors = check_file_size(
        output_size, config.validation.min_file_size
    )
    if not valid_size:
        validation_errors.extend(size_errors)

    valid_ratio, ratio_errors = check_conversion_ratio(
        output_size, original_size, config.validation.conversion_ratio_threshold
    )
    if not valid_ratio:
        validation_errors.extend(ratio_errors)

    try:
        read_result = fs.read_text(output_path, encoding="utf-8")
        if not read_result.success:
            validation_errors.append(f"Error reading output file: {read_result.error}")
            return validation_errors

        content = read_result.content
        if not content.strip():
            validation_errors.append("Output file is empty")
        elif len(content.strip()) < 10 and "# " not in content:
            validation_errors.append("Output file contains minimal content")
        else:
            has_headers = "# " in content or "## " in content
            large_content = len(content.strip()) > 100
            if not has_headers and large_content:
                logger.warning(f"No headers found in converted markdown: {output_path}")
                if config.validation.verify_structure:
                    validation_errors.append("No headers found in converted markdown")

        source_file_name = os.path.basename(input_path)
        if config.validation.check_links and source_file_name not in content:
            logger.debug(
                f"Source file reference missing in markdown output: {source_file_name}"
            )
    except Exception as e:
        validation_errors.append(f"Error reading output file: {str(e)}")

    return validation_errors
