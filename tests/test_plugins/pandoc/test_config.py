# tests/test_plugins/pandoc/test_config.py
"""
Tests for pandoc plugin configuration.

This module tests the configuration models and configuration provider
for the pandoc plugin.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from quackcore.fs.results import DataResult
from quackcore.plugins.pandoc.config import (
    ConversionConfig,
    MetricsConfig,
    PandocConfigProvider,
    PandocOptions,
    RetryConfig,
    ValidationConfig,
)


class TestPandocOptions:
    """Tests for PandocOptions model."""

    def test_default_values(self) -> None:
        """Test default values."""
        options = PandocOptions()
        assert options.wrap == "none"
        assert options.standalone is True
        assert options.markdown_headings == "atx"
        assert options.reference_links is False
        assert options.resource_path == []

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        options = PandocOptions(
            wrap="auto",
            standalone=False,
            markdown_headings="setext",
            reference_links=True,
            resource_path=[Path("/path1"), Path("/path2")],
        )
        assert options.wrap == "auto"
        assert options.standalone is False
        assert options.markdown_headings == "setext"
        assert options.reference_links is True
        assert options.resource_path == [Path("/path1"), Path("/path2")]


class TestValidationConfig:
    """Tests for ValidationConfig model."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = ValidationConfig()
        assert config.verify_structure is True
        assert config.min_file_size == 50
        assert config.conversion_ratio_threshold == 0.1
        assert config.check_links is False

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = ValidationConfig(
            verify_structure=False,
            min_file_size=100,
            conversion_ratio_threshold=0.5,
            check_links=True,
        )
        assert config.verify_structure is False
        assert config.min_file_size == 100
        assert config.conversion_ratio_threshold == 0.5
        assert config.check_links is True


class TestRetryConfig:
    """Tests for RetryConfig model."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = RetryConfig()
        assert config.max_conversion_retries == 3
        assert config.conversion_retry_delay == 1.0

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = RetryConfig(max_conversion_retries=5, conversion_retry_delay=2.0)
        assert config.max_conversion_retries == 5
        assert config.conversion_retry_delay == 2.0


class TestMetricsConfig:
    """Tests for MetricsConfig model."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = MetricsConfig()
        assert config.track_conversion_time is True
        assert config.track_file_sizes is True

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = MetricsConfig(track_conversion_time=False, track_file_sizes=False)
        assert config.track_conversion_time is False
        assert config.track_file_sizes is False


