# tests/test_integrations/pandoc/test_config.py
"""
Tests for Pandoc configuration classes.

This module tests the configuration classes for the Pandoc integration,
including PandocConfig and PandocConfigProvider.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from quackcore.config.models import LoggingConfig
from quackcore.integrations.pandoc.config import (
    MetricsConfig,
    PandocConfig,
    PandocConfigProvider,
    PandocOptions,
    RetryConfig,
    ValidationConfig,
)


class TestPandocConfig:
    """Tests for the Pandoc configuration classes."""

    def test_pandoc_options(self):
        """Test PandocOptions configuration model."""
        # Test default values
        options = PandocOptions()
        assert options.wrap == "none"
        assert options.standalone is True
        assert options.markdown_headings == "atx"
        assert options.reference_links is False
        assert options.resource_path == []

        # Test custom values
        options = PandocOptions(
            wrap="auto",
            standalone=False,
            markdown_headings="setext",
            reference_links=True,
            resource_path=[Path("/path/to/resources"), Path("/custom/resources")],
        )
        assert options.wrap == "auto"
        assert options.standalone is False
        assert options.markdown_headings == "setext"
        assert options.reference_links is True
        assert len(options.resource_path) == 2
        assert options.resource_path[0] == Path("/path/to/resources")

    def test_validation_config(self):
        """Test ValidationConfig configuration model."""
        # Test default values
        config = ValidationConfig()
        assert config.verify_structure is True
        assert config.min_file_size == 50
        assert config.conversion_ratio_threshold == 0.1
        assert config.check_links is False

        # Test custom values
        config = ValidationConfig(
            verify_structure=False,
            min_file_size=100,
            conversion_ratio_threshold=0.2,
            check_links=True,
        )
        assert config.verify_structure is False
        assert config.min_file_size == 100
        assert config.conversion_ratio_threshold == 0.2
        assert config.check_links is True

    def test_retry_config(self):
        """Test RetryConfig configuration model."""
        # Test default values
        config = RetryConfig()
        assert config.max_conversion_retries == 3
        assert config.conversion_retry_delay == 1.0

        # Test custom values
        config = RetryConfig(
            max_conversion_retries=5,
            conversion_retry_delay=2.5,
        )
        assert config.max_conversion_retries == 5
        assert config.conversion_retry_delay == 2.5

    def test_metrics_config(self):
        """Test MetricsConfig configuration model."""
        # Test default values
        config = MetricsConfig()
        assert config.track_conversion_time is True
        assert config.track_file_sizes is True

        # Test custom values
        config = MetricsConfig(
            track_conversion_time=False,
            track_file_sizes=False,
        )
        assert config.track_conversion_time is False
        assert config.track_file_sizes is False

    def test_pandoc_config(self):
        """Test the main PandocConfig configuration model."""
        # Test default values
        config = PandocConfig()
        assert isinstance(config.pandoc_options, PandocOptions)
        assert isinstance(config.validation, ValidationConfig)
        assert isinstance(config.retry_mechanism, RetryConfig)
        assert isinstance(config.metrics, MetricsConfig)
        assert config.html_to_md_extra_args == ["--strip-comments", "--no-highlight"]
        assert config.md_to_docx_extra_args == []
        assert config.output_dir == Path("./output")
        assert isinstance(config.logging, LoggingConfig)

        # Test custom values
        config = PandocConfig(
            pandoc_options=PandocOptions(wrap="auto"),
            validation=ValidationConfig(min_file_size=100),
            retry_mechanism=RetryConfig(max_conversion_retries=5),
            metrics=MetricsConfig(track_file_sizes=False),
            html_to_md_extra_args=["--custom-arg"],
            md_to_docx_extra_args=["--reference-doc=template.docx"],
            output_dir=Path("/custom/output"),
            logging=LoggingConfig(level="DEBUG"),
        )
        assert config.pandoc_options.wrap == "auto"
        assert config.validation.min_file_size == 100
        assert config.retry_mechanism.max_conversion_retries == 5
        assert config.metrics.track_file_sizes is False
        assert config.html_to_md_extra_args == ["--custom-arg"]
        assert config.md_to_docx_extra_args == ["--reference-doc=template.docx"]
        assert config.output_dir == Path("/custom/output")
        assert config.logging.level == "DEBUG"

    def test_validate_output_dir(self):
        """Test the output_dir validation in PandocConfig."""
        # Test with a valid path
        config = PandocConfig(output_dir=Path("/path/to/output"))
        assert config.output_dir == Path("/path/to/output")

        # The validator only validates the format, not existence
        config = PandocConfig(output_dir=Path("/nonexistent/directory"))
        assert config.output_dir == Path("/nonexistent/directory")


class TestPandocConfigProvider:
    """Tests for the PandocConfigProvider class."""

    def test_init(self):
        """Test initialization of the PandocConfigProvider."""
        provider = PandocConfigProvider()
        assert provider.name == "PandocConfig"
        assert provider.ENV_PREFIX == "QUACK_PANDOC_"
        assert provider.DEFAULT_CONFIG_LOCATIONS == [
            "./config/pandoc_config.yaml",
            "./config/quack_config.yaml",
            "./quack_config.yaml",
            "~/.quack/pandoc_config.yaml",
        ]

    def test_extract_config(self):
        """Test the _extract_config method."""
        provider = PandocConfigProvider()

        # Test with pandoc section
        config_data = {
            "pandoc": {
                "output_dir": "/path/to/output",
                "html_to_md_extra_args": ["--custom-arg"],
            }
        }
        extracted = provider._extract_config(config_data)
        assert extracted["output_dir"] == "/path/to/output"
        assert extracted["html_to_md_extra_args"] == ["--custom-arg"]

        # Test with conversion section
        config_data = {
            "conversion": {
                "output_dir": "/another/output",
                "pandoc_options": {"wrap": "auto"},
            }
        }
        extracted = provider._extract_config(config_data)
        assert extracted["output_dir"] == "/another/output"
        assert extracted["pandoc_options"]["wrap"] == "auto"

        # Test with neither section
        config_data = {
            "output_dir": "/direct/output",
            "pandoc_options": {"wrap": "preserve"},
        }
        extracted = provider._extract_config(config_data)
        assert extracted["output_dir"] == "/direct/output"
        assert extracted["pandoc_options"]["wrap"] == "preserve"

        # Test with empty config
        config_data = {}
        extracted = provider._extract_config(config_data)
        assert extracted == {}

    def test_validate_config(self):
        """Test the validate_config method."""
        provider = PandocConfigProvider()

        # Test valid configuration
        valid_config = {
            "output_dir": "/path/to/output",
            "html_to_md_extra_args": ["--custom-arg"],
        }
        assert provider.validate_config(valid_config) is True

        # Test invalid configuration
        with patch("quackcore.integrations.pandoc.config.PandocConfig") as mock_config:
            mock_config.side_effect = ValidationError.from_exception_data(
                "ValidationError",
                [{"loc": ("output_dir",), "msg": "Invalid path", "type": "value_error"}],
            )
            assert provider.validate_config(valid_config) is False

        # Test unexpected error
        with patch("quackcore.integrations.pandoc.config.PandocConfig") as mock_config:
            mock_config.side_effect = Exception("Unexpected error")
            assert provider.validate_config(valid_config) is False

    def test_get_default_config(self):
        """Test the get_default_config method."""
        provider = PandocConfigProvider()
        default_config = provider.get_default_config()

        # Check that all expected keys are present
        assert "pandoc_options" in default_config
        assert "validation" in default_config
        assert "retry_mechanism" in default_config
        assert "metrics" in default_config
        assert "html_to_md_extra_args" in default_config
        assert "md_to_docx_extra_args" in default_config
        assert "output_dir" in default_config
        assert "logging" in default_config

        # Verify the default output directory
        assert default_config["output_dir"] == Path("./output")

        # Verify default HTML to MD args
        assert default_config["html_to_md_extra_args"] == ["--strip-comments", "--no-highlight"]

    def test_env_vars_override(self):
        """Test configuration from environment variables."""
        provider = PandocConfigProvider()

        # Set environment variables
        with patch.dict(os.environ, {
            "QUACK_PANDOC_OUTPUT_DIR": "/env/output",
            "QUACK_PANDOC_HTML_TO_MD_EXTRA_ARGS": '["--env-arg"]',
        }):
            # Mock load_from_environment to capture the environment variables
            with patch.object(provider, "load_from_environment") as mock_load_env:
                mock_load_env.return_value = {
                    "output_dir": "/env/output",
                    "html_to_md_extra_args": ["--env-arg"],
                }

                # Mock the base class's load_config method to use our mocked environment
                with patch("quackcore.config.provider.BaseConfigProvider.load_config") as mock_load:
                    mock_load.return_value = MagicMock(
                        success=True,
                        content={
                            "output_dir": "/env/output",
                            "html_to_md_extra_args": ["--env-arg"],
                        }
                    )

                    # Call load_config and check the result
                    result = provider.load_config("/path/to/config.yaml")
                    assert result.success is True
                    assert result.content["output_dir"] == "/env/output"
                    assert result.content["html_to_md_extra_args"] == ["--env-arg"]