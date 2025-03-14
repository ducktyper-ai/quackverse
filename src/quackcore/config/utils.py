# src/quackcore/config/utils.py
"""
Utility functions for configuration management.

This module provides utility functions for working with configuration,
such as loading environment-specific configuration and validating configuration values.
"""

import os
from pathlib import Path
from typing import TypeVar

from quackcore.config.loader import _deep_merge, load_yaml_config
from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError

T = TypeVar("T")


def get_env() -> str:
    """
    Get the current environment.

    This checks the QUACK_ENV environment variable, falling back to 'development'
    if not set.

    Returns:
        str: Current environment name
    """
    return os.environ.get("QUACK_ENV", "development").lower()


def load_env_config(
    config: QuackConfig, config_dir: str | Path | None = None
) -> QuackConfig:
    """
    Load environment-specific configuration and merge it with the base configuration.

    Args:
        config: Base configuration
        config_dir: Directory containing environment configuration files

    Returns:
        QuackConfig: Configuration with environment-specific overrides

    Raises:
        QuackConfigurationError: If the environment configuration file cannot be loaded
    """
    env = get_env()

    if not config_dir:
        # Try to guess the config directory from the general config
        if "config" in config.general.project_name.lower():
            # If the project name contains 'config',
            # assume it's already a config directory
            return config

        # Use a heuristic: look for a 'config' directory in common locations
        candidates = [
            Path("./config"),
            Path("./configs"),
            Path(config.paths.base_dir) / "config",
            Path(config.paths.base_dir) / "configs",
        ]

        for candidate in candidates:
            if candidate.is_dir():
                config_dir = candidate
                break

        if not config_dir:
            # No config directory found, return the original config
            return config

    # Load environment-specific configuration
    env_file = Path(config_dir) / f"{env}.yaml"
    if not env_file.exists():
        # Try with .yml extension
        env_file = Path(config_dir) / f"{env}.yml"
        if not env_file.exists():
            # No environment-specific config, return the original
            return config

    try:
        env_config = load_yaml_config(env_file)

        # Merge with base configuration
        base_dict = config.to_dict()
        merged_dict = _deep_merge(base_dict, env_config)

        # Create new config object
        return QuackConfig.model_validate(merged_dict)

    except QuackConfigurationError:
        # If there's an error loading the environment config, return the original
        return config


def get_config_value(
    config: QuackConfig, path: str, default: T | None = None
) -> T | None:
    """
    Get a configuration value by path.

    The path is a dot-separated string of keys, e.g. 'logging.level'

    Args:
        config: Configuration object
        path: Path to the configuration value
        default: Default value if the path is not found

    Returns:
        Configuration value
    """
    config_dict = config.to_dict()
    parts = path.split(".")

    current = config_dict
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default

    return current


def validate_required_config(
    config: QuackConfig, required_keys: list[str]
) -> list[str]:
    """
    Validate that the configuration contains all required keys.

    Args:
        config: Configuration object
        required_keys: List of required configuration keys (dot notation)

    Returns:
        List of missing keys
    """
    missing = []
    for key in required_keys:
        if get_config_value(config, key) is None:
            missing.append(key)

    return missing


def _normalize_path(value: str | Path, base_dir: Path) -> str:
    """
    Normalize a single path value relative to a base directory.

    Args:
        value: A string or Path representing a path
        base_dir: Base directory for resolving relative paths

    Returns:
        Absolute path as string.
    """
    p = Path(value)
    return str(p) if p.is_absolute() else str(base_dir / p)


def normalize_paths(config: QuackConfig) -> QuackConfig:
    """
    Normalize all paths in the configuration.

    This converts all relative paths to absolute paths based on the base directory.

    Args:
        config: Configuration object

    Returns:
        Configuration with normalized paths
    """
    config_dict = config.to_dict()
    base_dir = Path(config_dict["paths"]["base_dir"])

    # Normalize the 'paths' section, except the base_dir key.
    for key, value in config_dict["paths"].items():
        if key != "base_dir" and isinstance(value, str | Path):
            config_dict["paths"][key] = _normalize_path(value, base_dir)

    # Normalize the plugins' paths if present.
    if "plugins" in config_dict and "paths" in config_dict["plugins"]:
        config_dict["plugins"]["paths"] = [
            _normalize_path(path, base_dir) for path in config_dict["plugins"]["paths"]
        ]

    # Normalize Google integration file paths.
    if "integrations" in config_dict and "google" in config_dict["integrations"]:
        google = config_dict["integrations"]["google"]
        for key in ["client_secrets_file", "credentials_file"]:
            if key in google and google[key]:
                google[key] = _normalize_path(google[key], base_dir)

    # Normalize logging file path.
    if (
        "logging" in config_dict
        and "file" in config_dict["logging"]
        and config_dict["logging"]["file"]
    ):
        config_dict["logging"]["file"] = _normalize_path(
            config_dict["logging"]["file"], base_dir
        )

    return QuackConfig.model_validate(config_dict)
