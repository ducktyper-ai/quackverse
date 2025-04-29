# quackcore/tests/test_integrations/pandoc/operations/test_md_to_docx.py
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.pandoc import (
    ConversionMetrics,
    PandocConfig,
)
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionMetrics
from quackcore.integrations.pandoc.operations import (
    convert_markdown_to_docx,
    validate_docx_conversion,
)

# --- Tests for Markdown to DOCX operations ---

@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
@patch(
    'quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once')
@patch('quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output')
def test_convert_markdown_to_docx_success(mock_get_output, mock_convert, mock_validate):
    """Test successful Markdown to DOCX conversion."""
    # Setup mocks
    mock_validate.return_value = 100  # Original size
    mock_get_output.return_value = (0.5, 80)  # conversion_time, output_size

    # Mock validate_conversion to return no errors
    with patch(
            'quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion') as mock_validate_conv:
        mock_validate_conv.return_value = []

        # Run conversion
        config = PandocConfig()
        metrics = ConversionMetrics()
        result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

        # Verify
        assert result.success
        assert mock_validate.called
        assert mock_convert.called
        assert mock_get_output.called
        assert metrics.successful_conversions == 1


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
def test_convert_markdown_to_docx_validation_error(mock_validate):
    """Test Markdown to DOCX conversion with validation error."""
    # Setup mock to raise error
    mock_validate.side_effect = QuackIntegrationError("Invalid Markdown", {})

    # Run conversion
    config = PandocConfig()
    metrics = ConversionMetrics()
    result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

    # Verify
    assert not result.success
    assert "Invalid Markdown" in result.error
    assert metrics.failed_conversions == 1
    assert "input.md" in metrics.errors


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
@patch(
    'quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once')
@patch('quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output')
def test_convert_markdown_to_docx_conversion_failure(mock_get_output, mock_convert,
                                                     mock_validate):
    """Test Markdown to DOCX conversion with pandoc failure."""
    # Setup mocks
    mock_validate.return_value = 100
    mock_convert.side_effect = QuackIntegrationError("Pandoc failed", {})

    # Run conversion
    config = PandocConfig()
    metrics = ConversionMetrics()
    result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

    # Verify
    assert not result.success
    assert "Pandoc failed" in result.error
    assert metrics.failed_conversions == 1


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
@patch(
    'quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once')
@patch('quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output')
def test_convert_markdown_to_docx_validation_failure(mock_get_output, mock_convert,
                                                     mock_validate):
    """Test Markdown to DOCX conversion with output validation failure."""
    # Setup mocks
    mock_validate.return_value = 100
    mock_get_output.return_value = (0.5, 80)

    # Mock validate_conversion to return errors
    with patch(
            'quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion') as mock_validate_conv:
        mock_validate_conv.return_value = ["Output validation failed"]

        # Set up config for max retries
        config = PandocConfig()
        config.retry_mechanism.max_conversion_retries = 2
        metrics = ConversionMetrics()

        # Run conversion
        result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

        # Verify
        assert not result.success
        assert "validation failed" in result.error.lower()
        assert mock_convert.call_count == 2  # Called twice due to retry
        assert metrics.failed_conversions == 1


def test_validate_conversion_md_to_docx(fs_stub):
    """Test validation of Markdown to DOCX conversion results."""
    config = PandocConfig()

    # Test successful validation
    with patch(
            'quackcore.integrations.pandoc.operations.md_to_docx.validate_docx_structure') as mock_validate_docx:
        mock_validate_docx.return_value = (True, [])

        errors = validate_docx_conversion("output.docx", "input.md", 100, config)
        assert not errors

    # Test file size too small
    config.validation.min_file_size = 200
    errors = validate_docx_conversion("output.docx", "input.md", 100, config)
    assert errors
    assert any("below the minimum threshold" in error for error in errors)

    # Test conversion ratio too small
    config.validation.min_file_size = 50
    fs_stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, size=5, modified=time.time()
    )
    errors = validate_docx_conversion("output.docx", "input.md", 100, config)
    assert errors
    assert any("less than" in error for error in errors)

    # Test docx structure validation
    with patch(
            'quackcore.integrations.pandoc.operations.md_to_docx.validate_docx_structure') as mock_validate_docx:
        mock_validate_docx.return_value = (False, ["Invalid DOCX structure"])

        config.validation.verify_structure = True
        errors = validate_docx_conversion("output.docx", "input.md", 100, config)
        assert errors
        assert any("Invalid DOCX structure" in error for error in errors)

# --- Markdown to DOCX Operation Tests ---

@patch('quackcore.fs.service.standalone')
def test_md_to_docx_validate_markdown_input_success(mock_fs):
    """Test successful validation of Markdown input."""
    # Setup mock fs
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=True, exists=True, size=1000
    )
    mock_fs.read_text.return_value = SimpleNamespace(
        success=True, content="# Test Markdown\n\nContent"
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _validate_markdown_input,
    )

    result_size = _validate_markdown_input("test.md")

    assert result_size == 1000
    assert mock_fs.get_file_info.called
    assert mock_fs.read_text.called


