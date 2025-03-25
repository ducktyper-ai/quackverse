# src/quackcore/integrations/pandoc/protocols.py
"""
Protocol definitions for Pandoc integration.

This module defines protocol classes for document conversion services,
ensuring proper typing throughout the codebase.
"""

from pathlib import Path
from typing import Protocol, TypeVar, runtime_checkable

from quackcore.integrations.pandoc.models import (
    ConversionTask,
)
from quackcore.integrations.results import IntegrationResult

# Generic type variables for flexible return types
T = TypeVar("T")
R = TypeVar("R")


@runtime_checkable
class DocumentConverterProtocol(Protocol):
    """Protocol for document converter implementations."""

    def convert_file(
        self, input_path: Path, output_path: Path, output_format: str
    ) -> IntegrationResult[Path]:
        """
        Convert a file from one format to another.

        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            output_format: Target format

        Returns:
            IntegrationResult[Path]: Result of the conversion
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
    ) -> IntegrationResult[list[Path]]:
        """
        Convert a batch of files.

        Args:
            tasks: List of conversion tasks
            output_dir: Directory to save converted files

        Returns:
            IntegrationResult[list[Path]]: Result of the batch conversion
        """
        ...


@runtime_checkable
class PandocConversionProtocol(Protocol):
    """Protocol for the main pandoc conversion operations."""

    def html_to_markdown(
        self, html_path: Path, output_path: Path | None = None
    ) -> IntegrationResult[Path]:
        """
        Convert HTML to Markdown.

        Args:
            html_path: Path to the HTML file
            output_path: Optional path to save the Markdown file

        Returns:
            IntegrationResult[Path]: Result of the conversion
        """
        ...

    def markdown_to_docx(
        self, markdown_path: Path, output_path: Path | None = None
    ) -> IntegrationResult[Path]:
        """
        Convert Markdown to DOCX.

        Args:
            markdown_path: Path to the Markdown file
            output_path: Optional path to save the DOCX file

        Returns:
            IntegrationResult[Path]: Result of the conversion
        """
        ...

    def convert_directory(
        self,
        input_dir: Path,
        output_format: str,
        output_dir: Path | None = None,
        file_pattern: str | None = None,
        recursive: bool = False,
    ) -> IntegrationResult[list[Path]]:
        """
        Convert all files in a directory.

        Args:
            input_dir: Directory containing files to convert
            output_format: Target format
            output_dir: Optional directory to save converted files
            file_pattern: Optional pattern to match files
            recursive: Whether to search subdirectories

        Returns:
            IntegrationResult[list[Path]]: Result of the conversion
        """
        ...
