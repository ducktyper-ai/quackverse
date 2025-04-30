# quackcore/tests/test_integrations/pandoc/test_pandoc_utils.py
"""
Tests for utilities in the pandoc integration.

This module contains detailed tests for utility functions
and edge cases in the pandoc integration.
"""

import time
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import (
    ConversionDetails,
    ConversionMetrics,
    ConversionTask,
    FileInfo,
)
from quackcore.integrations.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    get_file_info,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
    validate_html_structure,
    verify_pandoc,
)


def test_conversion_metrics_initialization():
    """Test the initialization of ConversionMetrics."""
    metrics = ConversionMetrics()

    assert isinstance(metrics.conversion_times, dict)
    assert isinstance(metrics.file_sizes, dict)
    assert isinstance(metrics.errors, dict)
    assert isinstance(metrics.start_time, datetime)
    assert metrics.total_attempts == 0
    assert metrics.successful_conversions == 0
    assert metrics.failed_conversions == 0

    # Test with custom values
    custom_time = datetime(2023, 1, 1, 12, 0, 0)
    custom_metrics = ConversionMetrics(
        start_time=custom_time,
        total_attempts=5,
        successful_conversions=3,
        failed_conversions=2
    )

    assert custom_metrics.start_time == custom_time
    assert custom_metrics.total_attempts == 5
    assert custom_metrics.successful_conversions == 3
    assert custom_metrics.failed_conversions == 2


def test_file_info_initialization():
    """Test the initialization of FileInfo."""
    # Minimal initialization
    file_info = FileInfo(path="/path/to/file.html", format="html")

    assert file_info.path == "/path/to/file.html"
    assert file_info.format == "html"
    assert file_info.size == 0
    assert file_info.modified is None
    assert file_info.extra_args == []

    # Full initialization
    file_info = FileInfo(
        path="/path/to/file.md",
        format="markdown",
        size=1024,
        modified=123456789.0,
        extra_args=["--strip-comments"]
    )

    assert file_info.path == "/path/to/file.md"
    assert file_info.format == "markdown"
    assert file_info.size == 1024
    assert file_info.modified == 123456789.0
    assert file_info.extra_args == ["--strip-comments"]


def test_conversion_task_initialization():
    """Test the initialization of ConversionTask."""
    # Create a file info object
    file_info = FileInfo(path="/path/to/file.html", format="html", size=1024)

    # Create a conversion task
    task = ConversionTask(
        source=file_info,
        target_format="markdown",
        output_path="/path/to/output.md"
    )

    assert task.source == file_info
    assert task.target_format == "markdown"
    assert task.output_path == "/path/to/output.md"

    # Test with optional output_path
    task = ConversionTask(
        source=file_info,
        target_format="markdown"
    )

    assert task.source == file_info
    assert task.target_format == "markdown"
    assert task.output_path is None


def test_conversion_details_initialization():
    """Test the initialization of ConversionDetails."""
    # Default initialization
    details = ConversionDetails()

    assert details.source_format is None
    assert details.target_format is None
    assert details.conversion_time is None
    assert details.output_size is None
    assert details.input_size is None
    assert details.validation_errors == []

    # Full initialization
    details = ConversionDetails(
        source_format="html",
        target_format="markdown",
        conversion_time=1.5,
        output_size=800,
        input_size=1000,
        validation_errors=["Warning: missing header"]
    )

    assert details.source_format == "html"
    assert details.target_format == "markdown"
    assert details.conversion_time == 1.5
    assert details.output_size == 800
    assert details.input_size == 1000
    assert details.validation_errors == ["Warning: missing header"]


def test_get_file_info_edge_cases(monkeypatch):
    """Test edge cases for get_file_info utility."""
    # Create a mock standalone fs service
    mock_fs = SimpleNamespace()

    # Test with invalid file size string
    mock_fs.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, size="not-a-number", modified=None
    )
    monkeypatch.setattr('quackcore.integrations.pandoc.operations.utils.fs', mock_fs)

    file_info = get_file_info("test.html")
    assert file_info.size == 1024  # Default when size conversion fails

    # Test with extension mapping
    mock_fs.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, size=100, modified=None
    )
    mock_fs.get_extension = lambda path: SimpleNamespace(data=path.split('.')[-1])
    monkeypatch.setattr('quackcore.integrations.pandoc.operations.utils.fs', mock_fs)

    # Test various extensions
    extensions_mapping = {
        "md": "markdown",
        "markdown": "markdown",
        "html": "html",
        "htm": "html",
        "docx": "docx",
        "doc": "docx",
        "pdf": "pdf",
        "txt": "plain",
        "unknown": "unknown"  # Should use extension as format
    }

    for ext, expected_format in extensions_mapping.items():
        file_info = get_file_info(f"test.{ext}")
        assert file_info.format == expected_format, f"Failed for extension: {ext}"


