# quackcore/src/quackcore/integrations/pandoc/converter.py
"""
Core converter implementation for Pandoc integration.

This module provides the main DocumentConverter class that implements
the document conversion functionality using Pandoc. In this refactored
version, all file paths are represented as strings. Filesystem _operations
such as reading file info, creating directories, writing output files, etc.,
are delegated to the quackcore.fs service functions.
"""

import os
import sys
import types
from collections.abc import Sequence
from datetime import datetime
from types import SimpleNamespace

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import OperationResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc import PandocConfig
from quackcore.integrations.pandoc.models import ConversionMetrics, ConversionTask
from quackcore.integrations.pandoc.operations import (
    verify_pandoc,
)
from quackcore.integrations.pandoc.protocols import (
    BatchConverterProtocol,
    DocumentConverterProtocol,
)
from quackcore.logging import get_logger

logger = get_logger(__name__)

# Ensure fs module is properly available
if 'quackcore.fs.service' not in sys.modules:
    # Create the module hierarchy if needed
    if 'quackcore' not in sys.modules:
        quackcore_mod = types.ModuleType('quackcore')
        sys.modules['quackcore'] = quackcore_mod

    if 'quackcore.fs' not in sys.modules:
        fs_mod = types.ModuleType('quackcore.fs')
        sys.modules['quackcore.fs'] = fs_mod

    service_mod = types.ModuleType('quackcore.fs.service')
    service_mod.standalone = SimpleNamespace()
    sys.modules['quackcore.fs.service'] = service_mod


