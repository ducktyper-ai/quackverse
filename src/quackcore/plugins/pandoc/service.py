# src/quackcore/integrations/pandoc/service.py
"""
Pandoc integration service for QuackCore.

This module provides the main service class for pandoc integration,
handling document conversion between various formats.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, NoneType

from quackcore.errors import QuackIntegrationError
from quackcore.fs import service as fs
from quackcore.integrations.base import BaseIntegrationService
from quackcore.integrations.pandoc.config import ConversionConfig, PandocConfigProvider
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import (
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
    FileInfo,
)
from quackcore.integrations.pandoc.operations import (
    get_file_info,
    verify_pandoc,
)
from quackcore.integrations.results import IntegrationResult
from quackcore.paths import resolver

logger = logging.getLogger(__name__)


class PandocService(BaseIntegrationService):
    """
    Integration service for pandoc document conversion.

    This service provides functionality for converting documents between
    various formats using pandoc, with a focus on HTML to Markdown and
    Markdown to DOCX conversion.
    """

    def __init__(
            self,
            config_path: str | Path | None = None,
            output_dir: str | Path | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the pandoc integration service.

        Args:
            config_path: Path to the configuration file
            output_dir: Directory to save converted files
            log_level: Logging level
        """
        # Create a configuration provider
        config_provider = PandocConfigProvider(log_level)
        super().__init__(config_provider, None, config_path, log_level)

        # Initialize custom attributes
        self.output_dir = output_dir
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

    def initialize(self) -> IntegrationResult[NoneType]:
        """
        Initialize the pandoc service.

        This method verifies pandoc availability and loads configuration.

        Returns:
            IntegrationResult: Result of initialization
        """
        try:
            # Call the parent initialization to load configuration
            init_result = super().initialize()
            if not init_result.success:
                return init_result

            # Ensure configuration is loaded
            if not hasattr(self, "config") or not self.config:
                return IntegrationResult.error_result(
                    "Failed to load configuration",
                    message="Configuration not available"
                )

            # Load and validate configuration
            config_dict = self.config

            try:
                conversion_config = ConversionConfig(**config_dict)
            except Exception as e:
                return IntegrationResult.error_result(
                    f"Invalid configuration: {str(e)}",
                    message="Configuration validation failed"
                )

            # Override output directory if specified
            if self.output_dir:
                conversion_config.output_dir = Path(self.output_dir)

            # Verify pandoc installation
            try:
                self._pandoc_version = verify_pandoc()
            except QuackIntegrationError as e:
                return IntegrationResult.error_result(
                    str(e),
                    message="Pandoc verification failed"
                )

            # Initialize converter
            self.converter = DocumentConverter(conversion_config)

            # Ensure output directory exists
            fs.create_directory(conversion_config.output_dir, exist_ok=True)

            self._initialized = True
            return IntegrationResult.success_result(
                message=f"Pandoc service initialized successfully. Version: {self._pandoc_version}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize pandoc service: {str(e)}")
            return IntegrationResult.error_result(
                f"Failed to initialize pandoc service: {str(e)}"
            )

    def html_to_markdown(
            self, html_path: Path, output_path: Path | None = None
    ) -> ConversionResult:
        """
        Convert HTML to Markdown.

        Args:
            html_path: Path to the HTML file
            output_path: Optional path to save the Markdown file

        Returns:
            ConversionResult: Result of the conversion
        """
        if init_error := self._ensure_initialized():
            return ConversionResult.error_result(
                f"Service not initialized: {init_error.error}"
            )

        try:
            html_path = resolver.resolve_project_path(html_path)

            # Determine output path if not provided
            if output_path is None:
                output_path = self.converter.config.output_dir / f"{html_path.stem}.md"
            else:
                output_path = resolver.resolve_project_path(output_path)

            # Perform conversion
            return self.converter.convert_file(html_path, output_path, "markdown")

        except Exception as e:
            logger.error(f"Error in HTML to Markdown conversion: {str(e)}")
            return ConversionResult.error_result(
                f"Error in HTML to Markdown conversion: {str(e)}",
                source_format="html",
                target_format="markdown",
            )

    def markdown_to_docx(
            self, markdown_path: Path, output_path: Path | None = None
    ) -> ConversionResult:
        """
        Convert Markdown to DOCX.

        Args:
            markdown_path: Path to the Markdown file
            output_path: Optional path to save the DOCX file

        Returns:
            ConversionResult: Result of the conversion
        """
        if init_error := self._ensure_initialized():
            return ConversionResult.error_result(
                f"Service not initialized: {init_error.error}"
            )

        try:
            markdown_path = resolver.resolve_project_path(markdown_path)

            # Determine output path if not provided
            if output_path is None:
                output_path = self.converter.config.output_dir / f"{markdown_path.stem}.docx"
            else:
                output_path = resolver.resolve_project_path(output_path)

            # Perform conversion
            return self.converter.convert_file(markdown_path, output_path, "docx")

        except Exception as e:
            logger.error(f"Error in Markdown to DOCX conversion: {str(e)}")
            return ConversionResult.error_result(
                f"Error in Markdown to DOCX conversion: {str(e)}",
                source_format="markdown",
                target_format="docx",
            )

    def convert_directory(
            self, input_dir: Path, output_format: str, output_dir: Path | None = None,
            file_pattern: str | None = None, recursive: bool = False
    ) -> BatchConversionResult:
        """
        Convert all files in a directory.

        Args:
            input_dir: Directory containing files to convert
            output_format: Target format (markdown or docx)
            output_dir: Optional directory to save converted files
            file_pattern: Optional pattern to match files (e.g., "*.html")
            recursive: Whether to search subdirectories

        Returns:
            BatchConversionResult: Result of the conversion
        """
        if init_error := self._ensure_initialized():
            return BatchConversionResult.error_result(
                f"Service not initialized: {init_error.error}"
            )

        try:
            input_dir = resolver.resolve_project_path(input_dir)

            # Determine output directory
            if output_dir is None:
                output_dir = self.converter.config.output_dir
            else:
                output_dir = resolver.resolve_project_path(output_dir)

            # Ensure directories exist
            if not input_dir.exists() or not input_dir.is_dir():
                return BatchConversionResult.error_result(
                    f"Input directory does not exist or is not a directory: {input_dir}"
                )

            fs.create_directory(output_dir, exist_ok=True)

            # Determine source format based on target format
            source_format = None
            if output_format == "markdown":
                source_format = "html"
                extension_pattern = file_pattern or "*.html"
            elif output_format == "docx":
                source_format = "markdown"
                extension_pattern = file_pattern or "*.md"
            else:
                return BatchConversionResult.error_result(
                    f"Unsupported output format: {output_format}"
                )

            # Find files to convert
            find_result = fs.find_files(input_dir, extension_pattern, recursive)
            if not find_result.success:
                return BatchConversionResult.error_result(
                    f"Failed to find files: {find_result.error}"
                )

            if not find_result.files:
                return BatchConversionResult.error_result(
                    f"No matching files found in {input_dir}"
                )

            # Create conversion tasks
            tasks = []
            for file_path in find_result.files:
                try:
                    file_info = get_file_info(file_path, source_format)

                    # Determine output path
                    if output_format == "markdown":
                        output_file = output_dir / f"{file_path.stem}.md"
                    else:  # docx
                        output_file = output_dir / f"{file_path.stem}.docx"

                    task = ConversionTask(
                        source=file_info,
                        target_format=output_format,
                        output_path=output_file
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {str(e)}")

            # Perform batch conversion
            if tasks:
                return self.converter.convert_batch(tasks, output_dir)
            else:
                return BatchConversionResult.error_result(
                    "No valid files found for conversion"
                )

        except Exception as e:
            logger.error(f"Error in directory conversion: {str(e)}")
            return BatchConversionResult.error_result(
                f"Error in directory conversion: {str(e)}"
            )

    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available.

        Returns:
            bool: True if pandoc is available, False otherwise
        """
        try:
            verify_pandoc()
            return True
        except Exception:
            return False

    def get_pandoc_version(self) -> str | None:
        """
        Get the pandoc version.

        Returns:
            str | None: Pandoc version string or None if not available
        """
        if self._pandoc_version:
            return self._pandoc_version

        try:
            self._pandoc_version = verify_pandoc()
            return self._pandoc_version
        except Exception:
            return None

    def get_metrics(self) -> ConversionMetrics:
        """
        Get conversion metrics.

        Returns:
            ConversionMetrics: Current conversion metrics
        """
        if self.converter:
            return self.converter.metrics
        return self.metrics