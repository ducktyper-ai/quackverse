# tests/test_plugins/pandoc/test_service.py
"""
Tests for pandoc service implementation.

This module tests the PandocService class, verifying that it correctly
initializes, configures, and executes conversion operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given
from hypothesis import strategies as st

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FindResult
from quackcore.plugins.pandoc.config import ConversionConfig
from quackcore.plugins.pandoc.models import (
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    FileInfo,
)
from quackcore.plugins.pandoc.service import PandocService


class TestPandocService:
    """Tests for the PandocService class."""

    def test_initialization(self) -> None:
        """Test basic initialization without starting services."""
        service = PandocService()
        assert service.name == "Pandoc"
        assert service.config is None
        assert service._initialized is False
        assert service.converter is None

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.fs.service.create_directory")
    def test_initialize_success(
        self, mock_create_dir: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test successful initialization of the service."""
        mock_verify.return_value = "2.18"

        # Mock successful config loading
        mock_config_result = MagicMock()
        mock_config_result.success = True
        mock_config_result.content = {
            "output_dir": "./test_output",
            "validation": {"min_file_size": 100},
        }

        service = PandocService()

        with patch.object(
            service.config_provider, "load_config", return_value=mock_config_result
        ):
            with patch("quackcore.plugins.pandoc.service.DocumentConverter"):
                result = service.initialize()

                assert result is True
                assert service._initialized is True
                assert service._pandoc_version == "2.18"
                assert service.config is not None
                assert service.config.validation.min_file_size == 100
                mock_create_dir.assert_called_once()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_initialize_config_failure(self, mock_verify: MagicMock) -> None:
        """Test initialization failure due to config issues."""
        # Mock failed config loading
        mock_config_result = MagicMock()
        mock_config_result.success = False
        mock_config_result.content = None

        service = PandocService()

        with patch.object(
            service.config_provider, "load_config", return_value=mock_config_result
        ):
            result = service.initialize()

            assert result is False
            assert service._initialized is False
            mock_verify.assert_not_called()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_initialize_pandoc_failure(self, mock_verify: MagicMock) -> None:
        """Test initialization failure due to pandoc issues."""
        mock_verify.side_effect = QuackIntegrationError("Pandoc not found")

        # Mock successful config loading
        mock_config_result = MagicMock()
        mock_config_result.success = True
        mock_config_result.content = {"output_dir": "./test_output"}

        service = PandocService()

        with patch.object(
            service.config_provider, "load_config", return_value=mock_config_result
        ):
            result = service.initialize()

            assert result is False
            assert service._initialized is False
            mock_verify.assert_called_once()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_html_to_markdown(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test HTML to Markdown conversion."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock successful conversion
        mock_result = ConversionResult.success_result(
            Path("output.md"),
            "html",
            "markdown",
            1.5,
            500,
            1000,
            "Successfully converted",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.converter.convert_file.return_value = mock_result
        service.config = ConversionConfig()

        result = service.html_to_markdown(Path("test.html"))

        assert result.success is True
        assert result.content == Path("output.md")
        assert result.source_format == "html"
        assert result.target_format == "markdown"
        service.converter.convert_file.assert_called_once()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_markdown_to_docx(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test Markdown to DOCX conversion."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock successful conversion
        mock_result = ConversionResult.success_result(
            Path("output.docx"),
            "markdown",
            "docx",
            1.5,
            800,
            500,
            "Successfully converted",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.converter.convert_file.return_value = mock_result
        service.config = ConversionConfig()

        result = service.markdown_to_docx(Path("test.md"))

        assert result.success is True
        assert result.content == Path("output.docx")
        assert result.source_format == "markdown"
        assert result.target_format == "docx"
        service.converter.convert_file.assert_called_once()

    def test_conversion_without_initialization(self) -> None:
        """Test conversion attempt without initialization."""
        service = PandocService()
        service._initialized = False

        with patch.object(service, "initialize", return_value=False):
            result = service.html_to_markdown(Path("test.html"))

            assert result.success is False
            assert "Service not initialized" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    @patch("quackcore.fs.service.find_files")
    def test_convert_directory(
        self, mock_find: MagicMock, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock file finding
        file_paths = [Path("file1.html"), Path("file2.html")]
        mock_find.return_value = FindResult(
            success=True, files=file_paths, pattern="*.html", message="Found 2 files"
        )

        # Mock successful batch conversion
        mock_result = BatchConversionResult.success_result(
            [Path("file1.md"), Path("file2.md")],
            [],
            ConversionMetrics(successful_conversions=2),
            "Batch conversion successful",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.converter.convert_batch.return_value = mock_result
        service.config = ConversionConfig()

        result = service.convert_directory(
            Path("input_dir"), "markdown", Path("output_dir")
        )

        assert result.success is True
        assert len(result.successful_files) == 2
        assert len(result.failed_files) == 0
        service.converter.convert_batch.assert_called_once()

    @given(st.booleans())
    def test_is_pandoc_available(self, should_succeed: bool) -> None:
        """Test pandoc availability check with property-based testing."""
        service = PandocService()

        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            if should_succeed:
                mock_verify.return_value = "2.18"
            else:
                mock_verify.side_effect = QuackIntegrationError("Pandoc not found")

            result = service.is_pandoc_available()
            assert result is should_succeed

    def test_get_pandoc_version(self) -> None:
        """Test getting pandoc version."""
        service = PandocService()

        # Test when version is already cached
        service._pandoc_version = "2.18"
        assert service.get_pandoc_version() == "2.18"

        # Test when version needs to be fetched
        service._pandoc_version = None
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.19"
            assert service.get_pandoc_version() == "2.19"

            # Test when verification fails
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")
            assert service.get_pandoc_version() is None

    def test_get_metrics(self) -> None:
        """Test getting conversion metrics."""
        service = PandocService()

        # Test with converter
        mock_metrics = ConversionMetrics(successful_conversions=5)
        service.converter = MagicMock()
        service.converter.metrics = mock_metrics

        assert service.get_metrics() == mock_metrics

        # Test without converter
        service.converter = None
        assert isinstance(service.get_metrics(), ConversionMetrics)

    def test_determine_conversion_params(self) -> None:
        """Test determining conversion parameters based on output format."""
        service = PandocService()

        # Test markdown output
        params = service._determine_conversion_params("markdown", None)
        assert params == ("html", "*.html")

        # Test docx output
        params = service._determine_conversion_params("docx", None)
        assert params == ("markdown", "*.md")

        # Test custom file pattern
        params = service._determine_conversion_params("markdown", "*.htm")
        assert params == ("html", "*.htm")

        # Test unsupported format
        params = service._determine_conversion_params("pdf", None)
        assert params is None

    @patch("quackcore.plugins.pandoc.service.get_file_info")
    def test_create_conversion_tasks(self, mock_get_info: MagicMock) -> None:
        """Test creating conversion tasks from file list."""
        files = [Path("file1.html"), Path("file2.html")]
        output_dir = Path("output")

        # Mock file info
        mock_info = FileInfo(path=Path("file1.html"), format="html", size=1000)
        mock_get_info.return_value = mock_info

        service = PandocService()
        tasks = service._create_conversion_tasks(files, "html", "markdown", output_dir)

        assert len(tasks) == 2
        for task in tasks:
            assert task.source.format == "html"
            assert task.target_format == "markdown"
            assert task.output_path.parent == output_dir
            assert task.output_path.suffix == ".md"

    def test_ensure_initialized_success(self) -> None:
        """Test ensuring service is initialized when it's already initialized."""
        service = PandocService()
        service._initialized = True

        assert service._ensure_initialized() is True

    def test_ensure_initialized_failure(self) -> None:
        """Test ensuring service is initialized when it's not yet initialized."""
        service = PandocService()
        service._initialized = False

        with patch.object(service, "initialize", return_value=False):
            assert service._ensure_initialized() is False
