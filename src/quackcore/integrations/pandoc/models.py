# src/quackcore/integrations/pandoc/models.py
"""
Data models for pandoc integration.

This module provides Pydantic models for representing conversion operations,
metrics, and results for document format conversions using Pandoc.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


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


class ConversionDetails(BaseModel):
    """Detailed information about a conversion operation."""

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
