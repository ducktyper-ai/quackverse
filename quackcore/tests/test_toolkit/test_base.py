# quackcore/tests/test_toolkit/test_base.py
"""
Tests for the BaseQuackToolPlugin class.
"""

import os
import shutil
import tempfile
import unittest
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from quackcore.fs.results import DataResult, OperationResult
from quackcore.toolkit.base import BaseQuackToolPlugin
from quackcore.workflow.output import DefaultOutputWriter, YAMLOutputWriter


class DummyQuackTool(BaseQuackToolPlugin):
    """
    Dummy implementation of BaseQuackToolPlugin for testing.
    """

    def __init__(self) -> None:
        # Patch filesystem access before calling init
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_dummy_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Call the parent init
            super().__init__("dummy_tool", "1.0.0")

            # Save mock filesystem for later use
            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        # No-op for testing
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        # Simple echo for testing
        return {"content": content, "options": options}


class CustomExtensionTool(BaseQuackToolPlugin):
    """
    Tool that uses a custom extension.
    """

    def __init__(self) -> None:
        # Patch filesystem access before calling init
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_custom_ext_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Call the parent init
            super().__init__("custom_ext_tool", "1.0.0")

            # Save mock filesystem for later use
            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        # No-op for testing
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        return {"content": content}

    def _get_output_extension(self) -> str:
        return ".yaml"


class RemoteHandlerTool(BaseQuackToolPlugin):
    """
    Tool that provides a custom remote handler.
    """

    def __init__(self) -> None:
        # Patch filesystem access before calling init
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_remote_handler_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Call the parent init
            super().__init__("remote_handler_tool", "1.0.0")

            # Save mock filesystem for later use
            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        # No-op for testing
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        return {"content": content}

    def get_remote_handler(self) -> Any:
        return MagicMock()


class CustomWriterTool(BaseQuackToolPlugin):
    """
    Tool that provides a custom output writer.
    """

    def __init__(self) -> None:
        # Patch filesystem access before calling init
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_custom_writer_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Call the parent init
            super().__init__("custom_writer_tool", "1.0.0")

            # Save mock filesystem for later use
            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        # No-op for testing
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        return {"content": content}

    def get_output_writer(self) -> YAMLOutputWriter:
        return YAMLOutputWriter()


class UnavailableTool(BaseQuackToolPlugin):
    """
    Tool that is not available.
    """

    def __init__(self) -> None:
        # Patch filesystem access before calling init
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_unavailable_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Call the parent init
            super().__init__("unavailable_tool", "1.0.0")

            # Save mock filesystem for later use
            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        # No-op for testing
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        return {"content": content}

    def is_available(self) -> bool:
        return False


