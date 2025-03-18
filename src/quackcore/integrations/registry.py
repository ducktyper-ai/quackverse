"""
Registry for QuackCore integrations.

This module provides a registry for discovering and managing integrations,
allowing for dynamic loading and access to integration services.

This implementation uses native collection types (list, dict), the pipe operator
for unions, and explicit return type annotations throughout. It also factors
out helper functions to reduce complexity, in line with best practices for Python 3.13.
"""

import importlib
import logging
import sys
from collections.abc import Iterable
from importlib.metadata import EntryPoint  # type: ignore
from typing import Protocol, TypeVar

from quackcore.errors import QuackError
from quackcore.integrations.protocols import IntegrationProtocol

T = TypeVar("T", bound=IntegrationProtocol)


class PluginLoaderProtocol(Protocol):
    def load_plugin(self, identifier: str) -> object:
        """
        Load a plugin given its identifier.
        """
        ...


class IntegrationRegistry:
    """Registry for QuackCore integrations."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize the integration registry.

        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self._integrations: dict[str, IntegrationProtocol] = {}

    def register(self, integration: IntegrationProtocol) -> None:
        """
        Register an integration with the registry.

        Args:
            integration: Integration to register

        Raises:
            QuackError: If the integration is already registered
        """
        integration_name = integration.name
        if integration_name in self._integrations:
            raise QuackError(
                f"Integration '{integration_name}' is already registered",
                {"integration_name": integration_name},
            )
        self._integrations[integration_name] = integration
        self.logger.debug(f"Registered integration: {integration_name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister an integration from the registry.

        Args:
            name: Name of the integration to unregister

        Returns:
            bool: True if the integration was unregistered, False if not found
        """
        if name in self._integrations:
            del self._integrations[name]
            self.logger.debug(f"Unregistered integration: {name}")
            return True

        self.logger.warning(f"Integration not found for unregistration: {name}")
        return False

    def get_integration(self, name: str) -> IntegrationProtocol | None:
        """
        Get an integration by name.

        Args:
            name: Name of the integration to get

        Returns:
            IntegrationProtocol | None: The integration if found, else None
        """
        return self._integrations.get(name)

    def get_integration_by_type(self, integration_type: type[T]) -> Iterable[T]:
        """
        Get all integrations of a specific type.

        Args:
            integration_type: Type of integrations to get

        Returns:
            Iterable[T]: Integrations of the specified type
        """
        for integration in self._integrations.values():
            if isinstance(integration, integration_type):
                yield integration

    def list_integrations(self) -> list[str]:
        """
        Get a list of all registered integration names.

        Returns:
            list[str]: List of integration names
        """
        return list(self._integrations.keys())

    def is_registered(self, name: str) -> bool:
        """
        Check if an integration is registered.

        Args:
            name: Name of the integration

        Returns:
            bool: True if the integration is registered
        """
        return name in self._integrations

    def discover_integrations(self) -> list[IntegrationProtocol]:
        """
        Discover integrations from entry points.

        Returns:
            list[IntegrationProtocol]: Discovered integrations
        """
        discovered_integrations: list[IntegrationProtocol] = []
        plugin_loader: PluginLoaderProtocol | None = self._get_plugin_loader()
        entry_points_list: list[EntryPoint] = self._get_entry_points(
            "quackcore.integrations"
        )

        for entry in entry_points_list:
            integration = self._load_integration_from_entry(entry, plugin_loader)
            if integration is not None:
                try:
                    self.register(integration)
                    discovered_integrations.append(integration)
                except QuackError as err:
                    self.logger.error(
                        f"Error registering integration {entry.name}: {err}"
                    )

        return discovered_integrations

    def load_integration_module(self, module_path: str) -> list[IntegrationProtocol]:
        """
        Load integrations from a module.

        Args:
            module_path: Path to the module

        Returns:
            list[IntegrationProtocol]: Loaded integrations

        Raises:
            QuackError: If module cannot be loaded or contains no integrations
        """
        loaded_integrations: list[IntegrationProtocol] = []
        plugin_loader: PluginLoaderProtocol | None = self._get_plugin_loader()

        # Try to load using the plugin loader first
        integration = self._load_integration_with_plugin_loader(
            module_path, plugin_loader
        )
        if integration is not None:
            try:
                self.register(integration)
                loaded_integrations.append(integration)
                return loaded_integrations
            except QuackError as err:
                self.logger.error(
                    f"Error registering integration from plugin loader: {err}"
                )

        # Fallback to manual module loading
        try:
            if module_path in sys.modules:
                module = sys.modules[module_path]
            else:
                module = importlib.import_module(module_path)
        except ImportError as e:
            error_msg = f"Failed to import module {module_path}: {e}"
            self.logger.error(error_msg)
            raise QuackError(
                error_msg,
                {"module_path": module_path, "error": str(e)},
                original_error=e,
            ) from e

        # Try to load using a factory function
        integration = self._load_integration_from_factory(module)
        if integration is not None:
            try:
                self.register(integration)
                loaded_integrations.append(integration)
                return loaded_integrations
            except QuackError as err:
                self.logger.error(
                    f"Error registering integration from create_integration: {err}"
                )

        # Otherwise, search for integration classes defined in the module
        integrations_from_module = self._load_integrations_from_module(module)
        for integ in integrations_from_module:
            try:
                self.register(integ)
                loaded_integrations.append(integ)
            except QuackError as err:
                self.logger.error(f"Error registering integration {integ.name}: {err}")

        if not loaded_integrations:
            self.logger.warning(f"No integrations found in module {module_path}")

        return loaded_integrations

    # Helper methods to reduce complexity

    def _get_plugin_loader(self) -> PluginLoaderProtocol | None:
        """
        Retrieve QuackCore's plugin loader if available.

        Returns:
            PluginLoaderProtocol or None if not available.
        """
        try:
            from quackcore.plugins.discovery import loader as plugin_loader

            return plugin_loader  # type: ignore
        except ImportError:
            self.logger.debug(
                "QuackCore plugin discovery not available, using fallback method"
            )
            return None

    def _get_entry_points(self, group: str) -> list[EntryPoint]:
        """
        Retrieve entry points for a given group.

        Args:
            group: The entry point group to search

        Returns:
            list[EntryPoint]: A list of entry point objects
        """
        try:
            from importlib.metadata import entry_points

            eps = entry_points(group=group)
            return list(eps)
        except Exception as e:
            self.logger.warning(
                f"Could not discover integrations using entry points: {e}"
            )
            return []

    def _load_integration_from_entry(
        self, entry: EntryPoint, plugin_loader: PluginLoaderProtocol | None
    ) -> IntegrationProtocol | None:
        """
        Load an integration from a given entry point.

        Args:
            entry: The entry point object
            plugin_loader: The plugin loader to use (if any)

        Returns:
            IntegrationProtocol instance if loaded successfully, else None.
        """
        try:
            self.logger.debug(f"Loading integration from entry point: {entry.name}")
            if plugin_loader is not None:
                try:
                    plugin = plugin_loader.load_plugin(entry.value)
                    if isinstance(plugin, IntegrationProtocol):
                        return plugin
                except (ImportError, AttributeError) as e:
                    self.logger.debug(
                        f"Plugin loader failed for {entry.name}: {e}, falling back"
                    )
            # Fall back to standard approach
            factory = entry.load()
            if callable(factory):
                integration = factory()
                if isinstance(integration, IntegrationProtocol):
                    return integration
                self.logger.warning(
                    f"Entry point {entry.name} did not return an IntegrationProtocol"
                )
            else:
                self.logger.warning(f"Entry point {entry.name} factory is not callable")
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to import integration from {entry.name}: {e}")
        except TypeError as e:
            self.logger.error(f"Type error loading integration from {entry.name}: {e}")
        except ValueError as e:
            self.logger.error(f"Value error loading integration from {entry.name}: {e}")
        except Exception as e:
            self.logger.error(
                f"Unexpected error loading integration from {entry.name}: {e}"
            )
        return None

    def _load_integration_with_plugin_loader(
        self, module_path: str, plugin_loader: PluginLoaderProtocol | None
    ) -> IntegrationProtocol | None:
        """
        Attempt to load an integration from a module using the plugin loader.

        Args:
            module_path: The module path to load
            plugin_loader: The plugin loader to use

        Returns:
            IntegrationProtocol instance if successful, else None.
        """
        if plugin_loader is not None:
            try:
                plugin = plugin_loader.load_plugin(module_path)
                if isinstance(plugin, IntegrationProtocol):
                    return plugin
            except (ImportError, AttributeError) as e:
                self.logger.debug(
                    f"Could not load module {module_path} using plugin loader: {e}"
                )
            except (TypeError, ValueError) as e:
                self.logger.debug(f"Plugin loader error for {module_path}: {e}")
        return None

    def _load_integration_from_factory(
        self, module: object
    ) -> IntegrationProtocol | None:
        """
        Attempt to load an integration via a factory function
        named 'create_integration' in the module.

        Args:
            module: The module object

        Returns:
            IntegrationProtocol instance if successful, else None.
        """
        if hasattr(module, "create_integration"):
            create_func = module.create_integration  # Direct attribute access
            if callable(create_func):
                try:
                    integration = create_func()
                    if isinstance(integration, IntegrationProtocol):
                        return integration
                except (TypeError, ValueError) as e:
                    self.logger.error(
                        f"Error calling create_integration in {module.__name__}: {e}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error in "
                        f"create_integration for {module.__name__}: {e}"
                    )
        return None

    def _load_integrations_from_module(
        self, module: object
    ) -> list[IntegrationProtocol]:
        """
        Search the module for integration classes that are defined within it.

        Args:
            module: The module object

        Returns:
            list[IntegrationProtocol]: List of instantiated integrations
        """
        integrations: list[IntegrationProtocol] = []
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, IntegrationProtocol)
                and attr.__module__ == module.__name__
                and attr is not IntegrationProtocol
            ):
                try:
                    integration = attr()
                    integrations.append(integration)
                except (TypeError, ValueError) as e:
                    self.logger.error(f"Error instantiating {attr_name}: {e}")
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error instantiating {attr_name}: {e}"
                    )
        return integrations