class DocumentConverter(DocumentConverterProtocol, BatchConverterProtocol):
    """
    Handles document conversion using Pandoc with retry and validation.

    All file paths throughout this class are handled as strings.
    """

    def __init__(self, config: PandocConfig) -> None:
        """
        Initialize the document converter.

        Args:
            config: The Pandoc conversion configuration.

        Raises:
            QuackIntegrationError: If Pandoc is not available.
        """
        self.config: PandocConfig = config
        self.metrics: ConversionMetrics = ConversionMetrics(start_time=datetime.now())
        self._pandoc_version: str = verify_pandoc()

    @property
    def pandoc_version(self) -> str:
        """Get the Pandoc version."""
        return self._pandoc_version

    def convert_file(
            self, input_path: str, output_path: str, output_format: str
    ) -> IntegrationResult[str]:
        """
        Convert a file from one format to another.

        Args:
            input_path: Input file path (as a string).
            output_path: Output file path (as a string).
            output_format: Target format (e.g. "markdown" or "docx").

        Returns:
            IntegrationResult containing the output file path (string).
        """
        try:
            # Use operations.utils directly (not api) to get file info
            from quackcore.integrations.pandoc.operations.utils import get_file_info
            input_info = get_file_info(input_path)

            # Create output directory from the output_path (using os.path.dirname)
            from quackcore.fs.service import standalone as fs
            output_dir = os.path.dirname(output_path)
            dir_result: OperationResult = fs.create_directory(output_dir, exist_ok=True)
            if not dir_result.success:
                return IntegrationResult.error_result(
                    f"Failed to create output directory: {dir_result.error}"
                )

            if input_info.format == "html" and output_format == "markdown":
                # Use operations directly instead of _operations
                from quackcore.integrations.pandoc.operations import (
                    convert_html_to_markdown,
                )
                result = convert_html_to_markdown(
                    input_path, output_path, self.config, self.metrics
                )
                if result.success and result.content:
                    # Unpack the returned tuple
                    output_path_str = result.content[0]
                    return IntegrationResult.success_result(
                        output_path_str,
                        message=f"Successfully converted {input_path} to Markdown",
                    )
                return IntegrationResult.error_result(
                    result.error or "Conversion failed"
                )
            elif input_info.format == "markdown" and output_format == "docx":
                # Use operations directly instead of _operations
                from quackcore.integrations.pandoc.operations import (
                    convert_markdown_to_docx,
                )
                result = convert_markdown_to_docx(
                    input_path, output_path, self.config, self.metrics
                )
                if result.success and result.content:
                    # Unpack the returned tuple
                    output_path_str = result.content[0]
                    return IntegrationResult.success_result(
                        output_path_str,
                        message=f"Successfully converted {input_path} to DOCX",
                    )
                return IntegrationResult.error_result(
                    result.error or "Conversion failed"
                )
            else:
                return IntegrationResult.error_result(
                    f"Unsupported conversion: {input_info.format} to {output_format}"
                )
        except QuackIntegrationError as e:
            logger.error(f"Integration error during conversion: {str(e)}")
            return IntegrationResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            return IntegrationResult.error_result(f"Conversion error: {str(e)}")

    def convert_batch(
            self, tasks: Sequence[ConversionTask], output_dir: str | None = None
    ) -> IntegrationResult[list[str]]:
        """
        Convert a batch of files.

        Args:
            tasks: Sequence of conversion tasks.
            output_dir: Directory to save converted files (as a string).
                        If not provided, the value from the configuration is used.

        Returns:
            IntegrationResult containing a list of successfully converted file paths (as strings).
        """
        # Use the provided output_dir, or fallback to the config value (already a string)
        from quackcore.fs.service import standalone as fs
        output_directory: str = (
            output_dir if output_dir is not None else self.config.output_dir
        )
        dir_result: OperationResult = fs.create_directory(
            output_directory, exist_ok=True
        )
        if not dir_result.success:
            return IntegrationResult.error_result(
                f"Failed to create output directory: {dir_result.error}"
            )

        successful_files: list[str] = []
        failed_files: list[str] = []
        self.metrics = ConversionMetrics(
            start_time=datetime.now(), total_attempts=len(tasks)
        )

        for task in tasks:
            try:
                # Determine the output path: if task.output_path is provided (as a string), use it.
                # Otherwise, construct the output filename from the source path and target format.
                if task.output_path is not None:
                    output_path = task.output_path
                else:
                    # Get the file name safely using fs.split_path
                    split_result = fs.split_path(task.source.path)
                    if not split_result.success:
                        logger.error(f"Failed to split path: {split_result.error}")
                        failed_files.append(task.source.path)
                        continue

                    # Extract the filename and stem
                    filename = split_result.data[-1]
                    base_name, _ = os.path.splitext(filename)

                    # Create the extension based on target format
                    ext = (
                        ".md"
                        if task.target_format == "markdown"
                        else f".{task.target_format}"
                    )

                    # Join the path components
                    join_result = fs.join_path(output_directory, base_name + ext)
                    if not join_result.success:
                        logger.error(f"Failed to join path: {join_result.error}")
                        failed_files.append(task.source.path)
                        continue

                    output_path = join_result.data

                result = self.convert_file(
                    task.source.path, output_path, task.target_format
                )
                if result.success and result.content:
                    successful_files.append(result.content)
                else:
                    failed_files.append(task.source.path)
                    logger.error(
                        f"Failed to convert {task.source.path} to {task.target_format}: {result.error}"
                    )
            except Exception as e:
                failed_files.append(task.source.path)
                logger.error(f"Error processing task for {task.source.path}: {str(e)}")
                self.metrics.errors[task.source.path] = str(e)
                self.metrics.failed_conversions += 1

        self.metrics.successful_conversions = len(successful_files)
        if len(failed_files) > self.metrics.failed_conversions:
            self.metrics.failed_conversions = len(failed_files)

        if not failed_files:
            return IntegrationResult.success_result(
                successful_files,
                message=f"Successfully converted {len(successful_files)} files",
            )
        elif successful_files:
            return IntegrationResult.success_result(
                successful_files,
                message=f"Partially successful: converted {len(successful_files)} files, failed to convert {len(failed_files)} files",
            )
        else:
            failed_files_str: str = ", ".join(failed_files[:5])
            if len(failed_files) > 5:
                failed_files_str += f" and {len(failed_files) - 5} more"
            error_msg: str = (
                f"Failed to convert any files. Failed files: {failed_files_str}"
            )
            return IntegrationResult.error_result(
                error=error_msg,
                message=f"All {len(failed_files)} conversion tasks failed. See logs for details.",
            )

    def validate_conversion(self, output_path: str, input_path: str) -> bool:
        """
        Validate the converted document.

        Args:
            output_path: Output file path (as a string).
            input_path: Input file path (as a string).

        Returns:
            True if validation passes, otherwise False.
        """
        from quackcore.fs.service import standalone as fs
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
            size_change_percentage = (
                (output_size / input_size * 100) if input_size > 0 else 0
            )
            logger.debug(
                f"Conversion size change: {input_size} → {output_size} bytes ({size_change_percentage:.1f}%)"
            )

            # Get file extension
            ext_result = fs.get_extension(output_path)
            if not ext_result.success:
                logger.error(f"Failed to get extension: {ext_result.error}")
                return False

            ext = ext_result.data

            if ext in ("md", "markdown"):
                try:
                    read_result = fs.read_text(output_path, encoding="utf-8")
                    if not read_result.success:
                        logger.error(
                            f"Failed to read markdown file: {read_result.error}"
                        )
                        return False
                    return len(read_result.content.strip()) > 0
                except Exception as e:
                    logger.error(f"Failed to read markdown file: {e}")
                    return False
            elif ext == "docx":
                from quackcore.integrations.pandoc.operations.utils import (
                    validate_docx_structure,
                )

                is_valid, _ = validate_docx_structure(
                    output_path, self.config.validation.check_links
                )
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
        config: The Pandoc conversion configuration.

    Returns:
        A new DocumentConverter instance.
    """
    return DocumentConverter(config)
