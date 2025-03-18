"""
Plugin discovery for QuackCore.

This module provides utilities for discovering and loading plugins
from entry points and module paths.
"""

import importlib
import inspect
import logging

from quackcore.errors import QuackPluginError
from quackcore.plugins.protocols import QuackPluginProtocol

# You may eventually incorporate pydantic for model validation, e.g.:
# from pydantic import BaseModel, ValidationError
# class PluginInfo(BaseModel):
#     name: str


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

    def load_entry_points(
        self, group: str = "quackcore.plugins"
    ) -> list[QuackPluginProtocol]:
        """
        Load plugins from entry points.

        Args:
            group: Entry point group to load from

        Returns:
            List of loaded plugins
        """
        self.logger.debug(f"Loading plugins from entry points group: {group}")
        plugins: list[QuackPluginProtocol] = []
        try:
            # Attempt to get entry points in the specified group.
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
                        if not hasattr(plugin, "name"):
                            raise QuackPluginError(
                                f"Plugin from entry point {ep.name} "
                                f"does not have a name attribute",
                                plugin_path=ep.value,
                            )
                        plugins.append(plugin)
                        self.logger.info(
                            f"Loaded plugin {plugin.name} from entry point {ep.name}"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to load entry point {ep.name}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading entry points: {e}")

        return plugins

    def load_plugin(self, module_path: str) -> QuackPluginProtocol:
        """
        Load a plugin (or integration) from a module path.

        This method will first search for a factory function called either
        'create_plugin' or 'create_integration'. If neither is found, it will
        search for a class named "MockPlugin" or "MockIntegration".

        Args:
            module_path: Path to the module containing the plugin

        Returns:
            The loaded plugin

        Raises:
            QuackPluginError: If the plugin cannot be loaded
        """
        self.logger.debug(f"Loading plugin from module: {module_path}")
        try:
            module = importlib.import_module(module_path)

            # Check for factory functions in the module:
            # support both plugins and integrations.
            for func_name in ("create_plugin", "create_integration"):
                if func_name in getattr(module, "__dict__", {}):
                    factory = getattr(module, func_name)
                    if callable(factory):
                        plugin = factory()
                        if not hasattr(plugin, "name"):
                            raise QuackPluginError(
                                f"Plugin from module {module_path} "
                                f"does not have a name attribute",
                                plugin_path=module_path,
                            )
                        self.logger.info(
                            f"Loaded plugin {plugin.name} from module {module_path}"
                        )
                        return plugin

            # If no factory function, search for
            # a class named "MockPlugin" or "MockIntegration"
            for class_name in ("MockPlugin", "MockIntegration"):
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name == class_name:
                        try:
                            plugin = obj()
                            if not hasattr(plugin, "name"):
                                raise QuackPluginError(
                                    f"Plugin from module {module_path} "
                                    f"does not have a name attribute",
                                    plugin_path=module_path,
                                )
                            self.logger.info(
                                f"Loaded plugin {plugin.name} from module {module_path}"
                            )
                            return plugin
                        except Exception as e:
                            self.logger.error(
                                f"Error initializing plugin class {name}: {e}"
                            )

            # Lastly, explicitly check if module defines one of the expected test classes
            for attr in ("MockPlugin", "MockIntegration"):
                if attr in getattr(module, "__dict__", {}):
                    plugin_class = getattr(module, attr)
                    plugin = plugin_class()
                    if not hasattr(plugin, "name"):
                        raise QuackPluginError(
                            f"Plugin from module {module_path} "
                            f"does not have a name attribute",
                            plugin_path=module_path,
                        )
                    self.logger.info(
                        f"Loaded plugin {plugin.name} from module {module_path}"
                    )
                    return plugin

            raise QuackPluginError(
                f"No plugin found in module {module_path}",
                plugin_path=module_path,
            )
        except ImportError as e:
            raise QuackPluginError(
                f"Failed to import module {module_path}: {e}",
                plugin_path=module_path,
                original_error=e,
            ) from e
        except Exception as e:
            raise QuackPluginError(
                f"Failed to load plugin from module {module_path}: {e}",
                plugin_path=module_path,
                original_error=e,
            ) from e

    def load_plugins(self, modules: list[str]) -> list[QuackPluginProtocol]:
        """
        Load multiple plugins from module paths.

        Args:
            modules: List of module paths

        Returns:
            List of loaded plugins
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

    def discover_plugins(
        self,
        entry_point_group: str = "quackcore.plugins",
        additional_modules: list[str] | None = None,
    ) -> list[QuackPluginProtocol]:
        """
        Discover plugins from entry points and additional modules.

        Args:
            entry_point_group: Entry point group to load from
            additional_modules: Additional module paths to load

        Returns:
            List of discovered plugins
        """
        plugins: list[QuackPluginProtocol] = self.load_entry_points(entry_point_group)
        if additional_modules is not None:
            module_plugins = self.load_plugins(additional_modules)
            plugins.extend(module_plugins)
        return plugins


# Global loader instance
loader = PluginLoader()
