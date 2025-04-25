"""
Tests for the BaseQuackToolPlugin class.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import pytest

from quackcore.integrations.core import IntegrationResult
from quackcore.toolkit import BaseQuackToolPlugin


class DummyQuackTool(BaseQuackToolPlugin):
    """
    Dummy implementation of BaseQuackToolPlugin for testing.
    """

    def __init__(self):
        super().__init__("dummy_tool", "1.0.0")

    def initialize_plugin(self):
        # No-op for testing
        pass

    def process_content(self, content, options):
        # Simple echo for testing
        return {"content": content, "options": options}


class TestBaseQuackToolPlugin(unittest.TestCase):
    """
    Test cases for BaseQuackToolPlugin.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.tool = DummyQuackTool()

        # Create a temp file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b'{"test": "data"}')
        self.temp_file.close()

    def tearDown(self):
        """
        Tear down test fixtures.
        """
        os.unlink(self.temp_file.name)

    def test_initialization(self):
        """
        Test that initialization sets up the tool correctly.
        """
        tool = DummyQuackTool()

        self.assertEqual(tool.name, "dummy_tool")
        self.assertEqual(tool.version, "1.0.0")
        self.assertIsNotNone(tool.logger)
        self.assertTrue(os.path.exists(tool._temp_dir))
        self.assertTrue(os.path.exists(tool._output_dir))

    def test_get_metadata(self):
        """
        Test that metadata is returned correctly.
        """
        metadata = self.tool.get_metadata()

        self.assertEqual(metadata.name, "dummy_tool")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertTrue(isinstance(metadata.description, str))

    def test_is_available(self):
        """
        Test that is_available returns True by default.
        """
        self.assertTrue(self.tool.is_available())

    def test_initialize(self):
        """
        Test that initialize works correctly.
        """
        result = self.tool.initialize()

        self.assertTrue(result.success)
        self.assertIn("Successfully initialized dummy_tool", result.message)

    @patch("quackcore.workflow.runners.FileWorkflowRunner")
    def test_process_file_success(self, mock_runner):
        """
        Test that process_file works correctly on success.
        """
        # Setup mock
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance

        mock_result = MagicMock()
        mock_result.success = True
        mock_runner_instance.run.return_value = mock_result

        # Call method
        result = self.tool.process_file(self.temp_file.name)

        # Assertions
        self.assertTrue(result.success)
        self.assertIn("File processed successfully", result.message)
        mock_runner.assert_called_once()
        mock_runner_instance.run.assert_called_once()

    @patch("quackcore.workflow.runners.FileWorkflowRunner")
    def test_process_file_failure(self, mock_runner):
        """
        Test that process_file handles failure correctly.
        """
        # Setup mock
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.metadata = {"error_message": "Test error"}
        mock_runner_instance.run.return_value = mock_result

        # Call method
        result = self.tool.process_file(self.temp_file.name)

        # Assertions
        self.assertFalse(result.success)
        self.assertIn("File processing failed", result.message)
        self.assertEqual(result.error, "Test error")

    @patch("quackcore.workflow.runners.FileWorkflowRunner")
    def test_process_file_exception(self, mock_runner):
        """
        Test that process_file handles exceptions correctly.
        """
        # Setup mock
        mock_runner.side_effect = Exception("Test exception")

        # Call method
        result = self.tool.process_file(self.temp_file.name)

        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test exception")

    def test_get_output_extension(self):
        """
        Test that _get_output_extension returns the default extension.
        """
        self.assertEqual(self.tool._get_output_extension(), ".json")

    def test_get_remote_handler(self):
        """
        Test that get_remote_handler returns None by default.
        """
        self.assertIsNone(self.tool.get_remote_handler())

    def test_get_output_writer(self):
        """
        Test that get_output_writer returns a DefaultOutputWriter.
        """
        writer = self.tool.get_output_writer()
        self.assertIsNotNone(writer)


if __name__ == "__main__":
    unittest.main()