# src/quackcore/config/plugin.py
"""
Plugin interface for the configuration module.

This module defines the plugin interface for the configuration module,
allowing QuackCore to expose configuration functionality to other modules.
"""

from pathlib import Path
from typing import Any, Protocol, TypeVar

from quackcore.config.loader import load_config
from quackcore.config.models import QuackConfig
from quackcore.config.utils import get_config_value, normalize_paths

T = TypeVar("T")


class ConfigPlugin(Protocol):
    """Protocol for configuration plugins."""

    @property
    def name(self) -> str:
        """Name of the plugin."""
        ...

    def load_config(
        self, config_path: str | Path | None = None, merge_env: bool = True
    ) -> QuackConfig:
        """
        Load configuration from a file and merge with environment and defaults.

        Args:
            config_path: Path to configuration file (optional)
            merge_env: Whether to merge with environment variables

        Returns:
            QuackConfig: Loaded configuration
        """
        ...

    def get_value(self, path: str, default: T | None = None) -> T | None:
        """
        Get a configuration value by path.

        The path is a dot-separated string of keys, e.g. 'logging.level'

        Args:
            path: Path to the configuration value
            default: Default value if the path is not found

        Returns:
            Configuration value
        """
        ...

    def get_base_dir(self) -> Path:
        """
        Get the base directory from the configuration.

        Returns:
            Path: Base directory
        """
        ...

    def get_output_dir(self) -> Path:
        """
        Get the output directory from the configuration.

        Returns:
            Path: Output directory
        """
        ...


class QuackConfigPlugin:
    """Implementation of the configuration plugin protocol."""

    def __init__(self) -> None:
        """Initialize the plugin."""
        self._config = load_config()

    @property
    def name(self) -> str:
        """Name of the plugin."""
        return "config"

    def load_config(
        self, config_path: str | Path | None = None, merge_env: bool = True
    ) -> QuackConfig:
        """
        Load configuration from a file and merge with environment and defaults.

        Args:
            config_path: Path to configuration file (optional)
            merge_env: Whether to merge with environment variables

        Returns:
            QuackConfig: Loaded configuration
        """
        self._config = load_config(config_path, merge_env)
        self._config = normalize_paths(self._config)
        return self._config

    def get_value(self, path: str, default: T | None = None) -> Any:
        """
        Get a configuration value by path.

        The path is a dot-separated string of keys, e.g. 'logging.level'

        Args:
            path: Path to the configuration value
            default: Default value if the path is not found

        Returns:
            Configuration value
        """
        return get_config_value(self._config, path, default)

    def get_base_dir(self) -> Path:
        """
        Get the base directory from the configuration.

        Returns:
            Path: Base directory
        """
        return Path(self._config.paths.base_dir)

    def get_output_dir(self) -> Path:
        """
        Get the output directory from the configuration.

        Returns:
            Path: Output directory
        """
        return Path(self._config.paths.output_dir)


def create_plugin() -> ConfigPlugin:
    """Create a new instance of the configuration plugin."""
    return QuackConfigPlugin()
