# src/quackcore/config/__init__.py
"""
Configuration package for QuackCore.

This package provides configuration handling for QuackCore,
with support for loading from files, environment variables,
and merging configurations from different sources.
"""

from quackcore.config.loader import load_config, merge_configs
from quackcore.config.models import (
    GeneralConfig,
    GoogleConfig,
    IntegrationsConfig,
    LoggingConfig,
    NotionConfig,
    PathsConfig,
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

# Create a global config object
config = load_config()

__all__ = [
    # Classes
    "QuackConfig",
    "GeneralConfig",
    "LoggingConfig",
    "PathsConfig",
    "IntegrationsConfig",
    "GoogleConfig",
    "NotionConfig",
    "PluginsConfig",
    # Functions
    "load_config",
    "merge_configs",
    "get_env",
    "load_env_config",
    "get_config_value",
    "validate_required_config",
    "normalize_paths",
    # Global instance
    "config",
]
