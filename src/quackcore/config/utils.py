# src/quackcore/config/utils.py
"""
Utility functions for configuration management.

This module provides utility functions for working with configuration,
such as loading environment-specific configuration and validating configuration values.
All file paths are handled exclusively as strings. Any path manipulation is delegated
to functions in the quackcore.fs module.
"""

import os
from collections.abc import Mapping
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
        config: Base configuration.
        config_dir: Directory (as a string) containing environment configuration files.

    Returns:
        QuackConfig: Configuration with environment-specific overrides.

    Raises:
        QuackConfigurationError: If the environment configuration file cannot be loaded.
    """
    env: str = get_env()

    if not config_dir:
        # If the project's name implies it's already a config directory, leave config_dir as None.
        if "config" in config.general.project_name.lower():
            return config

        # Use common candidate directories (all as strings) for configuration files.
        candidates: list[str] = [
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
    env_file: str = fs.join_path(config_dir, f"{env}.yaml")
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
        env_config: dict = load_yaml_config(env_file)
        # Merge with base configuration.
        base_dict: dict = config.to_dict()
        merged_dict: dict = _deep_merge(base_dict, env_config)
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
    config_dict: dict = config.to_dict()
    parts: list[str] = path.split(".")

    current: Any = config_dict
    for part in parts:
        if isinstance(current, Mapping) and part in current:
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
        list[str]: A list of keys that are missing.
    """
    missing: list[str] = []
    for key in required_keys:
        if get_config_value(config, key) is None:
            missing.append(key)
    return missing


def normalize_paths(config: QuackConfig) -> QuackConfig:
    """
    Normalize all paths in the configuration.

    This converts all relative paths to absolute paths based on the base directory.
    All paths are kept as strings. Additionally, extra keys such as 'assets_dir' and
    'temp_dir' are added if missing.

    Args:
        config: Configuration object.

    Returns:
        QuackConfig: A new QuackConfig object with all paths normalized.
    """
    # Get the configuration as a dictionary.
    config_dict: dict = config.to_dict()
    # Explicitly extract the base_dir from the dictionary to preserve a user-provided value.
    base_dir: str = config_dict.get("paths", {}).get("base_dir") or find_project_root()

    # Ensure the "paths" dict exists.
    if "paths" not in config_dict or not isinstance(config_dict["paths"], dict):
        config_dict["paths"] = {}
    # Force the base_dir to the provided value.
    config_dict["paths"]["base_dir"] = base_dir

    # Normalize each key in the paths section (except base_dir).
    for key, value in config_dict["paths"].items():
        if key != "base_dir" and isinstance(value, str):
            config_dict["paths"][key] = _normalize_path(value, base_dir)

    # Add extra keys if missing.
    if "assets_dir" not in config_dict["paths"]:
        config_dict["paths"]["assets_dir"] = _normalize_path("assets", base_dir)
    if "temp_dir" not in config_dict["paths"]:
        config_dict["paths"]["temp_dir"] = _normalize_path("temp", base_dir)

    # Normalize plugins paths.
    if (
        "plugins" in config_dict
        and isinstance(config_dict["plugins"], dict)
        and "paths" in config_dict["plugins"]
    ):
        plugin_paths = config_dict["plugins"]["paths"]
        if plugin_paths and isinstance(plugin_paths, list):
            config_dict["plugins"]["paths"] = [
                _normalize_path(p, base_dir) for p in plugin_paths
            ]

    # Normalize Google integration paths.
    if (
        "integrations" in config_dict
        and isinstance(config_dict["integrations"], dict)
        and "google" in config_dict["integrations"]
    ):
        google = config_dict["integrations"]["google"]
        for key in ["client_secrets_file", "credentials_file"]:
            if key in google and google[key]:
                google[key] = _normalize_path(google[key], base_dir)

    # Normalize logging file path.
    if (
        "logging" in config_dict
        and isinstance(config_dict["logging"], dict)
        and config_dict["logging"].get("file")
    ):
        config_dict["logging"]["file"] = _normalize_path(
            config_dict["logging"]["file"], base_dir
        )

    # Validate and build a new config using pydantic.
    normalized_config: QuackConfig = QuackConfig.model_validate(config_dict)
    # Ensure the base_dir remains as originally provided.
    normalized_config.paths.base_dir = base_dir

    return normalized_config


def _normalize_path(value: str, base_dir: str) -> str:
    """
    Normalize a path relative to a base directory.

    Args:
        value: Path to normalize.
        base_dir: Base directory.

    Returns:
        str: Normalized path as a string.
    """
    # Even though much of the system delegates to quackcore.fs for _operations,
    # here we use the standard library so that the provided base_dir is preserved.
    if os.path.isabs(value):
        return os.path.normpath(value)
    return os.path.normpath(os.path.join(base_dir, value))


def load_yaml_config(config_file: str) -> dict:
    """
    Load a YAML configuration file.

    This helper wraps the low-level functionality to load YAML content from a file.
    (Assumes the existence of a properly implemented loader in quackcore.config.loader)

    Args:
        config_file: Path to the YAML file as a string.

    Returns:
        dict: A dictionary containing the parsed YAML configuration.
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
        dict: A new dictionary containing the merged values.
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
        str: The project root directory as a string.
    """
    try:
        from quackcore.paths import resolver

        root: str = resolver.get_project_root()
        return root  # Assuming resolver.get_project_root() returns a string
    except Exception:
        return os.getcwd()
