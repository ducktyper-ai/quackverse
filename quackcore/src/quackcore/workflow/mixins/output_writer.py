# quackcore/src/quackcore/workflow/mixins/output_writer.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from quackcore.fs.service import get_service
from quackcore.workflow.results import FinalResult, OutputResult


class DefaultOutputWriter:
    """
    Default implementation for writing workflow outputs.
    Provides common output writing functionality with support for different data types.
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
            RuntimeError: If writing fails.
        """
        fs = get_service()
        out_dir = options.get("output_dir", "./output")
        fs.create_directory(out_dir, exist_ok=True)
        out_path = Path(out_dir) / f"{input_path.stem}.json"

        # Handle different content types
        if hasattr(result.content, "model_dump"):
            data = result.content.model_dump()
        elif isinstance(result.content, dict):
            data = result.content
        else:
            data = str(result.content)

        # Determine output format
        output_format = "json" if isinstance(data, dict) else "text"

        # Write as JSON or text depending on content type
        write_result = (
            fs.write_json(str(out_path), data, indent=2)
            if output_format == "json"
            else fs.write_text(str(out_path), data)
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
