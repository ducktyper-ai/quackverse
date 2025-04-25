# quackcore/src/quackcore/toolkit/mixins/integration_enabled.py
"""
Integration enabled mixin for QuackTool plugins.

This module provides a mixin that enables integration with various services
by providing a generic interface for resolving and accessing integration services.
"""

from typing import Generic, TypeVar

from quackcore.integrations.core import get_integration_service
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
            def _initialize_plugin(self):
                self._drive = self.resolve_integration(GoogleDriveService)
                # Now self._drive is a GoogleDriveService instance
        ```
    """

    _integration_service: T | None = None

    def resolve_integration(self, service_type: type[T]) -> T | None:
        """
        Lazily load the integration service of the given type.

        Stores the result for reuse on subsequent calls.

        Args:
            service_type: The type of integration service to resolve

        Returns:
            T | None: The resolved integration service, or None if not available
        """
        # Get the service
        service = get_integration_service(service_type)

        # Store the service for reuse
        self._integration_service = service

        # Initialize the service if it has an initialize method
        if service and hasattr(service, "initialize"):
            service.initialize()

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
