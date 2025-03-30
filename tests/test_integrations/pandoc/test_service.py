# tests/test_integrations/pandoc/test_service.py
"""
Tests for Pandoc integration service.

This module tests the PandocIntegration service class, including initialization,
configuration handling, and document conversion operations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import FileInfoResult, OperationResult
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import ConversionMetrics
from quackcore.integrations.pandoc.service import PandocIntegration


class TestPandocService:
    """Tests for the PandocIntegration service class."""

    @pytest.fixture
    def mock_config_provider(self):
        """Fixture to mock the config provider."""
        with patch("quackcore.integrations.pandoc.config.PandocConfigProvider") as mock:
            yield mock

    @pytest.fixture
    def mock_fs(self):
        """Fixture to mock the fs module."""
        with patch("quackcore.integrations.pandoc.service.fs") as mock_fs:
            # Setup default behavior for file info checks
            file_info = FileInfoResult(
                success=True,
                path="/path/to/file",
                exists=True,
                is_file=True,
            )
            mock_fs.service.get_file_info.return_value = file_info

            # Setup default behavior for directory creation
            dir_result = OperationResult(
                success=True,
                path="/path/to/output",
                message="Directory created",
            )
            mock_fs.create_directory.return_value = dir_result

            yield mock_fs

    def test_init(self, mock_config_provider):
        """Test initializing the service."""
        # Test initialization with default parameters
        service = PandocIntegration()
        assert service.name == "Pandoc"
        assert service.version == "1.0.0"
        assert service.output_dir is None
        assert isinstance(service.metrics, ConversionMetrics)
        assert service.converter is None

        # Test initialization with custom parameters
        service = PandocIntegration(
            config_path="/path/to/config.yaml",
            output_dir="/path/to/output",
            log_level=20,
        )
        assert service.output_dir == Path("/path/to/output")
        mock_config_provider.assert_called_with(20)

    def test_initialize_success(self, mock_config_provider, mock_fs):
        """Test successful initialization of the service."""
        # Create a mock config provider instance
        mock_provider = MagicMock()
        mock_config_provider.return_value = mock_provider

        # Setup mock for base class initialize
        with patch(
                "quackcore.integrations.core.base.BaseIntegrationService.initialize") as mock_base_init:
            mock_base_init.return_value = IntegrationResult.success_result()

            # Setup mock for verify_pandoc
            with patch(
                    "quackcore.integrations.pandoc.operations.verify_pandoc") as mock_verify:
                mock_verify.return_value = "2.11.4"

                # Test initialization
                service = PandocIntegration(output_dir="/path/to/output")
                result = service.initialize()

                # Assertions
                assert result.success is True
                assert "Pandoc integration initialized successfully" in result.message
                assert service._initialized is True
                assert isinstance(service.converter, DocumentConverter)
                mock_verify.assert_called_once()
                mock_fs.create_directory.assert_called_once()

    def test_initialize_invalid_config(self, mock_config_provider):
        """Test initialization with invalid configuration."""
        # Create a mock for base class initialize
        with patch(
                "quackcore.integrations.core.base.BaseIntegrationService.initialize") as mock_base_init:
            mock_base_init.return_value = IntegrationResult.success_result()

            # Setup mock for PandocConfig to raise an exception
            with patch(
                    "quackcore.integrations.pandoc.service.PandocConfig") as mock_config:
                mock_config.side_effect = Exception("Invalid configuration")

                # Test initialization
                service = PandocIntegration()
                result = service.initialize()

                # Assertions
                assert result.success is False
                assert "Invalid configuration" in result.error

    def test_initialize_verify_pandoc_failure(self, mock_config_provider, mock_fs):
        """Test initialization when pandoc verification fails."""
        # Create a mock for base class initialize
        with patch(
                "quackcore.integrations.core.base.BaseIntegrationService.initialize") as mock_base_init:
            mock_base_init.return_value = IntegrationResult.success_result()

            # Setup mock for verify_pandoc to raise an error
            with patch(
                    "quackcore.integrations.pandoc.operations.verify_pandoc") as mock_verify:
                mock_verify.side_effect = QuackIntegrationError("Pandoc not found")

                # Test initialization
                service = PandocIntegration()
                result = service.initialize()

                # Assertions
                assert result.success is False
                assert "Pandoc verification failed" in result.error

    def test_initialize_directory_creation_failure(self, mock_config_provider, mock_fs):
        """Test initialization when directory creation fails."""
        # Create a mock for base class initialize
        with patch(
                "quackcore.integrations.core.base.BaseIntegrationService.initialize") as mock_base_init:
            mock_base_init.return_value = IntegrationResult.success_result()

            # Setup mock for verify_pandoc
            with patch(
                    "quackcore.integrations.pandoc.operations.verify_pandoc") as mock_verify:
                mock_verify.return_value = "2.11.4"

                # Setup mock for directory creation to fail
                mock_fs.create_directory.return_value = OperationResult(
                    success=False,
                    path="/path/to/output",
                    error="Permission denied",
                )

                # Test initialization
                service = PandocIntegration(output_dir="/path/to/output")
                result = service.initialize()

                # Assertions
                assert result.success is False
                assert "Failed to create output directory" in result.error

    def test_html_to_markdown(self, mock_config_provider, mock_fs):
        """Test the HTML to Markdown conversion method."""
        # Create a properly initialized service
        service = self._create_initialized_service()

        # Mock the converter's convert_file method
        service.converter.convert_file = MagicMock(
            return_value=IntegrationResult.success_result(
                Path("/path/to/output/file.md"),
                message="Successfully converted HTML to Markdown",
            )
        )

        # Test the method
        result = service.html_to_markdown(Path("input.html"), Path("output.md"))

        # Assertions
        assert result.success is True
        assert result.content == Path("/path/to/output/file.md")
        service.converter.convert_file.assert_called_once()

    def test_html_to_markdown_not_initialized(self):
        """Test HTML to Markdown conversion when service is not initialized."""
        service = PandocIntegration()
        result = service.html_to_markdown(Path("input.html"))

        assert result.success is False
        assert "not initialized" in result.error

    def test_html_to_markdown_without_output_path(self, mock_config_provider, mock_fs):
        """Test HTML to Markdown conversion without specifying output path."""
        # Create a properly initialized service with a converter
        service = self._create_initialized_service()

        # Configure the converter mock
        service.converter.convert_file = MagicMock(
            return_value=IntegrationResult.success_result(
                Path("/path/to/output/input.md"),
                message="Successfully converted HTML to Markdown",
            )
        )

        # Configure the config for auto output path determination
        service.converter.config = PandocConfig(output_dir=Path("/path/to/output"))

        # Test the method
        result = service.html_to_markdown(Path("input.html"))

        # Assertions
        assert result.success is True
        assert result.content == Path("/path/to/output/input.md")
        service.converter.convert_file.assert_called_once()

    def test_markdown_to_docx(self, mock_config_provider, mock_fs):
        """Test the Markdown to DOCX conversion method."""
        # Create a properly initialized service
        service = self._create_initialized_service()

        # Mock the converter's convert_file method
        service.converter.convert_file = MagicMock(
            return_value=IntegrationResult.success_result(
                Path("/path/to/output/file.docx"),
                message="Successfully converted Markdown to DOCX",
            )
        )

        # Test the method
        result = service.markdown_to_docx(Path("input.md"), Path("output.docx"))

        # Assertions
        assert result.success is True
        assert result.content == Path("/path/to/output/file.docx")
        service.converter.convert_file.assert_called_once()

    def test_markdown_to_docx_not_initialized(self):
        """Test Markdown to DOCX conversion when service is not initialized."""
        service = PandocIntegration()
        result = service.markdown_to_docx(Path("input.md"))

        assert result.success is False
        assert "not initialized" in result.error

    def test_markdown_to_docx_without_output_path(self, mock_config_provider, mock_fs):
        """Test Markdown to DOCX conversion without specifying output path."""
        # Create a properly initialized service with a converter
        service = self._create_initialized_service()

        # Configure the converter mock
        service.converter.convert_file = MagicMock(
            return_value=IntegrationResult.success_result(
                Path("/path/to/output/input.docx"),
                message="Successfully converted Markdown to DOCX",
            )
        )

        # Configure the config for auto output path determination
        service.converter.config = PandocConfig(output_dir=Path("/path/to/output"))

        # Test the method
        result = service.markdown_to_docx(Path("input.md"))

        # Assertions
        assert result.success is True
        assert result.content == Path("/path/to/output/input.docx")
        service.converter.convert_file.assert_called_once()

    def test_convert_directory(self, mock_config_provider, mock_fs):
        """Test the convert directory method."""
        # Create a properly initialized service
        service = self._create_initialized_service()

        # Mock the converter's convert_batch method
        service.converter.convert_batch = MagicMock(
            return_value=IntegrationResult.success_result(
                [Path("/path/to/output/file1.md"), Path("/path/to/output/file2.md")],
                message="Successfully converted files",
            )
        )

        # Test the method
        result = service.convert_directory(
            Path("input_dir"),
            "markdown",
            Path("output_dir"),
            "*.html",
            True
        )

        # Assertions
        assert result.success is True
        assert len(result.content) == 2
        assert result.content[0] == Path("/path/to/output/file1.md")
        service.converter.convert_batch.assert_called_once()

    def test_convert_directory_not_initialized(self):
        """Test directory conversion when service is not initialized."""
        service = PandocIntegration()
        result = service.convert_directory(
            Path("input_dir"),
            "markdown"
        )

        assert result.success is False
        assert "not initialized" in result.error

    def test_convert_directory_invalid_format(self, mock_config_provider, mock_fs):
        """Test directory conversion with an invalid format."""
        # Create a properly initialized service
        service = self._create_initialized_service()

        # Test with invalid format
        result = service.convert_directory(
            Path("input_dir"),
            "invalid_format"
        )

        # Assertions
        assert result.success is False
        assert "Unsupported output format" in result.error

    def test_convert_directory_input_not_found(self, mock_config_provider, mock_fs):
        """Test directory conversion when input directory doesn't exist."""
        # Create a properly initialized service
        service = self._create_initialized_service()

        # Setup mock for file info to indicate directory doesn't exist
        mock_fs.service.get_file_info.return_value = FileInfoResult(
            success=True,
            path="/path/to/input",
            exists=False,
        )

        # Test the method
        result = service.convert_directory(
            Path("input_dir"),
            "markdown"
        )

        # Assertions
        assert result.success is False
        assert "Input directory does not exist" in result.error

    def test_is_pandoc_available(self, mock_config_provider):
        """Test the pandoc availability check method."""
        service = PandocIntegration()

        # Test when pandoc is available
        with patch(
                "quackcore.integrations.pandoc.operations.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.11.4"
            assert service.is_pandoc_available() is True

            # Test when pandoc is not available
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")
            assert service.is_pandoc_available() is False

    def test_get_pandoc_version(self, mock_config_provider):
        """Test getting the pandoc version."""
        service = PandocIntegration()

        # Test when version is already known
        service._pandoc_version = "2.11.4"
        assert service.get_pandoc_version() == "2.11.4"

        # Test when version is not known and must be retrieved
        service._pandoc_version = None
        with patch(
                "quackcore.integrations.pandoc.operations.verify_pandoc") as mock_verify:
            mock_verify.return_value = "2.11.4"
            assert service.get_pandoc_version() == "2.11.4"

            # Test when pandoc is not available
            mock_verify.side_effect = QuackIntegrationError("Pandoc not found")
            assert service.get_pandoc_version() is None

    def test_get_metrics(self, mock_config_provider):
        """Test getting conversion metrics."""
        service = PandocIntegration()

        # Test when converter exists
        converter_metrics = ConversionMetrics()
        converter_metrics.total_attempts = 5

        service.converter = MagicMock()
        service.converter.metrics = converter_metrics

        assert service.get_metrics() == converter_metrics

        # Test when converter doesn't exist
        service.converter = None
        assert isinstance(service.get_metrics(), ConversionMetrics)

    def _create_initialized_service(self) -> PandocIntegration:
        """Helper method to create a properly initialized service for testing."""
        service = PandocIntegration()
        service._initialized = True
        service.converter = MagicMock(spec=DocumentConverter)
        return service