# tests/test_config/test_utils.py
"""
Tests for configuration utility functions.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from quackcore.config.models import QuackConfig
from quackcore.config.utils import (
    get_config_value,
    get_env,
    load_env_config,
    normalize_paths,
    validate_required_config,
)


class TestConfigUtils:
    """Tests for configuration utility functions."""

    def test_get_env(self) -> None:
        """Test getting the current environment."""
        # Test with environment variable set
        with patch.dict(os.environ, {"QUACK_ENV": "production"}):
            assert get_env() == "production"

        # Test with environment variable in uppercase
        with patch.dict(os.environ, {"QUACK_ENV": "PRODUCTION"}):
            assert get_env() == "production"

        # Test with no environment variable (should default to "development")
        with patch.dict(os.environ, clear=True):
            assert get_env() == "development"

    def test_load_env_config(self, temp_dir: Path, sample_config: QuackConfig) -> None:
        """Test loading environment-specific configuration."""
        # Create environment config files
        dev_config = {
            "general": {"debug": True},
            "logging": {"level": "DEBUG"}
        }
        prod_config = {
            "general": {"debug": False},
            "logging": {"level": "INFO"}
        }

        dev_file = temp_dir / "development.yaml"
        prod_file = temp_dir / "production.yaml"
        test_file = temp_dir / "test.yml"  # Test with .yml extension

        with open(dev_file, "w") as f:
            yaml.dump(dev_config, f)

        with open(prod_file, "w") as f:
            yaml.dump(prod_config, f)

        with open(test_file, "w") as f:
            yaml.dump({"general": {"environment": "test"}}, f)

        # Test loading development config
        with patch("quackcore.config.utils.get_env", return_value="development"):
            config = load_env_config(sample_config, temp_dir)
            assert config.general.debug is True
            assert config.logging.level == "DEBUG"

        # Test loading production config
        with patch("quackcore.config.utils.get_env", return_value="production"):
            config = load_env_config(sample_config, temp_dir)
            assert config.general.debug is False
            assert config.logging.level == "INFO"

        # Test loading with .yml extension
        with patch("quackcore.config.utils.get_env", return_value="test"):
            config = load_env_config(sample_config, temp_dir)
            assert config.general.environment == "test"

        # Test loading non-existent environment (should return original)
        with patch("quackcore.config.utils.get_env", return_value="nonexistent"):
            config = load_env_config(sample_config, temp_dir)
            assert config is sample_config

        # Test with error loading environment config (should return original)
        with patch("quackcore.config.utils.get_env", return_value="development"):
            with patch("quackcore.config.utils.load_yaml_config",
                       side_effect=Exception("Test error")):
                config = load_env_config(sample_config, temp_dir)
                assert config is sample_config

        # Test without config_dir specified
        with patch("quackcore.config.utils.get_env", return_value="development"):
            # Test with project containing 'config' in name
            config_project = QuackConfig(general={"project_name": "config_project"})
            config = load_env_config(config_project)
            assert config is config_project

            # Test with existing config directory
            with patch("pathlib.Path.is_dir", return_value=True):
                with patch("quackcore.config.utils.load_yaml_config") as mock_load:
                    mock_load.return_value = dev_config
                    config = load_env_config(sample_config)
                    assert config.general.debug is True

    def test_get_config_value(self, sample_config: QuackConfig) -> None:
        """Test getting a configuration value by path."""
        # Test getting existing value
        assert get_config_value(sample_config, "general.project_name") == "TestProject"
        assert get_config_value(sample_config, "logging.level") == "DEBUG"

        # Test getting non-existent value
        assert get_config_value(sample_config, "nonexistent") is None
        assert get_config_value(sample_config, "general.nonexistent") is None

        # Test with default value
        assert get_config_value(sample_config, "nonexistent", "default") == "default"
        assert get_config_value(sample_config, "general.nonexistent",
                                "default") == "default"

        # Test getting nested values
        nested_config = QuackConfig(
            custom={
                "nested": {
                    "deeply": {
                        "value": 42
                    }
                }
            }
        )
        assert get_config_value(nested_config, "custom.nested.deeply.value") == 42
        assert get_config_value(nested_config, "custom.nested.nonexistent") is None

    def test_validate_required_config(self, sample_config: QuackConfig) -> None:
        """Test validating required configuration keys."""
        # Test with all required keys present
        missing = validate_required_config(
            sample_config,
            ["general.project_name", "logging.level", "paths.base_dir"]
        )
        assert missing == []

        # Test with some missing keys
        missing = validate_required_config(
            sample_config,
            ["general.nonexistent", "logging.file", "custom.key"]
        )
        assert "general.nonexistent" in missing
        assert "logging.file" in missing
        assert "custom.key" in missing

        # Test with mixed present and missing keys
        missing = validate_required_config(
            sample_config,
            ["general.project_name", "logging.nonexistent", "paths.base_dir"]
        )
        assert len(missing) == 1
        assert "logging.nonexistent" in missing

    def test_normalize_paths(self) -> None:
        """Test normalizing paths in configuration."""
        # Create a config with relative paths
        config = QuackConfig(
            paths={
                "base_dir": "/base/dir",
                "output_dir": "output",
                "data_dir": "data",
            },
            plugins={
                "paths": ["plugins", "../external/plugins"]
            },
            integrations={
                "google": {
                    "client_secrets_file": "secrets.json",
                    "credentials_file": "credentials.json"
                }
            },
            logging={
                "file": "logs/app.log"
            }
        )

        # Normalize paths
        normalized = normalize_paths(config)

        # Check that paths were normalized
        assert normalized.paths.base_dir == "/base/dir"  # Absolute path unchanged
        assert normalized.paths.output_dir == "/base/dir/output"  # Relative to base_dir
        assert normalized.paths.data_dir == "/base/dir/data"  # Relative to base_dir

        # Check plugin paths
        assert normalized.plugins.paths[0] == "/base/dir/plugins"
        assert normalized.plugins.paths[1] == "/base/dir/../external/plugins"

        # Check integration paths
        assert normalized.integrations.google.client_secrets_file == "/base/dir/secrets.json"
        assert normalized.integrations.google.credentials_file == "/base/dir/credentials.json"

        # Check logging path
        assert normalized.logging.file == "/base/dir/logs/app.log"

        # Check with already absolute paths
        config = QuackConfig(
            paths={
                "base_dir": "/base/dir",
                "output_dir": "/absolute/output",
                "data_dir": "/absolute/data",
            }
        )
        normalized = normalize_paths(config)
        assert normalized.paths.output_dir == "/absolute/output"  # Absolute path unchanged
        assert normalized.paths.data_dir == "/absolute/data"  # Absolute path unchanged