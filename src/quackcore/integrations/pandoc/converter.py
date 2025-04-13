# src/quackcore/integrations/pandoc/converter.py
"""
Core converter implementation for Pandoc integration.

This module provides the main DocumentConverter class that implements
the document conversion functionality using Pandoc.
"""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import OperationResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionMetrics, ConversionTask
from quackcore.integrations.pandoc.operations import (
    convert_html_to_markdown,
    convert_markdown_to_docx,
    verify_pandoc,
)
from quackcore.integrations.pandoc.operations.utils import get_file_info
from quackcore.integrations.pandoc.protocols import BatchConverterProtocol, DocumentConverterProtocol
from quackcore.logging import get_logger
from quackcore.fs import service as fs

logger = get_logger(__name__)


class DocumentConverter(DocumentConverterProtocol, BatchConverterProtocol):
    """
    Handles document conversion using pandoc with retry and validation.
    """

    def __init__(self, config: PandocConfig) -> None:
        """
        Initialize the document converter.

        Args:
            config: Conversion configuration.

        Raises:
            QuackIntegrationError: If pandoc is not available.
        """
        self.config: PandocConfig = config
        self.metrics: ConversionMetrics = ConversionMetrics(start_time=datetime.now())
        self._pandoc_version: str = verify_pandoc()

    @property
    def pandoc_version(self) -> str:
        """Get the pandoc version."""
        return self._pandoc_version

    def convert_file(self, input_path: Path, output_path: Path, output_format: str) -> IntegrationResult[Path]:
        """
        Convert a file from one format to another.

        Args:
            input_path: Path to the input file.
            output_path: Path to the output file.
            output_format: Target format (e.g., "markdown" or "docx").

        Returns:
            IntegrationResult[Path]: Result of the conversion containing the output path.
        """
        try:
            input_info = get_file_info(input_path)
            dir_result: OperationResult = fs.create_directory(output_path.parent, exist_ok=True)
            if not dir_result.success:
                return IntegrationResult.error_result(f"Failed to create output directory: {dir_result.error}")

            if input_info.format == "html" and output_format == "markdown":
                result = convert_html_to_markdown(input_path, output_path, self.config, self.metrics)
                if result.success and result.content:
                    return IntegrationResult.success_result(
                        result.content[0],
                        message=f"Successfully converted {input_path} to Markdown"
                    )
                return IntegrationResult.error_result(result.error or "Conversion failed")
            elif input_info.format == "markdown" and output_format == "docx":
                result = convert_markdown_to_docx(input_path, output_path, self.config, self.metrics)
                if result.success and result.content:
                    return IntegrationResult.success_result(
                        result.content[0],
                        message=f"Successfully converted {input_path} to DOCX"
                    )
                return IntegrationResult.error_result(result.error or "Conversion failed")
            else:
                return IntegrationResult.error_result(f"Unsupported conversion: {input_info.format} to {output_format}")
        except QuackIntegrationError as e:
            logger.error(f"Integration error during conversion: {str(e)}")
            return IntegrationResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            return IntegrationResult.error_result(f"Conversion error: {str(e)}")

    def convert_batch(self, tasks: Sequence[ConversionTask], output_dir: Path | None = None) -> IntegrationResult[list[Path]]:
        """
        Convert a batch of files.

        Args:
            tasks: List of conversion tasks.
            output_dir: Directory to save converted files (overrides task output paths).

        Returns:
            IntegrationResult[list[Path]]: Result of the batch conversion.
        """
        output_directory: Path = output_dir if output_dir is not None else self.config.output_dir
        dir_result: OperationResult = fs.create_directory(output_directory, exist_ok=True)
        if not dir_result.success:
            return IntegrationResult.error_result(f"Failed to create output directory: {dir_result.error}")

        successful_files: list[Path] = []
        failed_files: list[Path] = []
        self.metrics = ConversionMetrics(start_time=datetime.now(), total_attempts=len(tasks))

        for task in tasks:
            try:
                output_path: Path = task.output_path if task.output_path is not None else (
                    output_directory / (task.source.path.stem + (".md" if task.target_format == "markdown" else f".{task.target_format}"))
                )
                result = self.convert_file(task.source.path, output_path, task.target_format)
                if result.success and result.content:
                    successful_files.append(result.content)
                else:
                    failed_files.append(task.source.path)
                    logger.error(f"Failed to convert {task.source.path} to {task.target_format}: {result.error}")
            except Exception as e:
                failed_files.append(task.source.path)
                logger.error(f"Error processing task for {task.source.path}: {str(e)}")
                self.metrics.errors[str(task.source.path)] = str(e)
                self.metrics.failed_conversions += 1

        self.metrics.successful_conversions = len(successful_files)
        if len(failed_files) > self.metrics.failed_conversions:
            self.metrics.failed_conversions = len(failed_files)

        if not failed_files:
            return IntegrationResult.success_result(
                successful_files,
                message=f"Successfully converted {len(successful_files)} files"
            )
        elif successful_files:
            return IntegrationResult.success_result(
                successful_files,
                message=f"Partially successful: converted {len(successful_files)} files, failed to convert {len(failed_files)} files"
            )
        else:
            failed_files_str: str = ", ".join(str(f) for f in failed_files[:5])
            if len(failed_files) > 5:
                failed_files_str += f" and {len(failed_files) - 5} more"
            error_msg: str = f"Failed to convert any files. Failed files: {failed_files_str}"
            return IntegrationResult.error_result(
                error=error_msg,
                message=f"All {len(failed_files)} conversion tasks failed. See logs for details."
            )

    def validate_conversion(self, output_path: Path, input_path: Path) -> bool:
        """
        Validate the converted document.

        Args:
            output_path: Path to the output file.
            input_path: Path to the input file.

        Returns:
            bool: True if validation passed, False otherwise.
        """
        try:
            output_info = fs.get_file_info(output_path)
            input_info = fs.get_file_info(input_path)
            if not output_info.success or not output_info.exists:
                logger.error(f"Output file does not exist: {output_path}")
                return False
            if not input_info.success or not input_info.exists:
                logger.error(f"Input file does not exist: {input_path}")
                return False

            input_size = input_info.size or 0
            output_size = output_info.size or 0
            size_change_percentage = (output_size / input_size * 100) if input_size > 0 else 0
            logger.debug(f"Conversion size change: {input_size} → {output_size} bytes ({size_change_percentage:.1f}%)")

            extension = fs.get_extension(output_path)
            if extension in ("md", "markdown"):
                try:
                    read_result = fs.read_text(output_path, encoding="utf-8")
                    if not read_result.success:
                        logger.error(f"Failed to read markdown file: {read_result.error}")
                        return False
                    return len(read_result.content.strip()) > 0
                except Exception as e:
                    logger.error(f"Failed to read markdown file: {e}")
                    return False
            elif extension == "docx":
                from quackcore.integrations.pandoc.operations.utils import validate_docx_structure
                is_valid, _ = validate_docx_structure(output_path, self.config.validation.check_links)
                return is_valid
            else:
                return output_size > self.config.validation.min_file_size
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return False


def create_converter(config: PandocConfig) -> DocumentConverter:
    """
    Create a document converter instance.

    Args:
        config: Conversion configuration.

    Returns:
        DocumentConverter: Initialized document converter.
    """
    return DocumentConverter(config)
