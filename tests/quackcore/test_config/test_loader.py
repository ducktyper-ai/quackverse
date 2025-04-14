# tests/quackcore/test_config/test_loader.py
"""
Tests for configuration loading utilities.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from quackcore.config.loader import (
    DEFAULT_CONFIG_LOCATIONS,
    DEFAULT_CONFIG_VALUES,
    _convert_env_value,
    _deep_merge,
    _get_env_config,
    _is_float,
    find_config_file,
    load_config,
    load_yaml_config,
    merge_configs,
)
from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError


class TestConfigLoader:
    """Tests for the configuration loader."""

    def test_load_yaml_config(self, temp_dir: Path) -> None:
        """Test loading configuration from a YAML file."""
        # Create a YAML file
        config_data = {
            "general": {"project_name": "TestProject", "debug": True},
            "paths": {"base_dir": "/test/path"},
            "logging": {"level": "DEBUG"},
        }
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Test loading valid YAML
        loaded = load_yaml_config(config_file)
        assert loaded == config_data

        # Test loading empty YAML
        empty_file = temp_dir / "empty.yaml"
        empty_file.touch()
        loaded = load_yaml_config(empty_file)
        assert loaded == {}

        # Test loading invalid YAML
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: : yaml")
        with pytest.raises(QuackConfigurationError):
            load_yaml_config(invalid_file)

        # Test loading non-existent file
        with pytest.raises(QuackConfigurationError):
            load_yaml_config(temp_dir / "nonexistent.yaml")

    def test_deep_merge(self) -> None:
        """Test deep merging of dictionaries."""
        # Test basic merge
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        merged = _deep_merge(base, override)
        assert merged == {"a": 1, "b": 3, "c": 4}

        # Test nested merge
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 4, "z": 5}, "c": 6}
        merged = _deep_merge(base, override)
        assert merged == {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}

        # Test multi-level nested merge
        base = {"a": {"x": {"i": 1, "j": 2}, "y": 3}, "b": 4}
        override = {"a": {"x": {"j": 5, "k": 6}, "z": 7}, "c": 8}
        merged = _deep_merge(base, override)
        assert merged == {
            "a": {"x": {"i": 1, "j": 5, "k": 6}, "y": 3, "z": 7},
            "b": 4,
            "c": 8,
        }

        # Test when override is not a dictionary
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": "not_a_dict", "c": 4}
        merged = _deep_merge(base, override)
        assert merged == {"a": "not_a_dict", "b": 3, "c": 4}

    def test_is_float(self) -> None:
        """Test checking if a string represents a float."""
        assert _is_float("3.14") is True
        assert _is_float("0.0") is True
        assert _is_float("-2.5") is True

        assert _is_float("3") is False  # Integer
        assert _is_float("3.") is False  # Not a proper float format
        assert _is_float("abc") is False  # Not a number
        assert _is_float("3,14") is False  # Wrong decimal separator

    def test_convert_env_value(self) -> None:
        """Test converting environment variable string values to appropriate types."""
        # Test boolean conversion
        assert _convert_env_value("true") is True
        assert _convert_env_value("True") is True
        assert _convert_env_value("false") is False
        assert _convert_env_value("False") is False

        # Test integer conversion
        assert _convert_env_value("123") == 123
        assert _convert_env_value("0") == 0
        assert _convert_env_value("-456") == -456

        # Test float conversion
        assert _convert_env_value("3.14") == 3.14
        assert _convert_env_value("-2.5") == -2.5

        # Test string values
        assert _convert_env_value("hello") == "hello"
        assert _convert_env_value("123abc") == "123abc"
        assert _convert_env_value("") == ""

    def test_get_env_config(self) -> None:
        """Test getting configuration from environment variables."""
        # Set up test environment variables
        with patch.dict(
            os.environ,
            {
                "QUACK_GENERAL__PROJECT_NAME": "EnvProject",
                "QUACK_LOGGING__LEVEL": "DEBUG",
                "QUACK_PATHS__BASE_DIR": "/env/path",
                "QUACK_DEBUG": "true",  # Invalid format (no section)
                "OTHER_VAR": "ignored",  # Non-QUACK variable
            },
        ):
            config = _get_env_config()

            assert "general" in config
            assert config["general"]["project_name"] == "EnvProject"
            assert "logging" in config
            assert config["logging"]["level"] == "DEBUG"
            assert "paths" in config
            assert config["paths"]["base_dir"] == "/env/path"
            assert "debug" not in config  # Should be ignored (no section)
            assert "other_var" not in config  # Should be ignored (wrong prefix)

    def test_find_config_file(self) -> None:
        """Test finding a configuration file in standard locations."""
        # Test with QUACK_CONFIG environment variable
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "custom_config.yaml"
            config_path.touch()

            with patch.dict(os.environ, {"QUACK_CONFIG": str(config_path)}):
                found = find_config_file()
                assert found == config_path

        # Test with file in default locations
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Create a config file in one of the default locations
            config_path = tmp_path / "quack_config.yaml"
            config_path.touch()

            # Patch the default locations to include our temp path
            patched_locations = [str(config_path)] + DEFAULT_CONFIG_LOCATIONS
            with patch(
                "quackcore.config.loader.DEFAULT_CONFIG_LOCATIONS", patched_locations
            ):
                found = find_config_file()
                assert found == config_path

        # Test with project root detection
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Create a marker file to identify as project root
            (tmp_path / "pyproject.toml").touch()

            # Create a config file in the project root
            config_path = tmp_path / "quack_config.yaml"
            config_path.touch()

            # Patch project root detection
            with patch(
                "quackcore.config.loader.resolver.get_project_root",
                return_value=tmp_path,
            ):
                found = find_config_file()
                assert found == config_path

        # Test when no config file can be found
        with patch("os.path.exists", return_value=False):
            with patch(
                "quackcore.config.loader.resolver.get_project_root",
                side_effect=Exception,
            ):
                found = find_config_file()
                assert found is None

    def test_load_config(self) -> None:
        """Test loading configuration from various sources."""
        # Test loading with explicit config path
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "test_config.yaml"

            # Create a config file
            config_data = {
                "general": {"project_name": "TestProject", "debug": True},
                "paths": {"base_dir": "/test/path"},
                "logging": {"level": "DEBUG"},
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            # Load the config
            config = load_config(config_path)
            assert isinstance(config, QuackConfig)
            assert config.general.project_name == "TestProject"
            assert config.general.debug is True
            assert str(config.paths.base_dir) == "/test/path"
            assert config.logging.level == "DEBUG"

        # Test loading with environment variables
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "env_config.yaml"

            # Create a base config file
            base_config = {
                "general": {"project_name": "BaseProject", "debug": False},
                "logging": {"level": "INFO"},
            }
            with open(config_path, "w") as f:
                yaml.dump(base_config, f)

            # Set environment variables for override
            with patch.dict(
                os.environ,
                {
                    "QUACK_GENERAL__PROJECT_NAME": "EnvProject",
                    "QUACK_LOGGING__LEVEL": "DEBUG",
                },
            ):
                # Load with merge_env=True
                config = load_config(config_path, merge_env=True)
                assert config.general.project_name == "EnvProject"  # From env
                assert config.general.debug is False  # From file
                assert config.logging.level == "DEBUG"  # From env

                # Load with merge_env=False
                config = load_config(config_path, merge_env=False)
                assert config.general.project_name == "BaseProject"  # From file
                assert config.logging.level == "INFO"  # From file

        # Test loading with default values
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "partial_config.yaml"

            # Create a partial config file
            partial_config = {"general": {"project_name": "PartialProject"}}
            with open(config_path, "w") as f:
                yaml.dump(partial_config, f)

            # Load with merge_defaults=True
            config = load_config(config_path, merge_defaults=True)
            assert config.general.project_name == "PartialProject"  # From file
            assert (
                config.logging.level == DEFAULT_CONFIG_VALUES["logging"]["level"]
            )  # From defaults

            # Load with merge_defaults=False
            config = load_config(config_path, merge_defaults=False)
            assert config.general.project_name == "PartialProject"  # From file
            assert config.logging.level == "INFO"  # Default from model

        # Test with non-existent config file
        with pytest.raises(QuackConfigurationError):
            load_config("/nonexistent/path/config.yaml")

        # Test auto-discovery when no path provided
        with patch("quackcore.config.loader.find_config_file") as mock_find:
            # Set up mock to return a valid file
            config_file = MagicMock()
            mock_find.return_value = config_file

            # Mock the load_yaml_config function
            with patch("quackcore.config.loader.load_yaml_config") as mock_load:
                mock_load.return_value = {
                    "general": {"project_name": "DiscoveredProject"}
                }

                # Load without explicit path
                config = load_config()
                assert config.general.project_name == "DiscoveredProject"

                # Verify find_config_file was called
                mock_find.assert_called_once()

    def test_merge_configs(self, sample_config: QuackConfig) -> None:
        """Test merging configurations."""
        # Create an override dictionary
        override = {
            "general": {"debug": True},
            "logging": {"level": "DEBUG", "file": "/test/log.txt"},
            "custom": {"key": "value"},
        }

        # Merge configs
        merged = merge_configs(sample_config, override)

        # Verify merged values
        assert (
            merged.general.project_name == sample_config.general.project_name
        )  # Unchanged
        assert merged.general.debug is True  # Overridden
        assert merged.logging.level == "DEBUG"  # Overridden
        assert str(merged.logging.file) == "/test/log.txt"  # Overridden
        assert merged.custom["key"] == "value"  # Added

        # Test merging with empty override
        merged = merge_configs(sample_config, {})
        assert merged.model_dump() == sample_config.model_dump()  # Should be identical
