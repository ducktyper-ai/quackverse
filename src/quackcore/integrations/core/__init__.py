# src/quackcore/integrations/__init__.py
"""
Integrations package for QuackCore.

This package provides a framework for connecting QuackCore to external services
and platforms, with a modular approach that allows for community contributions.
"""

import logging

from quackcore.integrations.core.base import (
    BaseAuthProvider,
    BaseConfigProvider,
    BaseIntegrationService,
)
from quackcore.integrations.core.protocols import (
    AuthProviderProtocol,
    ConfigProviderProtocol,
    IntegrationProtocol,
    StorageIntegrationProtocol,
)
from quackcore.integrations.core.registry import IntegrationRegistry
from quackcore.integrations.core.results import AuthResult, ConfigResult, IntegrationResult

# Create a global registry instance
registry = IntegrationRegistry()

# Initialize by discovering integrations
try:
    registry.discover_integrations()
except Exception as e:
    logging.getLogger(__name__).warning(f"Error discovering integrations: {e}")

__all__ = [
    # Base classes
    "BaseAuthProvider",
    "BaseConfigProvider",
    "BaseIntegrationService",
    # Protocols
    "AuthProviderProtocol",
    "ConfigProviderProtocol",
    "IntegrationProtocol",
    "StorageIntegrationProtocol",
    # Results
    "AuthResult",
    "ConfigResult",
    "IntegrationResult",
    # Registry
    "IntegrationRegistry",
    "registry",
]