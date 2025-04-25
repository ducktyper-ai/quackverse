# quackcore/tests/test_toolkit/test_mixins.py
"""
Tests for the QuackTool mixins.
"""

import unittest
from collections.abc import Generator
from typing import TypeVar
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.core import IntegrationResult
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.toolkit.mixins.env_init import ToolEnvInitializerMixin
from quackcore.toolkit.mixins.integration_enabled import IntegrationEnabledMixin
from quackcore.toolkit.mixins.lifecycle import QuackToolLifecycleMixin
from quackcore.toolkit.mixins.output_handler import OutputFormatMixin


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


T = TypeVar("T", bound=BaseIntegrationService)


class TestIntegrationEnabledMixin(unittest.TestCase):
    """
    Test cases for IntegrationEnabledMixin.
    """

    @patch("quackcore.integrations.core.get_integration_service")
    def test_resolve_integration(self, mock_get_integration: MagicMock) -> None:
        """
        Test that resolve_integration correctly resolves the integration service.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()
        mock_service = MockIntegrationService()
        mock_get_integration.return_value = mock_service

        # Test
        result = mixin.resolve_integration(MockIntegrationService)

        # Assertions
        self.assertEqual(result, mock_service)
        self.assertTrue(mock_service.initialized)
        mock_get_integration.assert_called_once_with(MockIntegrationService)

    @patch("quackcore.integrations.core.get_integration_service")
    def test_resolve_integration_none(self, mock_get_integration: MagicMock) -> None:
        """
        Test that resolve_integration handles None return from get_integration_service.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()
        mock_get_integration.return_value = None

        # Test
        result = mixin.resolve_integration(MockIntegrationService)

        # Assertions
        self.assertIsNone(result)
        mock_get_integration.assert_called_once_with(MockIntegrationService)

    @patch("quackcore.integrations.core.get_integration_service")
    def test_resolve_integration_no_initialize(self, mock_get_integration: MagicMock) -> None:
        """
        Test that resolve_integration works with a service that doesn't have initialize.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[AnotherMockService]):
            pass

        mixin = TestMixin()
        mock_service = AnotherMockService()
        mock_get_integration.return_value = mock_service

        # Test
        result = mixin.resolve_integration(AnotherMockService)

        # Assertions
        self.assertEqual(result, mock_service)
        mock_get_integration.assert_called_once_with(AnotherMockService)

    @patch("quackcore.integrations.core.get_integration_service")
    def test_integration_property(self, mock_get_integration: MagicMock) -> None:
        """
        Test that the integration property works correctly.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()
        mock_service = MockIntegrationService()
        mock_get_integration.return_value = mock_service

        # Test - first access should resolve
        result = mixin.integration

        # Assertions
        self.assertEqual(result, mock_service)
        mock_get_integration.assert_called_once_with(MockIntegrationService)

        # Reset mock
        mock_get_integration.reset_mock()

        # Test - second access should use cached value
        result2 = mixin.integration

        # Assertions
        self.assertEqual(result2, mock_service)
        mock_get_integration.assert_not_called()

    def test_get_integration_service(self) -> None:
        """
        Test that get_integration_service returns the cached service.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()
        mock_service = MockIntegrationService()
        mixin._integration_service = mock_service

        # Test
        result = mixin.get_integration_service()

        # Assertions
        self.assertEqual(result, mock_service)

    def test_get_integration_service_none(self) -> None:
        """
        Test that get_integration_service returns None when no service is cached.
        """

        # Setup
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()
        mixin._integration_service = None

        # Test
        result = mixin.get_integration_service()

        # Assertions
        self.assertIsNone(result)

    def test_generic_type_parameter(self) -> None:
        """
        Test that the generic type parameter is correctly used.
        """

        # Setup a mixin with a specific service type
        class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
            pass

        mixin = TestMixin()

        # Setup a mixin with a different service type
        class AnotherMixin(IntegrationEnabledMixin[AnotherMockService]):
            pass

        another_mixin = AnotherMixin()

        # Create services
        mock_service = MockIntegrationService()
        another_service = AnotherMockService()

        # Set the services directly to bypass resolution
        mixin._integration_service = mock_service
        another_mixin._integration_service = another_service

        # Test service from the first mixin
        result1 = mixin.get_integration_service()
        self.assertIsInstance(result1, MockIntegrationService)
        self.assertEqual(result1.name, "mock_service")

        # Test service from the second mixin
        result2 = another_mixin.get_integration_service()
        self.assertIsInstance(result2, AnotherMockService)
        self.assertEqual(result2.name, "another_service")


class TestOutputFormatMixin(unittest.TestCase):
    """
    Test cases for OutputFormatMixin.
    """

    def test_get_output_extension(self) -> None:
        """
        Test that _get_output_extension returns the default extension.
        """
        mixin = OutputFormatMixin()
        self.assertEqual(mixin._get_output_extension(), ".json")

    def test_get_output_writer(self) -> None:
        """
        Test that get_output_writer returns None by default.
        """
        mixin = OutputFormatMixin()
        self.assertIsNone(mixin.get_output_writer())


class TestToolEnvInitializerMixin(unittest.TestCase):
    """
    Test cases for ToolEnvInitializerMixin.
    """

    @patch("importlib.import_module")
    def test_initialize_environment_success(self, mock_import: MagicMock) -> None:
        """
        Test that _initialize_environment correctly initializes the environment.
        """
        # Setup
        mixin = ToolEnvInitializerMixin()
        mock_module = MagicMock()
        mock_module.initialize.return_value = None
        mock_import.return_value = mock_module

        # Test
        result = mixin._initialize_environment("test_tool")

        # Assertions
        self.assertTrue(result.success)
        self.assertIn("Successfully initialized test_tool", result.message)
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()

    @patch("importlib.import_module")
    def test_initialize_environment_with_result(self, mock_import: MagicMock) -> None:
        """
        Test that _initialize_environment returns IntegrationResult from initialize.
        """
        # Setup
        mixin = ToolEnvInitializerMixin()
        mock_module = MagicMock()

        custom_result = IntegrationResult.success_result(
            message="Custom initialization message"
        )

        mock_module.initialize.return_value = custom_result
        mock_import.return_value = mock_module

        # Test
        result = mixin._initialize_environment("test_tool")

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Custom initialization message")
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()

    @patch("importlib.import_module")
    def test_initialize_environment_no_initialize(self, mock_import: MagicMock) -> None:
        """
        Test that _initialize_environment handles modules without initialize.
        """
        # Setup
        mixin = ToolEnvInitializerMixin()
        mock_module = MagicMock(spec=[])  # No initialize method
        mock_import.return_value = mock_module

        # Test
        result = mixin._initialize_environment("test_tool")

        # Assertions
        self.assertTrue(result.success)
        self.assertIn("no initialize function found", result.message)
        mock_import.assert_called_once_with("test_tool")

    @patch("importlib.import_module")
    def test_initialize_environment_import_error(self, mock_import: MagicMock) -> None:
        """
        Test that _initialize_environment handles import errors.
        """
        # Setup
        mixin = ToolEnvInitializerMixin()
        mock_import.side_effect = ImportError("Module not found")

        # Test
        result = mixin._initialize_environment("test_tool")

        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Module not found")
        self.assertIn("Failed to import test_tool", result.message)
        mock_import.assert_called_once_with("test_tool")

    @patch("importlib.import_module")
    def test_initialize_environment_other_error(self, mock_import: MagicMock) -> None:
        """
        Test that _initialize_environment handles general exceptions during initialization.
        """
        # Setup
        mixin = ToolEnvInitializerMixin()
        mock_module = MagicMock()
        mock_module.initialize.side_effect = Exception("Initialization failed")
        mock_import.return_value = mock_module

        # Test
        result = mixin._initialize_environment("test_tool")

        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Initialization failed")
        self.assertIn("Error initializing test_tool", result.message)
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()


class TestQuackToolLifecycleMixin(unittest.TestCase):
    """
    Test cases for QuackToolLifecycleMixin.
    """

    def setUp(self) -> None:
        """
        Set up test fixtures.
        """
        self.mixin = QuackToolLifecycleMixin()

    def test_pre_run(self) -> None:
        """
        Test that pre_run returns a success result.
        """
        result = self.mixin.pre_run()
        self.assertTrue(result.success)
        self.assertIn("Pre-run completed", result.message)

    def test_post_run(self) -> None:
        """
        Test that post_run returns a success result.
        """
        result = self.mixin.post_run()
        self.assertTrue(result.success)
        self.assertIn("Post-run completed", result.message)

    def test_run(self) -> None:
        """
        Test that run returns a success result.
        """
        result = self.mixin.run()
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_run_with_options(self) -> None:
        """
        Test that run accepts options parameter.
        """
        options = {"test_option": "value"}
        result = self.mixin.run(options)
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_validate(self) -> None:
        """
        Test that validate returns a success result.
        """
        result = self.mixin.validate()
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_validate_with_paths(self) -> None:
        """
        Test that validate accepts path parameters.
        """
        result = self.mixin.validate("input.txt", "output.txt")
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_upload(self) -> None:
        """
        Test that upload returns a success result.
        """
        result = self.mixin.upload("test.txt")
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_upload_with_destination(self) -> None:
        """
        Test that upload accepts destination parameter.
        """
        result = self.mixin.upload("test.txt", "remote_destination")
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)


# Pytest-style tests for mixins

class CustomOutputFormatMixin(OutputFormatMixin):
    """Custom implementation of OutputFormatMixin for testing."""

    def _get_output_extension(self) -> str:
        return ".csv"


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
def integration_enabled_mixin() -> Generator[IntegrationEnabledMixin[MockIntegrationService], None, None]:
    """Fixture that creates an IntegrationEnabledMixin."""
    class TestMixin(IntegrationEnabledMixin[MockIntegrationService]):
        pass

    mixin = TestMixin()
    yield mixin


class TestMixinsWithPytest:
    """
    Test cases using pytest fixtures for the mixins.
    """

    def test_output_format_default_extension(self, output_format_mixin: OutputFormatMixin) -> None:
        """Test the default extension from OutputFormatMixin."""
        assert output_format_mixin._get_output_extension() == ".json"

    def test_output_format_custom_extension(self, custom_output_format_mixin: CustomOutputFormatMixin) -> None:
        """Test a custom extension from a subclass of OutputFormatMixin."""
        assert custom_output_format_mixin._get_output_extension() == ".csv"

    def test_output_format_writer(self, output_format_mixin: OutputFormatMixin) -> None:
        """Test that get_output_writer returns None by default."""
        assert output_format_mixin.get_output_writer() is None

    def test_lifecycle_pre_run(self, lifecycle_mixin: QuackToolLifecycleMixin) -> None:
        """Test pre_run with pytest fixture."""
        result = lifecycle_mixin.pre_run()
        assert result.success
        assert "Pre-run completed" in result.message

    def test_lifecycle_post_run(self, lifecycle_mixin: QuackToolLifecycleMixin) -> None:
        """Test post_run with pytest fixture."""
        result = lifecycle_mixin.post_run()
        assert result.success
        assert "Post-run completed" in result.message

    @patch("quackcore.integrations.core.get_integration_service")
    def test_integration_mixin_resolve(
        self,
        mock_get_integration: MagicMock,
        integration_enabled_mixin: IntegrationEnabledMixin[MockIntegrationService]
    ) -> None:
        """Test resolving an integration service."""
        # Setup
        mock_service = MockIntegrationService()
        mock_get_integration.return_value = mock_service

        # Test
        result = integration_enabled_mixin.resolve_integration(MockIntegrationService)

        # Assertions
        assert result == mock_service
        assert mock_service.initialized
        mock_get_integration.assert_called_once_with(MockIntegrationService)

    def test_integration_mixin_property(
        self,
        integration_enabled_mixin: IntegrationEnabledMixin[MockIntegrationService]
    ) -> None:
        """Test the integration property."""
        # Setup - set the service directly
        mock_service = MockIntegrationService()
        integration_enabled_mixin._integration_service = mock_service

        # Test
        result = integration_enabled_mixin.integration

        # Assertions
        assert result == mock_service

    @patch("importlib.import_module")
    def test_initialize_environment_success_pytest(self, mock_import: MagicMock, tool_env_initializer_mixin: ToolEnvInitializerMixin) -> None:
        """Test that _initialize_environment correctly initializes the environment."""
        # Setup
        mock_module = MagicMock()
        mock_module.initialize.return_value = None
        mock_import.return_value = mock_module

        # Test
        result = tool_env_initializer_mixin._initialize_environment("test_tool")

        # Assertions
        assert result.success
        assert "Successfully initialized test_tool" in result.message
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()

    @patch("importlib.import_module")
    def test_initialize_environment_with_result_pytest(self, mock_import: MagicMock, tool_env_initializer_mixin: ToolEnvInitializerMixin) -> None:
        """Test that _initialize_environment returns IntegrationResult from initialize."""
        # Setup
        mock_module = MagicMock()

        custom_result = IntegrationResult.success_result(
            message="Custom initialization message"
        )

        mock_module.initialize.return_value = custom_result
        mock_import.return_value = mock_module

        # Test
        result = tool_env_initializer_mixin._initialize_environment("test_tool")

        # Assertions
        assert result.success
        assert result.message == "Custom initialization message"
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()

    @patch("importlib.import_module")
    def test_initialize_environment_no_initialize_pytest(self, mock_import: MagicMock, tool_env_initializer_mixin: ToolEnvInitializerMixin) -> None:
        """Test that _initialize_environment handles modules without initialize."""
        # Setup
        mock_module = MagicMock(spec=[])  # No initialize method
        mock_import.return_value = mock_module

        # Test
        result = tool_env_initializer_mixin._initialize_environment("test_tool")

        # Assertions
        assert result.success
        assert "no initialize function found" in result.message
        mock_import.assert_called_once_with("test_tool")

    @patch("importlib.import_module")
    def test_initialize_environment_import_error_pytest(self, mock_import: MagicMock, tool_env_initializer_mixin: ToolEnvInitializerMixin) -> None:
        """Test that _initialize_environment handles import errors."""
        # Setup
        mock_import.side_effect = ImportError("Module not found")

        # Test
        result = tool_env_initializer_mixin._initialize_environment("test_tool")

        # Assertions
        assert not result.success
        assert result.error == "Module not found"
        assert "Failed to import test_tool" in result.message
        mock_import.assert_called_once_with("test_tool")

    @patch("importlib.import_module")
    def test_initialize_environment_other_error_pytest(self, mock_import: MagicMock, tool_env_initializer_mixin: ToolEnvInitializerMixin) -> None:
        """Test that _initialize_environment handles general exceptions during initialization."""
        # Setup
        mock_module = MagicMock()
        mock_module.initialize.side_effect = Exception("Initialization failed")
        mock_import.return_value = mock_module

        # Test
        result = tool_env_initializer_mixin._initialize_environment("test_tool")

        # Assertions
        assert not result.success
        assert result.error == "Initialization failed"
        assert "Error initializing test_tool" in result.message
        mock_import.assert_called_once_with("test_tool")
        mock_module.initialize.assert_called_once()
