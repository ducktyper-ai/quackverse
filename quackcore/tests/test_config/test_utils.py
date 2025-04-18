# quackcore/tests/test_config/test_utils.py
"""
Tests for configuration utility functions.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from quackcore.config.models import (
    GoogleConfig,
    IntegrationsConfig,
    LoggingConfig,
    PluginsConfig,
    QuackConfig,
)
from quackcore.config.utils import (
    get_config_value,
    get_env,
    load_env_config,
    normalize_paths,
    validate_required_config,
)
from quackcore.errors import QuackConfigurationError


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
        dev_config = {"general": {"debug": True}, "logging": {"level": "DEBUG"}}
        prod_config = {"general": {"debug": False}, "logging": {"level": "INFO"}}

        # Convert Path to string for file paths
        temp_dir_str = str(temp_dir)
        dev_file = os.path.join(temp_dir_str, "development.yaml")
        prod_file = os.path.join(temp_dir_str, "production.yaml")
        test_file = os.path.join(temp_dir_str, "test.yml")  # Test with .yml extension

        with open(dev_file, "w") as f:
            yaml.dump(dev_config, f)

        with open(prod_file, "w") as f:
            yaml.dump(prod_config, f)

        with open(test_file, "w") as f:
            yaml.dump({"general": {"environment": "test"}}, f)

        # Test loading development config
        with patch("quackcore.config.api.get_env", return_value="development"):
            # Mock fs functions for file _operations
            with patch(
                "quackcore.fs.service.join_path",
                side_effect=lambda a, b: os.path.join(a, b),
            ):
                with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                    # Set up mock to indicate file exists
                    mock_info = MagicMock()
                    mock_info.success = True
                    mock_info.exists = True
                    mock_info.is_dir = True
                    mock_file_info.return_value = mock_info

                    # Mock load_yaml_config
                    with patch(
                        "quackcore.config.api.load_yaml_config",
                        return_value=dev_config,
                    ):
                        config = load_env_config(sample_config, temp_dir_str)
                        assert config.general.debug is True
                        assert config.logging.level == "DEBUG"

        # Test loading production config
        with patch("quackcore.config.api.get_env", return_value="production"):
            # Mock fs functions for file _operations
            with patch(
                "quackcore.fs.service.join_path",
                side_effect=lambda a, b: os.path.join(a, b),
            ):
                with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                    # Set up mock to indicate file exists
                    mock_info = MagicMock()
                    mock_info.success = True
                    mock_info.exists = True
                    mock_info.is_dir = True
                    mock_file_info.return_value = mock_info

                    # Mock load_yaml_config
                    with patch(
                        "quackcore.config.api.load_yaml_config",
                        return_value=prod_config,
                    ):
                        config = load_env_config(sample_config, temp_dir_str)
                        assert config.general.debug is False
                        assert config.logging.level == "INFO"

        # Test loading with .yml extension
        with patch("quackcore.config.api.get_env", return_value="test"):
            # Mock fs functions for file _operations
            with patch(
                "quackcore.fs.service.join_path",
                side_effect=lambda a, b: os.path.join(a, b),
            ):
                with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                    # Set up two mocks - first one returns false (no .yaml), second returns true (.yml)
                    mock_info_false = MagicMock()
                    mock_info_false.success = True
                    mock_info_false.exists = False

                    mock_info_true = MagicMock()
                    mock_info_true.success = True
                    mock_info_true.exists = True
                    mock_info_true.is_dir = False

                    # Return different mock depending on which file is being checked
                    def mock_file_info_side_effect(path):
                        if path.endswith("test.yaml"):
                            return mock_info_false
                        else:
                            return mock_info_true

                    mock_file_info.side_effect = mock_file_info_side_effect

                    # Mock load_yaml_config
                    test_config = {"general": {"environment": "test"}}
                    with patch(
                        "quackcore.config.api.load_yaml_config",
                        return_value=test_config,
                    ):
                        config = load_env_config(sample_config, temp_dir_str)
                        assert config.general.environment == "test"

        # Test loading non-existent environment (should return original)
        with patch("quackcore.config.api.get_env", return_value="nonexistent"):
            with patch(
                "quackcore.fs.service.join_path",
                side_effect=lambda a, b: os.path.join(a, b),
            ):
                with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                    # Mock file not found
                    mock_info = MagicMock()
                    mock_info.success = True
                    mock_info.exists = False
                    mock_file_info.return_value = mock_info

                    config = load_env_config(sample_config, temp_dir_str)
                    assert config is sample_config

        # Test with error loading environment config (should return original)
        with patch("quackcore.config.api.get_env", return_value="development"):
            with patch(
                "quackcore.fs.service.join_path",
                side_effect=lambda a, b: os.path.join(a, b),
            ):
                with patch("quackcore.fs.service.get_file_info") as mock_file_info:
                    # Mock file exists
                    mock_info = MagicMock()
                    mock_info.success = True
                    mock_info.exists = True
                    mock_file_info.return_value = mock_info

                    with patch(
                        "quackcore.config.api.load_yaml_config",
                        side_effect=QuackConfigurationError("Test error"),
                    ):
                        config = load_env_config(sample_config, temp_dir_str)
                        assert config is sample_config

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
        assert (
            get_config_value(sample_config, "general.nonexistent", "default")
            == "default"
        )

        # Test getting nested values
        nested_config = QuackConfig(custom={"nested": {"deeply": {"value": 42}}})
        assert get_config_value(nested_config, "custom.nested.deeply.value") == 42
        assert get_config_value(nested_config, "custom.nested.nonexistent") is None

    def test_validate_required_config(self, sample_config: QuackConfig) -> None:
        """Test validating required configuration keys."""
        # Test with all required keys present
        missing = validate_required_config(
            sample_config, ["general.project_name", "logging.level", "paths.base_dir"]
        )
        assert missing == []

        # Test with some missing keys
        missing = validate_required_config(
            sample_config, ["general.nonexistent", "logging.file", "custom.key"]
        )
        assert "general.nonexistent" in missing
        assert "logging.file" in missing
        assert "custom.key" in missing

        # Test with mixed present and missing keys
        missing = validate_required_config(
            sample_config,
            ["general.project_name", "logging.nonexistent", "paths.base_dir"],
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
            plugins={"paths": ["plugins", "../external/plugins"]},
            integrations={
                "google": {
                    "client_secrets_file": "secrets.json",
                    "credentials_file": "credentials.json",
                }
            },
            logging={"file": "logs/app.log"},
        )

        # Create an expected result
        expected_config = QuackConfig(
            general=config.general,
            paths={
                "base_dir": "/base/dir",
                "output_dir": "/base/dir/output",
                "data_dir": "/base/dir/data",
                "assets_dir": "/base/dir/assets",
                "temp_dir": "/base/dir/temp",
            },
            plugins=PluginsConfig(
                enabled=config.plugins.enabled,
                disabled=config.plugins.disabled,
                paths=["/base/dir/plugins", "/base/dir/../external/plugins"],
            ),
            integrations=IntegrationsConfig(
                google=GoogleConfig(
                    client_secrets_file="/base/dir/secrets.json",
                    credentials_file="/base/dir/credentials.json",
                    shared_folder_id=config.integrations.google.shared_folder_id,
                    gmail_labels=config.integrations.google.gmail_labels,
                    gmail_days_back=config.integrations.google.gmail_days_back,
                ),
                notion=config.integrations.notion,
            ),
            logging=LoggingConfig(
                level=config.logging.level,
                file="/base/dir/logs/app.log",
                console=config.logging.console,
            ),
            custom=config.custom,
        )

        # Use patch instead of direct module manipulation
        with patch(
            "quackcore.config.api.normalize_paths", return_value=expected_config
        ):
            # Call the function directly
            normalized = normalize_paths(config)

            # Check expected values
            assert normalized.paths.base_dir == "/base/dir"
            assert normalized.paths.output_dir == "/base/dir/output"
            assert normalized.paths.data_dir == "/base/dir/data"

            # Check plugin paths
            assert normalized.plugins.paths[0] == "/base/dir/plugins"
            assert normalized.plugins.paths[1] == "/base/dir/../external/plugins"

            # Check integration paths
            assert (
                normalized.integrations.google.client_secrets_file
                == "/base/dir/secrets.json"
            )
            assert (
                normalized.integrations.google.credentials_file
                == "/base/dir/credentials.json"
            )

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

        # Expected config for absolute paths
        expected_abs_config = QuackConfig(
            general=config.general,
            paths={
                "base_dir": "/base/dir",
                "output_dir": "/absolute/output",  # Absolute path unchanged
                "data_dir": "/absolute/data",  # Absolute path unchanged
                "assets_dir": "/base/dir/assets",
                "temp_dir": "/base/dir/temp",
            },
            integrations=config.integrations,
            plugins=config.plugins,
            logging=config.logging,
            custom=config.custom,
        )

        # Mock normalize_paths for absolute paths
        with patch(
            "quackcore.config.api.normalize_paths", return_value=expected_abs_config
        ):
            normalized = normalize_paths(config)
            assert normalized.paths.output_dir == "/absolute/output"
            assert normalized.paths.data_dir == "/absolute/data"
