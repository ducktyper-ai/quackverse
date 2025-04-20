# quackcore/tests/test_integrations/core/base/test_config_provider.py
"""
Tests for the BaseConfigProvider class.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.errors import QuackConfigurationError
from quackcore.integrations.core.base import BaseConfigProvider

from .config_provider_impl import (
    MockConfigProvider,
)


class TestBaseConfigProvider:
    """Tests for the BaseConfigProvider class."""

    def test_init(self) -> None:
        """Test initializing the config provider."""
        provider = MockConfigProvider()
        assert provider.name == "test_config"

    def test_abstract_methods(self) -> None:
        """Test that abstract methods must be implemented."""
        # Attempt to create a class without implementing all abstract methods
        with pytest.raises(TypeError):

            class InvalidProvider(BaseConfigProvider):
                @property
                def name(self) -> str:
                    return "invalid"

            InvalidProvider()  # This should raise TypeError

    def test_load_config_with_path(self, temp_dir: Path) -> None:
        """Test loading configuration with an explicit path."""
        # Create a config file
        config_file = temp_dir / "test_config.yaml"
        config_file.write_text("""
        test_section:
          test_key: test_value
        """)

        provider = MockConfigProvider()

        # Test successful load
        with patch("quackcore.fs.service.read_yaml") as mock_read:
            mock_read.return_value.success = True
            mock_read.return_value.data = {"test_section": {"test_key": "test_value"}}

            result = provider.load_config(str(config_file))
            assert result.success is True
            assert result.content == {"test_key": "test_value"}
            assert result.config_path == str(config_file)

        # Test file not found
        with patch("quackcore.fs.service.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = False

            with pytest.raises(QuackConfigurationError):
                provider.load_config(str(temp_dir / "nonexistent.yaml"))

        # Test invalid YAML
        with patch("quackcore.fs.service.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            with patch("quackcore.fs.service.read_yaml") as mock_read:
                mock_read.return_value.success = False
                mock_read.return_value.error = "Invalid YAML"

                with pytest.raises(QuackConfigurationError):
                    provider.load_config(str(config_file))

        # Test invalid configuration
        with patch("quackcore.fs.service.get_file_info") as mock_info:
            mock_info.return_value.success = True
            mock_info.return_value.exists = True

            with patch("quackcore.fs.service.read_yaml") as mock_read:
                mock_read.return_value.success = True
                mock_read.return_value.data = {"wrong_section": {}}

                with patch.object(provider, "validate_config") as mock_validate:
                    mock_validate.return_value = False

                    result = provider.load_config(str(config_file))
                    assert result.success is False
                    assert "validation failed" in result.error.lower()
