# quack-core/src/quack-core/workflow/mixins/integration_enabled.py
from __future__ import annotations

from typing import Generic, TypeVar

from quackcore.integrations.core import get_integration_service
from quackcore.integrations.core.base import BaseIntegrationService

T = TypeVar("T", bound=BaseIntegrationService)


class IntegrationEnabledMixin(Generic[T]):
    """
    Mixin that enables integration with a specified service type.
    Generically handles any integration service that matches the specified type.
    """

    def __init__(self):
        """
        Initialize the mixin with an explicit _integration_service attribute.
        """
        self._integration_service = None

    def resolve_integration(self, service_type: type[T]) -> T | None:
        """
        Lazily load and initialize an integration service.

        Args:
            service_type: The type of integration service to load.

        Returns:
            The initialized integration service, or None if unavailable.
        """
        # Only fetch the service if not already loaded
        if self._integration_service is None:
            # Get the service instance using the imported function
            service = get_integration_service(service_type)

            # Initialize if available
            if service is not None:
                if hasattr(service, "initialize"):
                    service.initialize()

                # Only set the service after initialization
                self._integration_service = service

        return self._integration_service

    def get_integration_service(self) -> T | None:
        """
        Return the integration service if available.

        Returns:
            The initialized integration service, or None if not initialized.
        """
        return self._integration_service
