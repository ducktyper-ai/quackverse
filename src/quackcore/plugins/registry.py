# src/quackcore/plugins/registry.py
import logging
from typing import TypeVar

from quackcore.errors import QuackPluginError
from quackcore.plugins.protocols import (
    CommandPluginProtocol,
    ExtensionPluginProtocol,
    ProviderPluginProtocol,
    QuackPluginProtocol,
    WorkflowPluginProtocol,
)

T = TypeVar("T")  # Generic for return types


class PluginRegistry:
    """Registry for QuackCore plugins."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        """Initialize the plugin registry."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Main plugin registry
        self._plugins: dict[str, QuackPluginProtocol] = {}

        # Type-specific registries
        self._command_plugins: dict[str, CommandPluginProtocol] = {}
        self._workflow_plugins: dict[str, WorkflowPluginProtocol] = {}
        self._extension_plugins: dict[str, ExtensionPluginProtocol] = {}
        self._provider_plugins: dict[str, ProviderPluginProtocol] = {}

        # Lookup registries
        self._extensions: dict[str, list[ExtensionPluginProtocol]] = {}
        self._commands: dict[str, CommandPluginProtocol] = {}
        self._workflows: dict[str, WorkflowPluginProtocol] = {}

    def register(self, plugin: QuackPluginProtocol) -> None:
        """Register a plugin."""
        plugin_name = plugin.name

        if plugin_name in self._plugins:
            raise QuackPluginError(
                f"Plugin '{plugin_name}' is already registered", plugin_name=plugin_name
            )

        # Register in main registry
        self._plugins[plugin_name] = plugin
        self.logger.debug(f"Registered plugin: {plugin_name}")

        # Register in type-specific registries
        self._register_by_type(plugin)

    def _register_by_type(self, plugin: QuackPluginProtocol) -> None:
        """Registers the plugin in the appropriate category registry."""
        if isinstance(plugin, CommandPluginProtocol):
            self._command_plugins[plugin.name] = plugin
            self._register_commands(plugin)
        if isinstance(plugin, WorkflowPluginProtocol):
            self._workflow_plugins[plugin.name] = plugin
            self._register_workflows(plugin)
        if isinstance(plugin, ExtensionPluginProtocol):
            self._extension_plugins[plugin.name] = plugin
            self._register_extension(plugin)
        if isinstance(plugin, ProviderPluginProtocol):
            self._provider_plugins[plugin.name] = plugin

    def _register_commands(self, plugin: CommandPluginProtocol) -> None:
        """Registers commands provided by a command plugin."""
        for command in plugin.list_commands():
            if command in self._commands:
                self.logger.warning(
                    f"Command '{command}' from plugin '{plugin.name}' "
                    f"overrides existing "
                    f"implementation from '{self._commands[command].name}'."
                )
            self._commands[command] = plugin
        self.logger.debug(
            f"Registered command plugin: {plugin.name} "
            f"with commands: {plugin.list_commands()}"
        )

    def _register_workflows(self, plugin: WorkflowPluginProtocol) -> None:
        """Registers workflows provided by a workflow plugin."""
        for workflow in plugin.list_workflows():
            if workflow in self._workflows:
                self.logger.warning(
                    f"Workflow '{workflow}' from plugin '{plugin.name}' "
                    f"overrides existing implementation "
                    f"from '{self._workflows[workflow].name}'."
                )
            self._workflows[workflow] = plugin
        self.logger.debug(
            f"Registered workflow plugin: {plugin.name} "
            f"with workflows: {plugin.list_workflows()}"
        )

    def _register_extension(self, plugin: ExtensionPluginProtocol) -> None:
        """Registers an extension plugin for a target plugin."""
        target = plugin.get_target_plugin()
        self._extensions.setdefault(target, []).append(plugin)
        self.logger.debug(
            f"Registered extension plugin: {plugin.name} targeting: {target}"
        )

    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name not in self._plugins:
            raise QuackPluginError(
                f"Plugin '{name}' is not registered", plugin_name=name
            )

        plugin = self._plugins.pop(name)
        self._unregister_by_type(plugin)

        self.logger.debug(f"Unregistered plugin: {name}")

    def _unregister_by_type(self, plugin: QuackPluginProtocol) -> None:
        """Handles removing the plugin from the appropriate category registry."""
        if isinstance(plugin, CommandPluginProtocol):
            self._command_plugins.pop(plugin.name, None)
            for command in plugin.list_commands():
                self._commands.pop(command, None)
        if isinstance(plugin, WorkflowPluginProtocol):
            self._workflow_plugins.pop(plugin.name, None)
            for workflow in plugin.list_workflows():
                self._workflows.pop(workflow, None)
        if isinstance(plugin, ExtensionPluginProtocol):
            self._extension_plugins.pop(plugin.name, None)
            target = plugin.get_target_plugin()
            self._extensions[target] = [
                p for p in self._extensions.get(target, []) if p.name != plugin.name
            ]
            if not self._extensions[target]:
                self._extensions.pop(target, None)
        if isinstance(plugin, ProviderPluginProtocol):
            self._provider_plugins.pop(plugin.name, None)

    def execute_command(self, command: str, *args: object, **kwargs: object) -> object:
        """
        Execute a command.

        Args:
            command: Name of the command.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The result of the command execution.

        Raises:
            QuackPluginError: If the command is not found.
        """
        plugin = self._commands.get(command)
        if not plugin:
            raise QuackPluginError(f"Command '{command}' not found", plugin_name=None)
        return plugin.execute_command(command, *args, **kwargs)

    def execute_workflow(
        self, workflow: str, *args: object, **kwargs: object
    ) -> object:
        """
        Execute a workflow.

        Args:
            workflow: Name of the workflow.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The result of the workflow execution.

        Raises:
            QuackPluginError: If the workflow is not found.
        """
        plugin = self._workflows.get(workflow)
        if not plugin:
            raise QuackPluginError(f"Workflow '{workflow}' not found", plugin_name=None)
        return plugin.execute_workflow(workflow, *args, **kwargs)

    def get_plugin(self, name: str) -> QuackPluginProtocol | None:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            QuackPluginProtocol: The plugin or None if not found
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

    def get_command_plugin(self, name: str) -> CommandPluginProtocol | None:
        """
        Get a command plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            CommandPluginProtocol: The plugin or None if not found
        """
        return self._command_plugins.get(name)

    def get_workflow_plugin(self, name: str) -> WorkflowPluginProtocol | None:
        """
        Get a workflow plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            WorkflowPluginProtocol: The plugin or None if not found
        """
        return self._workflow_plugins.get(name)

    def get_extension_plugin(self, name: str) -> ExtensionPluginProtocol | None:
        """
        Get an extension plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            ExtensionPluginProtocol: The plugin or None if not found
        """
        return self._extension_plugins.get(name)

    def get_provider_plugin(self, name: str) -> ProviderPluginProtocol | None:
        """
        Get a provider plugin by name.

        Args:
            name: Name of the plugin

        Returns:
            ProviderPluginProtocol: The plugin or None if not found
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

    def get_command_plugin_for_command(
        self, command: str
    ) -> CommandPluginProtocol | None:
        """
        Get the plugin that provides a command.

        Args:
            command: Name of the command

        Returns:
            CommandPluginProtocol: The plugin or None if not found
        """
        return self._commands.get(command)

    def get_workflow_plugin_for_workflow(
        self, workflow: str
    ) -> WorkflowPluginProtocol | None:
        """
        Get the plugin that provides a workflow.

        Args:
            workflow: Name of the workflow

        Returns:
            WorkflowPluginProtocol: The plugin or None if not found
        """
        return self._workflows.get(workflow)

    def get_extensions_for_plugin(self, target: str) -> list[ExtensionPluginProtocol]:
        """
        Get all extensions for a plugin.

        Args:
            target: Name of the target plugin

        Returns:
            List of extension plugins
        """
        return self._extensions.get(target, [])


# Global registry instance
registry = PluginRegistry()
