# quack-core/tests/test_toolkit/conftest.py
"""
Shared fixtures for QuackTool mixin tests.
"""

from collections.abc import Generator
from typing import TypeVar
from unittest.mock import patch

import pytest

from quack_core.integrations.core.base import BaseIntegrationService
from quack_core.toolkit.mixins.env_init import ToolEnvInitializerMixin
from quack_core.toolkit.mixins.integration_enabled import IntegrationEnabledMixin
from quack_core.toolkit.mixins.lifecycle import QuackToolLifecycleMixin
from quack_core.toolkit.mixins.output_handler import OutputFormatMixin


class MockIntegrationService(BaseIntegrationService):
    """
    Mock implementation of BaseIntegrationService for testing.
    """

    @property
    def name(self) -> str:
        return "mock_service"

    def __init__(self) -> None:
        super().__init__()
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True


class AnotherMockService(BaseIntegrationService):
    """
    Another mock implementation of BaseIntegrationService for testing.
    """

    @property
    def name(self) -> str:
        return "another_service"


class CustomOutputFormatMixin(OutputFormatMixin):
    """Custom implementation of OutputFormatMixin for testing."""

    def _get_output_extension(self) -> str:
        return ".csv"


T = TypeVar("T", bound=BaseIntegrationService)


@pytest.fixture
def output_format_mixin() -> OutputFormatMixin:
    """Fixture that creates an OutputFormatMixin."""
    return OutputFormatMixin()


@pytest.fixture
def custom_output_format_mixin() -> CustomOutputFormatMixin:
    """Fixture that creates a CustomOutputFormatMixin."""
    return CustomOutputFormatMixin()


@pytest.fixture
def tool_env_initializer_mixin() -> ToolEnvInitializerMixin:
    """Fixture that creates a ToolEnvInitializerMixin."""
    return ToolEnvInitializerMixin()


@pytest.fixture
def lifecycle_mixin() -> QuackToolLifecycleMixin:
    """Fixture that creates a QuackToolLifecycleMixin."""
    return QuackToolLifecycleMixin()


@pytest.fixture
def integration_enabled_mixin() -> Generator[
    IntegrationEnabledMixin[MockIntegrationService], None, None]:
    """Fixture that creates an IntegrationEnabledMixin."""

    class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
        pass

    with patch(
            "quack-core.integrations.core.get_integration_service") as mock_get_integration:
        # Set up the mock to return a MockIntegrationService
        mock_service = MockIntegrationService()
        mock_get_integration.return_value = mock_service

        mixin = TestMixin()
        # Now we need to manually call resolve_integration since the mixin
        # doesn't do this automatically in its __init__
        mixin.resolve_integration(MockIntegrationService)

        yield mixin
