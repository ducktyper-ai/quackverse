# tests/test_cli/test_config.py
"""
Tests for the CLI config module.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.cli.config import (
    _merge_cli_overrides,
    find_project_root,
    load_config,
)
from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError, QuackFileNotFoundError
from tests.test_cli.mocks import MockConfig


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_with_resolver(self):
        """Test using the path resolver."""
        # Use patches directly instead of importing from a different location
        with patch('quackcore.paths.resolver.get_project_root') as mock_get_root:
            # Set up mock to return a specific path
            mock_get_root.return_value = Path("/project/root")

            # Mock Path.cwd() to avoid fallback issues
            with patch.object(Path, "cwd", return_value=Path("/some/other/path")):
                # Call the function under test
                result = find_project_root()

                # Verify the result
                assert result == Path("/project/root")
                mock_get_root.assert_called_once()

    def test_with_exception(self):
        """Test handling exceptions from resolver."""
        # Test various exceptions that should be caught
        exceptions = [
            FileNotFoundError("File not found"),
            PermissionError("Permission denied"),
            ValueError("Invalid value"),
            NotImplementedError("Not implemented"),
        ]

        for exception in exceptions:
            with patch('quackcore.paths.resolver.get_project_root') as mock_get_root:
                mock_get_root.side_effect = exception

                # Mock Path.cwd() for deterministic test results
                with patch.object(Path, "cwd", return_value=Path("/fallback/path")):
                    # Call the function under test
                    result = find_project_root()

                    # Should fall back to cwd
                    assert result == Path("/fallback/path")

        # Special handling for QuackFileNotFoundError
        with patch('quackcore.paths.resolver.get_project_root') as mock_get_root:
            mock_get_root.side_effect = QuackFileNotFoundError("unknown",
                                                               "File not found")

            # Mock Path.cwd() for deterministic test results
            with patch.object(Path, "cwd", return_value=Path("/fallback/path")):
                # Call the function under test
                result = find_project_root()

                # Should fall back to cwd
                assert result == Path("/fallback/path")


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_with_explicit_path(self):
        """Test loading with an explicit config path."""
        with patch('quackcore.config.load_config') as mock_core_load_config:
            # Set up mock
            mock_config = MockConfig()
            mock_core_load_config.return_value = mock_config

            # Call the function under test
            config = load_config("/path/to/config.yaml")

            # Verify result and mock calls
            assert config is mock_config
            mock_core_load_config.assert_called_once_with("/path/to/config.yaml")

    def test_load_with_cli_overrides(self):
        """Test loading with CLI argument overrides."""
        with patch('quackcore.config.load_config') as mock_core_load_config:
            with patch('quackcore.cli.config._merge_cli_overrides') as mock_merge:
                # Set up mocks
                mock_config = MockConfig()
                mock_merged_config = MockConfig()
                mock_core_load_config.return_value = mock_config
                mock_merge.return_value = mock_merged_config

                # Call with CLI overrides
                cli_args = {"debug": True, "log_level": "DEBUG"}
                config = load_config(cli_overrides=cli_args)

                # Verify _merge_cli_overrides was called with the right arguments
                mock_merge.assert_called_once_with(mock_config, cli_args)
                assert config is mock_merged_config

    def test_load_with_environment(self):
        """Test loading with environment override."""
        with patch('quackcore.config.load_config') as mock_core_load_config:
            # Set up mock
            mock_config = MockConfig()
            mock_core_load_config.return_value = mock_config

            # Call with environment
            with patch.dict('os.environ', {}, clear=True):
                config = load_config(environment="production")

                # Verify environment was set and passed
                assert os.environ.get("QUACK_ENV") == "production"
                mock_core_load_config.assert_called_once_with(None, "production")
                assert config is mock_config

    def test_load_with_config_error(self):
        """Test handling configuration errors."""
        with patch('quackcore.config.load_config') as mock_core_load_config:
            # Set up mock to raise error
            mock_core_load_config.side_effect = QuackConfigurationError("Config error")

            # Test when config_path is given but raises an error
            with pytest.raises(QuackConfigurationError):
                load_config("/path/to/config.yaml")

            # Reset the mock for the next test
            mock_core_load_config.reset_mock()

            # Make sure it still raises the error
            mock_core_load_config.side_effect = QuackConfigurationError("Config error")

            # Test when no config_path is given and error occurs (should return default config)
            with patch('quackcore.config.models.QuackConfig') as mock_config_class:
                mock_default_config = MockConfig()
                mock_config_class.return_value = mock_default_config

                config = load_config()
                assert isinstance(config, QuackConfig)

    def test_normalize_paths(self):
        """Test that paths are normalized in the configuration."""
        with patch('quackcore.config.load_config') as mock_core_load_config:
            with patch('quackcore.config.utils.normalize_paths') as mock_normalize:
                # Set up mocks
                mock_config = MockConfig()
                mock_normalized_config = MockConfig()
                mock_core_load_config.return_value = mock_config
                mock_normalize.return_value = mock_normalized_config

                # Call the function
                config = load_config()

                # Verify normalize_paths was called
                mock_normalize.assert_called_once_with(mock_config)
                assert config is mock_normalized_config


class TestMergeCliOverrides:
    """Tests for _merge_cli_overrides function."""

    def test_merge_simple_overrides(self):
        """Test merging simple CLI overrides."""
        # Create a base config
        config = QuackConfig()

        # Create CLI overrides
        cli_overrides = {
            "debug": True,
            "log_level": "DEBUG",
            "output_dir": "/output",
        }

        # Mock dependencies
        with patch('quackcore.config.utils.get_config_value') as mock_get_value:
            with patch('quackcore.config.loader.merge_configs') as mock_merge:
                # Mock to return current values
                mock_get_value.side_effect = lambda cfg, path, default: None

                # Set up mock for merge_configs
                mock_merged_config = MockConfig()
                mock_merge.return_value = mock_merged_config

                # Call the function under test
                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called with the right overrides
                mock_merge.assert_called_once()

                # Verify the arguments passed to merge_configs
                call_args = mock_merge.call_args[0]
                assert call_args[0] is config  # First arg should be original config

                # Verify override dict contains expected keys and values
                override_dict = call_args[1]  # Second arg should be override dict
                for key, value in cli_overrides.items():
                    assert key in override_dict
                    assert override_dict[key] == value

                # Verify function returns merged config
                assert result is mock_merged_config

    def test_merge_with_nested_paths(self):
        """Test merging CLI overrides with nested paths."""
        # Create a base config
        config = QuackConfig()

        # Create CLI overrides with dot notation paths
        cli_overrides = {
            "general.debug": True,
            "logging.level": "DEBUG",
            "paths.output_dir": "/output",
        }

        # Mock dependencies
        with patch('quackcore.config.utils.get_config_value') as mock_get_value:
            with patch('quackcore.config.loader.merge_configs') as mock_merge:
                # Mock to return current values
                mock_get_value.side_effect = lambda cfg, path, default: None

                # Set up mock for merge_configs
                mock_merged_config = MockConfig()
                mock_merge.return_value = mock_merged_config

                # Call the function under test
                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called
                mock_merge.assert_called_once()

                # Check the nested structure was created correctly
                call_args = mock_merge.call_args[0]
                assert call_args[0] is config

                # Check the nested dict structure
                override_dict = call_args[1]
                assert "general" in override_dict
                assert override_dict["general"]["debug"] is True
                assert "logging" in override_dict
                assert override_dict["logging"]["level"] == "DEBUG"
                assert "paths" in override_dict
                assert override_dict["paths"]["output_dir"] == "/output"

                # Verify function returns merged config
                assert result is mock_merged_config

    def test_merge_with_ignored_keys(self):
        """Test that certain keys are ignored during merge."""
        # Create a base config
        config = QuackConfig()

        # Create CLI overrides with some keys that should be ignored
        cli_overrides = {
            "config": "/path/to/config.yaml",  # Should be ignored
            "help": True,  # Should be ignored
            "version": True,  # Should be ignored
            "debug": True,  # Should NOT be ignored
        }

        # Mock dependencies
        with patch('quackcore.config.utils.get_config_value') as mock_get_value:
            with patch('quackcore.config.loader.merge_configs') as mock_merge:
                # Mock to return current values
                mock_get_value.side_effect = lambda cfg, path, default: None

                # Set up mock for merge_configs
                mock_merged_config = MockConfig()
                mock_merge.return_value = mock_merged_config

                # Call the function under test
                result = _merge_cli_overrides(config, cli_overrides)

                # Verify merge_configs was called
                mock_merge.assert_called_once()

                # Check that ignored keys are not included
                call_args = mock_merge.call_args[0]
                override_dict = call_args[1]

                # Non-ignored key should be present
                assert "debug" in override_dict
                assert override_dict["debug"] is True

                # Ignored keys should not be present
                assert "config" not in override_dict
                assert "help" not in override_dict
                assert "version" not in override_dict

                # Verify function returns merged config
                assert result is mock_merged_config