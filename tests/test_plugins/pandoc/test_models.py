# tests/test_plugins/pandoc/test_models.py
"""
Tests for pandoc plugin data models.

This module tests the data models used throughout the pandoc plugin,
including conversion metrics, file info, tasks, and results.
"""

from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from quackcore.plugins.pandoc.models import (
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
    FileInfo,
)


class TestConversionMetrics:
    """Tests for ConversionMetrics model."""

    def test_default_values(self) -> None:
        """Test default values."""
        metrics = ConversionMetrics()
        assert metrics.conversion_times == {}
        assert metrics.file_sizes == {}
        assert metrics.errors == {}
        assert isinstance(metrics.start_time, datetime)
        assert metrics.total_attempts == 0
        assert metrics.successful_conversions == 0
        assert metrics.failed_conversions == 0

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        conversion_times = {"file1.html": {"start": 1000.0, "end": 1005.0}}
        file_sizes = {"file1.html": {"original": 1000, "converted": 500, "ratio": 0.5}}
        errors = {"file2.html": "Conversion failed"}

        metrics = ConversionMetrics(
            conversion_times=conversion_times,
            file_sizes=file_sizes,
            errors=errors,
            start_time=start_time,
            total_attempts=5,
            successful_conversions=3,
            failed_conversions=2,
        )

        assert metrics.conversion_times == conversion_times
        assert metrics.file_sizes == file_sizes
        assert metrics.errors == errors
        assert metrics.start_time == start_time
        assert metrics.total_attempts == 5
        assert metrics.successful_conversions == 3
        assert metrics.failed_conversions == 2

    @given(
        st.dictionaries(
            st.text(),
            st.dictionaries(
                st.one_of(st.just("start"), st.just("end")), st.floats(min_value=0)
            ),
        ),
        st.dictionaries(
            st.text(),
            st.dictionaries(
                st.one_of(st.just("original"), st.just("converted"), st.just("ratio")),
                st.one_of(st.integers(min_value=0), st.floats(min_value=0)),
            ),
        ),
        st.dictionaries(st.text(), st.text()),
        st.integers(min_value=0),
        st.integers(min_value=0),
        st.integers(min_value=0),
    )
    def test_property_based(
        self,
        conversion_times: dict,
        file_sizes: dict,
        errors: dict,
        total_attempts: int,
        successful_conversions: int,
        failed_conversions: int,
    ) -> None:
        """Property-based test for ConversionMetrics using hypothesis."""
        metrics = ConversionMetrics(
            conversion_times=conversion_times,
            file_sizes=file_sizes,
            errors=errors,
            total_attempts=total_attempts,
            successful_conversions=successful_conversions,
            failed_conversions=failed_conversions,
        )

        assert metrics.conversion_times == conversion_times
        assert metrics.file_sizes == file_sizes
        assert metrics.errors == errors
        assert metrics.total_attempts == total_attempts
        assert metrics.successful_conversions == successful_conversions
        assert metrics.failed_conversions == failed_conversions


class TestFileInfo:
    """Tests for FileInfo model."""

    def test_minimal_values(self) -> None:
        """Test with minimal required values."""
        file_info = FileInfo(path=Path("/path/to/file.html"), format="html")
        assert file_info.path == Path("/path/to/file.html")
        assert file_info.format == "html"
        assert file_info.size == 0
        assert file_info.modified is None
        assert file_info.extra_args == []

    def test_all_values(self) -> None:
        """Test with all values set."""
        file_info = FileInfo(
            path=Path("/path/to/file.md"),
            format="markdown",
            size=1000,
            modified=1609459200.0,  # 2021-01-01 00:00:00
            extra_args=["--strip-comments"],
        )
        assert file_info.path == Path("/path/to/file.md")
        assert file_info.format == "markdown"
        assert file_info.size == 1000
        assert file_info.modified == 1609459200.0
        assert file_info.extra_args == ["--strip-comments"]

    def test_required_fields(self) -> None:
        """Test that required fields raise validation error when missing."""
        with pytest.raises(ValidationError):
            FileInfo(format="html")  # Missing path

        with pytest.raises(ValidationError):
            FileInfo(path=Path("/path/to/file.html"))  # Missing format

    @given(
        st.builds(Path, st.text(min_size=1)),
        st.text(min_size=1),
        st.integers(min_value=0),
        st.one_of(st.none(), st.floats(min_value=0)),
        st.lists(st.text()),
    )
    def test_property_based(
        self,
        path: Path,
        format_str: str,
        size: int,
        modified: float | None,
        extra_args: list[str],
    ) -> None:
        """Property-based test for FileInfo using hypothesis."""
        file_info = FileInfo(
            path=path,
            format=format_str,
            size=size,
            modified=modified,
            extra_args=extra_args,
        )

        assert file_info.path == path
        assert file_info.format == format_str
        assert file_info.size == size
        assert file_info.modified == modified
        assert file_info.extra_args == extra_args


