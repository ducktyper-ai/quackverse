# tests/quackcore/test_integrations/pandoc/mocks.py
"""
Mock objects for Pandoc integration testing.

This module provides mock implementations of Pandoc-related objects
that can be used across different test modules.
"""

import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import (
    ConversionDetails,
    ConversionMetrics,
    ConversionTask,
    FileInfo,
)
from quackcore.integrations.pandoc.protocols import PandocConversionProtocol


def create_mock_pandoc_config(
    output_dir: str | Path = "/path/to/output",
) -> PandocConfig:
    """
    Create a mock PandocConfig for testing.

    Args:
        output_dir: The output directory path

    Returns:
        A configured PandocConfig instance
    """
    return PandocConfig(
        output_dir=Path(output_dir),
        html_to_md_extra_args=["--strip-comments", "--no-highlight"],
        md_to_docx_extra_args=["--reference-doc=template.docx"],
    )


def create_mock_metrics() -> ConversionMetrics:
    """
    Create a mock ConversionMetrics instance for testing.

    Returns:
        A ConversionMetrics instance
    """
    return ConversionMetrics(
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
        start_time=datetime(2021, 1, 1, 12, 0, 0),
        total_attempts=3,
        successful_conversions=2,
        failed_conversions=1,
    )


def create_mock_document_converter(
    config: PandocConfig | None = None,
    metrics: ConversionMetrics | None = None,
    pandoc_version: str = "2.11.4",
) -> DocumentConverter:
    """
    Create a mock DocumentConverter for testing.

    Args:
        config: Optional config to use, creates a default one if not provided
        metrics: Optional metrics to use, creates a default one if not provided
        pandoc_version: Pandoc version to return

    Returns:
        A mocked DocumentConverter instance
    """
    if config is None:
        config = create_mock_pandoc_config()

    if metrics is None:
        metrics = create_mock_metrics()

    # Create a mock DocumentConverter using patch to avoid real initialization
    with patch(
        "quackcore.integrations.pandoc._operations.verify_pandoc",
        return_value=pandoc_version,
    ):
        # Create a real DocumentConverter instance with our mocked dependencies
        converter = DocumentConverter(config)
        # Override metrics with our predefined metrics
        converter.metrics = metrics
        # Ensure pandoc_version is set
        converter._pandoc_version = pandoc_version

        return converter


