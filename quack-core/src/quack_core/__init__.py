# quack-core/src/quack-core/__init__.py
"""
QuackCore: Core infrastructure for the Quack ecosystem of media production tools.

This library provides shared infrastructure for the QuackVerse ecosystem,
centralizing common functionality like path resolution, configuration management,
and plugin architecture to enable seamless integration between specialized tools.
"""

__version__ = "0.1.0"

# Re-export commonly used components for convenience
from quack_core.config import config
from quack_core.config.loader import load_config
from quack_core.config.models import QuackConfig
from quack_core.errors import (
    QuackApiError,
    QuackBaseAuthError,
    QuackError,
    QuackIntegrationError,
    QuackQuotaExceededError,
    wrap_io_errors,
)
from quack_core.fs import service as fs
from quack_core.integrations.core import IntegrationRegistry
from quack_core.integrations.core import registry as integration_registry
from quack_core.paths import resolver as paths
from quack_core.plugins import QuackPluginProtocol, loader, registry

__all__ = [
    # Version
    "__version__",
    # Config
    "config",
    "load_config",
    "QuackConfig",
    # Paths
    "paths",
    # Filesystem
    "fs",
    # Plugins
    "registry",
    "loader",
    "QuackPluginProtocol",
    # Integrations
    "integration_registry",
    "IntegrationRegistry",
    # Errors
    "QuackError",
    "QuackIntegrationError",
    "QuackApiError",
    "QuackBaseAuthError",
    "QuackQuotaExceededError",
    "wrap_io_errors",
]
