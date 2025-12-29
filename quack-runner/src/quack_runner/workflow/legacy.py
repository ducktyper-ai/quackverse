# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/legacy.py
# module: quack_runner.workflow.legacy
# role: module
# neighbors: __init__.py, results.py, tool_runner.py
# exports: FileWorkflowRunner, LegacyDefaultOutputWriter, RemoteFileHandler, InputResult, OutputResult, FinalResult
# git_branch: refactor/toolkitWorkflow
# git_commit: 07a259e
# === QV-LLM:END ===


"""
LEGACY API for backward compatibility.

This module exports the v1.x workflow API for tools that haven't
migrated to the new doctrine-compliant pattern yet.

Deprecated: Use ToolRunner from quack_runner.workflow instead.

Migration path:
- v2.0-2.x: This API works (no warnings)
- v3.0: Deprecation warnings added
- v4.0: This module removed

For new tools, use:
    from quack_runner.workflow import ToolRunner
"""

# Legacy runner
from quack_runner.workflow.runners.file_runner import FileWorkflowRunner

# Legacy mixins (note: these have naming conflicts, use carefully)
from quack_runner.workflow.mixins.output_writer import (
    DefaultOutputWriter as LegacyDefaultOutputWriter
)

# Legacy protocols
from quack_runner.workflow.protocols.remote_handler import RemoteFileHandler

# Legacy result types
from quack_runner.workflow.results import FinalResult, InputResult, OutputResult

__all__ = [
    'FileWorkflowRunner',
    'LegacyDefaultOutputWriter',
    'RemoteFileHandler',
    'InputResult',
    'OutputResult',
    'FinalResult',
]

# Backward compatibility alias (will be removed in v4.0)
DefaultOutputWriter = LegacyDefaultOutputWriter