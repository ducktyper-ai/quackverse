# quackcore/src/quackcore/toolkit/mixins/integration_enabled.py
"""
Integration enabled mixin for QuackTool plugins.

This module provides a mixin that enables integration with various services
by providing a generic interface for resolving and accessing integration services.
"""

from typing import Any, Generic, TypeVar

# Import directly to ensure patching can work
import quackcore.integrations.core

from quackcore.integrations.core.base import BaseIntegrationService

T = TypeVar("T", bound=BaseIntegrationService)


class IntegrationEnabledMixin(Generic[T]):
    """
    Mixin that enables integration with a specified service type.

    This mixin provides a generic way to resolve and access integration
    services, such as GoogleDriveService, GitHubService, etc.

    Example:
        ```python
        class MyTool(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):
            def initialize_plugin(self):
                self._drive = self.resolve_integration(GoogleDriveService)
                # Now self._drive is a GoogleDriveService instance
        ```
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the mixin.

        This explicitly initializes the _integration_service to None
        to avoid issues with class variable sharing across instances.
        """
        # Set instance attribute (not class attribute)
        self._integration_service: T | None = None
        # Call parent __init__
        super().__init__(*args, **kwargs)

    def resolve_integration(self, service_type: type[T]) -> T | None:
        """
        Lazily load the integration service of the given type.

        Stores the result for reuse on subsequent calls.

        Args:
            service_type: The type of integration service to resolve

        Returns:
            T | None: The resolved integration service, or None if not available
        """
        # Use direct module reference to ensure patching works
        service = quackcore.integrations.core.get_integration_service(service_type)

        # Store the service for reuse
        self._integration_service = service

        # Initialize the service if it exists and has initialize method
        if service is not None and hasattr(service, "initialize") and callable(
                service.initialize):
            try:
                service.initialize()
            except Exception as e:
                if hasattr(self, "logger"):
                    self.logger.error(f"Failed to initialize integration service: {e}")

        # Return the service (could be None)
        return service

    def get_integration_service(self) -> T | None:
        """
        Get the resolved integration service.

        Returns:
            T | None: The resolved integration service, or None if not resolved yet
        """
        return self._integration_service

    @property
    def integration(self) -> T | None:
        """
        Shortcut to get the resolved integration service.

        Returns:
            T | None: The resolved integration service, or None if not resolved yet
        """
        return self.get_integration_service()