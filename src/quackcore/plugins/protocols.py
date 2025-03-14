# src/quackcore/plugins/protocols.py
"""
Plugin protocols for QuackCore.

This module defines the Protocol interfaces for plugins in the QuackCore system,
providing a common interface for all plugins to implement.
"""

from typing import Any, Callable, Protocol, TypeVar

T = TypeVar("T")  # Generic return type


class QuackPlugin(Protocol):
    """Base protocol for all QuackCore plugins."""

    @property
    def name(self) -> str:
        """
        Get the name of the plugin.

        Returns:
            str: Plugin name
        """
        ...


class PluginRegistry(Protocol):
    """Protocol for a plugin registry."""

    def register(self, plugin: QuackPlugin) -> None:
        """
        Register a plugin with the registry.

        Args:
            plugin: Plugin to register
        """
        ...

    def get_plugin(self, name: str) -> QuackPlugin | None:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            The plugin or None if not found
        """
        ...

    def list_plugins(self) -> list[str]:
        """
        Get a list of all registered plugin names.

        Returns:
            List of plugin names
        """
        ...

    def is_registered(self, name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            name: Name of the plugin

        Returns:
            True if the plugin is registered
        """
        ...


class PluginLoader(Protocol):
    """Protocol for a plugin loader."""

    def load_entry_points(self, group: str = "quackcore.plugins") -> list[QuackPlugin]:
        """
        Load plugins from entry points.

        Args:
            group: Entry point group to load from

        Returns:
            List of loaded plugins
        """
        ...

    def load_plugin(self, module_path: str) -> QuackPlugin:
        """
        Load a plugin from a module path.

        Args:
            module_path: Path to the module containing the plugin

        Returns:
            The loaded plugin
        """
        ...

    def load_plugins(self, modules: list[str]) -> list[QuackPlugin]:
        """
        Load multiple plugins from module paths.

        Args:
            modules: List of module paths

        Returns:
            List of loaded plugins
        """
        ...


class CommandPlugin(QuackPlugin, Protocol):
    """Protocol for plugins that provide commands."""

    def list_commands(self) -> list[str]:
        """
        List all commands provided by this plugin.

        Returns:
            List of command names
        """
        ...

    def get_command(self, name: str) -> Callable[..., Any] | None:
        """
        Get a command by name.

        Args:
            name: Name of the command

        Returns:
            The command function or None if not found
        """
        ...

    def execute_command(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a command.

        Args:
            name: Name of the command
            *args: Positional arguments to pass to the command
            **kwargs: Keyword arguments to pass to the command

        Returns:
            Result of the command
        """
        ...


class WorkflowPlugin(QuackPlugin, Protocol):
    """Protocol for plugins that provide workflows."""

    def list_workflows(self) -> list[str]:
        """
        List all workflows provided by this plugin.

        Returns:
            List of workflow names
        """
        ...

    def get_workflow(self, name: str) -> Callable[..., Any] | None:
        """
        Get a workflow by name.

        Args:
            name: Name of the workflow

        Returns:
            The workflow function or None if not found
        """
        ...

    def execute_workflow(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a workflow.

        Args:
            name: Name of the workflow
            *args: Positional arguments to pass to the workflow
            **kwargs: Keyword arguments to pass to the workflow

        Returns:
            Result of the workflow
        """
        ...


class ExtensionPlugin(QuackPlugin, Protocol):
    """Protocol for plugins that extend functionality of other plugins."""

    def get_target_plugin(self) -> str:
        """
        Get the name of the plugin this extension targets.

        Returns:
            Name of the target plugin
        """
        ...

    def get_extensions(self) -> dict[str, Callable[..., Any]]:
        """
        Get all extensions provided by this plugin.

        Returns:
            Dictionary of extension name to extension function
        """
        ...


class ProviderPlugin(QuackPlugin, Protocol):
    """Protocol for plugins that provide services."""

    def get_services(self) -> dict[str, Any]:
        """
        Get all services provided by this plugin.

        Returns:
            Dictionary of service name to service object
        """
        ...

    def get_service(self, name: str) -> Any | None:
        """
        Get a service by name.

        Args:
            name: Name of the service

        Returns:
            The service or None if not found
        """
        ...


class ConfigurablePlugin(QuackPlugin, Protocol):
    """Protocol for plugins that can be configured."""

    def configure(self, config: dict[str, Any]) -> None:
        """
        Configure the plugin.

        Args:
            config: Configuration dictionary
        """
        ...

    def get_config_schema(self) -> dict[str, Any]:
        """
        Get the configuration schema for this plugin.

        Returns:
            Dictionary describing the configuration schema
        """
        ...

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        ...
