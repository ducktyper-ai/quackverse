# src/quackcore/plugins/pandoc/converter.py
"""
Core converter implementation for pandoc integration.

This module provides the main DocumentConverter class that implements
the document conversion functionality.
"""

import logging
from datetime import datetime
from pathlib import Path

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import (  # FileInfo is not used in this file, so it's removed
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
)
from quackcore.plugins.pandoc.operations import (
    convert_html_to_markdown,
    convert_markdown_to_docx,
    get_file_info,
    verify_pandoc,
)

logger = logging.getLogger(__name__)


class DocumentConverter:
    """Handles document conversion using pandoc with retry and validation."""

    def __init__(self, config: ConversionConfig) -> None:
        """
        Initialize the document converter.

        Args:
            config: Conversion configuration

        Raises:
            QuackIntegrationError: If pandoc is not available
        """
        self.config = config
        self.metrics = ConversionMetrics()
        self._pandoc_version = verify_pandoc()  # Verify pandoc installation

    @property
    def pandoc_version(self) -> str:
        """
        Get the pandoc version.

        Returns:
            str: Pandoc version string
        """
        return self._pandoc_version

    def convert_file(
        self, input_path: Path, output_path: Path, output_format: str
    ) -> ConversionResult:
        """
        Convert a file from one format to another.

        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            output_format: Target format (markdown, docx, etc.)

        Returns:
            ConversionResult: Result of the conversion

        Raises:
            QuackIntegrationError: If the input file does not exist
        """
        # Initialize input_info to None so it's always defined
        input_info = None

        try:
            # Get file info and determine source format
            input_info = get_file_info(input_path)

            # Ensure output directory exists
            fs.create_directory(output_path.parent, exist_ok=True)

            # Perform conversion based on source and target formats
            if input_info.format == "html" and output_format == "markdown":
                return convert_html_to_markdown(
                    input_path, output_path, self.config, self.metrics
                )
            elif input_info.format == "markdown" and output_format == "docx":
                return convert_markdown_to_docx(
                    input_path, output_path, self.config, self.metrics
                )
            else:
                return ConversionResult.error_result(
                    f"Unsupported conversion: {input_info.format} to {output_format}",
                    source_format=input_info.format,
                    target_format=output_format,
                )

        except QuackIntegrationError as e:
            logger.error(f"Integration error during conversion: {str(e)}")
            return ConversionResult.error_result(
                str(e),
                source_format=input_info.format if input_info else None,
                target_format=output_format,
            )
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            return ConversionResult.error_result(
                f"Conversion error: {str(e)}",
                source_format=input_info.format if input_info else None,
                target_format=output_format,
            )

    def convert_batch(
        self, tasks: list[ConversionTask], output_dir: Path | None = None
    ) -> BatchConversionResult:
        """
        Convert a batch of files.

        Args:
            tasks: List of conversion tasks
            output_dir: Directory to save converted files (overrides task output paths)

        Returns:
            BatchConversionResult: Result of the batch conversion
        """
        output_directory = output_dir or self.config.output_dir
        fs.create_directory(output_directory, exist_ok=True)

        successful_files: list[Path] = []
        failed_files: list[Path] = []

        # Reset metrics for this batch
        self.metrics = ConversionMetrics(
            start_time=datetime.now(),
            total_attempts=len(tasks),
        )

        for task in tasks:
            try:
                # Determine output path if not specified in the task
                output_path = task.output_path
                if not output_path or output_dir:
                    extension = (
                        ".md"
                        if task.target_format == "markdown"
                        else f".{task.target_format}"
                    )
                    filename = task.source.path.stem + extension
                    output_path = output_directory / filename

                # Convert the file
                result = self.convert_file(
                    task.source.path, output_path, task.target_format
                )

                if result.success:
                    if result.content is not None:
                        successful_files.append(result.content)
                else:
                    failed_files.append(task.source.path)
                    logger.error(
                        f"Failed to convert {task.source.path} "
                        f"to {task.target_format}: {result.error}"
                    )
            except Exception as e:
                failed_files.append(task.source.path)
                logger.error(f"Error processing task for {task.source.path}: {str(e)}")
                self.metrics.errors[str(task.source.path)] = str(e)

        # Update metrics
        self.metrics.successful_conversions = len(successful_files)
        self.metrics.failed_conversions = len(failed_files)

        # Return batch result
        if not failed_files:
            return BatchConversionResult.success_result(
                successful_files,
                [],
                self.metrics,
                f"Successfully converted {len(successful_files)} files",
            )
        elif successful_files:
            return BatchConversionResult.success_result(
                successful_files,
                failed_files,
                self.metrics,
                f"Partially successful: "
                f"converted {len(successful_files)} files, "
                f"failed to convert {len(failed_files)} files",
            )
        else:
            return BatchConversionResult.error_result(
                "Failed to convert any files",
                [],
                failed_files,
                self.metrics,
            )

    def validate_conversion(self, output_path: Path, input_path: Path) -> bool:
        """
        Validate the converted document.

        Args:
            output_path: Path to the output file
            input_path: Path to the input file

        Returns:
            bool: True if validation passed, False otherwise
        """
        try:
            # Get file info - actually use input_info for validation
            input_info = fs.get_file_info(input_path)
            output_info = fs.get_file_info(output_path)

            if not output_info.success or not output_info.exists:
                logger.error(f"Output file does not exist: {output_path}")
                return False

            # Make sure the input file exists
            if not input_info.success or not input_info.exists:
                logger.error(f"Input file does not exist: {input_path}")
                return False

            # Calculate size difference for logging
            input_size = input_info.size or 0
            output_size = output_info.size or 0
            size_change_percentage = (
                (output_size / input_size * 100) if input_size > 0 else 0
            )
            logger.debug(
                f"Conversion size change: {input_size} → {output_size} "
                f"bytes ({size_change_percentage:.1f}%)"
            )

            # Validate based on file format
            extension = output_path.suffix.lower()

            if extension in (".md", ".markdown"):
                # For markdown, we can read the content and validate
                try:
                    content = output_path.read_text(encoding="utf-8")
                    return len(content.strip()) > 0
                except Exception as e:
                    logger.error(f"Failed to read markdown file: {e}")
                    return False
            elif extension == ".docx":
                from quackcore.plugins.pandoc.operations.utils import (
                    validate_docx_structure,
                )

                is_valid, _ = validate_docx_structure(
                    output_path, self.config.validation.check_links
                )
                return is_valid
            else:
                # For other formats, just check if the file exists with reasonable size
                return output_size > self.config.validation.min_file_size

        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return False


def create_converter(config: ConversionConfig) -> DocumentConverter:
    """
    Create a document converter instance.

    Args:
        config: Conversion configuration

    Returns:
        DocumentConverter: Initialized document converter
    """
    return DocumentConverter(config)
