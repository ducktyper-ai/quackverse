# src/quackcore/plugins/pandoc/protocols.py
"""
Protocol definitions for pandoc plugin.

This module defines protocol classes for pandoc conversion services,
ensuring proper typing throughout the codebase.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from quackcore.plugins.pandoc.models import (
    BatchConversionResult,
    ConversionResult,
    ConversionTask,
)


@runtime_checkable
class DocumentConverterProtocol(Protocol):
    """Protocol for document converter implementations."""

    def convert_file(
        self, input_path: Path, output_path: Path, output_format: str
    ) -> ConversionResult:
        """
        Convert a file from one format to another.

        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            output_format: Target format

        Returns:
            ConversionResult: Result of the conversion
        """
        ...

    def validate_conversion(self, output_path: Path, input_path: Path) -> bool:
        """
        Validate the converted document.

        Args:
            output_path: Path to the output file
            input_path: Path to the input file

        Returns:
            bool: True if validation passed, False otherwise
        """
        ...


@runtime_checkable
class BatchConverterProtocol(Protocol):
    """Protocol for batch document conversion."""

    def convert_batch(
        self, tasks: list[ConversionTask], output_dir: Path | None = None
    ) -> BatchConversionResult:
        """
        Convert a batch of files.

        Args:
            tasks: List of conversion tasks
            output_dir: Directory to save converted files

        Returns:
            BatchConversionResult: Result of the batch conversion
        """
        ...


@runtime_checkable
class PandocServiceProtocol(Protocol):
    """Protocol for the main pandoc service."""

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
        ...

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
        ...

    def convert_directory(
        self, input_dir: Path, output_format: str, output_dir: Path | None = None
    ) -> BatchConversionResult:
        """
        Convert all files in a directory.

        Args:
            input_dir: Directory containing files to convert
            output_format: Target format
            output_dir: Optional directory to save converted files

        Returns:
            BatchConversionResult: Result of the conversion
        """
        ...

    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available.

        Returns:
            bool: True if pandoc is available, False otherwise
        """
        ...

    def get_pandoc_version(self) -> str | None:
        """
        Get the pandoc version.

        Returns:
            str | None: Pandoc version string or None if not available
        """
        ...
