"""
Plugin discovery for QuackCore.

This module provides utilities for discovering and loading plugins
from entry points and module paths.

In line with Python 3.13 best practices, we use native types, pydantic
for model validation, and favor collections.abc over typing where possible.
"""

import importlib
import inspect
import logging

from pydantic import BaseModel, ValidationError

from quackcore.errors import QuackPluginError
from quackcore.plugins.protocols import QuackPluginProtocol


class PluginInfo(BaseModel):
    name: str


class PluginLoader:
    """Loader for QuackCore plugins."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize the plugin loader.

        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    def _validate_plugin(
        self, plugin: QuackPluginProtocol, module_path: str
    ) -> QuackPluginProtocol:
        """
        Validate that the plugin has the required attributes using pydantic.

        Args:
            plugin: The plugin instance to validate.
            module_path: The module path from which the plugin was loaded.

        Returns:
            The validated plugin instance.

        Raises:
            QuackPluginError: If validation fails.
        """
        try:
            PluginInfo(name=plugin.name)
        except ValidationError as e:
            raise QuackPluginError(
                f"Plugin from module {module_path} "
                f"does not have valid plugin info: {e}",
                plugin_path=module_path,
            ) from e
        return plugin

    def _load_from_factory(
        self, module: object, module_path: str
    ) -> QuackPluginProtocol | None:
        """
        Attempt to load a plugin using factory functions defined in the module.

        Args:
            module: The imported module.
            module_path: The module path.

        Returns:
            The loaded plugin if found, otherwise None.
        """
        for func_name in ("create_plugin", "create_integration"):
            if func_name in getattr(module, "__dict__", {}):
                factory = getattr(module, func_name)
                if callable(factory):
                    try:
                        plugin = factory()
                        plugin = self._validate_plugin(plugin, module_path)
                        self.logger.info(
                            f"Loaded plugin {plugin.name} from "
                            f"module {module_path} using factory {func_name}"
                        )
                        return plugin
                    except Exception as e:
                        self.logger.error(
                            f"Error in factory function {func_name} "
                            f"in module {module_path}: {e}"
                        )
        return None

    def _load_from_class(
        self, module: object, module_path: str
    ) -> QuackPluginProtocol | None:
        """
        Attempt to load a plugin by searching for specific classes in the module.

        Args:
            module: The imported module.
            module_path: The module path.

        Returns:
            The loaded plugin if found, otherwise None.
        """
        for class_name in ("MockPlugin", "MockIntegration"):
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name == class_name:
                    try:
                        plugin = obj()
                        plugin = self._validate_plugin(plugin, module_path)
                        self.logger.info(
                            f"Loaded plugin {plugin.name} from "
                            f"module {module_path} using class {class_name}"
                        )
                        return plugin
                    except Exception as e:
                        self.logger.error(
                            f"Error initializing plugin class {name} "
                            f"in module {module_path}: {e}"
                        )
        return None

    def _load_from_dict(
        self, module: object, module_path: str
    ) -> QuackPluginProtocol | None:
        """
        As a fallback, attempt to load a plugin
        by directly checking the module's __dict__.

        Args:
            module: The imported module.
            module_path: The module path.

        Returns:
            The loaded plugin if found, otherwise None.
        """
        for attr in ("MockPlugin", "MockIntegration"):
            if attr in getattr(module, "__dict__", {}):
                try:
                    plugin_class = getattr(module, attr)
                    plugin = plugin_class()
                    plugin = self._validate_plugin(plugin, module_path)
                    self.logger.info(
                        f"Loaded plugin {plugin.name} from "
                        f"module {module_path} using attribute {attr}"
                    )
                    return plugin
                except Exception as e:
                    self.logger.error(
                        f"Error initializing plugin from "
                        f"attribute {attr} in module {module_path}: {e}"
                    )
        return None

    def load_plugin(self, module_path: str) -> QuackPluginProtocol:
        """
        Load a plugin (or integration) from a module path.

        This method first searches for a factory function called either
        'create_plugin' or 'create_integration'. If neither is found, it
        searches for a class named "MockPlugin" or "MockIntegration", and finally
        checks the module's __dict__ for these attributes.

        Args:
            module_path: Path to the module containing the plugin.

        Returns:
            The loaded plugin.

        Raises:
            QuackPluginError: If the plugin cannot be loaded.
        """
        self.logger.debug(f"Loading plugin from module: {module_path}")
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise QuackPluginError(
                f"Failed to import module {module_path}: {e}",
                plugin_path=module_path,
                original_error=e,
            ) from e

        plugin: QuackPluginProtocol | None = self._load_from_factory(
            module, module_path
        )
        if plugin is not None:
            return plugin

        plugin = self._load_from_class(module, module_path)
        if plugin is not None:
            return plugin

        plugin = self._load_from_dict(module, module_path)
        if plugin is not None:
            return plugin

        raise QuackPluginError(
            f"No plugin found in module {module_path}",
            plugin_path=module_path,
        )

    def load_plugins(self, modules: list[str]) -> list[QuackPluginProtocol]:
        """
        Load multiple plugins from module paths.

        Args:
            modules: List of module paths.

        Returns:
            List of loaded plugins.
        """
        plugins: list[QuackPluginProtocol] = []
        for module_path in modules:
            try:
                plugin = self.load_plugin(module_path)
                plugins.append(plugin)
            except QuackPluginError as e:
                self.logger.error(
                    f"Failed to load plugin from module {module_path}: {e}"
                )
        return plugins

    def load_entry_points(
        self, group: str = "quackcore.plugins"
    ) -> list[QuackPluginProtocol]:
        """
        Load plugins from entry points.

        Args:
            group: Entry point group to load from.

        Returns:
            List of loaded plugins.
        """
        self.logger.debug(f"Loading plugins from entry points group: {group}")
        plugins: list[QuackPluginProtocol] = []
        try:
            discovered_eps: list = []
            try:
                from importlib.metadata import entry_points

                eps = entry_points(group=group)
                discovered_eps = list(eps)
            except (ImportError, AttributeError) as e:
                self.logger.debug(f"Error getting entry points: {e}")
                return plugins

            for ep in discovered_eps:
                try:
                    self.logger.debug(f"Loading entry point: {ep.name} from {ep.value}")
                    factory = ep.load()
                    if callable(factory):
                        plugin = factory()
                        plugin = self._validate_plugin(plugin, ep.value)
                        plugins.append(plugin)
                        self.logger.info(
                            f"Loaded plugin {plugin.name} from entry point {ep.name}"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to load entry point {ep.name}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading entry points: {e}")

        return plugins

    def discover_plugins(
        self,
        entry_point_group: str = "quackcore.plugins",
        additional_modules: list[str] | None = None,
    ) -> list[QuackPluginProtocol]:
        """
        Discover plugins from entry points and additional modules.

        Args:
            entry_point_group: Entry point group to load from.
            additional_modules: Additional module paths to load.

        Returns:
            List of discovered plugins.
        """
        plugins: list[QuackPluginProtocol] = self.load_entry_points(entry_point_group)
        if additional_modules is not None:
            module_plugins = self.load_plugins(additional_modules)
            plugins.extend(module_plugins)
        return plugins


# Global loader instance
loader = PluginLoader()
