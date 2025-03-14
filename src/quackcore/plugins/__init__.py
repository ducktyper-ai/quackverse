# src/quackcore/plugins/__init__.py
"""
Plugin system for QuackCore.

This package provides a plugin system for QuackCore, allowing
modules to be dynamically loaded and registered at runtime.
"""

from quackcore.plugins.discovery import PluginLoader, loader
from quackcore.plugins.protocols import (
    CommandPlugin,
    ConfigurablePlugin,
    ExtensionPlugin,
    PluginLoader,
    PluginRegistry,
    ProviderPlugin,
    QuackPlugin,
    WorkflowPlugin,
)
from quackcore.plugins.registry import PluginRegistry, registry

# Initialize the plugin system by loading core plugins
# This is done on import so that the registry is populated with core plugins
core_plugins = loader.load_entry_points()
for plugin in core_plugins:
    registry.register(plugin)

__all__ = [
    # Classes
    "PluginRegistry",
    "PluginLoader",
    # Protocol interfaces
    "QuackPlugin",
    "CommandPlugin",
    "WorkflowPlugin",
    "ExtensionPlugin",
    "ProviderPlugin",
    "ConfigurablePlugin",
    # Global instances
    "registry",
    "loader",
]
