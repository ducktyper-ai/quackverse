# tests/test_plugins/pandoc/test_service_extended.py
"""
Extended tests for pandoc service implementation.

This module provides additional tests for the PandocService class,
focusing on previously untested code paths to increase coverage.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestPandocServiceExtended:
    """Extended tests for the PandocService class."""

    def test_initialization_with_custom_output_dir(self) -> None:
        """Test initialization with custom output directory."""
        custom_output_dir = Path("/custom/output/dir")
        service = PandocService(output_dir=custom_output_dir)

        assert service.name == "Pandoc"
        assert service.output_dir == custom_output_dir
        assert service._initialized is False
        assert service.converter is None

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_initialize_with_invalid_config(self, mock_verify: MagicMock) -> None:
        """Test initialization with invalid configuration."""
        # Mock invalid config format
        mock_config_result = MagicMock()
        mock_config_result.success = True
        mock_config_result.content = {
            "invalid_key": "value"
        }  # Will cause validation failure

        service = PandocService()

        with patch.object(
            service.config_provider, "load_config", return_value=mock_config_result
        ):
            result = service.initialize()

            assert result is False
            assert service._initialized is False
            mock_verify.assert_not_called()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_initialize_with_override_output_dir(self, mock_verify: MagicMock) -> None:
        """Test initialization with output directory override."""
        mock_verify.return_value = "2.18"

        # Mock successful config loading
        mock_config_result = MagicMock()
        mock_config_result.success = True
        mock_config_result.content = {
            "output_dir": "./default_output",
        }

        # Override output directory
        override_output_dir = Path("/override/output/dir")
        service = PandocService(output_dir=override_output_dir)

        with (
            patch.object(
                service.config_provider, "load_config", return_value=mock_config_result
            ),
            patch("quackcore.plugins.pandoc.service.DocumentConverter"),
            patch("quackcore.fs.service.create_directory"),
        ):
            result = service.initialize()

            assert result is True
            assert service._initialized is True
            assert service.config is not None
            assert service.config.output_dir == override_output_dir
            mock_verify.assert_called_once()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_general_initialization_error(self, mock_verify: MagicMock) -> None:
        """Test handling of any unexpected initialization error."""
        # Mock unexpected error during initialization
        mock_verify.side_effect = Exception("Unexpected initialization error")

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

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    def test_html_to_markdown_uninitialized(self, mock_verify: MagicMock) -> None:
        """Test HTML to Markdown conversion without initialization."""
        service = PandocService()
        service._initialized = False

        # Mock initialization to fail
        with patch.object(service, "initialize", return_value=False):
            result = service.html_to_markdown(Path("test.html"))

            assert result.success is False
            assert "Service not initialized" in result.error if result.error else ""
            mock_verify.assert_not_called()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_html_to_markdown_custom_output(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test HTML to Markdown with custom output path."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Create service and initialize
        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock converter
        mock_result = ConversionResult.success_result(
            Path("custom/output.md"),
            "html",
            "markdown",
            1.5,
            500,
            1000,
            "Successfully converted",
        )
        service.converter.convert_file.return_value = mock_result

        # Call with custom output path
        result = service.html_to_markdown(Path("test.html"), Path("custom/output.md"))

        assert result.success is True
        assert result.content == Path("custom/output.md")
        service.converter.convert_file.assert_called_once_with(
            Path("test.html"), Path("custom/output.md"), "markdown"
        )

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_html_to_markdown_missing_converter(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test HTML to Markdown when converter is not initialized."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        service = PandocService()
        service._initialized = True
        service.converter = None  # Missing converter
        service.config = ConversionConfig()

        result = service.html_to_markdown(Path("test.html"))

        assert result.success is False
        assert "Converter not initialized" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_html_to_markdown_missing_output_dir(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test HTML to Markdown when output directory cannot be determined."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        service = PandocService()
        service._initialized = True
        service.converter = None  # No converter to get output dir from
        service.config = None  # No config

        result = service.html_to_markdown(Path("test.html"))

        assert result.success is False
        assert "Cannot determine output path" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_html_to_markdown_exception(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test HTML to Markdown with unexpected exception."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = Exception("Unexpected error")

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        result = service.html_to_markdown(Path("test.html"))

        assert result.success is False
        assert (
            "Error in HTML to Markdown conversion" in result.error
            if result.error
            else ""
        )
        assert "Unexpected error" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_markdown_to_docx_uninitialized(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test Markdown to DOCX conversion without initialization."""
        service = PandocService()
        service._initialized = False

        # Mock initialization to fail
        with patch.object(service, "initialize", return_value=False):
            result = service.markdown_to_docx(Path("test.md"))

            assert result.success is False
            assert "Service not initialized" in result.error if result.error else ""
            mock_verify.assert_not_called()

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_markdown_to_docx_missing_converter(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test Markdown to DOCX when converter is not initialized."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        service = PandocService()
        service._initialized = True
        service.converter = None  # Missing converter
        service.config = ConversionConfig()

        result = service.markdown_to_docx(Path("test.md"))

        assert result.success is False
        assert "Converter not initialized" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_convert_directory_nonexistent_dir(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion with non-existent input directory."""
        mock_verify.return_value = "2.18"
        mock_resolve.return_value = Path("/nonexistent/dir")

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock Path.exists() to return False
        with patch.object(Path, "exists", return_value=False):
            result = service.convert_directory(Path("/nonexistent/dir"), "markdown")

            assert result.success is False
            assert (
                "Input directory does not exist" in result.error if result.error else ""
            )

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    def test_convert_directory_unsupported_format(
        self, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion with unsupported output format."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock Path.exists() and is_dir() to return True
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
        ):
            result = service.convert_directory(
                Path("/input/dir"),
                "pdf",  # Unsupported format
            )

            assert result.success is False
            assert (
                "Unsupported output format: pdf" in result.error if result.error else ""
            )

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    @patch("quackcore.fs.service.find_files")
    def test_convert_directory_no_matching_files(
        self, mock_find: MagicMock, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion when no matching files are found."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock find_files to return empty result
        mock_find.return_value = FindResult(
            success=True, files=[], pattern="*.html", message="No files found"
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock Path.exists() and is_dir() to return True
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
            patch("quackcore.fs.service.create_directory"),
        ):
            result = service.convert_directory(Path("/input/dir"), "markdown")

            assert result.success is False
            assert "No matching files found" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    @patch("quackcore.fs.service.find_files")
    def test_convert_directory_find_files_failure(
        self, mock_find: MagicMock, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion when find_files operation fails."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock find_files to fail
        mock_find.return_value = FindResult(
            success=False,
            files=[],
            pattern="*.html",
            message="",
            error="Permission denied",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock Path.exists() and is_dir() to return True
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
            patch("quackcore.fs.service.create_directory"),
        ):
            result = service.convert_directory(Path("/input/dir"), "markdown")

            assert result.success is False
            assert "Failed to find files" in result.error if result.error else ""

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    @patch("quackcore.fs.service.find_files")
    def test_convert_directory_no_valid_files(
        self, mock_find: MagicMock, mock_resolve: MagicMock, mock_verify: MagicMock
    ) -> None:
        """Test directory conversion when found files are invalid."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock find_files to return files
        mock_find.return_value = FindResult(
            success=True,
            files=[Path("/input/dir/file1.html"), Path("/input/dir/file2.html")],
            pattern="*.html",
            message="Found 2 files",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock _create_conversion_tasks to return empty list (all files invalid)
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
            patch("quackcore.fs.service.create_directory"),
            patch.object(service, "_create_conversion_tasks", return_value=[]),
        ):
            result = service.convert_directory(Path("/input/dir"), "markdown")

            assert result.success is False
            assert (
                "No valid files found for conversion" in result.error
                if result.error
                else ""
            )

    @patch("quackcore.plugins.pandoc.service.verify_pandoc")
    @patch("quackcore.plugins.pandoc.service.resolver.resolve_project_path")
    @patch("quackcore.fs.service.find_files")
    @patch("quackcore.fs.service.create_directory")
    def test_convert_directory_recursive(
        self,
        mock_create_dir: MagicMock,
        mock_find: MagicMock,
        mock_resolve: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """Test directory conversion with recursive flag."""
        mock_verify.return_value = "2.18"
        mock_resolve.side_effect = lambda x: x  # Return input unchanged

        # Mock find_files to return files
        mock_find.return_value = FindResult(
            success=True,
            files=[Path("/input/dir/file1.html"), Path("/input/dir/subdir/file2.html")],
            pattern="*.html",
            message="Found 2 files",
        )

        service = PandocService()
        service._initialized = True
        service.converter = MagicMock()
        service.config = ConversionConfig()

        # Mock successful batch conversion
        mock_result = BatchConversionResult.success_result(
            [Path("file1.md"), Path("subdir/file2.md")],
            [],
            ConversionMetrics(successful_conversions=2),
            "Batch conversion successful",
        )
        service.converter.convert_batch.return_value = mock_result

        # Mock Path.exists() and is_dir() to return True
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
            patch.object(service, "_create_conversion_tasks") as mock_create_tasks,
        ):
            # Call with recursive=True
            result = service.convert_directory(
                Path("/input/dir"), "markdown", recursive=True
            )

            # Verify recursive flag was passed to find_files
            mock_find.assert_called_once_with(
                Path("/input/dir"),
                "*.html",
                True,  # recursive=True
            )

            assert result.success is True
            assert len(result.successful_files) == 2
            service.converter.convert_batch.assert_called_once()

    def test_determine_conversion_params(self) -> None:
        """Test determining conversion parameters for different formats."""
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
        """Test creating conversion tasks with warning handling."""
        # Set up mock file info
        mock_info = FileInfo(path=Path("file1.html"), format="html", size=1000)
        mock_get_info.side_effect = [
            mock_info,  # First file succeeds
            QuackIntegrationError("File not found"),  # Second file fails
            mock_info,  # Third file succeeds
        ]

        files = [
            Path("file1.html"),
            Path("file2.html"),  # Will fail
            Path("file3.html"),
        ]
        output_dir = Path("output")

        service = PandocService()

        # Create tasks - should include only valid files
        tasks = service._create_conversion_tasks(files, "html", "markdown", output_dir)

        # Should have 2 tasks (file1 and file3, file2 should be skipped with warning)
        assert len(tasks) == 2
        assert tasks[0].source.path == Path("file1.html")
        assert tasks[0].target_format == "markdown"
        assert tasks[0].output_path == output_dir / "file1.md"
        assert tasks[1].source.path == Path("file3.html")
        assert mock_get_info.call_count == 3

    def test_is_pandoc_available_with_mock(self) -> None:
        """Test detecting pandoc availability with mocking."""
        service = PandocService()

        # Case 1: Pandoc is available
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.18"
            assert service.is_pandoc_available() is True
            mock_verify.assert_called_once()

        # Case 2: Integration error
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")
            assert service.is_pandoc_available() is False
            mock_verify.assert_called_once()

        # Case 3: Import error
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.side_effect = ImportError("No module named 'pypandoc'")
            assert service.is_pandoc_available() is False
            mock_verify.assert_called_once()

        # Case 4: OS error
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.side_effect = OSError("Command not found")
            assert service.is_pandoc_available() is False
            mock_verify.assert_called_once()

    def test_get_pandoc_version(self) -> None:
        """Test getting pandoc version in different scenarios."""
        service = PandocService()

        # Case 1: Version already cached
        service._pandoc_version = "2.18"
        assert service.get_pandoc_version() == "2.18"

        # Case 2: Version not cached, successfully fetched
        service._pandoc_version = None
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.19"
            assert service.get_pandoc_version() == "2.19"
            mock_verify.assert_called_once()

        # Case 3: Version not cached, fetch fails
        service._pandoc_version = None
        with patch("quackcore.plugins.pandoc.service.verify_pandoc") as mock_verify:
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")
            assert service.get_pandoc_version() is None
            mock_verify.assert_called_once()

    def test_get_metrics(self) -> None:
        """Test getting conversion metrics."""
        service = PandocService()

        # Case 1: With converter
        mock_metrics = ConversionMetrics(successful_conversions=5)
        service.converter = MagicMock()
        service.converter.metrics = mock_metrics

        metrics = service.get_metrics()
        assert metrics == mock_metrics
        assert metrics.successful_conversions == 5

        # Case 2: Without converter
        service.converter = None
        metrics = service.get_metrics()
        assert isinstance(metrics, ConversionMetrics)
        assert metrics == service.metrics  # Should return service's own metrics

    def test_ensure_initialized_already_initialized(self) -> None:
        """Test ensuring service is initialized when it's already initialized."""
        service = PandocService()
        service._initialized = True

        assert service._ensure_initialized() is True

    def test_ensure_initialized_success(self) -> None:
        """Test ensuring service is initialized with successful initialization."""
        service = PandocService()
        service._initialized = False

        with patch.object(service, "initialize", return_value=True):
            assert service._ensure_initialized() is True
            assert service._initialized is True

    def test_ensure_initialized_failure(self) -> None:
        """Test ensuring service is initialized with failed initialization."""
        service = PandocService()
        service._initialized = False

        with patch.object(service, "initialize", return_value=False):
            assert service._ensure_initialized() is False
            assert (
                service._initialized is False
            )  # tests/test_plugins/pandoc/test_service_extended.py
