# quackcore/tests/test_toolkit/conftest.py
"""
Shared fixtures for QuackTool toolkit tests.
"""

import os
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.core.base import BaseIntegrationService

# Import directly from the modules rather than the package to avoid circular imports
from quackcore.toolkit.base import BaseQuackToolPlugin
from quackcore.toolkit.mixins.integration_enabled import IntegrationEnabledMixin


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


class SimpleMockTool(BaseQuackToolPlugin):
    """
    Simple mock implementation of BaseQuackToolPlugin for testing fixtures.
    """

    def __init__(self) -> None:
        # Patch filesystem access to avoid issues
        with patch('quackcore.fs.service.get_service') as mock_get_service, \
             patch('os.getcwd') as mock_getcwd:

            # Configure the mock
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs
            self.mock_fs = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix="quack_simple_mock_tool_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = tempfile.gettempdir()
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Set up for file_info in process_file tests
            file_info_result = MagicMock()
            file_info_result.exists = True
            mock_fs.get_file_info.return_value = file_info_result

            # Set getcwd to return a valid directory
            mock_getcwd.return_value = tempfile.gettempdir()

            # Call the parent init
            super().__init__("simple_mock_tool", "1.0.0")

    def initialize_plugin(self) -> None:
        pass

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        return {"processed": True, "content": content, "options": options}


@pytest.fixture
def mock_integration_service() -> MockIntegrationService:
    """
    Create a mock integration service.
    """
    return MockIntegrationService()


@pytest.fixture
def simple_mock_tool() -> Generator[SimpleMockTool, None, None]:
    """
    Create a simple mock tool.
    """
    with patch('os.getcwd', return_value=tempfile.gettempdir()):
        tool = SimpleMockTool()
        try:
            yield tool
        finally:
            # Clean up any temporary resources
            if hasattr(tool, "_temp_dir") and os.path.exists(tool._temp_dir):
                try:
                    os.rmdir(tool._temp_dir)
                except OSError:
                    pass


@pytest.fixture
def temp_test_file() -> Generator[str, None, None]:
    """
    Create a temporary test file.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(b'{"test": "data"}')
    temp_file.close()
    try:
        yield temp_file.name
    finally:
        os.unlink(temp_file.name)


@pytest.fixture
def mock_fs_service() -> MagicMock:
    """
    Create a mock filesystem service.
    """
    mock_fs = MagicMock()

    # Configure successful result responses
    temp_dir_result = MagicMock()
    temp_dir_result.success = True
    temp_dir_result.data = tempfile.mkdtemp(prefix="quack_test_")
    mock_fs.create_temp_directory.return_value = temp_dir_result

    cwd_result = MagicMock()
    cwd_result.success = True
    cwd_result.data = tempfile.gettempdir()
    mock_fs.normalize_path.return_value = cwd_result

    join_path_result = MagicMock()
    join_path_result.success = True
    join_path_result.data = os.path.join(tempfile.gettempdir(), "output")
    mock_fs.join_path.return_value = join_path_result

    dir_result = MagicMock()
    dir_result.success = True
    dir_result.data = os.path.join(tempfile.gettempdir(), "output")
    mock_fs.ensure_directory.return_value = dir_result

    # Add file_info result for process_file tests
    file_info_result = MagicMock()
    file_info_result.exists = True
    mock_fs.get_file_info.return_value = file_info_result

    return mock_fs


@pytest.fixture
def tool_with_mock_fs(mock_fs_service: MagicMock) -> Generator[SimpleMockTool, None, None]:
    """
    Create a tool with a mocked filesystem service.
    """
    with patch('quackcore.fs.service.get_service', return_value=mock_fs_service), \
         patch('os.getcwd', return_value=tempfile.gettempdir()):
        tool = SimpleMockTool()
        try:
            yield tool
        finally:
            # Clean up temporary resources
            if hasattr(tool, "_temp_dir") and os.path.exists(tool._temp_dir):
                try:
                    os.rmdir(tool._temp_dir)
                except OSError:
                    pass


class TestMockClass(IntegrationEnabledMixin[MockIntegrationService], BaseQuackToolPlugin):
    """A test class combining IntegrationEnabledMixin and BaseQuackToolPlugin."""

    def __init__(self, name: str, version: str) -> None:
        # Patch filesystem access to avoid issues
        with patch('quackcore.fs.service.get_service') as mock_get_service, \
             patch('os.getcwd') as mock_getcwd:

            # Configure the mock
            mock_fs = MagicMock()
            mock_get_service.return_value = mock_fs

            # Configure successful temp directory creation
            temp_result = MagicMock()
            temp_result.success = True
            temp_result.data = tempfile.mkdtemp(prefix=f"quack_{name}_")
            mock_fs.create_temp_directory.return_value = temp_result

            # Configure successful path handling
            cwd_result = MagicMock()
            cwd_result.success = True
            cwd_result.data = tempfile.gettempdir()
            mock_fs.normalize_path.return_value = cwd_result

            output_path_result = MagicMock()
            output_path_result.success = True
            output_path_result.data = os.path.join(tempfile.gettempdir(), "output")
            mock_fs.join_path.return_value = output_path_result

            # Configure successful directory creation
            dir_result = MagicMock()
            dir_result.success = True
            dir_result.data = output_path_result.data
            mock_fs.ensure_directory.return_value = dir_result

            # Set up for file_info in process_file tests
            file_info_result = MagicMock()
            file_info_result.exists = True
            mock_fs.get_file_info.return_value = file_info_result

            # Set getcwd to return a valid directory
            mock_getcwd.return_value = tempfile.gettempdir()

            # Call the parent init
            super().__init__(name, version)

            self.mock_fs = mock_fs

    def initialize_plugin(self) -> None:
        """Initialize the plugin by resolving the integration service."""
        self._service = self.resolve_integration(MockIntegrationService)

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Process content with this tool."""
        return {"content": content, "options": options}


@pytest.fixture
def integration_enabled_tool() -> Generator[TestMockClass, None, None]:
    """
    Create a tool with integration enabled mixin.
    """
    # Create a mock for the integration service
    mock_service = MockIntegrationService()

    # Patch get_integration_service to return our mock
    with patch('quackcore.integrations.core.get_integration_service', return_value=mock_service), \
         patch('os.getcwd', return_value=tempfile.gettempdir()):
        tool = TestMockClass("integration_tool", "1.0.0")
        try:
            yield tool
        finally:
            # Clean up temporary resources
            if hasattr(tool, "_temp_dir") and os.path.exists(tool._temp_dir):
                try:
                    os.rmdir(tool._temp_dir)
                except OSError:
                    pass
