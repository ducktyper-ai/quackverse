# src/quackcore/config/utils.py
"""
Utility functions for configuration management.

This module provides utility functions for working with configuration,
such as loading environment-specific configuration and validating configuration values.
All file paths are handled exclusively as strings. Any path
manipulation is delegated to functions in the quackcore.fs module.
"""

import os
from typing import Any, TypeVar

from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError
from quackcore.fs import service as fs

T = TypeVar("T")


def get_env() -> str:
    """
    Get the current environment.

    This checks the QUACK_ENV environment variable, falling back to 'development'
    if not set.

    Returns:
        str: Current environment name (lowercase)
    """
    return os.environ.get("QUACK_ENV", "development").lower()


def load_env_config(config: QuackConfig, config_dir: str | None = None) -> QuackConfig:
    """
    Load environment-specific configuration and merge it with the base configuration.

    Args:
        config: Base configuration
        config_dir: Directory (as a string) containing environment configuration files

    Returns:
        QuackConfig: Configuration with environment-specific overrides

    Raises:
        QuackConfigurationError: If the environment configuration file cannot be loaded
    """
    env = get_env()

    if not config_dir:
        # If the project's name implies it's already a config directory, leave config_dir as None.
        if "config" in config.general.project_name.lower():
            return config

        # Use common candidate directories (all as strings) for configuration files.
        candidates = [
            fs.join_path(".", "config"),
            fs.join_path(".", "configs"),
            fs.join_path(config.paths.base_dir, "config"),
            fs.join_path(config.paths.base_dir, "configs"),
        ]

        for candidate in candidates:
            info = fs.get_file_info(candidate)
            if info.success and info.exists and info.is_dir:
                config_dir = candidate
                break

        if not config_dir:
            # If no candidate was found, return the original configuration.
            return config

    # Build the environment-specific config file path using fs.join_path.
    env_file = fs.join_path(config_dir, f"{env}.yaml")
    file_info = fs.get_file_info(env_file)
    if not (file_info.success and file_info.exists):
        # Try with .yml extension if .yaml is not found.
        env_file = fs.join_path(config_dir, f"{env}.yml")
        file_info = fs.get_file_info(env_file)
        if not (file_info.success and file_info.exists):
            # No environment-specific config was found; return the original configuration.
            return config

    try:
        # load_yaml_config is assumed to read YAML from a string–identified file.
        env_config = load_yaml_config(env_file)
        # Merge with base configuration.
        base_dict = config.to_dict()
        merged_dict = _deep_merge(base_dict, env_config)
        # Create a new config object using validated model data.
        return QuackConfig.model_validate(merged_dict)
    except QuackConfigurationError:
        # If a configuration-related error occurs during loading, return the original config.
        return config


def get_config_value(
    config: QuackConfig, path: str, default: T | None = None
) -> T | None:
    """
    Get a configuration value by dot-separated path.

    Args:
        config: Configuration object.
        path: Dot-separated string of keys (e.g. 'logging.level').
        default: Default value if the path is not found.

    Returns:
        The configuration value if found; otherwise, the default.
    """
    config_dict = config.to_dict()
    parts = path.split(".")

    current: Any = config_dict
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
        config: Configuration object.
        required_keys: List of required configuration keys (in dot notation).

    Returns:
        A list of keys that are missing.
    """
    missing = []
    for key in required_keys:
        if get_config_value(config, key) is None:
            missing.append(key)
    return missing


def normalize_paths(config: QuackConfig) -> QuackConfig:
    """
    Normalize all paths in the configuration.

    This converts all relative paths to absolute paths based on the base directory.
    In this refactoring, all paths are kept as strings.

    Args:
        config: Configuration object.

    Returns:
        A new QuackConfig object with all paths normalized as strings.
    """
    config_dict = config.to_dict()
    # Normalize the base directory using fs.normalize_path (which returns a string).
    base_dir = fs.normalize_path(config_dict["paths"]["base_dir"])
    config_dict["paths"]["base_dir"] = base_dir

    # Normalize the remaining paths in the 'paths' section.
    for key, value in config_dict["paths"].items():
        if key != "base_dir" and isinstance(value, (str,)):
            config_dict["paths"][key] = _normalize_path(value, base_dir)

    # Normalize plugins’ paths if available.
    if "plugins" in config_dict and "paths" in config_dict["plugins"]:
        config_dict["plugins"]["paths"] = [
            _normalize_path(p, base_dir)
            for p in config_dict["plugins"]["paths"]
            if isinstance(p, str)
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

    # Return a new QuackConfig with the updated configuration.
    return QuackConfig.model_validate(config_dict)


def _normalize_path(value: str, base_dir: str) -> str:
    """
    Normalize a single path value relative to a base directory.

    Args:
        value: A path as a string.
        base_dir: Base directory as a string.

    Returns:
        An absolute, normalized path as a string.
    """
    if os.path.isabs(value):
        return fs.normalize_path(value)
    else:
        return fs.join_path(base_dir, value)


def load_yaml_config(config_file: str) -> dict:
    """
    Load a YAML configuration file.

    This helper wraps the low-level functionality to load YAML content from a file.
    (Assumes the existence of a properly implemented loader in quackcore.config.loader)

    Args:
        config_file: Path to the YAML file as a string.

    Returns:
        A dictionary containing the parsed YAML configuration.
    """
    # Import the YAML loader here to avoid circular imports.
    from quackcore.config.loader import load_yaml_config as _load_yaml

    return _load_yaml(config_file)


def _deep_merge(a: dict, b: dict) -> dict:
    """
    Recursively merge dictionary b into dictionary a.

    Args:
        a: Base dictionary.
        b: Dictionary to merge into a.

    Returns:
        A new dictionary containing the merged values.
    """
    out = dict(a)
    for key, b_value in b.items():
        a_value = out.get(key)
        if isinstance(a_value, dict) and isinstance(b_value, dict):
            out[key] = _deep_merge(a_value, b_value)
        else:
            out[key] = b_value
    return out


def find_project_root() -> str:
    """
    Find the project root directory.

    The project root is determined by checking for common markers such as a git repository,
    a pyproject.toml file, or a setup.py file.

    Returns:
        The project root directory as a string.
    """
    try:
        # Use the resolver from quackcore.paths (which should return a string)
        from quackcore.paths import resolver

        root = resolver.get_project_root()
        return root  # Assuming resolver.get_project_root() returns a string
    except Exception:
        return os.getcwd()
