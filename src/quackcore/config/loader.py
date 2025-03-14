# src/quackcore/config/loader.py
"""
Configuration loading utilities for QuackCore.

This module provides utilities for loading and merging configurations
from various sources, with support for environment-specific overrides.
"""

import os
from pathlib import Path
from typing import Any, TypeVar

import yaml

from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError, wrap_io_errors
from quackcore.paths import resolver

T = TypeVar("T")  # Generic type for flexible typing


DEFAULT_CONFIG_LOCATIONS = [
    # Current working directory
    "./quack_config.yaml",
    "./config/quack_config.yaml",
    # User home directory
    "~/.quack/config.yaml",
    # System-wide configuration
    "/etc/quack/config.yaml",
]

ENV_PREFIX = "QUACK_"


@wrap_io_errors
def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary with configuration values

    Raises:
        QuackConfigurationError: If the file cannot be loaded
    """
    try:
        with open(Path(path), "r") as file:
            config = yaml.safe_load(file)
        return config or {}
    except (yaml.YAMLError, OSError) as e:
        raise QuackConfigurationError(f"Failed to load YAML config: {e}", path) from e


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _get_env_config() -> dict[str, Any]:
    """
    Get configuration from environment variables.

    Environment variables are expected to be in the format:
    QUACK_SECTION__KEY=value
    where SECTION is the configuration section and KEY is the key within that section.

    Returns:
        Dictionary with configuration values
    """
    config = {}
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            key_parts = key[len(ENV_PREFIX) :].lower().split("__")
            if len(key_parts) < 2:
                continue

            # Convert string values to appropriate types
            if value.lower() == "true":
                typed_value = True
            elif value.lower() == "false":
                typed_value = False
            elif value.isdigit():
                typed_value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                typed_value = float(value)
            else:
                typed_value = value

            # Build nested dictionary
            current = config
            for i, part in enumerate(key_parts):
                if i == len(key_parts) - 1:
                    current[part] = typed_value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

    return config


def find_config_file() -> Path | None:
    """
    Find a configuration file in standard locations.

    Returns:
        Path to the configuration file if found, None otherwise
    """
    # Check environment variable first
    if config_path := os.environ.get("QUACK_CONFIG"):
        path = Path(config_path).expanduser()
        if path.exists():
            return path

    # Check default locations
    for location in DEFAULT_CONFIG_LOCATIONS:
        path = Path(location).expanduser()
        if path.exists():
            return path

    # Try to find project root and check for config there
    try:
        root = resolver.find_project_root()
        for name in ["quack_config.yaml", "config/quack_config.yaml"]:
            path = root / name
            if path.exists():
                return path
    except Exception:
        pass

    return None


def load_config(
    config_path: str | Path | None = None,
    merge_env: bool = True,
    merge_defaults: bool = True,
) -> QuackConfig:
    """
    Load configuration from a file and merge with environment and defaults.

    Args:
        config_path: Path to configuration file (optional)
        merge_env: Whether to merge with environment variables
        merge_defaults: Whether to merge with default values

    Returns:
        QuackConfig: Loaded configuration

    Raises:
        QuackConfigurationError: If no configuration could be loaded
    """
    config_dict = {}

    # Load from file if specified
    if config_path:
        file_path = Path(config_path).expanduser()
        if not file_path.exists():
            raise QuackConfigurationError(
                f"Configuration file not found: {file_path}", file_path
            )
        config_dict = load_yaml_config(file_path)
    else:
        # Try to find a configuration file
        if file_path := find_config_file():
            config_dict = load_yaml_config(file_path)

    # Merge with environment variables if requested
    if merge_env:
        env_config = _get_env_config()
        config_dict = _deep_merge(config_dict, env_config)

    # Create configuration object
    config = QuackConfig.model_validate(config_dict)

    return config


def merge_configs(base: QuackConfig, override: dict[str, Any]) -> QuackConfig:
    """
    Merge a base configuration with override values.

    Args:
        base: Base configuration
        override: Override values

    Returns:
        QuackConfig: Merged configuration
    """
    # Convert base to dict
    base_dict = base.to_dict()

    # Deep merge the dictionaries
    merged = _deep_merge(base_dict, override)

    # Create new config from merged dict
    return QuackConfig.model_validate(merged)
