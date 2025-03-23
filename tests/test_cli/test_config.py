# tests/test_cli/test_config.py
"""
Tests for the CLI config module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.cli.config import (
    _merge_cli_overrides,
    find_project_root,
    load_config,
)
from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_with_resolver(self) -> None:
        """Test using the path resolver."""
        with patch("quackcore.paths.resolver.get_project_root") as mock_get_root:
            mock_get_root.return_value = Path("/project/root")

            # Call the function under test
            result = find_project_root()

            # Verify result and mock calls
            assert result == Path("/project/root")
            mock_get_root.assert_called_once()

    def test_with_exception(self) -> None:
        """Test handling exceptions from resolver."""
        with patch("quackcore.paths.resolver.get_project_root") as mock_get_root:
            # Test various exceptions that should be caught
            for exception in [
                FileNotFoundError,
                PermissionError,
                ValueError,
                NotImplementedError,
            ]:
                mock_get_root.side_effect = exception("Test error")

                # Call the function under test
                result = find_project_root()

                # Should fall back to cwd
                assert result == Path.cwd()


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_with_explicit_path(self) -> None:
        """Test loading with an explicit config path."""
        with patch("quackcore.config.load_config") as mock_core_load_config:
            mock_config = QuackConfig()
            mock_core_load_config.return_value = mock_config

            # Call the function under test
            config = load_config("/path/to/config.yaml")

            # Verify result and mock calls
            assert config is mock_config
            mock_core_load_config.assert_called_once_with("/path/to/config.yaml")

    def test_load_with_cli_overrides(self) -> None:
        """Test loading with CLI argument overrides."""
        with patch("quackcore.config.load_config") as mock_core_load_config:
            mock_config = QuackConfig()
            mock_core_load_config.return_value = mock_config

            # Call with CLI overrides
            cli_args = {"debug": True, "log_level": "DEBUG"}

            with patch("quackcore.cli.config._merge_cli_overrides") as mock_merge:
                mock_merge.return_value = mock_config

                config = load_config(cli_overrides=cli_args)

                # Verify _merge_cli_overrides was called with the right arguments
                mock_merge.assert_called_once_with(mock_config, cli_args)
                assert config is mock_config

    def test_load_with_environment(self) -> None:
        """Test loading with environment override."""
        with patch("quackcore.config.load_config") as mock_core_load_config:
            mock_config = QuackConfig()
            mock_core_load_config.return_value = mock_config

            # Call with environment
            config = load_config(environment="production")

            # Verify environment was passed to core load_config
            mock_core_load_config.assert_called_once_with(None, "production")
            assert config is mock_config

    def test_load_with_config_error(self) -> None:
        """Test handling configuration errors."""
        with patch("quackcore.config.load_config") as mock_core_load_config:
            # Test when config_path is given but raises an error
            mock_core_load_config.side_effect = QuackConfigurationError("Config error")

            with pytest.raises(QuackConfigurationError):
                load_config("/path/to/config.yaml")

            # Test when no config_path is given and error occurs (should return default config)
            mock_core_load_config.side_effect = QuackConfigurationError("Config error")

            config = load_config()
            assert isinstance(config, QuackConfig)

    def test_normalize_paths(self) -> None:
        """Test that paths are normalized in the configuration."""
        with patch("quackcore.config.load_config") as mock_core_load_config:
            mock_config = QuackConfig()
            mock_core_load_config.return_value = mock_config

            with patch("quackcore.config.utils.normalize_paths") as mock_normalize:
                mock_normalize.return_value = mock_config

                config = load_config()

                # Verify normalize_paths was called
                mock_normalize.assert_called_once_with(mock_config)
                assert config is mock_config


class TestMergeCliOverrides:
    """Tests for _merge_cli_overrides function."""

    def test_merge_simple_overrides(self) -> None:
        """Test merging simple CLI overrides."""
        # Create a base config
        config = QuackConfig()

        # Create CLI overrides
        cli_overrides = {
            "debug": True,
            "log_level": "DEBUG",
            "output_dir": "/output",
        }

        # Call the function under test
        with patch("quackcore.config.utils.get_config_value") as mock_get_value:
            # Mock to return current values for get_config_value
            mock_get_value.side_effect = lambda cfg, path, default: None

            with patch("quackcore.config.loader.merge_configs") as mock_merge:
                mock_merged_config = QuackConfig()
                mock_merge.return_value = mock_merged_config

                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called with the right overrides
                expected_overrides = {
                    "debug": True,
                    "log_level": "DEBUG",
                    "output_dir": "/output",
                }
                mock_merge.assert_called_once()
                assert result is mock_merged_config

    def test_merge_with_nested_paths(self) -> None:
        """Test merging CLI overrides with nested paths."""
        # Create a base config
        config = QuackConfig()

        # Create CLI overrides
        cli_overrides = {
            "general.debug": True,
            "logging.level": "DEBUG",
            "paths.output_dir": "/output",
        }

        # Call the function under test
        with patch("quackcore.config.utils.get_config_value") as mock_get_value:
            # Mock to return current values for get_config_value
            mock_get_value.side_effect = lambda cfg, path, default: None

            with patch("quackcore.config.loader.merge_configs") as mock_merge:
                mock_merged_config = QuackConfig()
                mock_merge.return_value = mock_merged_config

                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called with the right overrides
                mock_merge.assert_called_once()
                call_args = mock_merge.call_args[0]
                assert call_args[0] is config

                # The second argument should be the dictionary to merge
                override_dict = call_args[1]
                assert "general" in override_dict
                assert override_dict["general"]["debug"] is True
                assert "logging" in override_dict
                assert override_dict["logging"]["level"] == "DEBUG"
                assert "paths" in override_dict
                assert override_dict["paths"]["output_dir"] == "/output"

                assert result is mock_merged_config

    def test_merge_with_ignored_keys(self) -> None:
        """Test that certain keys are ignored during merge."""
        config = QuackConfig()

        # Create CLI overrides with keys that should be ignored
        cli_overrides = {
            "config": "/path/to/config.yaml",
            "help": True,
            "version": True,
            "debug": True,  # This one should not be ignored
        }

        # Call the function under test
        with patch("quackcore.config.utils.get_config_value") as mock_get_value:
            # Mock to return current values for get_config_value
            mock_get_value.side_effect = lambda cfg, path, default: None

            with patch("quackcore.config.loader.merge_configs") as mock_merge:
                mock_merged_config = QuackConfig()
                mock_merge.return_value = mock_merged_config

                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called with only non-ignored keys
                mock_merge.assert_called_once()
                call_args = mock_merge.call_args[0]
                override_dict = call_args[1]

                assert "debug" in override_dict
                assert "config" not in override_dict
                assert "help" not in override_dict
                assert "version" not in override_dict
