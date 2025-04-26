# quackcore/tests/test_toolkit/test_toolkit_integration.py
"""
Integration tests for the toolkit package as a whole.

These tests focus on how the toolkit components work together
in realistic usage scenarios.
"""

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.core import IntegrationResult
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.plugins.protocols import QuackPluginMetadata
from quackcore.toolkit.base import BaseQuackToolPlugin
from quackcore.toolkit.mixins.env_init import ToolEnvInitializerMixin
from quackcore.toolkit.mixins.integration_enabled import IntegrationEnabledMixin
from quackcore.toolkit.mixins.lifecycle import QuackToolLifecycleMixin
from quackcore.toolkit.mixins.output_handler import OutputFormatMixin
from quackcore.workflow.output import YAMLOutputWriter

# Custom test implementations

class MockUploadService(BaseIntegrationService):
    """Mock service that can upload files."""

    @property
    def name(self) -> str:
        return "mock_upload"

    def __init__(self) -> None:
        super().__init__()
        self.uploads = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def upload_file(self, file_path: str,
                    destination: str | None = None) -> IntegrationResult:
        """Track uploaded files."""
        self.uploads.append((file_path, destination))
        return IntegrationResult.success_result(
            message=f"Uploaded {file_path} to {destination or 'default location'}"
        )


# Helper to create mock filesystem for tests
def create_mock_fs() -> MagicMock:
    """Create a mock filesystem service for testing."""
    mock_fs = MagicMock()

    # Configure successful temp directory creation
    temp_result = MagicMock()
    temp_result.success = True
    temp_result.path = Path(tempfile.mkdtemp(prefix="quack_test_"))
    mock_fs.create_temp_directory.return_value = temp_result

    # Configure successful path handling
    cwd_result = MagicMock()
    cwd_result.success = True
    cwd_result.path = Path(tempfile.gettempdir())
    mock_fs.normalize_path.return_value = cwd_result

    output_path_result = MagicMock()
    output_path_result.success = True
    output_path_result.path = Path(os.path.join(tempfile.gettempdir(), "output"))
    mock_fs.join_path.return_value = output_path_result

    # Configure successful directory creation
    dir_result = MagicMock()
    dir_result.success = True
    dir_result.path = output_path_result.path
    mock_fs.ensure_directory.return_value = dir_result

    # Set up for file_info in process_file tests
    file_info_result = MagicMock()
    file_info_result.exists = True
    mock_fs.get_file_info.return_value = file_info_result

    return mock_fs


class CompleteTool(
    IntegrationEnabledMixin[MockUploadService],
    QuackToolLifecycleMixin,
    OutputFormatMixin,
    ToolEnvInitializerMixin,
    BaseQuackToolPlugin
):
    """A complete tool using all mixins."""

    def __init__(self, name: str, version: str) -> None:
        # Patch get_service to avoid filesystem issues
        with patch('quackcore.fs.service.get_service') as mock_get_service, \
                patch('os.getcwd') as mock_getcwd, \
                patch('quackcore.config.tooling.logger.setup_tool_logging'), \
                patch('quackcore.config.tooling.logger.get_logger'):
            # Configure mocks
            mock_fs = create_mock_fs()
            mock_get_service.return_value = mock_fs
            mock_getcwd.return_value = tempfile.gettempdir()

            # Initialize
            super().__init__(name, version)

            # Save mock filesystem for testing
            self.mock_fs = mock_fs

        self.process_called = False
        self.processed_content = None
        self.processed_options = None
        self._upload_service = None  # Will be set in initialize_plugin

    def initialize_plugin(self) -> None:
        # Resolve the upload service
        self._upload_service = self.resolve_integration(MockUploadService)

    def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Process content by tracking the call and returning a result."""
        self.process_called = True
        self.processed_content = content
        self.processed_options = options
        return {
            "result": "Processed successfully",
            "content": content,
            "options": options
        }

    def _get_output_extension(self) -> str:
        """Override to use YAML output."""
        return ".yaml"

    def get_output_writer(self) -> YAMLOutputWriter:
        """Provide a YAML writer."""
        return YAMLOutputWriter()

    def run(self, options: dict[str, Any] | None = None) -> IntegrationResult:
        """Run the full tool workflow."""
        # Call pre_run from the lifecycle mixin
        pre_result = self.pre_run()
        if not pre_result.success:
            return pre_result

        # Create a temporary input file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b'sample content')
        temp_file.close()

        try:
            # Process the file using BaseQuackToolPlugin's process_file
            process_result = self.process_file(temp_file.name, options=options)
            if not process_result.success:
                return process_result

            # Generate output path
            output_path = os.path.join(
                self._output_dir,
                f"{os.path.basename(temp_file.name)}_output{self._get_output_extension()}"
            )

            # Upload the output if we have an upload service
            if self._upload_service:
                upload_result = self._upload_service.upload_file(
                    output_path, f"results/{os.path.basename(output_path)}"
                )
                if not upload_result.success:
                    return upload_result

            # Call post_run from the lifecycle mixin
            post_result = self.post_run()
            if not post_result.success:
                return post_result

            return IntegrationResult.success_result(
                message="Tool execution complete",
                metadata={
                    "input_file": temp_file.name,
                    "output_file": output_path
                }
            )
        finally:
            # Clean up the temporary file
            os.unlink(temp_file.name)


# Tests

@pytest.fixture
def mock_upload_service() -> MockUploadService:
    """Create a mock upload service."""
    return MockUploadService()


@pytest.fixture
def complete_tool(mock_upload_service: MockUploadService) -> CompleteTool:
    """Create a complete tool with all mixins."""
    # Patch the integration service resolution
    with patch('quackcore.integrations.core.get_integration_service',
               return_value=mock_upload_service), \
            patch('quackcore.config.tooling.logger.configure_logger'):
        tool = CompleteTool("complete_tool", "1.0.0")
        return tool


@pytest.fixture
def sample_file() -> str:
    """Create a sample file for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    temp_file.write(b'{"key": "value"}')
    temp_file.close()
    try:
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