@patch('quackcore.fs.service.standalone')
def test_md_to_docx_validate_markdown_input_file_not_found(mock_fs):
    """Test validation of Markdown input when file is not found."""
    # Setup mock fs
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=True, exists=False
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _validate_markdown_input,
    )

    with pytest.raises(QuackIntegrationError) as excinfo:
        _validate_markdown_input("missing.md")

    assert "Input file not found" in str(excinfo.value)


@patch('quackcore.fs.service.standalone')
def test_md_to_docx_validate_markdown_input_read_error(mock_fs):
    """Test validation of Markdown input with read error."""
    # Setup mock fs
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=True, exists=True, size=1000
    )
    mock_fs.read_text.return_value = SimpleNamespace(
        success=False, error="Read error"
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _validate_markdown_input,
    )

    with pytest.raises(QuackIntegrationError) as excinfo:
        _validate_markdown_input("test.md")

    assert "Could not read Markdown file" in str(excinfo.value)


@patch('quackcore.fs.service.standalone')
def test_md_to_docx_validate_markdown_input_empty_file(mock_fs):
    """Test validation of empty Markdown input."""
    # Setup mock fs
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=True, exists=True, size=0
    )
    mock_fs.read_text.return_value = SimpleNamespace(
        success=True, content=""
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _validate_markdown_input,
    )

    with pytest.raises(QuackIntegrationError) as excinfo:
        _validate_markdown_input("empty.md")

    assert "Markdown file is empty" in str(excinfo.value)


def test_md_to_docx_convert_once_success():
    """Test successful single conversion of Markdown to DOCX."""
    # Mock fs and pypandoc
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch('pypandoc.convert_file') as mock_convert:
        # Setup mocks
        mock_fs.split_path.return_value = ["path", "to", "file.md"]
        mock_fs.join_path.return_value = "path/to"
        mock_fs.create_directory.return_value = SimpleNamespace(success=True)

        # Import and test the function
        from quackcore.integrations.pandoc.operations.md_to_docx import (
            _convert_markdown_to_docx_once,
        )

        config = PandocConfig()
        _convert_markdown_to_docx_once("test.md", "output.docx", config)

        assert mock_convert.called
        assert mock_fs.create_directory.called


def test_md_to_docx_convert_once_directory_error():
    """Test Markdown to DOCX conversion with directory creation error."""
    # Mock fs
    with patch('quackcore.fs.service.standalone') as mock_fs:
        # Setup mock to fail directory creation
        mock_fs.split_path.return_value = ["path", "to", "file.md"]
        mock_fs.join_path.return_value = "path/to"
        mock_fs.create_directory.return_value = SimpleNamespace(
            success=False, error="Permission denied"
        )

        # Import and test the function
        from quackcore.integrations.pandoc.operations.md_to_docx import (
            _convert_markdown_to_docx_once,
        )

        config = PandocConfig()
        with pytest.raises(QuackIntegrationError) as excinfo:
            _convert_markdown_to_docx_once("test.md", "output.docx", config)

        assert "Failed to create output directory" in str(excinfo.value)


def test_md_to_docx_convert_once_pandoc_error():
    """Test Markdown to DOCX conversion with pandoc error."""
    # Mock fs and pypandoc
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch('pypandoc.convert_file') as mock_convert:
        # Setup mocks
        mock_fs.split_path.return_value = ["path", "to", "file.md"]
        mock_fs.join_path.return_value = "path/to"
        mock_fs.create_directory.return_value = SimpleNamespace(success=True)
        mock_convert.side_effect = Exception("Pandoc conversion failed")

        # Import and test the function
        from quackcore.integrations.pandoc.operations.md_to_docx import (
            _convert_markdown_to_docx_once,
        )

        config = PandocConfig()
        with pytest.raises(QuackIntegrationError) as excinfo:
            _convert_markdown_to_docx_once("test.md", "output.docx", config)

        assert "Pandoc conversion failed" in str(excinfo.value)


@patch('quackcore.fs.service.standalone')
@patch('quackcore.integrations.pandoc.operations.md_to_docx.time')
def test_md_to_docx_get_conversion_output_success(mock_time, mock_fs):
    """Test successful retrieval of conversion output metrics."""
    # Setup mocks
    mock_time.time.return_value = 1000.0
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=True, size=2000
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _get_conversion_output,
    )

    start_time = 999.0  # 1 second before current time
    conversion_time, output_size = _get_conversion_output("output.docx", start_time)

    assert conversion_time == 1.0
    assert output_size == 2000


