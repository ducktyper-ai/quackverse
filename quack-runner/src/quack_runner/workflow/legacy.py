# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/legacy.py
# module: quack_runner.workflow.legacy
# role: module
# neighbors: __init__.py, results.py, tool_runner.py
# exports: FileWorkflowRunner, LegacyWorkflowOutputWriter, RemoteFileHandler, InputResult, OutputResult, FinalResult
# git_branch: refactor/toolkitWorkflow
# git_commit: de0fa70
# === QV-LLM:END ===


"""
LEGACY API for backward compatibility.

This module exports the v1.x workflow API for tools that haven't
migrated to the new doctrine-compliant pattern yet.

All classes here are LEGACY and maintained only for backward compatibility.
They are NOT doctrine-compliant and should not be used for new tools.

Deprecated: Will be removed in v4.0

For new tools, use:
    from quack_runner.workflow import ToolRunner
    from quack_core.tools import BaseQuackTool
"""

# Legacy runner
from quack_runner.workflow.runners.file_runner import FileWorkflowRunner

# Legacy output writer (renamed to avoid collision)
from quack_runner.workflow.mixins.output_writer import LegacyWorkflowOutputWriter

# Legacy protocols
from quack_runner.workflow.protocols.remote_handler import RemoteFileHandler

# Legacy result types
from quack_runner.workflow.results import FinalResult, InputResult, OutputResult

__all__ = [
    'FileWorkflowRunner',
    'LegacyWorkflowOutputWriter',
    'RemoteFileHandler',
    'InputResult',
    'OutputResult',
    'FinalResult',
]

# Backward compatibility aliases (will be removed in v4.0)
DefaultOutputWriter = LegacyWorkflowOutputWriter

# Note: IntegrationEnabledMixin from quack_runner was a doctrine violation
# It used global service registry and automatic initialization.
# The new doctrine-compliant version is in quack_core.tools.
# If you need the old behavior, extract it from git history.