class TestToolkitIntegration:
    """Test the toolkit components working together."""

    def test_complete_tool_initialization(self, complete_tool: CompleteTool,
                                          mock_upload_service: MockUploadService) -> None:
        """Test that the complete tool initializes correctly."""
        # Verify the tool properties
        assert complete_tool.name == "complete_tool"
        assert complete_tool.version == "1.0.0"

        # Verify the integration service was resolved and initialized
        assert mock_upload_service.initialized
        assert complete_tool._upload_service == mock_upload_service

        # Verify output format settings
        assert complete_tool._get_output_extension() == ".yaml"
        assert isinstance(complete_tool.get_output_writer(), YAMLOutputWriter)

    def test_complete_tool_metadata(self, complete_tool: CompleteTool) -> None:
        """Test that the tool returns proper metadata."""
        metadata = complete_tool.get_metadata()

        assert isinstance(metadata, QuackPluginMetadata)
        assert metadata.name == "complete_tool"
        assert metadata.version == "1.0.0"

    @patch('quackcore.workflow.runners.file_runner.FileWorkflowRunner')
    def test_complete_tool_process_file(self, mock_runner: MagicMock,
                                        complete_tool: CompleteTool,
                                        sample_file: str) -> None:
        """Test processing a file with the complete tool."""
        # Setup mock runner
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance

        mock_result = MagicMock()
        mock_result.success = True
        mock_runner_instance.run.return_value = mock_result

        # Process a file
        options = {"format": "fancy"}
        result = complete_tool.process_file(sample_file, options=options)

        # Verify the result
        assert result.success

        # Verify the runner was called with correct parameters
        mock_runner.assert_called_once()
        # Verify options were passed
        args, kwargs = mock_runner_instance.run.call_args
        assert args[1] == options

    @patch('quackcore.workflow.runners.file_runner.FileWorkflowRunner')
    def test_complete_tool_run(self, mock_runner: MagicMock,
                               complete_tool: CompleteTool,
                               mock_upload_service: MockUploadService) -> None:
        """Test running the complete tool workflow."""
        # Setup mock runner
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance

        mock_result = MagicMock()
        mock_result.success = True
        mock_runner_instance.run.return_value = mock_result

        # Run the tool with options
        options = {"format": "fancy"}
        result = complete_tool.run(options)

        # Verify the result
        assert result.success
        assert "Tool execution complete" in result.message

        # Verify the file was processed
        mock_runner.assert_called_once()

        # Verify the upload service was used
        assert len(mock_upload_service.uploads) > 0

    def test_integration_property(self, complete_tool: CompleteTool,
                                  mock_upload_service: MockUploadService) -> None:
        """Test that the integration property returns the service."""
        # Access the integration through the property
        service = complete_tool.integration

        # Verify it's the mock service
        assert service == mock_upload_service

    @patch('quackcore.integrations.core.get_integration_service')
    def test_upload_without_service(self, mock_get_integration: MagicMock,
                                    mock_upload_service: MockUploadService) -> None:
        """Test uploading a file when integration service is not available."""
        # Create a new tool without an integration service
        mock_get_integration.return_value = None

        # We need to initialize a new tool for this test
        with patch('quackcore.config.tooling.logger.configure_logger'), \
                patch('quackcore.config.tooling.logger.setup_tool_logging'), \
                patch('quackcore.config.tooling.logger.get_logger'):
            tool = CompleteTool("test_tool", "1.0.0")

            # Check that the integration is None
            assert tool._upload_service is None

            # Setting up a Run test for this tool would be complicated
            # Just check the initialization is correct
            assert tool.name == "test_tool"
            assert tool.version == "1.0.0"