@patch('quackcore.fs.service.standalone')
def test_md_to_docx_get_conversion_output_file_info_error(mock_fs):
    """Test get conversion output with file info error."""
    # Setup mock to fail getting file info
    mock_fs.get_file_info.return_value = SimpleNamespace(
        success=False, error="File not found"
    )

    # Import and test the function
    from quackcore.integrations.pandoc.operations.md_to_docx import (
        _get_conversion_output,
    )

    with pytest.raises(QuackIntegrationError) as excinfo:
        _get_conversion_output("output.docx", time.time())

    assert "Failed to get info for converted file" in str(excinfo.value)


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
@patch(
    'quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once')
@patch('quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output')
@patch('quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion')
def test_convert_markdown_to_docx_full_success(mock_validate, mock_get_output,
                                               mock_convert, mock_validate_input):
    """Test full successful Markdown to DOCX conversion workflow."""
    # Setup mocks
    mock_validate_input.return_value = 1000  # Original size
    mock_get_output.return_value = (0.5, 2000)  # conversion_time, output_size
    mock_validate.return_value = []  # No validation errors

    # Test the function
    config = PandocConfig()
    metrics = ConversionMetrics()

    result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

    # Verify
    assert result.success
    assert mock_validate_input.called
    assert mock_convert.called
    assert mock_get_output.called
    assert mock_validate.called
    assert metrics.successful_conversions == 1
    assert "input.md" not in metrics.errors


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
@patch(
    'quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once')
@patch('quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output')
@patch('quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion')
def test_convert_markdown_to_docx_validation_failure(mock_validate, mock_get_output,
                                                     mock_convert, mock_validate_input):
    """Test Markdown to DOCX conversion with validation failures."""
    # Setup mocks
    mock_validate_input.return_value = 1000  # Original size
    mock_get_output.return_value = (0.5, 500)  # conversion_time, output_size
    mock_validate.return_value = ["Validation error"]  # Validation error

    # Configure max retries
    config = PandocConfig()
    config.retry_mechanism.max_conversion_retries = 2
    metrics = ConversionMetrics()

    result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

    # Verify
    assert not result.success
    assert "maximum retries" in result.error
    assert mock_validate_input.called
    assert mock_convert.call_count == 2  # Called twice due to retry
    assert mock_get_output.call_count == 2
    assert mock_validate.call_count == 2
    assert metrics.failed_conversions == 1
    assert "input.md" in metrics.errors


@patch('quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input')
def test_convert_markdown_to_docx_validation_error(mock_validate_input):
    """Test Markdown to DOCX conversion with input validation error."""
    # Setup mock to raise error
    mock_validate_input.side_effect = QuackIntegrationError("Invalid Markdown", {})

    # Test the function
    config = PandocConfig()
    metrics = ConversionMetrics()

    result = convert_markdown_to_docx("input.md", "output.docx", config, metrics)

    # Verify
    assert not result.success
    assert "Invalid Markdown" in result.error
    assert metrics.failed_conversions == 1
    assert "input.md" in metrics.errors


@patch('quackcore.integrations.pandoc.operations.md_to_docx._check_docx_metadata')
def test_md_to_docx_validate_conversion_docx_structure(mock_check_metadata):
    """Test validation of converted DOCX document."""
    config = PandocConfig()

    # Test successful validation
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch(
                'quackcore.integrations.pandoc.operations.md_to_docx.validate_docx_structure') as mock_validate_docx:
        mock_fs.get_file_info.return_value = SimpleNamespace(
            success=True, exists=True, size=2000
        )
        mock_validate_docx.return_value = (True, [])

        from quackcore.integrations.pandoc.operations.md_to_docx import (
            validate_conversion,
        )

        errors = validate_conversion("output.docx", "input.md", 1000, config)
        assert not errors

        # Test with structure verification enabled
        config.validation.verify_structure = True
        mock_fs.get_file_info.return_value = SimpleNamespace(
            success=True, exists=True, size=2000
        )

        errors = validate_conversion("output.docx", "input.md", 1000, config)
        assert not errors
        assert mock_validate_docx.called
        assert mock_check_metadata.called


def test_md_to_docx_check_metadata():
    """Test checking DOCX metadata."""
    from quackcore.integrations.pandoc.operations.md_to_docx import _check_docx_metadata

    # Test with docx module available
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch('importlib.import_module') as mock_import:
        mock_fs.split_path.return_value = ["path", "to", "input.md"]
        mock_doc = MagicMock()
        mock_doc.core_properties.title = "Document Title"
        mock_docx = MagicMock()
        mock_docx.Document.return_value = mock_doc
        mock_import.return_value = mock_docx

        # This should not raise any exceptions
        _check_docx_metadata("output.docx", "input.md", True)

        assert mock_import.called
        assert mock_fs.split_path.called

    # Test with import error
    with patch('quackcore.fs.service.standalone') as mock_fs, \
            patch('importlib.import_module') as mock_import, \
            patch(
                'quackcore.integrations.pandoc.operations.md_to_docx.logger') as mock_logger:
        mock_import.side_effect = ImportError("docx module not found")

        # This should not raise exceptions, just log a debug message
        _check_docx_metadata("output.docx", "input.md", True)

        assert mock_import.called
        assert mock_logger.debug.called
