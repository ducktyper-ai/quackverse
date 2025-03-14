# tests/test_plugins/test_registry.py
"""
Tests for the plugin registry.
"""

from unittest.mock import MagicMock

import pytest

from quackcore.errors import QuackPluginError
from quackcore.plugins.protocols import (
    CommandPluginProtocol,
    ExtensionPluginProtocol,
    ProviderPluginProtocol,
    QuackPluginProtocol,
    WorkflowPluginProtocol,
)
from quackcore.plugins.registry import PluginRegistry


# Mock plugin implementations for testing
class BasicPlugin(QuackPluginProtocol):
    """Basic plugin implementation for testing."""

    @property
    def name(self) -> str:
        return "basic_plugin"


class CommandPlugin(CommandPluginProtocol):
    """Command plugin implementation for testing."""

    @property
    def name(self) -> str:
        return "command_plugin"

    def list_commands(self) -> list[str]:
        return ["cmd1", "cmd2"]

    def get_command(self, name: str) -> callable | None:
        if name in self.list_commands():
            return lambda *args, **kwargs: f"Executed {name}"
        return None

    def execute_command(self, name: str, *args: object, **kwargs: object) -> str:
        cmd = self.get_command(name)
        if cmd:
            return cmd(*args, **kwargs)
        raise ValueError(f"Command {name} not found")


class WorkflowPlugin(WorkflowPluginProtocol):
    """Workflow plugin implementation for testing."""

    @property
    def name(self) -> str:
        return "workflow_plugin"

    def list_workflows(self) -> list[str]:
        return ["flow1", "flow2"]

    def get_workflow(self, name: str) -> callable | None:
        if name in self.list_workflows():
            return lambda *args, **kwargs: f"Ran {name}"
        return None

    def execute_workflow(self, name: str, *args: object, **kwargs: object) -> str:
        wf = self.get_workflow(name)
        if wf:
            return wf(*args, **kwargs)
        raise ValueError(f"Workflow {name} not found")


class ExtensionPlugin(ExtensionPluginProtocol):
    """Extension plugin implementation for testing."""

    @property
    def name(self) -> str:
        return "extension_plugin"

    def get_target_plugin(self) -> str:
        return "target_plugin"

    def get_extensions(self) -> dict[str, callable]:
        return {
            "ext1": lambda: "Extension 1",
            "ext2": lambda: "Extension 2"
        }


class ProviderPlugin(ProviderPluginProtocol):
    """Provider plugin implementation for testing."""

    @property
    def name(self) -> str:
        return "provider_plugin"

    def get_services(self) -> dict[str, object]:
        return {
            "service1": "Service 1",
            "service2": "Service 2"
        }

    def get_service(self, name: str) -> object | None:
        return self.get_services().get(name)


