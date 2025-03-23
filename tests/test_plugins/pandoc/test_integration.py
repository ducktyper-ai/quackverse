# tests/test_plugins/pandoc/test_integration.py
"""
Integration tests for pandoc plugin.

This module tests the complete workflow from service to operations,
verifying that all components work together properly.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from quackcore.plugins.pandoc import ConversionResult
from quackcore.plugins.pandoc.service import PandocService


@pytest.fixture
def temp_dir() -> str:
    """Create a temporary directory for test files."""
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def test_html_file(temp_dir: str) -> Path:
    """Create a test HTML file."""
    html_content = """<!DOCTYPE html>
    <html>
    <head>
        <title>Test Document</title>
    </head>
    <body>
        <h1>Test Header</h1>
        <p>This is a paragraph with <a href="https://example.com">a link</a>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>"""

    html_path = Path(temp_dir) / "test.html"
    html_path.write_text(html_content)
    return html_path


@pytest.fixture
def test_md_file(temp_dir: str) -> Path:
    """Create a test Markdown file."""
    md_content = """# Test Header

This is a paragraph with [a link](https://example.com).

- Item 1
- Item 2
"""

    md_path = Path(temp_dir) / "test.md"
    md_path.write_text(md_content)
    return md_path


class TestPandocIntegration:
    """Integration tests for the pandoc plugin."""

    @pytest.mark.integration
    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_service_initialization(self, mock_verify: MagicMock,
                                    temp_dir: str) -> None:
        """Test service initialization with custom config."""
        mock_verify.return_value = "2.18"

        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)

        config_path = Path(temp_dir) / "pandoc_config.yaml"
        config_content = """
        output_dir: {}
        validation:
          min_file_size: 100
          verify_structure: true
        """.format(str(output_dir).replace("\\", "\\\\"))

        config_path.write_text(config_content)

        service = PandocService(config_path=config_path)

        # Test initialization
        with patch("quackcore.fs.service.create_directory"):
            success = service.initialize()

            assert success is True
            assert service._initialized is True
            assert service.config is not None
            assert service.config.output_dir == output_dir
            assert service.config.validation.min_file_size == 100
            mock_verify.assert_called_once()

    @pytest.mark.integration
    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("pypandoc.convert_file")
    def test_html_to_markdown_workflow(
            self, mock_convert: MagicMock, mock_verify: MagicMock, test_html_file: Path,
            temp_dir: str
    ) -> None:
        """Test the complete workflow from HTML to Markdown."""
        mock_verify.return_value = "2.18"

        # Mock pypandoc conversion to return markdown
        mock_convert.return_value = """# Test Header

This is a paragraph with [a link](https://example.com).

- Item 1
- Item 2
"""

        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)

        service = PandocService(output_dir=output_dir)

        # Mock file system operations
        with patch("quackcore.fs.service.create_directory"), \
                patch("quackcore.fs.service.get_file_info") as mock_get_info, \
                patch("quackcore.fs.service.write_text") as mock_write:

            # Mock file info for HTML file
            mock_html_info = MagicMock(
                success=True,
                exists=True,
                path=str(test_html_file),
                size=500,
                modified=1609459200.0,
            )

            # Mock file info for Markdown output
            mock_md_info = MagicMock(
                success=True,
                exists=True,
                path=str(output_dir / "test.md"),
                size=200,
                modified=1609459300.0,
            )

            # Set up get_file_info to return different values depending on the path
            def get_info_side_effect(path):
                if str(path) == str(test_html_file):
                    return mock_html_info
                else:
                    return mock_md_info

            mock_get_info.side_effect = get_info_side_effect

            # Mock successful write
            mock_write.return_value = MagicMock(success=True)

            # Initialize and convert
            service.initialize()
            result = service.html_to_markdown(test_html_file)

            # Check conversion result
            assert result.success is True
            assert result.source_format == "html"
            assert result.target_format == "markdown"
            assert result.output_size is not None
            assert result.content is not None
            mock_convert.assert_called_once()

    @pytest.mark.integration
    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("pypandoc.convert_file")
    def test_markdown_to_docx_workflow(
            self, mock_convert: MagicMock, mock_verify: MagicMock, test_md_file: Path,
            temp_dir: str
    ) -> None:
        """Test the complete workflow from Markdown to DOCX."""
        mock_verify.return_value = "2.18"

        # Mock pypandoc conversion (pypandoc doesn't return data for docx conversion)
        mock_convert.return_value = None

        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)

        service = PandocService(output_dir=output_dir)

        # Mock file system operations
        with patch("quackcore.fs.service.create_directory"), \
                patch("quackcore.fs.service.get_file_info") as mock_get_info, \
                patch(
                    "quackcore.plugins.pandoc.operations.utils.validate_docx_structure") as mock_validate:

            # Mock file info for Markdown file
            mock_md_info = MagicMock(
                success=True,
                exists=True,
                path=str(test_md_file),
                size=200,
                modified=1609459200.0,
            )

            # Mock file info for DOCX output
            mock_docx_info = MagicMock(
                success=True,
                exists=True,
                path=str(output_dir / "test.docx"),
                size=800,
                modified=1609459300.0,
            )

            # Set up get_file_info to return different values depending on the path
            def get_info_side_effect(path):
                if str(path) == str(test_md_file):
                    return mock_md_info
                else:
                    return mock_docx_info

            mock_get_info.side_effect = get_info_side_effect

            # Mock successful DOCX validation
            mock_validate.return_value = (True, [])

            # Initialize and convert
            service.initialize()
            result = service.markdown_to_docx(test_md_file)

            # Check conversion result
            assert result.success is True
            assert result.source_format == "markdown"
            assert result.target_format == "docx"
            assert result.output_size is not None
            assert result.content is not None
            mock_convert.assert_called_once()

    @pytest.mark.integration
    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_convert_directory_workflow(
            self, mock_verify: MagicMock, temp_dir: str
    ) -> None:
        """Test the directory conversion workflow."""
        mock_verify.return_value = "2.18"

        # Create input directory with multiple HTML files
        input_dir = Path(temp_dir) / "input"
        input_dir.mkdir(exist_ok=True)

        # Create test HTML files
        for i in range(3):
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Test Document {i}</title>
            </head>
            <body>
                <h1>Test Header {i}</h1>
                <p>This is a paragraph {i}.</p>
            </body>
            </html>"""

            html_path = input_dir / f"test{i}.html"
            html_path.write_text(html_content)

        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)

        service = PandocService(output_dir=output_dir)

        # Mock file system operations
        with patch("quackcore.fs.service.create_directory"), \
                patch("quackcore.fs.service.find_files") as mock_find, \
                patch(
                    "quackcore.plugins.pandoc.service.get_file_info") as mock_get_info, \
                patch.object(service, "html_to_markdown") as mock_convert:
            # Mock find files
            mock_find.return_value = MagicMock(
                success=True,
                files=[
                    Path(input_dir / "test0.html"),
                    Path(input_dir / "test1.html"),
                    Path(input_dir / "test2.html"),
                ],
                pattern="*.html",
                message="Found 3 files",
            )

            # Mock file info
            mock_get_info.return_value = MagicMock(
                path=Path(input_dir / "test0.html"),
                format="html",
                size=200,
            )

            # Mock successful conversions
            mock_convert.side_effect = [
                ConversionResult.success_result(
                    Path(output_dir / f"test{i}.md"),
                    "html",
                    "markdown",
                    1.0,
                    100,
                    200,
                    f"Successfully converted test{i}.html"
                )
                for i in range(3)
            ]

            # Initialize and convert directory
            service.initialize()
            result = service.convert_directory(input_dir, "markdown", output_dir)

            # Check conversion result
            assert result.success is True
            assert len(result.successful_files) == 3
            assert len(result.failed_files) == 0
            assert mock_convert.call_count == 3

    @pytest.mark.integration
    def test_full_conversion_with_actual_pandoc(self, test_html_file: Path,
                                                temp_dir: str) -> None:
        """
        Test actual conversion using pandoc if available.
        This test is skipped if pandoc is not installed.
        """
        service = PandocService(output_dir=Path(temp_dir) / "output")

        # Skip if pandoc is not available
        if not service.is_pandoc_available():
            pytest.skip("Pandoc is not installed")

        # Initialize the service
        success = service.initialize()
        assert success is True

        # Convert HTML to Markdown
        result_md = service.html_to_markdown(test_html_file)

        # Check conversion was successful
        assert result_md.success is True
        assert result_md.content is not None
        assert result_md.content.exists()

        # Convert Markdown to DOCX
        result_docx = service.markdown_to_docx(result_md.content)

        # Check conversion was successful
        assert result_docx.success is True
        assert result_docx.content is not None
        assert result_docx.content.exists()

        # Check metrics
        metrics = service.get_metrics()
        assert metrics.successful_conversions >= 2
        assert metrics.failed_conversions == 0