class TestConversionConfig:
    """Tests for ConversionConfig model."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = ConversionConfig()
        assert isinstance(config.pandoc_options, PandocOptions)
        assert isinstance(config.validation, ValidationConfig)
        assert isinstance(config.retry_mechanism, RetryConfig)
        assert isinstance(config.metrics, MetricsConfig)
        assert config.html_to_md_extra_args == ["--strip-comments", "--no-highlight"]
        assert config.md_to_docx_extra_args == []
        assert config.output_dir == Path("./output")

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        custom_pandoc_options = PandocOptions(wrap="auto")
        custom_validation = ValidationConfig(min_file_size=100)
        custom_retry = RetryConfig(max_conversion_retries=5)
        custom_metrics = MetricsConfig(track_conversion_time=False)

        config = ConversionConfig(
            pandoc_options=custom_pandoc_options,
            validation=custom_validation,
            retry_mechanism=custom_retry,
            metrics=custom_metrics,
            html_to_md_extra_args=["--custom-arg"],
            md_to_docx_extra_args=["--another-arg"],
            output_dir=Path("/custom/output"),
        )

        assert config.pandoc_options == custom_pandoc_options
        assert config.validation == custom_validation
        assert config.retry_mechanism == custom_retry
        assert config.metrics == custom_metrics
        assert config.html_to_md_extra_args == ["--custom-arg"]
        assert config.md_to_docx_extra_args == ["--another-arg"]
        assert config.output_dir == Path("/custom/output")

    def test_validate_output_dir(self) -> None:
        """Test the output_dir validator."""
        # Test with existing directory
        with patch.object(Path, "exists", return_value=True):
            config = ConversionConfig(output_dir=Path("/existing/dir"))
            assert config.output_dir == Path("/existing/dir")

        # Test with non-existing directory
        with patch.object(Path, "exists", return_value=False):
            config = ConversionConfig(output_dir=Path("/nonexistent/dir"))
            assert config.output_dir == Path("/nonexistent/dir")


class TestPandocConfigProvider:
    """Tests for PandocConfigProvider."""

    def test_init(self) -> None:
        """Test initialization."""
        provider = PandocConfigProvider()
        assert provider.logger.level == logging.INFO

        provider = PandocConfigProvider(log_level=logging.DEBUG)
        assert provider.logger.level == logging.DEBUG

    def test_name(self) -> None:
        """Test name property."""
        provider = PandocConfigProvider()
        assert provider.name == "PandocConfig"

    def test_load_config_with_path(self) -> None:
        """Test loading config from a specified path."""
        provider = PandocConfigProvider()

        # Test successful load
        mock_yaml_result = DataResult(
            success=True,
            path="/config/pandoc_config.yaml",
            data={"pandoc_options": {"wrap": "auto"}},
            format="yaml",
        )

        with patch("quackcore.fs.service.read_yaml") as mock_read_yaml:
            mock_read_yaml.return_value = mock_yaml_result

            with patch.object(provider, "validate_config", return_value=True):
                result = provider.load_config("/config/pandoc_config.yaml")

                assert result.success is True
                assert result.path == "/config/pandoc_config.yaml"
                assert "pandoc_options" in result.data
                assert result.data["pandoc_options"]["wrap"] == "auto"

        # Test file not found
        mock_yaml_error = DataResult(
            success=False,
            path="/nonexistent/config.yaml",
            data={},
            format="yaml",
            error="File not found",
        )

        with patch("quackcore.fs.service.read_yaml") as mock_read_yaml:
            mock_read_yaml.return_value = mock_yaml_error

            result = provider.load_config("/nonexistent/config.yaml")

            assert result.success is False
            assert result.error == "File not found"

    def test_load_config_without_path(self) -> None:
        """Test loading config without a specified path."""
        provider = PandocConfigProvider()

        # Test with config from QuackCore system
        mock_config = MagicMock()
        mock_config.custom = {"pandoc": {"pandoc_options": {"wrap": "auto"}}}

        with patch("quackcore.config.loader.load_config") as mock_load_config:
            mock_load_config.return_value = mock_config

            with patch.object(provider, "validate_config", return_value=True):
                result = provider.load_config()

                assert result.success is True
                assert "pandoc_options" in result.data
                assert result.data["pandoc_options"]["wrap"] == "auto"

        # Test with empty config, should use default
        mock_config.custom = {}

        with patch("quackcore.config.loader.load_config") as mock_load_config:
            mock_load_config.return_value = mock_config

            with patch.object(provider, "get_default_config") as mock_get_default:
                mock_get_default.return_value = {"pandoc_options": {"wrap": "preserve"}}

                with patch.object(provider, "validate_config", return_value=True):
                    result = provider.load_config()

                    assert result.success is True
                    assert "pandoc_options" in result.data
                    assert result.data["pandoc_options"]["wrap"] == "preserve"

    def test_extract_config(self) -> None:
        """Test extracting pandoc-specific configuration."""
        provider = PandocConfigProvider()

        # Test with 'pandoc' section
        config_data = {"pandoc": {"option1": "value1"}}
        extracted = provider._extract_config(config_data)
        assert extracted == {"option1": "value1"}

        # Test with 'conversion' section
        config_data = {"conversion": {"option2": "value2"}}
        extracted = provider._extract_config(config_data)
        assert extracted == {"option2": "value2"}

        # Test with neither section
        config_data = {"option3": "value3"}
        extracted = provider._extract_config(config_data)
        assert extracted == {"option3": "value3"}

    def test_validate_config(self) -> None:
        """Test validating configuration data."""
        provider = PandocConfigProvider()

        # Test valid configuration
        valid_config = {
            "pandoc_options": {"wrap": "none"},
            "validation": {"min_file_size": 100},
            "retry_mechanism": {"max_conversion_retries": 3},
            "metrics": {"track_conversion_time": True},
            "output_dir": "/output",
        }

        assert provider.validate_config(valid_config) is True

        # Test invalid configuration
        with patch("quackcore.plugins.pandoc.config.ConversionConfig") as mock_config:
            mock_config.side_effect = ValidationError.from_exception_data(
                title="", line_errors=[]
            )

            assert provider.validate_config({"invalid": "config"}) is False

    def test_get_default_config(self) -> None:
        """Test getting default configuration values."""
        provider = PandocConfigProvider()
        default_config = provider.get_default_config()

        # Verify that the default config has all expected sections
        assert "pandoc_options" in default_config
        assert "validation" in default_config
        assert "retry_mechanism" in default_config
        assert "metrics" in default_config
        assert "output_dir" in default_config
        assert "html_to_md_extra_args" in default_config
        assert "md_to_docx_extra_args" in default_config
