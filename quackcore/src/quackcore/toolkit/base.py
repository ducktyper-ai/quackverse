# quackcore/src/quackcore/toolkit/base.py
"""
Base class implementation for QuackTool plugins.

This module provides the foundational class that all QuackTool plugins
should inherit from, implementing common functionality and enforcing
the QuackToolPluginProtocol.
"""

import abc
import logging
import os
import tempfile
from logging import Logger
from typing import Any

from quackcore.config.tooling.logger import get_logger, setup_tool_logging
from quackcore.fs.service import get_service
from quackcore.integrations.core import IntegrationResult
from quackcore.plugins.protocols import QuackPluginMetadata
from quackcore.toolkit.protocol import (
    QuackToolPluginProtocol,  # Import directly from protocol module
)
from quackcore.workflow.output import (
    DefaultOutputWriter,
    OutputWriter,
    YAMLOutputWriter,
)
from quackcore.workflow.runners.file_runner import FileWorkflowRunner


class BaseQuackToolPlugin(QuackToolPluginProtocol, abc.ABC):
    """
    Base class for all QuackTool plugins.

    Provides common functionality and enforces the required interface
    for all QuackTool plugins. Concrete tool implementations should
    inherit from this class and implement the abstract methods.
    """

    def __init__(self, name: str, version: str):
        """
        Initialize the base QuackTool plugin.

        Args:
            name: The name of the tool
            version: The version of the tool
        """
        # Set up default paths in case filesystem operations fail
        self._temp_dir = os.path.join(tempfile.gettempdir(), f"quack_{name}_temp")
        self._output_dir = os.path.join(tempfile.gettempdir(), f"quack_{name}_output")

        # Setup logging first since it doesn't depend on filesystem
        try:
            setup_tool_logging(name)
            self._logger = get_logger(name)
        except Exception as e:
            # If logging setup fails, create a basic logger
            self._logger = logging.getLogger(name)
            self._logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            self._logger.addHandler(handler)
            self._logger.warning(f"Failed to set up proper logging: {str(e)}")

        # Get the filesystem service
        try:
            self.fs = get_service()
        except Exception as e:
            self._logger.error(f"Failed to get filesystem service: {str(e)}")
            raise RuntimeError(f"Failed to initialize filesystem service: {str(e)}")

        self._name = name
        self._version = version

        # Create a temporary directory for this tool
        try:
            temp_result = self.fs.create_temp_directory(prefix=f"quack_{name}_")
            if hasattr(temp_result, 'success') and temp_result.success:
                if hasattr(temp_result, 'data'):
                    self._temp_dir = temp_result.data
                elif hasattr(temp_result, 'path'):
                    self._temp_dir = str(temp_result.path)
            else:
                self._temp_dir = tempfile.mkdtemp(prefix=f"quack_{name}_")
                self._logger.info(f"Created temp directory: {self._temp_dir}")
        except Exception as e:
            self._logger.warning(f"Error creating temp directory: {str(e)}")
            self._temp_dir = tempfile.mkdtemp(prefix=f"quack_{name}_")
            self._logger.info(f"Created temp directory: {self._temp_dir}")

        # Get output directory safely
        try:
            cwd_result = self.fs.normalize_path(".")
            if hasattr(cwd_result, 'success') and cwd_result.success:
                cwd_path = None
                if hasattr(cwd_result, 'data'):
                    cwd_path = cwd_result.data
                elif hasattr(cwd_result, 'path'):
                    cwd_path = str(cwd_result.path)

                if cwd_path:
                    output_path_result = self.fs.join_path(cwd_path, "output")
                    if hasattr(output_path_result,
                               'success') and output_path_result.success:
                        if hasattr(output_path_result, 'data'):
                            self._output_dir = output_path_result.data
                        elif hasattr(output_path_result, 'path'):
                            self._output_dir = str(output_path_result.path)
        except Exception as e:
            self._logger.warning(f"Error determining output directory: {str(e)}")
            # Keep the default output directory

        # Ensure output directory exists safely
        try:
            dir_result = self.fs.ensure_directory(self._output_dir)
            if not (hasattr(dir_result, 'success') and dir_result.success):
                fallback_dir = tempfile.mkdtemp(prefix=f"quack_{name}_output_")
                self._logger.warning(
                    f"Failed to create output directory at {self._output_dir}, falling back to {fallback_dir}")
                self._output_dir = fallback_dir
        except Exception as e:
            self._logger.warning(f"Error creating output directory: {str(e)}")
            fallback_dir = tempfile.mkdtemp(prefix=f"quack_{name}_output_")
            self._logger.warning(
                f"Exception during directory creation: {str(e)}, falling back to {fallback_dir}")
            self._output_dir = fallback_dir

        # Initialize the plugin
        try:
            self.initialize_plugin()
        except Exception as e:
            self._logger.error(f"Error initializing plugin: {str(e)}")
            raise

    @property
    def name(self) -> str:
        """
        Returns the name of the tool.

        Returns:
            str: The tool's name identifier.
        """
        return self._name

    @property
    def version(self) -> str:
        """
        Returns the version of the tool.

        Returns:
            str: Semantic version of the tool.
        """
        return self._version

    @property
    def logger(self) -> Logger:
        """
        Returns the logger instance for the tool.

        Returns:
            Logger: Logger instance for the tool.
        """
        return self._logger

    def get_metadata(self) -> QuackPluginMetadata:
        """
        Returns metadata about the plugin.

        Returns:
            QuackPluginMetadata: Structured metadata for the plugin.
        """
        return QuackPluginMetadata(
            name=self.name,
            version=self.version,
            description=self.__doc__ or "",
        )

    def initialize(self) -> IntegrationResult:
        """
        Initialize the plugin and verify it's ready to use.

        Returns:
            IntegrationResult: Result of the initialization process.
        """
        try:
            if not self.is_available():
                return IntegrationResult.error_result(
                    error="Tool is not available",
                    message=f"The tool {self.name} is not available"
                )

            return IntegrationResult.success_result(
                message=f"Successfully initialized {self.name} v{self.version}"
            )
        except Exception as e:
            self.logger.exception(f"Failed to initialize {self.name}")
            return IntegrationResult.error_result(
                error=str(e),
                message=f"Failed to initialize {self.name}"
            )

    def is_available(self) -> bool:
        """
        Check if the plugin is available and ready to use.

        Returns:
            bool: True if the plugin is available, False otherwise.
        """
        return True

    def process_file(
            self,
            file_path: str,
            output_path: str | None = None,
            options: dict[str, Any] | None = None
    ) -> IntegrationResult:
        """
        Process a file with the plugin using FileWorkflowRunner.

        Args:
            file_path: Path to the file to process
            output_path: Optional path where to write output (if None, uses default)
            options: Optional dictionary of processing options

        Returns:
            IntegrationResult: Result of the processing operation
        """
        try:
            # Validate file exists
            file_info = self.fs.get_file_info(file_path)
            if not file_info.exists:
                return IntegrationResult.error_result(
                    error=f"File not found: {file_path}",
                    message="File processing failed: input file not found"
                )

            # Create options dict if None
            options_dict = options or {}

            # Initialize the runner with necessary components
            runner = FileWorkflowRunner(
                processor=self.process_content,
                remote_handler=self.get_remote_handler(),
                output_writer=self.get_output_writer(),
            )

            # Run the workflow
            result = runner.run(file_path, options_dict)

            if result.success:
                return IntegrationResult.success_result(
                    content=result,
                    message="File processed successfully"
                )
            else:
                # Extract error message with proper fallbacks
                error_message = "Unknown error"

                # First try to get error directly from result
                if hasattr(result, "error") and result.error:
                    error_message = result.error
                # Then look in metadata if available
                elif hasattr(result, "metadata") and isinstance(result.metadata, dict):
                    error_message = result.metadata.get("error_message", error_message)

                return IntegrationResult.error_result(
                    error=error_message,
                    message="File processing failed"
                )
        except Exception as e:
            self.logger.exception("Failed to process file")
            return IntegrationResult.error_result(
                error=str(e),
                message="File processing failed"
            )

    def get_output_writer(self) -> OutputWriter | None:
        """
        Get the output writer for this tool.

        Override this method to return a custom OutputWriter if the tool wants.
        By default, returns a DefaultOutputWriter which outputs JSON.

        Note: To change the output extension, override the _get_output_extension() method.
        For non-JSON formats, return a different writer like YAMLOutputWriter.

        Returns:
            OutputWriter | None: The output writer to use, or None for default behavior
        """
        # Return the default JSON writer
        # Note: The extension from _get_output_extension() is not used directly,
        # but tools should override this entire method to return appropriate writer
        # if they want a different format
        extension = self._get_output_extension()
        if extension in (".yaml", ".yml"):
            return YAMLOutputWriter()

        return DefaultOutputWriter()

    def get_remote_handler(self) -> Any | None:
        """
        Get the remote handler for this tool.

        Override this method to return a custom remote handler if the tool wants.
        By default, returns None.

        Returns:
            Any | None: The remote handler to use, or None for default
        """
        return None

    def _get_output_extension(self) -> str:
        """
        Get the file extension for output files.

        Override this method to return a different extension if needed.

        Returns:
            str: File extension (with leading dot) for output files
        """
        return ".json"

    @abc.abstractmethod
    def initialize_plugin(self) -> None:
        """
        Initialize plugin-specific resources and dependencies.

        This method should be implemented by concrete plugin classes
        to set up any required resources, dependencies, or state.
        """
        pass

    @abc.abstractmethod
    def process_content(self, content: Any, options: dict[str, Any]) -> Any:
        """
        Process content with this tool.

        This is the core processing logic that concrete plugins must implement.
        It receives the loaded content and must return the processed result.

        Args:
            content: The loaded content to process
            options: Dictionary of processing options

        Returns:
            Any: The processed content
        """
        pass
