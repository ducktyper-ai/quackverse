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

        try:
            from importlib.metadata import entry_points

            # Get entry points in the quackcore.integrations group
            integration_entries = entry_points(group="quackcore.integrations")

            for entry in integration_entries:
                try:
                    self.logger.debug(
                        f"Loading integration from entry point: {entry.name}"
                    )
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
                except Exception as e:
                    self.logger.error(
                        f"Failed to load integration from {entry.name}: {e}"
                    )

        except (ImportError, AttributeError) as e:
            self.logger.warning(f"Could not discover integrations: {e}")

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
                    integration = create_func()
                    if isinstance(integration, IntegrationProtocol):
                        self.register(integration)
                        loaded_integrations.append(integration)
                        return loaded_integrations

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
                    except Exception as e:
                        self.logger.error(f"Error instantiating {attr_name}: {e}")

            if not loaded_integrations:
                self.logger.warning(f"No integrations found in module {module_path}")

            return loaded_integrations

        except Exception as e:
            self.logger.error(
                f"Failed to load integrations from module {module_path}: {e}"
            )
            raise QuackError(
                f"Failed to load integrations from module {module_path}",
                {"module_path": module_path, "error": str(e)},
                original_error=e,
            ) from e
