# tests/test_integrations/base/test_base.py
"""
Main entry point for base integration tests.

This file imports all the specific test modules to ensure they are discovered
by pytest when running the test suite.
"""

# Import test modules to ensure they are discovered by pytest
from tests.test_integrations.base.test_auth_provider import TestBaseAuthProvider
from tests.test_integrations.base.test_config_provider import TestBaseConfigProvider
from tests.test_integrations.base.test_config_provider_discovery import (
    TestBaseConfigProviderDiscovery,
)
from tests.test_integrations.base.test_integration_service import (
    TestBaseIntegrationService,
)

# Export the test classes for direct import
__all__ = [
    "TestBaseAuthProvider",
    "TestBaseConfigProvider",
    "TestBaseConfigProviderDiscovery",
    "TestBaseIntegrationService",
]
