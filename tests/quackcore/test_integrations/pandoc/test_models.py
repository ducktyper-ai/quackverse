# tests/quackcore/test_integrations/pandoc/test_models.py
"""
Tests for Pandoc data models.

This module tests the data models used for representing conversion _operations,
metrics, and file information in the Pandoc integration.
"""

from datetime import datetime
from pathlib import Path

from quackcore.integrations.pandoc.models import (
    ConversionDetails,
    ConversionMetrics,
    ConversionTask,
    FileInfo,
)


class TestPandocModels:
    """Tests for Pandoc data models."""

    def test_file_info_model(self):
        """Test the FileInfo model."""
        # Test with minimal required fields
        file_info = FileInfo(path="/path/to/file.html",
                             format="html")  # Changed from Path to string
        assert file_info.path == "/path/to/file.html"  # Changed from Path to string
        assert file_info.format == "html"
        assert file_info.size == 0
        assert file_info.modified is None
        assert file_info.extra_args == []

        # Test with all fields specified
        file_info = FileInfo(
            path="/path/to/file.md",  # Changed from Path to string
            format="markdown",
            size=1024,
            modified=1609459200.0,  # 2021-01-01 00:00:00
            extra_args=["--reference-doc=template.docx"],
        )
        assert file_info.path == "/path/to/file.md"  # Changed from Path to string
        assert file_info.format == "markdown"
        assert file_info.size == 1024
        assert file_info.modified == 1609459200.0
        assert file_info.extra_args == ["--reference-doc=template.docx"]

    def test_conversion_task_model(self):
        """Test the ConversionTask model."""
        # Create a FileInfo instance to use in the task
        source_file = FileInfo(path="/path/to/file.html", format="html",
                               size=512)  # Changed from Path to string

        # Test with minimal required fields
        task = ConversionTask(source=source_file, target_format="markdown")
        assert task.source == source_file
        assert task.target_format == "markdown"
        assert task.output_path is None

        # Test with all fields specified
        task = ConversionTask(
            source=source_file,
            target_format="docx",
            output_path="/path/to/output.docx",  # Changed from Path to string
        )
        assert task.source == source_file
        assert task.target_format == "docx"
        assert task.output_path == "/path/to/output.docx"  # Changed from Path to string

    def test_conversion_task_model(self):
        """Test the ConversionTask model."""
        # Create a FileInfo instance to use in the task
        source_file = FileInfo(path=Path("/path/to/file.html"), format="html", size=512)

        # Test with minimal required fields
        task = ConversionTask(source=source_file, target_format="markdown")
        assert task.source == source_file
        assert task.target_format == "markdown"
        assert task.output_path is None

        # Test with all fields specified
        task = ConversionTask(
            source=source_file,
            target_format="docx",
            output_path=Path("/path/to/output.docx"),
        )
        assert task.source == source_file
        assert task.target_format == "docx"
        assert task.output_path == Path("/path/to/output.docx")

    def test_conversion_details_model(self):
        """Test the ConversionDetails model."""
        # Test with default values
        details = ConversionDetails()
        assert details.source_format is None
        assert details.target_format is None
        assert details.conversion_time is None
        assert details.output_size is None
        assert details.input_size is None
        assert details.validation_errors == []

        # Test with all fields specified
        details = ConversionDetails(
            source_format="html",
            target_format="markdown",
            conversion_time=2.5,
            output_size=1024,
            input_size=2048,
            validation_errors=["Warning: Some elements could not be converted"],
        )
        assert details.source_format == "html"
        assert details.target_format == "markdown"
        assert details.conversion_time == 2.5
        assert details.output_size == 1024
        assert details.input_size == 2048
        assert len(details.validation_errors) == 1
        assert "Warning" in details.validation_errors[0]

    def test_conversion_metrics_model(self):
        """Test the ConversionMetrics model."""
        # Test with default values
        metrics = ConversionMetrics()
        assert metrics.conversion_times == {}
        assert metrics.file_sizes == {}
        assert metrics.errors == {}
        assert isinstance(metrics.start_time, datetime)
        assert metrics.total_attempts == 0
        assert metrics.successful_conversions == 0
        assert metrics.failed_conversions == 0

        # Test with a specific start time
        start_time = datetime(2021, 1, 1, 12, 0, 0)
        metrics = ConversionMetrics(start_time=start_time)
        assert metrics.start_time == start_time

        # Test with all fields specified
        metrics = ConversionMetrics(
            conversion_times={
                "file1.html": {"start": 1000.0, "end": 1002.5},
                "file2.html": {"start": 1005.0, "end": 1008.0},
            },
            file_sizes={
                "file1.html": {"original": 1024, "converted": 512, "ratio": 0.5},
                "file2.html": {"original": 2048, "converted": 1024, "ratio": 0.5},
            },
            errors={
                "file3.html": "File not found",
            },
            start_time=start_time,
            total_attempts=3,
            successful_conversions=2,
            failed_conversions=1,
        )
        assert len(metrics.conversion_times) == 2
        assert metrics.conversion_times["file1.html"]["start"] == 1000.0
        assert metrics.conversion_times["file2.html"]["end"] == 1008.0
        assert len(metrics.file_sizes) == 2
        assert metrics.file_sizes["file1.html"]["original"] == 1024
        assert metrics.file_sizes["file2.html"]["ratio"] == 0.5
        assert len(metrics.errors) == 1
        assert metrics.errors["file3.html"] == "File not found"
        assert metrics.start_time == start_time
        assert metrics.total_attempts == 3
        assert metrics.successful_conversions == 2
        assert metrics.failed_conversions == 1

    def test_conversion_metrics_tracking(self):
        """Test tracking conversions with the ConversionMetrics model."""
        # Create a metrics instance
        metrics = ConversionMetrics()

        # Track a successful conversion
        metrics.successful_conversions += 1
        metrics.total_attempts += 1
        metrics.conversion_times["file1.html"] = {"start": 1000.0, "end": 1002.5}
        metrics.file_sizes["file1.html"] = {
            "original": 1024,
            "converted": 512,
            "ratio": 0.5,
        }

        assert metrics.total_attempts == 1
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 0
        assert "file1.html" in metrics.conversion_times
        assert "file1.html" in metrics.file_sizes

        # Track a failed conversion
        metrics.failed_conversions += 1
        metrics.total_attempts += 1
        metrics.errors["file2.html"] = "Conversion failed"

        assert metrics.total_attempts == 2
        assert metrics.successful_conversions == 1
        assert metrics.failed_conversions == 1
        assert "file2.html" in metrics.errors
        assert len(metrics.errors) == 1
