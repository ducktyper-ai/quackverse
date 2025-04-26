# quackcore/src/quackcore/workflow/runners/file_runner.py
from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from quackcore.logging import get_logger
from quackcore.workflow.protocols.remote_handler import RemoteFileHandler
from quackcore.workflow.results import FinalResult, InputResult, OutputResult


class WorkflowError(Exception):
    """Custom exception for workflow-related errors."""
    pass


class FileWorkflowRunner:
    """
    Runner for file-based workflows.

    Manages the entire file processing lifecycle: input resolution, content loading,
    processing, and output writing. Supports both local and remote files through
    the RemoteFileHandler protocol.
    """

    def __init__(
            self,
            processor: Callable[[str, dict[str, Any]], tuple[bool, Any, str]],
            remote_handler: RemoteFileHandler | None = None,
            output_writer: Any | None = None,
            logger: Any | None = None,
    ) -> None:
        """
        Initialize the FileWorkflowRunner.

        Args:
            processor: Function that processes file content and returns (success, result, error).
            remote_handler: Optional handler for remote files.
            output_writer: Optional custom output writer.
            logger: Optional custom logger.
        """
        self.logger = logger or get_logger(__name__)
        self.processor = processor
        self.remote_handler = remote_handler
        self.output_writer = output_writer

    def resolve_input(self, source: str) -> InputResult:
        """
        Resolve the input source, handling remote files if needed.

        Args:
            source: Path or URL to the input file.

        Returns:
            InputResult containing the resolved file path.
        """
        if self.remote_handler is not None and self.remote_handler.is_remote(source):
            self.logger.debug(f"Detected remote source: {source}")
            input_result = self.remote_handler.download(source)
            # Enhance metadata with source information
            input_result.metadata.update({
                "input_type": "remote",
                "source": source
            })
            return input_result

        self.logger.debug(f"Using local source: {source}")
        return InputResult(
            path=Path(source),
            metadata={"input_type": "local"}
        )

    def load_content(self, input_result: InputResult) -> str:
        """
        Load content from the input file.

        Args:
            input_result: The resolved input.

        Returns:
            The content of the file as a string.

        Raises:
            RuntimeError: If reading fails.
        """
        from quackcore.fs.service import get_service
        fs = get_service()
        self.logger.debug(f"Loading content from: {input_result.path}")
        read_result = fs.read_text(str(input_result.path))
        if not read_result.success:
            raise WorkflowError(f"Failed to read file content: {read_result.error}")
        return read_result.content

    def run_processor(self, content: Any, options: dict[str, Any]) -> OutputResult:
        """
        Run the processor function with the given content and options.

        Args:
            content: Content to process
            options: Processing options

        Returns:
            OutputResult: Result of processing
        """
        try:
            # Call the processor function with content and options
            result = self.processor(content, options)

            # If result is already an OutputResult, return it
            if isinstance(result, OutputResult):
                return result

            # Otherwise convert to OutputResult
            if isinstance(result, dict):
                # Check for success flag in result
                success = True
                if "success" in result:
                    success = bool(result["success"])

                # Check for error information
                error = None
                if not success and "error" in result:
                    error = result["error"]

                # Create OutputResult
                return OutputResult(
                    success=success,
                    content=result,
                    raw_text=error
                )
            else:
                # For non-dict returns, assume success
                return OutputResult(
                    success=True,
                    content=result,
                    raw_text=None
                )
        except Exception as e:
            # Log and return error
            self.logger.exception(f"Error in processor: {e}")
            return OutputResult(
                success=False,
                content=None,
                raw_text=str(e)
            )

    def write_output(self, result: OutputResult, input_path: Path,
                     options: dict[str, Any]) -> FinalResult:
        """
        Write the output result.

        Args:
            result: The output result to write.
            input_path: The original input path.
            options: Options for writing.

        Returns:
            FinalResult containing the output file path.
        """
        # Skip writing if dry_run is enabled
        if options.get("dry_run", False):
            self.logger.warning("Dry run mode: skipping output writing")
            return FinalResult(
                success=True,
                metadata={
                    "input_file": str(input_path),
                    "dry_run": True,
                    "processor_success": result.success
                }
            )

        try:
            if self.output_writer is not None:
                final_result = self.output_writer.write(result, input_path, options)
                # Note: Not setting success=True explicitly here as the output_writer
                # implementation is responsible for setting the appropriate success state
                return final_result
            else:
                # Default JSON writer
                from quackcore.fs.service import get_service
                fs = get_service()

                # Use temp directory if requested
                if options.get("use_temp_dir", False):
                    out_dir = tempfile.mkdtemp(prefix="quackcore_")
                    self.logger.info(f"Using temporary directory: {out_dir}")
                    options["output_dir"] = out_dir
                else:
                    out_dir = options.get("output_dir", "./output")

                fs.create_directory(out_dir, exist_ok=True)
                out_path = Path(out_dir) / f"{input_path.stem}.json"

                write_result = fs.write_json(str(out_path), result.content, indent=2)
                if not write_result.success:
                    raise WorkflowError(f"Failed to write output: {write_result.error}")

                return FinalResult(
                    success=True,
                    result_path=out_path,
                    metadata={
                        "input_file": str(input_path),
                        "output_file": str(out_path),
                        "output_format": "json",
                        "processor_success": result.success
                    }
                )
        except Exception as e:
            self.logger.exception(f"Output writing failed: {e}")
            # Truncate very large error messages
            error_message = str(e)
            if len(error_message) > 1000:
                error_message = error_message[:997] + "..."

            return FinalResult(
                success=False,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": error_message,
                    "input_file": str(input_path)
                }
            )

    def run(self, source: str, options: dict[str, Any] | None = None) -> FinalResult:
        """
        Run the complete workflow.

        Args:
            source: The source file path or URL.
            options: Optional processing options. Supports:
                - dry_run (bool): Skip output writing
                - use_temp_dir (bool): Use temporary directory for output
                - output_dir (str): Custom output directory path

        Returns:
            FinalResult containing the result of the workflow.
        """
        options = options or {}
        try:
            self.logger.info(f"Starting workflow for source: {source}")
            input_result = self.resolve_input(source)

            content = self.load_content(input_result)
            output = self.run_processor(content, options)

            final_result = self.write_output(output, input_result.path, options)

            # Add additional metadata
            final_result.metadata.update({
                "source": source,
                **input_result.metadata
            })

            if not output.success:
                final_result.success = False
                final_result.metadata["processor_error"] = output.raw_text

            self.logger.info(
                f"Workflow completed with success={final_result.success} "
                f"for source: {source}"
            )
            return final_result

        except Exception as e:
            self.logger.exception(f"Workflow run failed: {e}")
            # Truncate very large error messages
            error_message = str(e)
            if len(error_message) > 1000:
                error_message = error_message[:997] + "..."

            return FinalResult(
                success=False,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": error_message,
                    "source": source
                }
            )
