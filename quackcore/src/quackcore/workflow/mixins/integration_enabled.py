# quackcore/workflow/mixins/integration_enabled.py
from __future__ import annotations

from typing import Generic, TypeVar

from quackcore.integrations.core import get_integration_service
from quackcore.integrations.core.protocols import BaseIntegrationService

T = TypeVar("T", bound=BaseIntegrationService)


class IntegrationEnabledMixin(Generic[T]):
    """
    Mixin that enables integration with a specified service type.
    Generically handles any integration service that matches the specified type.
    """
    _integration_service: T | None = None

    def resolve_integration(self, service_type: type[T]) -> T | None:
        """
        Lazily load and initialize an integration service.

        Args:
            service_type: The type of integration service to load.

        Returns:
            The initialized integration service, or None if unavailable.
        """
        if self._integration_service is None:
            self._integration_service = get_integration_service(service_type)
        if self._integration_service is not None and hasattr(self._integration_service,
                                                             "initialize"):
            self._integration_service.initialize()
        return self._integration_service

    def get_integration_service(self) -> T | None:
        """
        Return the integration service if available.

        Returns:
            The initialized integration service, or None if not initialized.
        """
        return self._integration_service