class TestBaseQuackToolPlugin(unittest.TestCase):
    """
    Test cases for BaseQuackToolPlugin.
    """

    def setUp(self) -> None:
        """
        Set up test fixtures.
        """
        self.tool = DummyQuackTool()

        # Create a temp file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b'{"test": "data"}')
        self.temp_file.close()

    def tearDown(self) -> None:
        """
        Tear down test fixtures.
        """
        os.unlink(self.temp_file.name)

    @patch("quackcore.config.tooling.logger.setup_tool_logging")
    @patch("quackcore.config.tooling.logger.get_logger")
    def test_initialization(self, mock_get_logger: MagicMock, mock_setup_logging: MagicMock) -> None:
        """
        Test that initialization sets up the tool correctly.
        """
        # Setup mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Use a patch for all filesystem operations
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_test_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Create the tool with the mocked filesystem
            tool = DummyQuackTool()

            # Verify basic properties
            self.assertEqual(tool.name, "dummy_tool")
            self.assertEqual(tool.version, "1.0.0")
            self.assertEqual(tool.logger, mock_logger)

            # Verify logging setup
            mock_setup_logging.assert_called_once_with("dummy_tool")
            mock_get_logger.assert_called_once_with("dummy_tool")

    def test_get_metadata(self) -> None:
        """
        Test that metadata is returned correctly.
        """
        metadata = self.tool.get_metadata()

        self.assertEqual(metadata.name, "dummy_tool")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertTrue(isinstance(metadata.description, str))

    def test_is_available(self) -> None:
        """
        Test that is_available returns True by default.
        """
        self.assertTrue(self.tool.is_available())

    def test_initialize(self) -> None:
        """
        Test that initialize works correctly.
        """
        result = self.tool.initialize()

        self.assertTrue(result.success)
        self.assertIn("Successfully initialized dummy_tool", result.message)

    def test_initialize_unavailable(self) -> None:
        """
        Test that initialize handles unavailable tools.
        """
        tool = UnavailableTool()
        result = tool.initialize()

        self.assertFalse(result.success)
        self.assertIn("Tool is not available", result.error)
        self.assertIn("not available", result.message)

    def test_initialize_exception(self) -> None:
        """
        Test that initialize handles exceptions.
        """
        with patch.object(DummyQuackTool, 'is_available', side_effect=Exception("Test exception")):
            result = self.tool.initialize()

            self.assertFalse(result.success)
            self.assertEqual(result.error, "Test exception")
            self.assertIn("Failed to initialize", result.message)

    @patch("quackcore.workflow.runners.FileWorkflowRunner")
    def test_process_file_success(self, mock_runner: MagicMock) -> None:
        """
        Test that process_file works correctly on success.
        """
        # Set up mock file info
        self.tool.mock_fs.get_file_info.return_value = MagicMock(exists=True)

        # Setup mock runner
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
    def test_process_file_failure(self, mock_runner: MagicMock) -> None:
        """
        Test that process_file handles failure correctly.
        """
        # Set up mock file info
        self.tool.mock_fs.get_file_info.return_value = MagicMock(exists=True)

        # Setup mock runner
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
    def test_process_file_error_from_result(self, mock_runner: MagicMock) -> None:
        """
        Test that process_file handles failure with error property.
        """
        # Set up mock file info
        self.tool.mock_fs.get_file_info.return_value = MagicMock(exists=True)

        # Setup mock runner
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.metadata = {}
        mock_result.error = "Direct error property"
        mock_runner_instance.run.return_value = mock_result

        # Call method
        result = self.tool.process_file(self.temp_file.name)

        # Assertions
        self.assertFalse(result.success)
        self.assertIn("File processing failed", result.message)
        self.assertEqual(result.error, "Direct error property")

    @patch("quackcore.workflow.runners.FileWorkflowRunner")
    def test_process_file_exception(self, mock_runner: MagicMock) -> None:
        """
        Test that process_file handles exceptions correctly.
        """
        # Set up mock file info
        self.tool.mock_fs.get_file_info.return_value = MagicMock(exists=True)

        # Setup mock runner
        mock_runner.side_effect = Exception("Test exception")

        # Call method
        result = self.tool.process_file(self.temp_file.name)

        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test exception")

    def test_process_file_not_found(self) -> None:
        """
        Test that process_file handles file not found correctly.
        """
        # Configure file_info to return file not found
        file_info = MagicMock()
        file_info.exists = False
        self.tool.mock_fs.get_file_info.return_value = file_info

        # Call method
        result = self.tool.process_file("nonexistent_file.txt")

        # Assertions
        self.assertFalse(result.success)
        self.assertIn("not found", result.error)
        self.assertIn("input file not found", result.message)

    def test_get_output_extension(self) -> None:
        """
        Test that _get_output_extension returns the default extension.
        """
        self.assertEqual(self.tool._get_output_extension(), ".json")

    def test_get_output_extension_custom(self) -> None:
        """
        Test that _get_output_extension returns custom extension when overridden.
        """
        tool = CustomExtensionTool()
        self.assertEqual(tool._get_output_extension(), ".yaml")

    def test_get_remote_handler(self) -> None:
        """
        Test that get_remote_handler returns None by default.
        """
        self.assertIsNone(self.tool.get_remote_handler())

    def test_get_remote_handler_custom(self) -> None:
        """
        Test that get_remote_handler returns custom handler when overridden.
        """
        tool = RemoteHandlerTool()
        self.assertIsNotNone(tool.get_remote_handler())

    def test_get_output_writer(self) -> None:
        """
        Test that get_output_writer returns a DefaultOutputWriter.
        """
        writer = self.tool.get_output_writer()
        self.assertIsInstance(writer, DefaultOutputWriter)

    def test_get_output_writer_yaml(self) -> None:
        """
        Test that get_output_writer returns a YAMLOutputWriter when extension is .yaml.
        """
        tool = CustomExtensionTool()
        writer = tool.get_output_writer()
        self.assertIsInstance(writer, YAMLOutputWriter)

    def test_get_output_writer_custom(self) -> None:
        """
        Test that get_output_writer returns custom writer when overridden.
        """
        tool = CustomWriterTool()
        writer = tool.get_output_writer()
        self.assertIsInstance(writer, YAMLOutputWriter)

    def test_filesystem_error_handling(self) -> None:
        """
        Test that initialization handles filesystem errors gracefully.
        """
        with patch('quackcore.fs.service.get_service') as mock_get_service:
            # Setup the filesystem service to fail when creating temp directory
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            temp_result = MagicMock()
            temp_result.success = False
            mock_fs.create_temp_directory.return_value = temp_result

            # Set up the dir_result for the output directory to fail as well
            dir_result = MagicMock()
            dir_result.success = False
            mock_fs.ensure_directory.return_value = dir_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = os.path.join(tempfile.gettempdir(), "test_cwd")
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "test_cwd", "output")
            mock_fs.join_path.return_value = output_path_result

            # Initialize a tool with these mocked services
            tool = DummyQuackTool()

            # The tool should have fallen back to using tempfile
            self.assertTrue(os.path.exists(tool._temp_dir))
            self.assertTrue(os.path.exists(tool._output_dir))

            # Both should have the prefix
            self.assertTrue(os.path.basename(tool._temp_dir).startswith("quack_"))