class TestConversionTask:
    """Tests for ConversionTask model."""

    def test_minimal_values(self) -> None:
        """Test with minimal required values."""
        source = FileInfo(path=Path("/path/to/file.html"), format="html")
        task = ConversionTask(source=source, target_format="markdown")
        assert task.source == source
        assert task.target_format == "markdown"
        assert task.output_path is None

    def test_all_values(self) -> None:
        """Test with all values set."""
        source = FileInfo(path=Path("/path/to/file.html"), format="html")
        task = ConversionTask(
            source=source,
            target_format="markdown",
            output_path=Path("/path/to/output.md"),
        )
        assert task.source == source
        assert task.target_format == "markdown"
        assert task.output_path == Path("/path/to/output.md")

    def test_required_fields(self) -> None:
        """Test that required fields raise validation error when missing."""
        source = FileInfo(path=Path("/path/to/file.html"), format="html")

        with pytest.raises(ValidationError):
            ConversionTask(source=source)  # Missing target_format

        with pytest.raises(ValidationError):
            ConversionTask(target_format="markdown")  # Missing source


class TestConversionResult:
    """Tests for ConversionResult model."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = ConversionResult()
        assert result.success is True
        assert result.content is None
        assert result.source_format is None
        assert result.target_format is None
        assert result.conversion_time is None
        assert result.output_size is None
        assert result.input_size is None
        assert result.validation_errors == []
        assert result.message is None
        assert result.error is None

    def test_success_result_factory(self) -> None:
        """Test success_result factory method."""
        output_path = Path("/path/to/output.md")
        result = ConversionResult.success_result(
            output_path=output_path,
            source_format="html",
            target_format="markdown",
            conversion_time=1.5,
            output_size=500,
            input_size=1000,
            message="Conversion successful",
        )

        assert result.success is True
        assert result.content == output_path
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        assert result.conversion_time == 1.5
        assert result.output_size == 500
        assert result.input_size == 1000
        assert result.message == "Conversion successful"
        assert result.error is None

        # Test with minimal parameters
        minimal_result = ConversionResult.success_result(output_path=output_path)
        assert minimal_result.success is True
        assert minimal_result.content == output_path
        assert minimal_result.message == f"Successfully converted to {output_path}"

    def test_error_result_factory(self) -> None:
        """Test error_result factory method."""
        result = ConversionResult.error_result(
            error="Conversion failed",
            validation_errors=["File too small", "Invalid structure"],
            source_format="html",
            target_format="markdown",
            message="Additional info",
        )

        assert result.success is False
        assert result.content is None
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        assert result.error == "Conversion failed"
        assert result.validation_errors == ["File too small", "Invalid structure"]
        assert result.message == "Additional info"

        # Test with minimal parameters
        minimal_result = ConversionResult.error_result(error="Conversion failed")
        assert minimal_result.success is False
        assert minimal_result.error == "Conversion failed"
        assert minimal_result.validation_errors == []
        assert minimal_result.source_format is None
        assert minimal_result.target_format is None
        assert minimal_result.message is None


class TestBatchConversionResult:
    """Tests for BatchConversionResult model."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = BatchConversionResult()
        assert result.success is True
        assert result.content == []
        assert result.successful_files == []
        assert result.failed_files == []
        assert result.metrics is None
        assert result.message is None
        assert result.error is None

    def test_success_result_factory(self) -> None:
        """Test success_result factory method."""
        successful_files = [Path("/path/to/file1.md"), Path("/path/to/file2.md")]
        failed_files = [Path("/path/to/file3.md")]
        metrics = ConversionMetrics(successful_conversions=2, failed_conversions=1)

        result = BatchConversionResult.success_result(
            successful_files=successful_files,
            failed_files=failed_files,
            metrics=metrics,
            message="Batch conversion successful",
        )

        assert result.success is True
        assert result.content == successful_files
        assert result.successful_files == successful_files
        assert result.failed_files == failed_files
        assert result.metrics == metrics
        assert result.message == "Batch conversion successful"
        assert result.error is None

        # Test with minimal parameters
        minimal_result = BatchConversionResult.success_result(
            successful_files=successful_files
        )
        assert minimal_result.success is True
        assert minimal_result.content == successful_files
        assert (
            minimal_result.message
            == f"Successfully converted {len(successful_files)} files"
        )
        assert minimal_result.failed_files == []
        assert minimal_result.metrics is None

    def test_error_result_factory(self) -> None:
        """Test error_result factory method."""
        successful_files = [Path("/path/to/file1.md")]
        failed_files = [Path("/path/to/file2.md"), Path("/path/to/file3.md")]
        metrics = ConversionMetrics(successful_conversions=1, failed_conversions=2)

        result = BatchConversionResult.error_result(
            error="Batch conversion failed",
            successful_files=successful_files,
            failed_files=failed_files,
            metrics=metrics,
            message="Additional info",
        )

        assert result.success is False
        assert result.content == successful_files
        assert result.successful_files == successful_files
        assert result.failed_files == failed_files
        assert result.metrics == metrics
        assert result.error == "Batch conversion failed"
        assert result.message == "Additional info"

        # Test with minimal parameters
        minimal_result = BatchConversionResult.error_result(
            error="Batch conversion failed"
        )
        assert minimal_result.success is False
        assert minimal_result.error == "Batch conversion failed"
        assert minimal_result.successful_files == []
        assert minimal_result.failed_files == []
        assert minimal_result.metrics is None
        assert minimal_result.message is None
