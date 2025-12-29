# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/mixins/output_writer.py
# module: quack_runner.workflow.mixins.output_writer
# role: module
# neighbors: __init__.py, integration_enabled.py, save_output_mixin.py
# exports: WorkflowError, LegacyWorkflowOutputWriter
# git_branch: refactor/toolkitWorkflow
# git_commit: de0fa70
# === QV-LLM:END ===



"""
LEGACY: Output writer for FileWorkflowRunner.

Renamed from DefaultOutputWriter to avoid collision with output/writers.py.

This is for legacy FileWorkflowRunner only.
ToolRunner (v2.0+) handles output writing internally.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quack_runner.workflow.results import FinalResult, OutputResult


class WorkflowError(Exception):
    """Custom exception for workflow-related errors."""


class LegacyWorkflowOutputWriter:
    """
    LEGACY: Output writer for FileWorkflowRunner.

    Renamed from "DefaultOutputWriter" in v2.0 to avoid naming collision
    with output/writers.JsonOutputWriter.

    This class writes OutputResult → FinalResult for legacy workflows.
    ToolRunner doesn't use this.
    """

    def write(self, result: OutputResult, input_path: Path,
              options: dict[str, Any]) -> FinalResult:
        """
        Write the output result to a file.

        Args:
            result: The output result to write.
            input_path: The original input file path.
            options: Additional options for writing.

        Returns:
            FinalResult containing the path to the written file.

        Raises:
            WorkflowError: If writing fails.
        """
        from quack_core.lib.fs.service import standalone
        fs = standalone
        out_dir = options.get("output_dir", "./output")
        fs.create_directory(out_dir, exist_ok=True)

        # Determine output format and extension
        is_text = isinstance(result.content, str)
        output_format = "text" if is_text else "json"
        extension = ".txt" if is_text else ".json"

        # Use the same extension as input file for text content
        out_path = Path(out_dir) / f"{input_path.stem}{extension}"

        # Handle different content types
        if hasattr(result.content, "model_dump"):
            data = result.content.model_dump()
        elif isinstance(result.content, dict):
            data = result.content
        else:
            data = str(result.content)

        # Write as JSON or text depending on content type
        write_result = (
            fs.write_json(out_path, data, indent=2)
            if output_format == "json"
            else fs.write_text(out_path, data)
        )

        if not write_result.success:
            raise WorkflowError(write_result.error)

        return FinalResult(
            success=True,
            result_path=out_path,
            metadata={
                "input_file": str(input_path),
                "output_file": str(out_path),
                "output_format": output_format,
                "output_size": len(str(data))
            }
        )


# Backward compatibility alias (will be removed in v4.0)
DefaultOutputWriter = LegacyWorkflowOutputWriter