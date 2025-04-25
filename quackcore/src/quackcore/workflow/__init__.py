# quackcore/workflow/__init__.py
"""
quackcore.workflow – Provides modular runners and mixins for tool workflows.

This module offers a flexible workflow system for file processing with support for 
remote file handling, customizable output writing, and structured result types.
"""

from .mixins.integration_enabled import IntegrationEnabledMixin
from .mixins.output_writer import DefaultOutputWriter
from .protocols.remote_handler import RemoteFileHandler
from .results import FinalResult, InputResult, OutputResult
from .runners.file_runner import FileWorkflowRunner

__all__ = [
    'FileWorkflowRunner',
    'IntegrationEnabledMixin',
    'DefaultOutputWriter',
    'RemoteFileHandler',
    'InputResult',
    'OutputResult',
    'FinalResult'
]

# Example Tool Implementation (for reference)
"""
from quackcore.workflow.mixins.integration_enabled import IntegrationEnabledMixin
from quackcore.integrations.google.drive import GoogleDriveService
from quackcore.workflow.runners.file_runner import FileWorkflowRunner
from quackcore.toolkit.base import BaseQuackToolPlugin, IntegrationResult
from typing import Any

class QuackMetadataTool(
    IntegrationEnabledMixin[GoogleDriveService],
    BaseQuackToolPlugin,
):
    def _initialize_plugin(self) -> IntegrationResult:
        self._drive_service = self.resolve_integration(GoogleDriveService)
        return IntegrationResult.success_result("Ready")

    def process_content(self, content: str, options: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
        # Tool's specific processing
        try:
            # Processing logic here
            summary = "example summary"
            return True, {"summary": summary}, ""
        except Exception as e:
            return False, {}, f"Processing error: {str(e)}"

    def run(self, file_path: str, options: dict[str, Any]) -> FinalResult:
        runner = FileWorkflowRunner(
            processor=self.process_content,
            remote_handler=self._drive_service,
        )
        return runner.run(file_path, options)
"""
