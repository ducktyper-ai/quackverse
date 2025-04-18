# src/quackcore/integrations/pandoc/operations/md_to_docx.py
"""
Markdown to DOCX conversion _operations.

This module provides functions for converting Markdown documents to DOCX
using pandoc with optimized settings and error handling.
"""

import importlib
import time

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
    validate_docx_structure,
)
from quackcore.logging import get_logger

logger = get_logger(__name__)


def _validate_markdown_input(markdown_path: str) -> int:
    """
    Validate the input Markdown file and return its size.

    Args:
        markdown_path: Path to the Markdown file as a string.

    Returns:
        int: Size of the input Markdown file.

    Raises:
        QuackIntegrationError: If the input file is missing or empty.
    """
    file_info = fs.get_file_info(markdown_path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(
            f"Input file not found: {markdown_path}",
            {"path": markdown_path, "format": "markdown"},
        )

    try:
        original_size = int(file_info.size) if file_info.size is not None else 0
    except (TypeError, ValueError):
        logger.warning(
            f"Could not convert file size to integer: {file_info.size}, using default"
        )
        original_size = 0

    try:
        read_result = fs.read_text(markdown_path, encoding="utf-8")
        if not read_result.success:
            raise QuackIntegrationError(
                f"Could not read Markdown file: {read_result.error}",
                {"path": markdown_path},
            )
        markdown_content = read_result.content
        if not markdown_content.strip():
            raise QuackIntegrationError(
                f"Markdown file is empty: {markdown_path}",
                {"path": markdown_path},
            )
    except Exception as e:
        if isinstance(e, QuackIntegrationError):
            raise
        raise QuackIntegrationError(
            f"Could not read Markdown file: {str(e)}",
            {"path": markdown_path},
        ) from e

    return original_size


def _convert_markdown_to_docx_once(
    markdown_path: str, output_path: str, config: PandocConfig
) -> None:
    """
    Perform a single conversion attempt from Markdown to DOCX using pandoc.

    Args:
        markdown_path: Path to the Markdown file as a string.
        output_path: Path to save the DOCX file as a string.
        config: Conversion configuration.

    Raises:
        QuackIntegrationError: If pandoc conversion fails.
    """
    extra_args: list[str] = prepare_pandoc_args(
        config, "markdown", "docx", config.md_to_docx_extra_args
    )

    # Get the parent directory of the output file by splitting and joining parts
    parent_dir = fs.join_path(*fs.split_path(output_path)[:-1])
    dir_result = fs.create_directory(parent_dir, exist_ok=True)
    if not dir_result.success:
        raise QuackIntegrationError(
            f"Failed to create output directory: {dir_result.error}",
            {"path": parent_dir, "operation": "create_directory"},
        )

    logger.debug(f"Converting {markdown_path} to DOCX with args: {extra_args}")
    try:
        import pypandoc

        pypandoc.convert_file(
            markdown_path,
            "docx",
            format="markdown",
            outputfile=output_path,
            extra_args=extra_args,
        )
    except Exception as e:
        raise QuackIntegrationError(
            f"Pandoc conversion failed: {str(e)}",
            {"path": markdown_path, "format": "markdown"},
        ) from e


def _get_conversion_output(output_path: str, start_time: float) -> tuple[float, int]:
    """
    Retrieve conversion timing and output file size.

    Args:
        output_path: Path to the output DOCX file as a string.
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
            {"path": output_path, "format": "docx"},
        )

    try:
        output_size = int(output_info.size) if output_info.size is not None else 0
    except (TypeError, ValueError):
        logger.warning(
            f"Could not convert output size to integer: {output_info.size}, using default"
        )
        output_size = 0

    return conversion_time, output_size


def convert_markdown_to_docx(
    markdown_path: str,
    output_path: str,
    config: PandocConfig,
    metrics: ConversionMetrics | None = None,
) -> IntegrationResult[tuple[str, ConversionDetails]]:
    """
    Convert a Markdown file to DOCX.

    Args:
        markdown_path: Path to the Markdown file as a string.
        output_path: Path to save the DOCX file as a string.
        config: Conversion configuration.
        metrics: Optional metrics tracker.

    Returns:
        IntegrationResult[tuple[str, ConversionDetails]]: Result of the conversion.
    """
    # Get file name from the input path using fs.split_path
    filename: str = fs.split_path(markdown_path)[-1]

    if metrics is None:
        metrics = ConversionMetrics()

    try:
        original_size: int = _validate_markdown_input(markdown_path)
        max_retries: int = config.retry_mechanism.max_conversion_retries
        retry_count: int = 0

        while retry_count < max_retries:
            start_time: float = time.time()
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
                    retry_count += 1
                    if retry_count >= max_retries:
                        metrics.failed_conversions += 1
                        metrics.errors[markdown_path] = error_str
                        return IntegrationResult.error_result(
                            f"Conversion failed after maximum retries: {error_str}"
                        )

                    logger.warning(
                        f"Markdown to DOCX conversion attempt {retry_count} failed: {error_str}"
                    )
                    time.sleep(config.retry_mechanism.conversion_retry_delay)
                    continue

                track_metrics(
                    filename, start_time, original_size, output_size, metrics, config
                )
                metrics.successful_conversions += 1

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
                    metrics.failed_conversions += 1
                    metrics.errors[markdown_path] = str(e)
                    error_msg = (
                        f"Integration error: {str(e)}"
                        if isinstance(e, QuackIntegrationError)
                        else f"Failed to convert Markdown to DOCX: {str(e)}"
                    )
                    return IntegrationResult.error_result(error_msg)
                time.sleep(config.retry_mechanism.conversion_retry_delay)

        return IntegrationResult.error_result("Conversion failed after maximum retries")

    except Exception as e:
        metrics.failed_conversions += 1
        metrics.errors[markdown_path] = str(e)
        return IntegrationResult.error_result(
            f"Failed to convert Markdown to DOCX: {str(e)}"
        )


def validate_conversion(
    output_path: str, input_path: str, original_size: int, config: PandocConfig
) -> list[str]:
    """
    Validate the converted DOCX document.

    Args:
        output_path: Path to the output DOCX file as a string.
        input_path: Path to the input Markdown file as a string.
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

    try:
        output_size = int(output_info.size) if output_info.size is not None else 0
    except (TypeError, ValueError):
        logger.warning(
            f"Could not convert output size to integer: {output_info.size}, using default"
        )
        output_size = 0

    valid_size, size_errors = check_file_size(output_size, validation.min_file_size)
    if not valid_size:
        validation_errors.extend(size_errors)

    valid_ratio, ratio_errors = check_conversion_ratio(
        output_size, original_size, validation.conversion_ratio_threshold
    )
    if not valid_ratio:
        validation_errors.extend(ratio_errors)

    if validation.verify_structure and fs.get_file_info(output_path).exists:
        is_valid, structure_errors = validate_docx_structure(
            output_path, validation.check_links
        )
        if not is_valid:
            validation_errors.extend(structure_errors)
        _check_docx_metadata(output_path, input_path, validation.check_links)

    return validation_errors


def _check_docx_metadata(docx_path: str, source_path: str, check_links: bool) -> None:
    """
    Check DOCX metadata for references to the source file.
    This function is separated to handle import errors cleanly.

    Args:
        docx_path: Path to the DOCX file as a string.
        source_path: Path to the source file as a string.
        check_links: Whether to check for links/references.
    """
    try:
        try:
            docx = importlib.import_module("docx")
            Document = docx.Document
        except ImportError:
            logger.debug("python-docx not available for detailed metadata check")
            return

        doc = Document(docx_path)
        source_filename = fs.split_path(source_path)[-1]
        source_found = False

        if hasattr(doc, "core_properties"):
            core_props = doc.core_properties

            if (
                hasattr(core_props, "title")
                and core_props.title
                and source_filename in str(core_props.title)
            ):
                source_found = True
            elif (
                hasattr(core_props, "comments")
                and core_props.comments
                and source_filename in str(core_props.comments)
            ):
                source_found = True
            elif (
                hasattr(core_props, "subject")
                and core_props.subject
                and source_filename in str(core_props.subject)
            ):
                source_found = True

        if not source_found and check_links:
            logger.debug(
                f"Source file reference missing in document metadata: {source_filename}"
            )

    except Exception as e:
        logger.debug(f"Could not check document metadata: {str(e)}")