class MockPandocConversionService(PandocConversionProtocol):
    """Mock implementation of PandocConversionProtocol for testing."""

    def __init__(
        self,
        initialized: bool = True,
        converter: DocumentConverter | None = None,
        pandoc_version: str = "2.11.4",
        output_dir: str | Path | None = "/path/to/output",
        log_level: int = logging.INFO,
    ):
        """
        Initialize the mock Pandoc conversion service.

        Args:
            initialized: Whether the service is initialized
            converter: Optional DocumentConverter mock
            pandoc_version: Pandoc version to report
            output_dir: Output directory path
            log_level: Logging level
        """
        self._initialized = initialized
        self.converter = converter or create_mock_document_converter()
        self._pandoc_version = pandoc_version
        self.output_dir = Path(output_dir) if output_dir else None
        self.logger = logging.getLogger("mock_pandoc_service")
        self.logger.setLevel(log_level)
        self.metrics = create_mock_metrics()

    def html_to_markdown(
        self, html_path: Path, output_path: Path | None = None
    ) -> IntegrationResult[Path]:
        """
        Mock HTML to Markdown conversion.

        Args:
            html_path: Path to the HTML file
            output_path: Optional path to save the Markdown file

        Returns:
            IntegrationResult with conversion result
        """
        if not self._initialized:
            return IntegrationResult.error_result("Pandoc integration not initialized")

        if output_path is None:
            if self.output_dir:
                output_path = self.output_dir / f"{html_path.stem}.md"
            else:
                return IntegrationResult.error_result(
                    "Cannot determine output path, converter not initialized"
                )

        # Simulate successful conversion
        if self.converter:
            return self.converter.convert_file(html_path, output_path, "markdown")

        return IntegrationResult.error_result("Converter not initialized")

    def markdown_to_docx(
        self, markdown_path: Path, output_path: Path | None = None
    ) -> IntegrationResult[Path]:
        """
        Mock Markdown to DOCX conversion.

        Args:
            markdown_path: Path to the Markdown file
            output_path: Optional path to save the DOCX file

        Returns:
            IntegrationResult with conversion result
        """
        if not self._initialized:
            return IntegrationResult.error_result("Pandoc integration not initialized")

        if output_path is None:
            if self.output_dir:
                output_path = self.output_dir / f"{markdown_path.stem}.docx"
            else:
                return IntegrationResult.error_result(
                    "Cannot determine output path, converter not initialized"
                )

        # Simulate successful conversion
        if self.converter:
            return self.converter.convert_file(markdown_path, output_path, "docx")

        return IntegrationResult.error_result("Converter not initialized")

    def convert_directory(
        self,
        input_dir: Path,
        output_format: str,
        output_dir: Path | None = None,
        file_pattern: str | None = None,
        recursive: bool = False,
    ) -> IntegrationResult[list[Path]]:
        """
        Mock directory conversion.

        Args:
            input_dir: Directory containing files to convert
            output_format: Target format (markdown or docx)
            output_dir: Optional directory to save converted files
            file_pattern: Optional pattern to match files
            recursive: Whether to search subdirectories

        Returns:
            IntegrationResult with conversion results
        """
        if not self._initialized:
            return IntegrationResult.error_result("Pandoc integration not initialized")

        # Determine source format and file extension pattern
        if output_format == "markdown":
            source_format = "html"
            extension_pattern = file_pattern or "*.html"
        elif output_format == "docx":
            source_format = "markdown"
            extension_pattern = file_pattern or "*.md"
        else:
            return IntegrationResult.error_result(
                f"Unsupported output format: {output_format}"
            )

        # Create mock file paths
        if output_format == "markdown":
            mock_files = [
                Path(f"/path/to/output/file1.md"),
                Path(f"/path/to/output/file2.md"),
            ]
        else:  # docx
            mock_files = [
                Path(f"/path/to/output/file1.docx"),
                Path(f"/path/to/output/file2.docx"),
            ]

        return IntegrationResult.success_result(
            mock_files,
            message=f"Successfully converted {len(mock_files)} files",
        )

    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available.

        Returns:
            True if pandoc is available, False otherwise
        """
        return self._pandoc_version is not None

    def get_pandoc_version(self) -> str | None:
        """
        Get the pandoc version.

        Returns:
            Pandoc version string or None if not available
        """
        return self._pandoc_version

    def get_metrics(self) -> ConversionMetrics:
        """
        Get conversion metrics.

        Returns:
            ConversionMetrics with mock data
        """
        if self.converter:
            return getattr(self.converter, "metrics", self.metrics)
        return self.metrics


def create_successful_conversion_mock() -> MagicMock:
    """
    Create a mock that returns successful conversion results.

    Returns:
        A MagicMock configured for successful conversions
    """
    mock = MagicMock()

    # Configure HTML to Markdown conversion
    mock.html_to_markdown.return_value = IntegrationResult.success_result(
        Path("/path/to/output/file.md"),
        message="Successfully converted HTML to Markdown",
    )

    # Configure Markdown to DOCX conversion
    mock.markdown_to_docx.return_value = IntegrationResult.success_result(
        Path("/path/to/output/file.docx"),
        message="Successfully converted Markdown to DOCX",
    )

    # Configure directory conversion
    mock.convert_directory.return_value = IntegrationResult.success_result(
        [Path("/path/to/output/file1.md"), Path("/path/to/output/file2.md")],
        message="Successfully converted 2 files",
    )

    return mock


def create_error_conversion_mock() -> MagicMock:
    """
    Create a mock that returns error conversion results.

    Returns:
        A MagicMock configured for error conversions
    """
    mock = MagicMock()

    # Configure HTML to Markdown conversion error
    mock.html_to_markdown.return_value = IntegrationResult.error_result(
        "Failed to convert HTML to Markdown"
    )

    # Configure Markdown to DOCX conversion error
    mock.markdown_to_docx.return_value = IntegrationResult.error_result(
        "Failed to convert Markdown to DOCX"
    )

    # Configure directory conversion error
    mock.convert_directory.return_value = IntegrationResult.error_result(
        "Failed to convert directory"
    )

    return mock


def mock_verify_pandoc_success() -> str:
    """
    Mock for successful pandoc verification.

    Returns:
        Pandoc version string
    """
    return "2.11.4"


def mock_verify_pandoc_failure() -> None:
    """
    Mock for failed pandoc verification.

    Raises:
        QuackIntegrationError: Always raised to simulate failure
    """
    raise QuackIntegrationError("Pandoc not found")


def create_file_info(
    path: str | Path,
    format_name: str = "html",
    size: int = 1024,
    modified: float | None = None,
    extra_args: list[str] | None = None,
) -> FileInfo:
    """
    Create a FileInfo object for testing.

    Args:
        path: File path
        format_name: File format
        size: File size in bytes
        modified: Last modified timestamp
        extra_args: Extra pandoc arguments

    Returns:
        Configured FileInfo object
    """
    return FileInfo(
        path=Path(path),
        format=format_name,
        size=size,
        modified=modified or 1609459200.0,  # 2021-01-01 00:00:00
        extra_args=extra_args or [],
    )


def create_conversion_task(
    source_path: str | Path,
    source_format: str = "html",
    target_format: str = "markdown",
    output_path: str | Path | None = None,
    size: int = 1024,
) -> ConversionTask:
    """
    Create a ConversionTask object for testing.

    Args:
        source_path: Source file path
        source_format: Source file format
        target_format: Target file format
        output_path: Output file path
        size: Source file size in bytes

    Returns:
        Configured ConversionTask
    """
    source = create_file_info(source_path, source_format, size)
    output = Path(output_path) if output_path else None

    return ConversionTask(
        source=source,
        target_format=target_format,
        output_path=output,
    )


def create_conversion_details(
    source_format: str = "html",
    target_format: str = "markdown",
    conversion_time: float = 2.5,
    output_size: int = 512,
    input_size: int = 1024,
    validation_errors: list[str] | None = None,
) -> ConversionDetails:
    """
    Create a ConversionDetails object for testing.

    Args:
        source_format: Source file format
        target_format: Target file format
        conversion_time: Time taken for conversion in seconds
        output_size: Output file size in bytes
        input_size: Input file size in bytes
        validation_errors: List of validation errors

    Returns:
        Configured ConversionDetails
    """
    return ConversionDetails(
        source_format=source_format,
        target_format=target_format,
        conversion_time=conversion_time,
        output_size=output_size,
        input_size=input_size,
        validation_errors=validation_errors or [],
    )


def setup_mock_file_info_for_tests(mock_fs, size: int = 512) -> None:
    """
    Setup mock file_info with predefined values for tests.

    This is a helper for tests to ensure that file_info.size returns a consistent value
    that tests expect.

    Args:
        mock_fs: The mocked fs service
        size: The file size to return (default: 512)
    """
    # Create a concrete FileInfoResult with the expected size
    file_info = FileInfoResult(
        success=True,
        path="/path/to/file",
        exists=True,
        is_file=True,
        size=size,
    )

    # Set up the file_info attribute with a concrete value
    mock_fs._get_file_info.return_value = file_info
    mock_fs.service._get_file_info.return_value = file_info


def setup_mock_file_info_with_size(mock_fs, path: str | Path, size: int) -> None:
    """
    Setup a mock file_info with specific path and size for tests.

    Args:
        mock_fs: The mocked fs service
        path: The file path to use
        size: The file size to return
    """
    # Create a concrete FileInfoResult with the specified path and size
    file_info = FileInfoResult(
        success=True,
        path=str(path),
        exists=True,
        is_file=True,
        size=size,
    )

    # Set up the file_info return value with a concrete value
    mock_fs.service._get_file_info.return_value = file_info
    mock_fs._get_file_info.return_value = file_info


def patch_operations_module():
    """
    Create patches for the _operations module to avoid real Pandoc calls.

    This function returns a context manager that patches key _operations
    to prevent calls to the real Pandoc installation.

    Returns:
        A context manager for patching _operations
    """
    # Create patches for all _operations that might access Pandoc
    verify_patch = patch(
        "quackcore.integrations.pandoc._operations.verify_pandoc", return_value="2.11.4"
    )

    html_to_md_patch = patch(
        "quackcore.integrations.pandoc._operations.convert_html_to_markdown",
        return_value=IntegrationResult.success_result(
            (Path("/path/to/output/file.md"), None),
            message="Successfully converted HTML to Markdown",
        ),
    )

    md_to_docx_patch = patch(
        "quackcore.integrations.pandoc._operations.convert_markdown_to_docx",
        return_value=IntegrationResult.success_result(
            (Path("/path/to/output/file.docx"), None),
            message="Successfully converted Markdown to DOCX",
        ),
    )

    # Return a nested context manager
    return patch.multiple(
        "quackcore.integrations.pandoc._operations",
        verify_pandoc=verify_patch.start(),
        convert_html_to_markdown=html_to_md_patch.start(),
        convert_markdown_to_docx=md_to_docx_patch.start(),
    )