@pytest.fixture
def dummy_tool() -> Generator[DummyQuackTool, None, None]:
    """Fixture that creates a DummyQuackTool for pytest-style tests."""
    with patch("os.getcwd", return_value=tempfile.gettempdir()):
        tool = DummyQuackTool()
        try:
            yield tool
        finally:
            # Clean up any temporary resources
            if hasattr(tool, "_temp_dir") and os.path.exists(tool._temp_dir):
                try:
                    shutil.rmtree(tool._temp_dir)
                except OSError:
                    pass


class TestBaseQuackToolPluginWithPytest:
    """
    Test cases using pytest fixtures for BaseQuackToolPlugin.
    """

    def test_fixture_initialization(self, dummy_tool: DummyQuackTool) -> None:
        """Test that the fixture correctly initializes the tool."""
        assert dummy_tool.name == "dummy_tool"
        assert dummy_tool.version == "1.0.0"

    def test_dataresult_handling(self, dummy_tool: DummyQuackTool) -> None:
        """Test how the tool handles DataResult objects."""
        # Create a DataResult to pass to a Path
        data_result = DataResult(data="test_path", success=True)

        # Use patch_filesystem_operations from conftest.py
        path = Path(data_result)

        # Verify the path was created with the correct string
        assert str(path) == "test_path"

    def test_operationresult_handling(self, dummy_tool: DummyQuackTool) -> None:
        """Test how the tool handles OperationResult objects."""
        # Create an OperationResult to pass to a Path
        op_result = OperationResult(data="op_path", success=True)

        # Use patch_filesystem_operations from conftest.py
        path = Path(op_result)

        # Verify the path was created with the correct string
        assert str(path) == "op_path"


if __name__ == "__main__":
    unittest.main()
