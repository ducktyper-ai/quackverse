# quackcore/tests/test_integrations/pandoc/operations/test_utils.py
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.pandoc import (
    ConversionMetrics,
    PandocConfig,
)
from quackcore.integrations.pandoc.operations import validate_html_structure
from quackcore.integrations.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    get_file_info,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
    verify_pandoc,
)

# --- Tests for operations.utils ---

def test_verify_pandoc_success(mock_pypandoc):
    """Test successful verification of pandoc."""
    version = verify_pandoc()
    assert version == "2.11.0"
    assert mock_pypandoc.get_pandoc_version.called


def test_verify_pandoc_import_error(monkeypatch):
    """Test handling of ImportError during pandoc verification."""
    # Remove pypandoc from modules
    if 'pypandoc' in pytest.importorskip("sys").modules:
        monkeypatch.delitem(pytest.importorskip("sys").modules, 'pypandoc')

    with pytest.raises(QuackIntegrationError) as exc_info:
        verify_pandoc()

    assert "pypandoc module is not installed" in str(exc_info.value)


def test_verify_pandoc_os_error(mock_pypandoc):
    """Test handling of OSError during pandoc verification."""
    mock_pypandoc.get_pandoc_version.side_effect = OSError("Pandoc not found")

    with pytest.raises(QuackIntegrationError) as exc_info:
        verify_pandoc()

    assert "Pandoc is not installed" in str(exc_info.value)


def test_prepare_pandoc_args():
    """Test preparation of pandoc conversion arguments."""
    config = PandocConfig()

    # Test HTML to Markdown args
    html_md_args = prepare_pandoc_args(config, "html", "markdown")
    assert "--wrap=none" in html_md_args
    assert "--standalone" in html_md_args
    assert "--markdown-headings=atx" in html_md_args
    assert "--strip-comments" in html_md_args

    # Test Markdown to DOCX args
    md_docx_args = prepare_pandoc_args(config, "markdown", "docx")
    assert "--wrap=none" in md_docx_args
    assert "--standalone" in md_docx_args
    assert "--markdown-headings=atx" in md_docx_args

    # Test with custom extra args
    custom_args = prepare_pandoc_args(config, "html", "markdown", ["--custom-arg"])
    assert "--custom-arg" in custom_args


def test_get_file_info(fs_stub):
    """Test getting file information for conversion."""
    # Test with HTML file
    html_info = get_file_info("test.html")
    assert html_info.path == "test.html"
    assert html_info.format == "html"
    assert html_info.size == 100

    # Test with Markdown file
    md_info = get_file_info("test.md")
    assert md_info.path == "test.md"
    assert md_info.format == "markdown"

    # Test with format hint override
    hint_info = get_file_info("test.txt", format_hint="html")
    assert hint_info.format == "html"

    # Test with file not found
    fs_stub.get_file_info = lambda path: SimpleNamespace(success=False, exists=False)
    with pytest.raises(QuackIntegrationError):
        get_file_info("missing.html")


def test_validate_html_structure(mock_bs4):
    """Test validation of HTML document structure."""
    # Valid HTML
    valid, errors = validate_html_structure("<html><body><h1>Title</h1></body></html>")
    assert valid
    assert not errors

    # Invalid HTML (no body)
    mock_bs4.BeautifulSoup.return_value.find.return_value = False
    invalid, errors = validate_html_structure("<html><head></head></html>")
    assert not invalid
    assert "missing body" in errors[0].lower()

    # Check links
    mock_bs4.BeautifulSoup.return_value.find.return_value = True
    mock_bs4.BeautifulSoup.return_value.find_all.return_value = [
        MagicMock(get=lambda attr: "")  # Empty href
    ]
    invalid, errors = validate_html_structure(
        "<html><body><a href=\"\"></a></body></html>", check_links=True)
    assert not invalid
    assert "empty links" in errors[0].lower()


def test_validate_docx_structure(mock_docx):
    """Test validation of DOCX document structure."""
    with patch('sys.modules', {'docx': mock_docx}):
        # Valid DOCX
        valid, errors = validate_docx_structure("test.docx")
        assert valid
        assert not errors

        # Empty DOCX
        mock_docx.Document.return_value.paragraphs = []
        valid, errors = validate_docx_structure("empty.docx")
        assert not valid
        assert "no paragraphs" in errors[0].lower()

    # Test with docx not installed - ensure docx is not in modules
    with patch.dict('sys.modules', {}, clear=True):  # Clear modules
        # This should skip validation and return true when docx module is not available
        valid, errors = validate_docx_structure("test.docx")
        assert valid
        assert not errors

def test_check_file_size():
    """Test validation of file size."""
    # Valid size
    valid, errors = check_file_size(100, 50)
    assert valid
    assert not errors

    # Invalid size
    invalid, errors = check_file_size(30, 50)
    assert not invalid
    assert "below the minimum threshold" in errors[0]


def test_check_conversion_ratio():
    """Test validation of conversion ratio."""
    # Valid ratio
    valid, errors = check_conversion_ratio(80, 100, 0.1)
    assert valid
    assert not errors

    # Invalid ratio
    invalid, errors = check_conversion_ratio(5, 100, 0.1)
    assert not invalid
    assert "less than" in errors[0]


def test_track_metrics():
    """Test tracking of conversion metrics."""
    metrics = ConversionMetrics()
    config = PandocConfig()

    track_metrics(
        "test.html",
        time.time() - 1.0,  # Start time 1 second ago
        100,  # Original size
        80,  # Converted size
        metrics,
        config
    )

    # Verify metrics were recorded
    assert "test.html" in metrics.conversion_times
    assert "test.html" in metrics.file_sizes
    assert metrics.file_sizes["test.html"]["original"] == 100
    assert metrics.file_sizes["test.html"]["converted"] == 80
    assert metrics.file_sizes["test.html"]["ratio"] == 0.8

    # Test with metrics tracking disabled
    metrics = ConversionMetrics()
    config.metrics.track_conversion_time = False
    config.metrics.track_file_sizes = False

    track_metrics(
        "test2.html",
        time.time(),
        200,
        160,
        metrics,
        config
    )

    # Verify metrics were not recorded
    assert "test2.html" not in metrics.conversion_times
    assert "test2.html" not in metrics.file_sizes
