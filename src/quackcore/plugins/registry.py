# src/quackcore/plugins/registry.py
"""
Plugin registry for QuackCore.

This module provides a registry for plugins in the QuackCore system,
allowing plugins to be registered and retrieved by name.
"""

import logging
from typing import Any, TypeVar

from quackcore.errors import QuackPluginError
from quackcore.plugins.protocols import (
    CommandPlugin,
    ExtensionPlugin,
    ProviderPlugin,
    QuackPlugin,
    WorkflowPlugin,
)

T = TypeVar("T")  # Generic for the return type


class PluginRegistry:
    """Registry for QuackCore plugins."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize the plugin registry.

        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Main registry of all plugins
        self._plugins: dict[str, QuackPlugin] = {}

        # Type-specific registries
        self._command_plugins: dict[str, CommandPlugin] = {}
        self._workflow_plugins: dict[str, WorkflowPlugin] = {}
        self._extension_plugins: dict[str, ExtensionPlugin] = {}
        self._provider_plugins: dict[str, ProviderPlugin] = {}

        # Extension registry
        # Maps target plugin names to a list of extensions for that plugin
        self._extensions: dict[str, list[ExtensionPlugin]] = {}

        # Command registry
        # Maps command names to the plugin that provides them
        self._commands: dict[str, CommandPlugin] = {}

        # Workflow registry
        # Maps workflow names to the plugin that provides them
        self._workflows: dict[str, WorkflowPlugin] = {}

    def register(self, plugin: QuackPlugin) -> None:
        """
        Register a plugin with the registry.

        Args:
            plugin: Plugin to register

        Raises:
            QuackPluginError: If a plugin with the same name is already registered
        """
        plugin_name = plugin.name

        if plugin_name in self._plugins:
            raise QuackPluginError(
                f"Plugin '{plugin_name}' is already registered",
                plugin_name=plugin_name,
            )

        # Register in the main registry
        self._plugins[plugin_name] = plugin
        self.logger.debug(f"Registered plugin: {plugin_name}")

        # Register in type-specific registries
        self._register_by_type(plugin)

    def _register_by_type(self, plugin: QuackPlugin) -> None:
        """
        Register a plugin in type-specific registries.

        Args:
            plugin: Plugin to register
        """
        # Command plugin
        if isinstance(plugin, CommandPlugin):
            self._command_plugins[plugin.name] = plugin
            for command in plugin.list_commands():
                if command in self._commands:
                    self.logger.warning(
                        f"Command '{command}' provided by plugin '{plugin.name}' "
                        f"overrides existing implementation from plugin "
                        f"'{self._commands[command].name}'"
                    )
                self._commands[command] = plugin
            self.logger.debug(
                f"Registered command plugin: {plugin.name} "
                f"with commands: {plugin.list_commands()}"
            )

        # Workflow plugin
        if isinstance(plugin, WorkflowPlugin):
            self._workflow_plugins[plugin.name] = plugin
            for workflow in plugin.list_workflows():
                if workflow in self._workflows:
                    self.logger.warning(
                        f"Workflow '{workflow}' provided by plugin '{plugin.name}' "
                        f"overrides existing implementation from plugin "
                        f"'{self._workflows[workflow].name}'"
                    )
                self._workflows[workflow] = plugin
            self.logger.debug(
                f"Registered workflow plugin: {plugin.name} "
                f"with workflows: {plugin.list_workflows()}"
            )

        # Extension plugin
        if isinstance(plugin, ExtensionPlugin):
            self._extension_plugins[plugin.name] = plugin
            target = plugin.get_target_plugin()
            if target not in self._extensions:
                self._extensions[target] = []
            self._extensions[target].append(plugin)
            self.logger.debug(
                f"Registered extension plugin: {plugin.name} targeting: {target}"
            )

        # Provider plugin
        if isinstance(plugin, ProviderPlugin):
            self._provider_plugins[plugin.name] = plugin
            self.logger.debug(
                f"Registered provider plugin: {plugin.name} "
                f"with services: {list(plugin.get_services().keys())}"
            )

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin from the registry.

        Args:
            name: Name of the plugin to unregister

        Raises:
            QuackPluginError: If the plugin is not registered
        """
        if name not in self._plugins:
            raise QuackPluginError(
                f"Plugin '{name}' is not registered",
                plugin_name=name,
            )

        plugin = self._plugins[name]

        # Unregister from the main registry
        del self._plugins[name]

        # Unregister from type-specific registries
        if name in self._command_plugins:
            plugin = self._command_plugins[name]
            del self._command_plugins[name]
            for command in plugin.list_commands():
                if command in self._commands and self._commands[command].name == name:
                    del self._commands[command]

        if name in self._workflow_plugins:
            plugin = self._workflow_plugins[name]
            del self._workflow_plugins[name]
            for workflow in plugin.list_workflows():
                if (
                    workflow in self._workflows
                    and self._workflows[workflow].name == name
                ):
                    del self._workflows[workflow]

        if name in self._extension_plugins:
            plugin = self._extension_plugins[name]
            del self._extension_plugins[name]
            target = plugin.get_target_plugin()
            if target in self._extensions:
                self._extensions[target] = [
                    p for p in self._extensions[target] if p.name != name
                ]
                if not self._extensions[target]:
                    del self._extensions[target]

        if name in self._provider_plugins:
            del self._provider_plugins[name]

        self.logger.debug(f"Unregistered plugin: {name}")

    def get_plugin(self, name: str) -> QuackPlugin | None:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            QuackPlugin: The plugin or None if not found
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """
        Get a list of all registered plugin names.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    def is_registered(self, name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            name: Name of the plugin

        Returns:
            True if the plugin is registered
        """
        return name in self._plugins

    def get_command_plugin(self, name: str) -> CommandPlugin | None:
        """
        Get a command plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            CommandPlugin: The plugin or None if not found
        """
        return self._command_plugins.get(name)

    def get_workflow_plugin(self, name: str) -> WorkflowPlugin | None:
        """
        Get a workflow plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            WorkflowPlugin: The plugin or None if not found
        """
        return self._workflow_plugins.get(name)

    def get_extension_plugin(self, name: str) -> ExtensionPlugin | None:
        """
        Get an extension plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            ExtensionPlugin: The plugin or None if not found
        """
        return self._extension_plugins.get(name)

    def get_provider_plugin(self, name: str) -> ProviderPlugin | None:
        """
        Get a provider plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            ProviderPlugin: The plugin or None if not found
        """
        return self._provider_plugins.get(name)

    def list_command_plugins(self) -> list[str]:
        """
        Get a list of all registered command plugin names.

        Returns:
            List of command plugin names
        """
        return list(self._command_plugins.keys())

    def list_workflow_plugins(self) -> list[str]:
        """
        Get a list of all registered workflow plugin names.

        Returns:
            List of workflow plugin names
        """
        return list(self._workflow_plugins.keys())

    def list_extension_plugins(self) -> list[str]:
        """
        Get a list of all registered extension plugin names.

        Returns:
            List of extension plugin names
        """
        return list(self._extension_plugins.keys())

    def list_provider_plugins(self) -> list[str]:
        """
        Get a list of all registered provider plugin names.

        Returns:
            List of provider plugin names
        """
        return list(self._provider_plugins.keys())

    def list_commands(self) -> list[str]:
        """
        Get a list of all registered command names.

        Returns:
            List of command names
        """
        return list(self._commands.keys())

    def list_workflows(self) -> list[str]:
        """
        Get a list of all registered workflow names.

        Returns:
            List of workflow names
        """
        return list(self._workflows.keys())

    def get_command_plugin_for_command(self, command: str) -> CommandPlugin | None:
        """
        Get the plugin that provides a command.

        Args:
            command: Name of the command

        Returns:
            CommandPlugin: The plugin or None if not found
        """
        return self._commands.get(command)

    def get_workflow_plugin_for_workflow(self, workflow: str) -> WorkflowPlugin | None:
        """
        Get the plugin that provides a workflow.

        Args:
            workflow: Name of the workflow

        Returns:
            WorkflowPlugin: The plugin or None if not found
        """
        return self._workflows.get(workflow)

    def get_extensions_for_plugin(self, target: str) -> list[ExtensionPlugin]:
        """
        Get all extensions for a plugin.

        Args:
            target: Name of the target plugin

        Returns:
            List of extension plugins
        """
        return self._extensions.get(target, [])

    def execute_command(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a command.

        Args:
            command: Name of the command
            *args: Positional arguments to pass to the command
            **kwargs: Keyword arguments to pass to the command

        Returns:
            Result of the command

        Raises:
            QuackPluginError: If the command is not found
        """
        plugin = self._commands.get(command)
        if not plugin:
            raise QuackPluginError(
                f"Command '{command}' not found",
                plugin_name=None,
            )
        return plugin.execute_command(command, *args, **kwargs)

    def execute_workflow(self, workflow: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a workflow.

        Args:
            workflow: Name of the workflow
            *args: Positional arguments to pass to the workflow
            **kwargs: Keyword arguments to pass to the workflow

        Returns:
            Result of the workflow

        Raises:
            QuackPluginError: If the workflow is not found
        """
        plugin = self._workflows.get(workflow)
        if not plugin:
            raise QuackPluginError(
                f"Workflow '{workflow}' not found",
                plugin_name=None,
            )
        return plugin.execute_workflow(workflow, *args, **kwargs)


# Global registry instance
registry = PluginRegistry()
