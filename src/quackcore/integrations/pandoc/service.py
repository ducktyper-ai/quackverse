# src/quackcore/integrations/pandoc/service.py
"""
Pandoc integration service for QuackCore.

This module provides the main service class for Pandoc integration,
handling document conversion between various formats.
All file path parameters and return types are represented as strings.
Filesystem _operations such as resolution and joining are delegated to quackcore.fs.
"""

import os
from collections.abc import Sequence
from datetime import datetime
from typing import cast

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs  # fs functions accept and return strings
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig, PandocConfigProvider
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import (
    ConversionMetrics,
    ConversionTask,
    FileInfo,
)
from quackcore.integrations.pandoc.operations import (
    get_file_info,
    verify_pandoc,
)
from quackcore.integrations.pandoc.protocols import PandocConversionProtocol
from quackcore.logging import LOG_LEVELS, LogLevel, get_logger
from quackcore.paths import resolver

logger = get_logger(__name__)


class PandocIntegration(BaseIntegrationService, PandocConversionProtocol):
    """
    Integration service for Pandoc document conversion.

    This service provides functionality for converting documents between
    various formats using Pandoc, with a focus on HTML to Markdown and
    Markdown to DOCX conversion.
    All file paths are handled as strings.
    """

    def __init__(
        self,
        config_path: str | None = None,
        output_dir: str | None = None,
        log_level: int = LOG_LEVELS[LogLevel.INFO],
    ) -> None:
        """
        Initialize the Pandoc integration service.

        Args:
            config_path: Path to the configuration file (as a string)
            output_dir: Directory to save converted files (as a string)
            log_level: Logging level
        """
        config_provider = PandocConfigProvider(log_level)
        super().__init__(config_provider, None, config_path, log_level)

        # Store output_dir as a string
        self.output_dir: str | None = output_dir if output_dir else None
        self.metrics = ConversionMetrics(start_time=datetime.now())
        self.converter: DocumentConverter | None = None
        self._pandoc_version: str | None = None

    @property
    def name(self) -> str:
        """Get the name of the integration."""
        return "Pandoc"

    @property
    def version(self) -> str:
        """Get the version of the integration."""
        return "1.0.0"

    def initialize(self) -> IntegrationResult:
        """
        Initialize the Pandoc integration.

        This method verifies Pandoc availability and loads configuration.

        Returns:
            IntegrationResult: Result of initialization.
        """
        try:
            init_result = super().initialize()
            if not init_result.success:
                return init_result

            # Load configuration as a dictionary
            config_dict = self.config or {}
            try:
                conversion_config = PandocConfig(**config_dict)
            except Exception as e:
                logger.error(f"Invalid configuration: {str(e)}")
                return IntegrationResult.error_result(
                    f"Invalid configuration: {str(e)}"
                )

            # Override output directory if specified
            if self.output_dir:
                conversion_config.output_dir = self.output_dir

            try:
                self._pandoc_version = verify_pandoc()
            except QuackIntegrationError as e:
                logger.error(f"Pandoc verification failed: {str(e)}")
                return IntegrationResult.error_result(
                    f"Pandoc verification failed: {str(e)}"
                )

            self.converter = DocumentConverter(conversion_config)

            # Ensure output directory exists by delegating to fs; all paths are strings.
            result = fs.create_directory(conversion_config.output_dir, exist_ok=True)
            if not result.success:
                return IntegrationResult.error_result(
                    f"Failed to create output directory: {result.error}"
                )

            self._initialized = True
            logger.info(
                f"Pandoc integration initialized successfully. Version: {self._pandoc_version}"
            )
            return IntegrationResult.success_result(
                message=f"Pandoc integration initialized successfully. Version: {self._pandoc_version}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Pandoc integration: {str(e)}")
            return IntegrationResult.error_result(
                f"Failed to initialize Pandoc integration: {str(e)}"
            )

    def html_to_markdown(
        self, html_path: str, output_path: str | None = None
    ) -> IntegrationResult[str]:
        """
        Convert HTML to Markdown.

        Args:
            html_path: Absolute path to the HTML file (as a string).
            output_path: Optional absolute path to save the Markdown file (as a string).

        Returns:
            IntegrationResult[str]: Result of the conversion with the output file path.
        """
        if not self._initialized:
            return cast(
                IntegrationResult[str],
                IntegrationResult.error_result("Pandoc integration not initialized"),
            )

        try:
            html_path = resolver._resolve_project_path(html_path)

            if output_path is None and self.converter:
                config = getattr(self.converter, "config", None)
                if isinstance(config, PandocConfig):
                    stem = os.path.splitext(os.path.basename(html_path))[0]
                    output_path = fs.join_path(config.output_dir, f"{stem}.md")
                else:
                    return cast(
                        IntegrationResult[str],
                        IntegrationResult.error_result(
                            "Cannot determine output path, invalid converter configuration"
                        ),
                    )
            elif output_path:
                output_path = resolver.resolve_project_path(output_path)
            else:
                return cast(
                    IntegrationResult[str],
                    IntegrationResult.error_result(
                        "Cannot determine output path, converter not initialized"
                    ),
                )

            if self.converter:
                return self.converter.convert_file(html_path, output_path, "markdown")
            else:
                return cast(
                    IntegrationResult[str],
                    IntegrationResult.error_result("Converter not initialized"),
                )
        except Exception as e:
            logger.error(f"Error in HTML to Markdown conversion: {str(e)}")
            return cast(
                IntegrationResult[str],
                IntegrationResult.error_result(
                    f"Error in HTML to Markdown conversion: {str(e)}"
                ),
            )

    def markdown_to_docx(
        self, markdown_path: str, output_path: str | None = None
    ) -> IntegrationResult[str]:
        """
        Convert Markdown to DOCX.

        Args:
            markdown_path: Absolute path to the Markdown file (as a string).
            output_path: Optional absolute path to save the DOCX file (as a string).

        Returns:
            IntegrationResult[str]: Result of the conversion with the output file path.
        """
        if not self._initialized:
            return cast(
                IntegrationResult[str],
                IntegrationResult.error_result("Pandoc integration not initialized"),
            )

        try:
            markdown_path = resolver._resolve_project_path(markdown_path)

            if output_path is None and self.converter:
                config = getattr(self.converter, "config", None)
                if isinstance(config, PandocConfig):
                    stem = os.path.splitext(os.path.basename(markdown_path))[0]
                    output_path = fs.join_path(config.output_dir, f"{stem}.docx")
                else:
                    return cast(
                        IntegrationResult[str],
                        IntegrationResult.error_result(
                            "Cannot determine output path, invalid converter configuration"
                        ),
                    )
            elif output_path:
                output_path = resolver._resolve_project_path(output_path)
            else:
                return cast(
                    IntegrationResult[str],
                    IntegrationResult.error_result(
                        "Cannot determine output path, converter not initialized"
                    ),
                )

            if self.converter:
                return self.converter.convert_file(markdown_path, output_path, "docx")
            else:
                return cast(
                    IntegrationResult[str],
                    IntegrationResult.error_result("Converter not initialized"),
                )
        except Exception as e:
            logger.error(f"Error in Markdown to DOCX conversion: {str(e)}")
            return cast(
                IntegrationResult[str],
                IntegrationResult.error_result(
                    f"Error in Markdown to DOCX conversion: {str(e)}"
                ),
            )

    def convert_directory(
        self,
        input_dir: str,
        output_format: str,
        output_dir: str | None = None,
        file_pattern: str | None = None,
        recursive: bool = False,
    ) -> IntegrationResult[list[str]]:
        """
        Convert all files in a directory.

        Args:
            input_dir: Absolute path to the directory containing files to convert (as a string).
            output_format: Target format ("markdown" or "docx").
            output_dir: Optional absolute path to the directory in which to save converted files (as a string).
            file_pattern: Optional pattern to match files (e.g., "*.html").
            recursive: Whether to search subdirectories.

        Returns:
            IntegrationResult[list[str]]: Result of the conversion with a list of output file paths.
        """
        if not self._initialized:
            return cast(
                IntegrationResult[list[str]],
                IntegrationResult.error_result("Pandoc integration not initialized"),
            )

        try:
            input_dir = resolver._resolve_project_path(input_dir)
            input_dir_info = fs.get_file_info(input_dir)
            if (
                not input_dir_info.success
                or not input_dir_info.exists
                or not input_dir_info.is_dir
            ):
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result(
                        f"Input directory does not exist or is not a directory: {input_dir}"
                    ),
                )

            if self.converter:
                config = getattr(self.converter, "config", None)
                if isinstance(config, PandocConfig):
                    output_dir = (
                        resolver._resolve_project_path(output_dir)
                        if output_dir
                        else config.output_dir
                    )
                else:
                    return cast(
                        IntegrationResult[list[str]],
                        IntegrationResult.error_result(
                            "Invalid converter configuration"
                        ),
                    )
            else:
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result("Converter not initialized"),
                )

            dir_result = fs.create_directory(output_dir, exist_ok=True)
            if not dir_result.success:
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result(
                        f"Failed to create output directory: {dir_result.error}"
                    ),
                )

            params = self._determine_conversion_params(output_format, file_pattern)
            if params is None:
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result(
                        f"Unsupported output format: {output_format}"
                    ),
                )
            source_format, extension_pattern = params

            find_result = fs.find_files(input_dir, extension_pattern, recursive)
            if not find_result.success or not find_result.files:
                msg = (
                    f"No matching files found in {input_dir}"
                    if find_result.success
                    else f"Failed to find files: {find_result.error}"
                )
                return cast(
                    IntegrationResult[list[str]], IntegrationResult.error_result(msg)
                )

            tasks = self._create_conversion_tasks(
                find_result.files, source_format, output_format, output_dir
            )
            if not tasks:
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result(
                        "No valid files found for conversion"
                    ),
                )

            if self.converter:
                return self.converter.convert_batch(tasks, output_dir)
            else:
                return cast(
                    IntegrationResult[list[str]],
                    IntegrationResult.error_result("Converter not initialized"),
                )
        except Exception as e:
            logger.error(f"Error in directory conversion: {str(e)}")
            return cast(
                IntegrationResult[list[str]],
                IntegrationResult.error_result(
                    f"Error in directory conversion: {str(e)}"
                ),
            )

    def _determine_conversion_params(
        self, output_format: str, file_pattern: str | None
    ) -> tuple[str, str] | None:
        """
        Determine the source format and file extension pattern based on the target output format.

        Args:
            output_format: Desired target format ("markdown" or "docx").
            file_pattern: Optional file pattern override.

        Returns:
            tuple: (source_format, extension_pattern) or None if output_format is unsupported.
        """
        if output_format == "markdown":
            return "html", file_pattern or "*.html"
        elif output_format == "docx":
            return "markdown", file_pattern or "*.md"
        return None

    def _create_conversion_tasks(
        self,
        files: Sequence[str],
        source_format: str,
        output_format: str,
        output_dir: str,
    ) -> list[ConversionTask]:
        """
        Create a list of conversion tasks from the found files.

        Args:
            files: List of file paths found (as strings).
            source_format: Source format (e.g., "html" or "markdown").
            output_format: Target format (e.g., "markdown" or "docx").
            output_dir: Directory to save converted files (as a string).

        Returns:
            list[ConversionTask]: List of conversion tasks.
        """
        tasks: list[ConversionTask] = []
        for file_path in files:
            try:
                file_info: FileInfo = get_file_info(file_path, source_format)
                stem = os.path.splitext(os.path.basename(file_path))[0]
                if output_format == "markdown":
                    output_file = fs.join_path(output_dir, f"{stem}.md")
                else:
                    output_file = fs.join_path(output_dir, f"{stem}.docx")
                task = ConversionTask(
                    source=file_info,
                    target_format=output_format,
                    output_path=output_file,
                )
                tasks.append(task)
            except Exception as e:
                logger.warning(f"Skipping file {file_path}: {str(e)}")
        return tasks

    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available.

        Returns:
            bool: True if pandoc is available, False otherwise.
        """
        try:
            verify_pandoc()
            return True
        except (QuackIntegrationError, ImportError, OSError):
            return False

    def get_pandoc_version(self) -> str | None:
        """
        Get the pandoc version.

        Returns:
            str | None: Pandoc version string or None if not available.
        """
        if self._pandoc_version:
            return self._pandoc_version

        try:
            self._pandoc_version = verify_pandoc()
            return self._pandoc_version
        except (QuackIntegrationError, ImportError, OSError):
            return None

    def get_metrics(self) -> ConversionMetrics:
        """
        Get conversion metrics.

        Returns:
            ConversionMetrics: Current conversion metrics.
        """
        if self.converter:
            return getattr(self.converter, "metrics", self.metrics)
        return self.metrics
