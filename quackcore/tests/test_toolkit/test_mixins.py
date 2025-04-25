# quackcore/tests/test_toolkit/test_mixins.py
"""
Tests for the QuackTool mixins.
"""

import unittest
from unittest.mock import MagicMock, patch

from quackcore.integrations.core.protocols import BaseIntegrationService
from quackcore.toolkit import (
    IntegrationEnabledMixin,
    OutputFormatMixin,
    QuackToolLifecycleMixin,
    ToolEnvInitializerMixin,
)


class MockIntegrationService(BaseIntegrationService):
    """
    Mock implementation of BaseIntegrationService for testing.
    """

    def __init__(self):
        self.initialized = False

    def initialize(self):
        self.initialized = True


class TestIntegrationEnabledMixin(unittest.TestCase):
    """
    Test cases for IntegrationEnabledMixin.
    """

    @patch("quackcore.integrations.core.get_integration_service")
    def test_resolve_integration(self, mock_get_integration):
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
    def test_integration_property(self, mock_get_integration):
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


class TestOutputFormatMixin(unittest.TestCase):
    """
    Test cases for OutputFormatMixin.
    """

    def test_get_output_extension(self):
        """
        Test that _get_output_extension returns the default extension.
        """
        mixin = OutputFormatMixin()
        self.assertEqual(mixin._get_output_extension(), ".json")

    def test_get_output_writer(self):
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
    def test_initialize_environment_success(self, mock_import):
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
    def test_initialize_environment_no_initialize(self, mock_import):
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
    def test_initialize_environment_import_error(self, mock_import):
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


class TestQuackToolLifecycleMixin(unittest.TestCase):
    """
    Test cases for QuackToolLifecycleMixin.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.mixin = QuackToolLifecycleMixin()

    def test_pre_run(self):
        """
        Test that pre_run returns a success result.
        """
        result = self.mixin.pre_run()
        self.assertTrue(result.success)
        self.assertIn("Pre-run completed", result.message)

    def test_post_run(self):
        """
        Test that post_run returns a success result.
        """
        result = self.mixin.post_run()
        self.assertTrue(result.success)
        self.assertIn("Post-run completed", result.message)

    def test_run(self):
        """
        Test that run returns a success result.
        """
        result = self.mixin.run()
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_validate(self):
        """
        Test that validate returns a success result.
        """
        result = self.mixin.validate()
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)

    def test_upload(self):
        """
        Test that upload returns a success result.
        """
        result = self.mixin.upload("test.txt")
        self.assertTrue(result.success)
        self.assertIn("not implemented", result.message)


if __name__ == "__main__":
    unittest.main()
