# src/quackcore/integrations/registry.py
"""
Registry for QuackCore integrations.

This module provides a registry for discovering and managing integrations,
allowing for dynamic loading and access to integration services.
"""

import importlib
import logging
import sys
from collections.abc import Iterable
from typing import TypeVar

from quackcore.errors import QuackError
from quackcore.integrations.protocols import IntegrationProtocol

T = TypeVar("T", bound=IntegrationProtocol)


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
            IntegrationProtocol | None: The integration or None if not found
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
        discovered_integrations = []
        plugin_loader = None

        # Try to use QuackCore's plugin discovery mechanism
        try:
            from quackcore.plugins.discovery import loader as plugin_loader
        except ImportError:
            from quackcore.plugins.discovery import loader as plugin_loader

            self.logger.debug(
                "QuackCore plugin discovery not available, using fallback method"
            )

        try:
            from importlib.metadata import entry_points

            # Get entry points in the quackcore.integrations group
            integration_entries = entry_points(group="quackcore.integrations")

            for entry in integration_entries:
                try:
                    self.logger.debug(
                        f"Loading integration from entry point: {entry.name}"
                    )

                    # Try to use the plugin loader if available
                    if plugin_loader is not None:
                        try:
                            plugin = plugin_loader.load_plugin(entry.value)
                            if isinstance(plugin, IntegrationProtocol):
                                self.register(plugin)
                                discovered_integrations.append(plugin)
                                continue
                        except (ImportError, AttributeError) as e:
                            self.logger.debug(
                                f"Plugin loader failed for {entry.name}: {e}, falling back"
                            )

                    # Fall back to standard approach
                    factory = entry.load()
                    if callable(factory):
                        integration = factory()
                        if isinstance(integration, IntegrationProtocol):
                            self.register(integration)
                            discovered_integrations.append(integration)
                        else:
                            self.logger.warning(
                                f"Entry point {entry.name} did not return an IntegrationProtocol"
                            )
                except (ImportError, AttributeError) as e:
                    self.logger.error(
                        f"Failed to import integration from {entry.name}: {e}"
                    )
                except TypeError as e:
                    self.logger.error(
                        f"Type error loading integration from {entry.name}: {e}"
                    )
                except ValueError as e:
                    self.logger.error(
                        f"Value error loading integration from {entry.name}: {e}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error loading integration from {entry.name}: {e}"
                    )

        except (ImportError, AttributeError) as e:
            self.logger.warning(
                f"Could not discover integrations using entry points: {e}"
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
        loaded_integrations = []
        plugin_loader = None

        # Try to use QuackCore's plugin discovery if available
        try:
            from quackcore.plugins.discovery import loader as plugin_loader

            try:
                plugin = plugin_loader.load_plugin(module_path)
                if isinstance(plugin, IntegrationProtocol):
                    self.register(plugin)
                    return [plugin]
            except (ImportError, AttributeError) as e:
                self.logger.debug(
                    f"Could not load module {module_path} using plugin loader: {e}"
                )
            except (TypeError, ValueError) as e:
                self.logger.debug(f"Plugin loader error for {module_path}: {e}")
        except ImportError:
            from quackcore.plugins.discovery import loader as plugin_loader

            self.logger.debug("QuackCore plugin discovery not available")

        # Fallback to manual module loading
        try:
            # Check if module is already imported
            if module_path in sys.modules:
                module = sys.modules[module_path]
            else:
                module = importlib.import_module(module_path)

            # Look for create_integration factory
            if hasattr(module, "create_integration"):
                create_func = getattr(module, "create_integration")
                if callable(create_func):
                    try:
                        integration = create_func()
                        if isinstance(integration, IntegrationProtocol):
                            self.register(integration)
                            loaded_integrations.append(integration)
                            return loaded_integrations
                    except (TypeError, ValueError) as e:
                        self.logger.error(
                            f"Error calling create_integration in {module_path}: {e}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Unexpected error in create_integration for {module_path}: {e}"
                        )

            # Look for integrations defined in the module
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue

                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, IntegrationProtocol)
                    and attr.__module__ == module.__name__
                    and attr != IntegrationProtocol
                ):
                    try:
                        integration = attr()
                        self.register(integration)
                        loaded_integrations.append(integration)
                    except (TypeError, ValueError) as e:
                        self.logger.error(f"Error instantiating {attr_name}: {e}")
                    except Exception as e:
                        self.logger.error(
                            f"Unexpected error instantiating {attr_name}: {e}"
                        )

            if not loaded_integrations:
                self.logger.warning(f"No integrations found in module {module_path}")

            return loaded_integrations

        except ImportError as e:
            error_msg = f"Failed to import module {module_path}: {e}"
            self.logger.error(error_msg)
            raise QuackError(
                error_msg,
                {"module_path": module_path, "error": str(e)},
                original_error=e,
            ) from e
        except Exception as e:
            error_msg = f"Failed to load integrations from module {module_path}: {e}"
            self.logger.error(error_msg)
            raise QuackError(
                error_msg,
                {"module_path": module_path, "error": str(e)},
                original_error=e,
            ) from e