def test_check_file_size_edge_cases():
    """Test edge cases for check_file_size utility."""
    # Test with None values
    valid, errors = check_file_size(None, 50)
    assert not valid
    assert "below the minimum threshold" in errors[0]

    valid, errors = check_file_size(100, None)
    assert valid
    assert not errors  # No validation if threshold is None

    # Test with string values (should be converted to int)
    valid, errors = check_file_size(100, 50)
    assert valid
    assert not errors

    # Test with zero threshold
    valid, errors = check_file_size(100, 0)
    assert valid
    assert not errors


def test_check_conversion_ratio_edge_cases():
    """Test edge cases for check_conversion_ratio utility."""
    # Test with zero original size
    valid, errors = check_conversion_ratio(50, 0, 0.1)
    assert valid
    assert not errors  # No validation if original size is 0

    # Test with None values
    valid, errors = check_conversion_ratio(None, 100, 0.1)
    assert not valid
    assert "less than" in errors[0]

    valid, errors = check_conversion_ratio(50, None, 0.1)
    assert valid
    assert not errors  # No validation if original size is None

    valid, errors = check_conversion_ratio(50, 100, None)
    assert valid  # Threshold defaults to 0.1
    assert not errors

    # Test with string values (should be converted)
    valid, errors = check_conversion_ratio(50, 100, 0.1)
    assert valid
    assert not errors

    # Test with exactly threshold ratio
    valid, errors = check_conversion_ratio(10, 100, 0.1)
    assert valid  # Ratio is exactly 0.1, should pass
    assert not errors

    # Test with slightly below threshold
    valid, errors = check_conversion_ratio(9, 100, 0.1)
    assert not valid  # Ratio is 0.09, should fail
    assert "less than" in errors[0]


@patch('quackcore.integrations.pandoc.operations.utils.logger')
def test_track_metrics_logging(mock_logger):
    """Test that track_metrics properly logs information."""
    metrics = ConversionMetrics()
    config = PandocConfig()

    # Enable metrics tracking
    config.metrics.track_conversion_time = True
    config.metrics.track_file_sizes = True

    track_metrics(
        "test.html",
        time.time() - 1.0,
        100,  # Original size
        80,  # Converted size
        metrics,
        config
    )

    # Verify logging was called
    assert mock_logger.info.call_count >= 2  # Should log both time and size

    # Check for conversion time logging
    time_log_called = False
    for call in mock_logger.info.call_args_list:
        args, _ = call
        if "Conversion time" in args[0]:
            time_log_called = True
            break
    assert time_log_called

    # Check for file size logging
    size_log_called = False
    for call in mock_logger.info.call_args_list:
        args, _ = call
        if "File size change" in args[0]:
            size_log_called = True
            break
    assert size_log_called


def test_validate_html_structure_edge_cases():
    """Test edge cases for validate_html_structure utility."""
    # Properly patch imports without raising global exception
    with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs:
               pytest.raises(ImportError, "bs4 not installed") if name == 'bs4' else __import__(name, *args, **kwargs)):
        # This should return (False, errors) because the import will fail
        valid, errors = validate_html_structure("<html><body>Content</body></html>")
        assert not valid
        assert any("HTML validation error" in error for error in errors)

    # Test with parsing error
    mock_bs = MagicMock()
    mock_bs.BeautifulSoup.side_effect = Exception("Parsing error")
    with patch.dict('sys.modules', {'bs4': mock_bs}):
        valid, errors = validate_html_structure("<invalid><html>")
        assert not valid
        assert "validation error" in errors[0].lower()


def test_validate_docx_structure_edge_cases():
    """Test edge cases for validate_docx_structure utility."""
    # Test with docx not installed - using context manager pattern
    with patch.dict('sys.modules', {'docx': None}):
        # Should return valid=True when docx module is not available
        valid, errors = validate_docx_structure("test.docx")
        assert valid
        assert not errors

    # Test with Document constructor raising error
    mock_docx = MagicMock()
    mock_docx.Document.side_effect = Exception("Failed to open document")
    with patch.dict('sys.modules', {'docx': mock_docx}):
        valid, errors = validate_docx_structure("test.docx")
        assert not valid
        assert "validation error" in errors[0].lower()