class TestPluginRegistry:
    """Tests for the PluginRegistry class."""

    def test_init(self) -> None:
        """Test initializing the registry."""
        registry = PluginRegistry()
        assert registry._plugins == {}
        assert registry._command_plugins == {}
        assert registry._workflow_plugins == {}
        assert registry._extension_plugins == {}
        assert registry._provider_plugins == {}
        assert registry._extensions == {}
        assert registry._commands == {}
        assert registry._workflows == {}

    def test_register_basic_plugin(self) -> None:
        """Test registering a basic plugin."""
        registry = PluginRegistry()
        plugin = BasicPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin

        # Test registering duplicate (should raise)
        with pytest.raises(QuackPluginError):
            registry.register(plugin)

    def test_register_command_plugin(self) -> None:
        """Test registering a command plugin."""
        registry = PluginRegistry()
        plugin = CommandPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin
        assert registry._command_plugins[plugin.name] is plugin

        # Check command registration
        for cmd in plugin.list_commands():
            assert registry._commands[cmd] is plugin

    def test_register_workflow_plugin(self) -> None:
        """Test registering a workflow plugin."""
        registry = PluginRegistry()
        plugin = WorkflowPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin
        assert registry._workflow_plugins[plugin.name] is plugin

        # Check workflow registration
        for wf in plugin.list_workflows():
            assert registry._workflows[wf] is plugin

    def test_register_extension_plugin(self) -> None:
        """Test registering an extension plugin."""
        registry = PluginRegistry()
        plugin = ExtensionPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin
        assert registry._extension_plugins[plugin.name] is plugin

        # Check extension registration for target
        target = plugin.get_target_plugin()
        assert plugin in registry._extensions[target]

    def test_register_provider_plugin(self) -> None:
        """Test registering a provider plugin."""
        registry = PluginRegistry()
        plugin = ProviderPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin
        assert registry._provider_plugins[plugin.name] is plugin

    def test_register_multiple_types(self) -> None:
        """Test registering a plugin that implements multiple protocols."""

        # Create a plugin with multiple interfaces
        class MultiPlugin(CommandPluginProtocol, WorkflowPluginProtocol):
            @property
            def name(self) -> str:
                return "multi_plugin"

            def list_commands(self) -> list[str]:
                return ["cmd1", "cmd2"]

            def get_command(self, name: str) -> callable | None:
                return lambda: f"Command {name}"

            def execute_command(self, name: str, *args: object,
                                **kwargs: object) -> str:
                return f"Executed {name}"

            def list_workflows(self) -> list[str]:
                return ["flow1", "flow2"]

            def get_workflow(self, name: str) -> callable | None:
                return lambda: f"Workflow {name}"

            def execute_workflow(self, name: str, *args: object,
                                 **kwargs: object) -> str:
                return f"Ran {name}"

        registry = PluginRegistry()
        plugin = MultiPlugin()

        registry.register(plugin)
        assert registry._plugins[plugin.name] is plugin
        assert registry._command_plugins[plugin.name] is plugin
        assert registry._workflow_plugins[plugin.name] is plugin

        # Check command registration
        for cmd in plugin.list_commands():
            assert registry._commands[cmd] is plugin

        # Check workflow registration
        for wf in plugin.list_workflows():
            assert registry._workflows[wf] is plugin

    def test_command_override(self) -> None:
        """Test that newer command plugins override older ones for the same command."""
        registry = PluginRegistry()

        # Create two command plugins with overlapping commands
        class Plugin1(CommandPluginProtocol):
            @property
            def name(self) -> str:
                return "plugin1"

            def list_commands(self) -> list[str]:
                return ["common", "cmd1"]

            def get_command(self, name: str) -> callable | None:
                return lambda: f"Plugin1 {name}"

            def execute_command(self, name: str, *args: object,
                                **kwargs: object) -> str:
                return f"Plugin1 executed {name}"

        class Plugin2(CommandPluginProtocol):
            @property
            def name(self) -> str:
                return "plugin2"

            def list_commands(self) -> list[str]:
                return ["common", "cmd2"]

            def get_command(self, name: str) -> callable | None:
                return lambda: f"Plugin2 {name}"

            def execute_command(self, name: str, *args: object,
                                **kwargs: object) -> str:
                return f"Plugin2 executed {name}"

        plugin1 = Plugin1()
        plugin2 = Plugin2()

        # Register first plugin
        registry.register(plugin1)
        assert registry._commands["common"] is plugin1
        assert registry._commands["cmd1"] is plugin1

        # Register second plugin (should override common command)
        registry.register(plugin2)
        assert registry._commands["common"] is plugin2
        assert registry._commands["cmd1"] is plugin1
        assert registry._commands["cmd2"] is plugin2

    def test_workflow_override(self) -> None:
        """Test that newer workflow plugins override older ones for the same workflow."""
        registry = PluginRegistry()

        # Create two workflow plugins with overlapping workflows
        class Plugin1(WorkflowPluginProtocol):
            @property
            def name(self) -> str:
                return "plugin1"

            def list_workflows(self) -> list[str]:
                return ["common", "flow1"]

            def get_workflow(self, name: str) -> callable | None:
                return lambda: f"Plugin1 {name}"

            def execute_workflow(self, name: str, *args: object,
                                 **kwargs: object) -> str:
                return f"Plugin1 ran {name}"

        class Plugin2(WorkflowPluginProtocol):
            @property
            def name(self) -> str:
                return "plugin2"

            def list_workflows(self) -> list[str]:
                return ["common", "flow2"]

            def get_workflow(self, name: str) -> callable | None:
                return lambda: f"Plugin2 {name}"

            def execute_workflow(self, name: str, *args: object,
                                 **kwargs: object) -> str:
                return f"Plugin2 ran {name}"

        plugin1 = Plugin1()
        plugin2 = Plugin2()

        # Register first plugin
        registry.register(plugin1)
        assert registry._workflows["common"] is plugin1
        assert registry._workflows["flow1"] is plugin1

        # Register second plugin (should override common workflow)
        registry.register(plugin2)
        assert registry._workflows["common"] is plugin2
        assert registry._workflows["flow1"] is plugin1
        assert registry._workflows["flow2"] is plugin2

    def test_unregister_plugin(self) -> None:
        """Test unregistering a plugin."""
        registry = PluginRegistry()

        # Register different types of plugins
        basic = BasicPlugin()
        command = CommandPlugin()
        workflow = WorkflowPlugin()
        extension = ExtensionPlugin()
        provider = ProviderPlugin()

        registry.register(basic)
        registry.register(command)
        registry.register(workflow)
        registry.register(extension)
        registry.register(provider)

        # Unregister basic plugin
        registry.unregister(basic.name)
        assert basic.name not in registry._plugins

        # Unregister command plugin
        registry.unregister(command.name)
        assert command.name not in registry._plugins
        assert command.name not in registry._command_plugins
        for cmd in command.list_commands():
            assert cmd not in registry._commands

        # Unregister workflow plugin
        registry.unregister(workflow.name)
        assert workflow.name not in registry._plugins
        assert workflow.name not in registry._workflow_plugins
        for wf in workflow.list_workflows():
            assert wf not in registry._workflows

        # Unregister extension plugin
        registry.unregister(extension.name)
        assert extension.name not in registry._plugins
        assert extension.name not in registry._extension_plugins
        target = extension.get_target_plugin()
        assert extension not in registry._extensions.get(target, [])

        # Unregister provider plugin
        registry.unregister(provider.name)
        assert provider.name not in registry._plugins
        assert provider.name not in registry._provider_plugins

        # Test unregistering non-existent plugin
        with pytest.raises(QuackPluginError):
            registry.unregister("nonexistent_plugin")

    def test_execute_command(self) -> None:
        """Test executing a command through the registry."""
        registry = PluginRegistry()
        plugin = CommandPlugin()
        registry.register(plugin)

        # Test executing a registered command
        result = registry.execute_command("cmd1")
        assert result == "Executed cmd1"

        # Test with arguments
        result = registry.execute_command("cmd2", "arg1", key="value")
        assert result == "Executed cmd2"

        # Test executing non-existent command
        with pytest.raises(QuackPluginError):
            registry.execute_command("nonexistent")

    def test_execute_workflow(self) -> None:
        """Test executing a workflow through the registry."""
        registry = PluginRegistry()
        plugin = WorkflowPlugin()
        registry.register(plugin)

        # Test executing a registered workflow
        result = registry.execute_workflow("flow1")
        assert result == "Ran flow1"

        # Test with arguments
        result = registry.execute_workflow("flow2", "arg1", key="value")
        assert result == "Ran flow2"

        # Test executing non-existent workflow
        with pytest.raises(QuackPluginError):
            registry.execute_workflow("nonexistent")

    def test_plugin_getters(self) -> None:
        """Test getting plugins from the registry."""
        registry = PluginRegistry()

        # Register different types of plugins
        basic = BasicPlugin()
        command = CommandPlugin()
        workflow = WorkflowPlugin()
        extension = ExtensionPlugin()
        provider = ProviderPlugin()

        registry.register(basic)
        registry.register(command)
        registry.register(workflow)
        registry.register(extension)
        registry.register(provider)

        # Test get_plugin
        assert registry.get_plugin(basic.name) is basic
        assert registry.get_plugin("nonexistent") is None

        # Test get_command_plugin
        assert registry.get_command_plugin(command.name) is command
        assert registry.get_command_plugin(basic.name) is None

        # Test get_workflow_plugin
        assert registry.get_workflow_plugin(workflow.name) is workflow
        assert registry.get_workflow_plugin(basic.name) is None

        # Test get_extension_plugin
        assert registry.get_extension_plugin(extension.name) is extension
        assert registry.get_extension_plugin(basic.name) is None

        # Test get_provider_plugin
        assert registry.get_provider_plugin(provider.name) is provider
        assert registry.get_provider_plugin(basic.name) is None

    def test_list_plugins(self) -> None:
        """Test listing plugins."""
        registry = PluginRegistry()

        # Register different types of plugins
        basic = BasicPlugin()
        command = CommandPlugin()
        workflow = WorkflowPlugin()

        registry.register(basic)
        registry.register(command)
        registry.register(workflow)

        # Test list_plugins
        assert set(registry.list_plugins()) == {basic.name, command.name, workflow.name}

        # Test list_command_plugins
        assert set(registry.list_command_plugins()) == {command.name}

        # Test list_workflow_plugins
        assert set(registry.list_workflow_plugins()) == {workflow.name}

        # Test list_commands
        assert set(registry.list_commands()) == set(command.list_commands())

        # Test list_workflows
        assert set(registry.list_workflows()) == set(workflow.list_workflows())

    def test_is_registered(self) -> None:
        """Test checking if a plugin is registered."""
        registry = PluginRegistry()
        plugin = BasicPlugin()

        assert not registry.is_registered(plugin.name)

        registry.register(plugin)
        assert registry.is_registered(plugin.name)

        registry.unregister(plugin.name)
        assert not registry.is_registered(plugin.name)

    def test_get_command_plugin_for_command(self) -> None:
        """Test getting the plugin that provides a command."""
        registry = PluginRegistry()
        plugin = CommandPlugin()
        registry.register(plugin)

        assert registry.get_command_plugin_for_command("cmd1") is plugin
        assert registry.get_command_plugin_for_command("nonexistent") is None

    def test_get_workflow_plugin_for_workflow(self) -> None:
        """Test getting the plugin that provides a workflow."""
        registry = PluginRegistry()
        plugin = WorkflowPlugin()
        registry.register(plugin)

        assert registry.get_workflow_plugin_for_workflow("flow1") is plugin
        assert registry.get_workflow_plugin_for_workflow("nonexistent") is None

    def test_get_extensions_for_plugin(self) -> None:
        """Test getting extensions for a target plugin."""
        registry = PluginRegistry()
        extension1 = ExtensionPlugin()

        # Create another extension targeting the same plugin
        class Extension2(ExtensionPluginProtocol):
            @property
            def name(self) -> str:
                return "extension2"

            def get_target_plugin(self) -> str:
                return "target_plugin"

            def get_extensions(self) -> dict[str, callable]:
                return {"ext3": lambda: "Extension 3"}

        extension2 = Extension2()

        registry.register(extension1)
        registry.register(extension2)

        # Test getting extensions for the target
        extensions = registry.get_extensions_for_plugin("target_plugin")
        assert len(extensions) == 2
        assert extension1 in extensions
        assert extension2 in extensions

        # Test getting extensions for non-existent target
        assert registry.get_extensions_for_plugin("nonexistent") == []