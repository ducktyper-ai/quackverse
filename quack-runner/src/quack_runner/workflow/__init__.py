# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/__init__.py
# module: quack_runner.workflow.__init__
# role: module
# neighbors: results.py, tool_runner.py
# exports: ToolRunner, FileWorkflowRunner, IntegrationEnabledMixin, DefaultOutputWriter, RemoteFileHandler, InputResult, OutputResult, FinalResult
# git_branch: refactor/toolkitWorkflow
# git_commit: 82e6d2b
# === QV-LLM:END ===



"""
quack_runner.workflow – Provides modular runners and mixins for tool workflows.

This module offers a flexible workflow system for file processing with support for
remote file handling, customizable output writing, and structured result types.

Changes in v2.0:
- Added ToolRunner for executing doctrine-compliant tools (BaseQuackTool with run())
- FileWorkflowRunner remains for backward compatibility with legacy tools
- Both runners coexist during migration period
"""

# NEW: Tool runner for doctrine-compliant tools
from quack_runner.workflow.tool_runner import ToolRunner

# EXISTING: Legacy file runner (still supported)
from quack_runner.workflow.runners.file_runner import FileWorkflowRunner

# EXISTING: Mixins and protocols
from quack_runner.workflow.mixins.integration_enabled import IntegrationEnabledMixin
from quack_runner.workflow.mixins.output_writer import DefaultOutputWriter
from quack_runner.workflow.protocols.remote_handler import RemoteFileHandler

# EXISTING: Result types
from quack_runner.workflow.results import FinalResult, InputResult, OutputResult

__all__ = [
    # NEW v2.0
    'ToolRunner',

    # EXISTING (legacy support)
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
NEW PATTERN (v2.0+):
from quack_core.tools import BaseQuackTool, ToolContext
from quack_core.contracts import CapabilityResult, EchoRequest
from quack_runner.workflow import ToolRunner

class EchoTool(BaseQuackTool):
    def run(self, request: EchoRequest, ctx: ToolContext) -> CapabilityResult[str]:
        return CapabilityResult.ok(data=f"Hello {request.text}", msg="Success")

# Run with ToolRunner
tool = EchoTool()
runner = ToolRunner(tool)
manifest = runner.run_on_file(
    input_path="input.txt",
    request_builder=lambda c: EchoRequest(text=c),
    output_dir="output"
)

LEGACY PATTERN (deprecated but still works):
from quack_core.tools import BaseQuackToolPlugin
from quack_runner.workflow import FileWorkflowRunner

class OldTool(BaseQuackToolPlugin):
    def process_content(self, content, options):
        return {"result": content}

# Run with FileWorkflowRunner
runner = FileWorkflowRunner(
    processor=tool.process_content,
    remote_handler=None,
    output_writer=None
)
result = runner.run("input.txt", {})
"""