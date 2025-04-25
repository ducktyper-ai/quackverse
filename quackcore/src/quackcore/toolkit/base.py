# quackcore/src/quackcore/toolkit/base.py
"""
Base class implementation for QuackTool plugins.

This module provides the foundational class that all QuackTool plugins
should inherit from, implementing common functionality and enforcing
the QuackToolPluginProtocol.
"""

import abc
import os
import tempfile
from logging import Logger
from typing import Any, cast

from quackcore.integrations.core import IntegrationResult
from quackcore.config.tooling.logger import setup_tool_logging
from quackcore.plugins.protocols import QuackPluginMetadata
from quackcore.workflow.runners.file_runner import FileWorkflowRunner
from quackcore.workflow.output import OutputWriter, DefaultOutputWriter


class BaseQuackToolPlugin(abc.ABC):
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
        self._name = name
        self._version = version
        self._temp_dir = tempfile.mkdtemp(prefix=f"quack_{name}_")
        self._output_dir = os.path.join(os.getcwd(), "output")

        # Ensure output directory exists
        os.makedirs(self._output_dir, exist_ok=True)

        # Setup logging
        self._logger = setup_tool_logging(name)

        # Initialize the plugin
        self.initialize_plugin()

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
            runner = FileWorkflowRunner(
                processor=self.process_content,
                remote_handler=self.get_remote_handler(),
                output_writer=self.get_output_writer(),
            )

            result = runner.run(file_path, options or {})

            if result.success:
                return IntegrationResult.success_result(
                    content=result,
                    message="File processed successfully"
                )
            else:
                # Get error message, with fallback if it doesn't exist
                error_message = "Unknown error"
                if hasattr(result, "metadata") and isinstance(result.metadata, dict):
                    error_message = result.metadata.get("error_message", error_message)
                elif hasattr(result, "error") and result.error:
                    error_message = result.error

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
        By default, returns a DefaultOutputWriter with the extension hint from
        _get_output_extension().

        Returns:
            OutputWriter | None: The output writer to use, or None for default
        """
        return DefaultOutputWriter(extension=self._get_output_extension())

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