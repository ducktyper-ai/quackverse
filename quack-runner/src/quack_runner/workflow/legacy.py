# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/legacy.py
# module: quack_runner.workflow.legacy
# role: module
# neighbors: __init__.py, results.py, tool_runner.py
# exports: FileWorkflowRunner, LegacyWorkflowOutputWriter, DefaultOutputWriter, RemoteFileHandler, InputResult, OutputResult, FinalResult
# git_branch: refactor/toolkitWorkflow
# git_commit: e4fa88d
# === QV-LLM:END ===



"""
LEGACY API for backward compatibility.

⚠️ DEPRECATED - DO NOT USE IN NEW CODE ⚠️

This module exports the v1.x workflow API for tools that haven't
migrated to the new doctrine-compliant pattern yet.

All classes here are LEGACY and maintained only for backward compatibility.
They are NOT doctrine-compliant and should not be used for new tools.

Deprecated: Will be removed in v4.0

For new tools, use:
    from quack_runner.workflow import ToolRunner
    from quack_core.tools import BaseQuackTool

DOCTRINE FENCE (fix #4, #5):
Legacy code in this module may:
- Use global service registries
- Perform I/O from Ring B
- Auto-initialize services
This is acceptable ONLY because it's explicitly quarantined as LEGACY.
The new ToolRunner path never touches this code.
"""

import warnings

# Issue loud deprecation warning on import (fix #4)
warnings.warn(
    "quack_runner.workflow.legacy is deprecated. "
    "Migrate to ToolRunner and doctrine-compliant tools. "
    "This module will be removed in v4.0.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy runner
from quack_runner.workflow.runners.file_runner import FileWorkflowRunner

# Legacy output writer (renamed to avoid collision)
from quack_runner.workflow.mixins.output_writer import (
    LegacyWorkflowOutputWriter,
    DefaultOutputWriter,  # Deprecated alias
)

# Legacy protocols
from quack_runner.workflow.protocols.remote_handler import RemoteFileHandler

# Legacy result types
from quack_runner.workflow.results import FinalResult, InputResult, OutputResult

__all__ = [
    'FileWorkflowRunner',
    'LegacyWorkflowOutputWriter',
    'DefaultOutputWriter',  # Deprecated alias
    'RemoteFileHandler',
    'InputResult',
    'OutputResult',
    'FinalResult',
]

# IMPORTANT NOTE on removed exports (fix #4):
#
# IntegrationEnabledMixin from quack_runner was a doctrine violation.
# It used global service registry and automatic initialization.
#
# The doctrine-compliant version is in quack_core.tools and works differently:
# - Services from ctx.services (runner-provided)
# - No global registry
# - No auto-initialization
#
# If you need the old behavior, it was removed in v2.0.
# You must migrate to the new pattern or extract from git history.
#
# DO NOT create a new legacy integration mixin - it violates doctrine
# even in "legacy" context. Tools should migrate to new pattern.