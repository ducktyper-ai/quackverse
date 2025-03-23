# src/quackcore/cli/config.py
"""
Configuration utilities for CLI applications.

This module provides functions for loading and managing configuration
in CLI applications, with proper precedence handling between CLI options,
environment variables, and configuration files.
"""

import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError


def _merge_cli_overrides(
        config: QuackConfig, cli_overrides: Mapping[str, Any]
) -> QuackConfig:
    """
    Merge CLI overrides into the configuration.

    Args:
        config: The base configuration
        cli_overrides: A mapping of CLI arguments

    Returns:
        The configuration with overrides merged in
    """
    from quackcore.config.loader import merge_configs

    override_dict: dict[str, Any] = {}
    for key, value in cli_overrides.items():
        if value is None:
            continue
        if key in ("config", "help", "version"):
            continue
        parts = key.replace("-", "_").split(".")
        current = override_dict
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                current.setdefault(part, {})
                current = current[part]

    if override_dict:
        config = merge_configs(config, override_dict)
    return config


@lru_cache(maxsize=1)
def load_config(
        config_path: str | Path | None = None,
        cli_overrides: Mapping[str, Any] | None = None,
        environment: str | None = None,
) -> QuackConfig:
    """
    Load configuration with standard precedence:
    CLI overrides > environment variables > config file.

    This function is cached to avoid reloading the same configuration
    multiple times during a single run.

    Args:
        config_path: Optional path to config file
        cli_overrides: Optional dict of CLI argument overrides
        environment: Optional environment name to override QUACK_ENV

    Returns:
        Loaded and normalized QuackConfig

    Raises:
        QuackConfigurationError: If configuration loading fails
    """
    from quackcore.config import load_config as quack_load_config
    from quackcore.config.utils import load_env_config, normalize_paths

    if environment:
        os.environ["QUACK_ENV"] = environment

    try:
        config = quack_load_config(config_path)
    except QuackConfigurationError:
        if config_path:
            raise
        config = QuackConfig()

    config = load_env_config(config)

    if cli_overrides:
        config = _merge_cli_overrides(config, cli_overrides)

    return normalize_paths(config)


def find_project_root() -> Path:
    """
    Find the project root directory.

    The project root is determined by checking common markers like
    a git repository, pyproject.toml, or setup.py file.

    Returns:
        Path to the project root
    """
    from quackcore.paths import resolver

    try:
        return resolver.get_project_root()
    except (FileNotFoundError, PermissionError, ValueError, NotImplementedError):
        return Path.cwd()