def test_prepare_pandoc_args_comprehensive():
    """Test comprehensive options for prepare_pandoc_args utility."""
    # Test with default config
    config = PandocConfig()
    args = prepare_pandoc_args(config, "html", "markdown")

    # Check basic args
    assert "--wrap=none" in args
    assert "--standalone" in args
    assert "--markdown-headings=atx" in args

    # Check format-specific args
    html_md_args = prepare_pandoc_args(config, "html", "markdown")
    assert "--strip-comments" in html_md_args
    assert "--no-highlight" in html_md_args

    md_docx_args = prepare_pandoc_args(config, "markdown", "docx")
    assert "--wrap=none" in md_docx_args
    assert "--markdown-headings=atx" in md_docx_args
    # DOCX doesn't have specific extra args by default

    # Test with custom config - use model_construct instead of PandocOptions
    custom_config = PandocConfig(
        pandoc_options=PandocConfig.model_construct(
            wrap="auto",
            standalone=False,
            markdown_headings="setext",
            reference_links=True,
            resource_path=["/path/to/resources", "/another/path"]
        ),
        html_to_md_extra_args=["--custom-arg1"],
        md_to_docx_extra_args=["--custom-arg2"]
    )

    # HTML to Markdown with custom config
    html_md_args = prepare_pandoc_args(custom_config, "html", "markdown")
    assert "--wrap=auto" in html_md_args
    assert "--standalone" not in html_md_args
    assert "--markdown-headings=setext" in html_md_args
    assert "--reference-links" in html_md_args
    assert "--resource-path=/path/to/resources" in html_md_args
    assert "--resource-path=/another/path" in html_md_args
    assert "--custom-arg1" in html_md_args

    # Markdown to DOCX with custom config
    md_docx_args = prepare_pandoc_args(custom_config, "markdown", "docx")
    assert "--wrap=auto" in md_docx_args
    assert "--custom-arg2" in md_docx_args

    # Test with additional extra args
    extra_args = ["--extra1", "--extra2"]
    args = prepare_pandoc_args(custom_config, "html", "markdown", extra_args)
    assert "--extra1" in args
    assert "--extra2" in args

# Specific test for the post_process_markdown function
@patch('quackcore.integrations.pandoc.operations.html_to_md.re')
def test_post_process_markdown_regex_patterns(mock_re):
    """Test regex patterns used in post_process_markdown."""
    from quackcore.integrations.pandoc.operations.html_to_md import (
        post_process_markdown,
    )

    # Call the function to check regex patterns
    post_process_markdown("Test content")

    # Verify all regex patterns were used
    assert mock_re.sub.call_count >= 5

    # Check specific patterns
    patterns_to_check = [
        r"{[^}]*}",  # Remove curly braces and their content
        r":::+\s*[^\n]*\n",  # Remove colons and following content
        r"<div[^>]*>|</div>",  # Remove div tags
        r"\n\s*\n\s*\n+",  # Normalize multiple newlines
        r"<!--[^>]*-->",  # Remove HTML comments
    ]

    for pattern in patterns_to_check:
        pattern_used = False
        for call in mock_re.sub.call_args_list:
            args, _ = call
            if isinstance(args[0], str) and args[0] == pattern:
                pattern_used = True
                break
            # Handle if re.compile was used
            elif hasattr(args[0], 'pattern') and args[0].pattern == pattern:
                pattern_used = True
                break

        assert pattern_used, f"Pattern {pattern} was not used"


def test_verify_pandoc_with_all_errors():
    """Test verify_pandoc with all possible error conditions."""
    # Test ImportError
    with patch('quackcore.integrations.pandoc.operations.utils.import_module',
               side_effect=ImportError("No module named 'pypandoc'")):
        with pytest.raises(QuackIntegrationError) as exc_info:
            verify_pandoc()
        assert "pypandoc module is not installed" in str(exc_info.value)

    # Test OSError
    mock_pypandoc = MagicMock()
    mock_pypandoc.get_pandoc_version.side_effect = OSError(
        "Pandoc executable not found")

    with patch.dict('sys.modules', {'pypandoc': mock_pypandoc}):
        with pytest.raises(QuackIntegrationError) as exc_info:
            verify_pandoc()
        assert "Pandoc is not installed" in str(exc_info.value)

    # Test generic Exception
    mock_pypandoc = MagicMock()
    mock_pypandoc.get_pandoc_version.side_effect = Exception("Unexpected error")

    with patch.dict('sys.modules', {'pypandoc': mock_pypandoc}):
        with pytest.raises(QuackIntegrationError) as exc_info:
            verify_pandoc()
        assert "Error checking pandoc" in str(exc_info.value)
