# src/quackcore/plugins/pandoc/models.py
"""
Data models for pandoc plugin.

This module provides data models for representing conversion operations,
metrics, and results.
"""

from datetime import datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # Generic type for result content


class ConversionMetrics(BaseModel):
    """Metrics for document conversion operations."""

    conversion_times: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Dictionary of filename to conversion time details",
    )
    file_sizes: dict[str, dict[str, int | float]] = Field(
        default_factory=dict, description="Dictionary of filename to file size details"
    )
    errors: dict[str, str] = Field(
        default_factory=dict, description="Dictionary of filename to error messages"
    )
    start_time: datetime = Field(
        default_factory=datetime.now, description="Time when metrics collection started"
    )
    total_attempts: int = Field(
        default=0, description="Total number of conversion attempts"
    )
    successful_conversions: int = Field(
        default=0, description="Number of successful conversions"
    )
    failed_conversions: int = Field(
        default=0, description="Number of failed conversions"
    )


class FileInfo(BaseModel):
    """Information about a file for conversion."""

    path: Path = Field(..., description="Path to the file")
    format: str = Field(..., description="File format")
    size: int = Field(default=0, description="File size in bytes")
    modified: float | None = Field(default=None, description="Last modified timestamp")
    extra_args: list[str] = Field(
        default_factory=list, description="Extra arguments for pandoc"
    )


class ConversionTask(BaseModel):
    """Represents a document conversion task."""

    source: FileInfo = Field(..., description="Source file info")
    target_format: str = Field(..., description="Target format")
    output_path: Path | None = Field(default=None, description="Output path")


class ConversionResult(BaseModel):
    """Result of a document conversion operation."""

    success: bool = Field(
        default=True, description="Whether the conversion was successful"
    )
    content: Path | None = Field(default=None, description="Path to the converted file")
    source_format: str | None = Field(default=None, description="Source format")
    target_format: str | None = Field(default=None, description="Target format")
    conversion_time: float | None = Field(
        default=None, description="Conversion time in seconds"
    )
    output_size: int | None = Field(
        default=None, description="Output file size in bytes"
    )
    input_size: int | None = Field(default=None, description="Input file size in bytes")
    validation_errors: list[str] = Field(
        default_factory=list, description="Document validation errors"
    )
    message: str | None = Field(
        default=None, description="Additional message about the operation"
    )
    error: str | None = Field(
        default=None, description="Error message if conversion failed"
    )

    @classmethod
    def success_result(
        cls,
        output_path: Path,
        source_format: str | None = None,
        target_format: str | None = None,
        conversion_time: float | None = None,
        output_size: int | None = None,
        input_size: int | None = None,
        message: str | None = None,
    ) -> "ConversionResult":
        """
        Create a successful conversion result.

        Args:
            output_path: Path to the output file
            source_format: Source format
            target_format: Target format
            conversion_time: Conversion time in seconds
            output_size: Output file size in bytes
            input_size: Input file size in bytes
            message: Optional success message

        Returns:
            ConversionResult: Successful result
        """
        return cls(
            success=True,
            content=output_path,
            source_format=source_format,
            target_format=target_format,
            conversion_time=conversion_time,
            output_size=output_size,
            input_size=input_size,
            message=message or f"Successfully converted to {output_path}",
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        validation_errors: list[str] | None = None,
        source_format: str | None = None,
        target_format: str | None = None,
        message: str | None = None,
    ) -> "ConversionResult":
        """
        Create an error conversion result.

        Args:
            error: Error message
            validation_errors: Validation errors if any
            source_format: Source format
            target_format: Target format
            message: Optional additional message

        Returns:
            ConversionResult: Error result
        """
        return cls(
            success=False,
            content=None,
            source_format=source_format,
            target_format=target_format,
            error=error,
            validation_errors=validation_errors or [],
            message=message,
        )


class BatchConversionResult(BaseModel):
    """Result of a batch document conversion operation."""

    success: bool = Field(
        default=True, description="Whether the batch conversion was successful"
    )
    content: list[Path] = Field(
        default_factory=list, description="List of paths to converted files"
    )
    successful_files: list[Path] = Field(
        default_factory=list, description="Successfully converted files"
    )
    failed_files: list[Path] = Field(
        default_factory=list, description="Files that failed to convert"
    )
    metrics: ConversionMetrics | None = Field(
        default=None, description="Conversion metrics"
    )
    message: str | None = Field(
        default=None, description="Additional message about the operation"
    )
    error: str | None = Field(
        default=None, description="Error message if batch conversion failed"
    )

    @classmethod
    def success_result(
        cls,
        successful_files: list[Path],
        failed_files: list[Path] | None = None,
        metrics: ConversionMetrics | None = None,
        message: str | None = None,
    ) -> "BatchConversionResult":
        """
        Create a successful batch conversion result.

        Args:
            successful_files: Successfully converted files
            failed_files: Files that failed to convert
            metrics: Conversion metrics
            message: Optional success message

        Returns:
            BatchConversionResult: Successful result
        """
        return cls(
            success=True,
            content=successful_files,
            successful_files=successful_files,
            failed_files=failed_files or [],
            metrics=metrics,
            message=message or f"Successfully converted {len(successful_files)} files",
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        successful_files: list[Path] | None = None,
        failed_files: list[Path] | None = None,
        metrics: ConversionMetrics | None = None,
        message: str | None = None,
    ) -> "BatchConversionResult":
        """
        Create an error batch conversion result.

        Args:
            error: Error message
            successful_files: Successfully converted files
            failed_files: Files that failed to convert
            metrics: Conversion metrics
            message: Optional additional message

        Returns:
            BatchConversionResult: Error result
        """
        return cls(
            success=False,
            content=successful_files or [],
            successful_files=successful_files or [],
            failed_files=failed_files or [],
            metrics=metrics,
            error=error,
            message=message,
        )
