# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/tool_runner.py
# module: quack_runner.workflow.tool_runner
# role: module
# neighbors: __init__.py, results.py, legacy.py
# exports: ToolRunner, serialize_output
# git_branch: refactor/toolkitWorkflow
# git_commit: 07a259e
# === QV-LLM:END ===



"""
Tool runner for executing QuackTools with file I/O.

This runner bridges between the pure capability interface (tools returning
CapabilityResult) and file-based workflows (reading inputs, writing outputs).

Responsibilities:
- Build ToolContext with ALL required services
- Load input files
- Call tool.run(request, ctx)
- Translate CapabilityResult → RunManifest
- Write output artifacts (with proper serialization)
- Handle errors

The runner owns all I/O operations. Tools remain pure.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING
from datetime import datetime
from dataclasses import is_dataclass, asdict
import tempfile
import os

from quack_core.contracts import (
    CapabilityResult,
    CapabilityStatus,
    RunManifest,
    ToolInfo,
    ManifestInput,
    ArtifactRef,
    ArtifactKind,
    StorageRef,
    StorageScheme,
    generate_run_id,
    utcnow,
    CapabilityError,
)
from quack_core.tools.context import ToolContext
from quack_core.lib.logging import get_logger
from quack_core.lib.fs.service import standalone as fs

if TYPE_CHECKING:
    from quack_core.tools import BaseQuackTool


def serialize_output(data: Any) -> Any:
    """
    Serialize data to JSON-compatible format.

    Args:
        data: Data to serialize

    Returns:
        JSON-serializable data

    Raises:
        ValueError: If data cannot be serialized
    """
    # Pydantic model
    if hasattr(data, 'model_dump'):
        return data.model_dump()

    # Dataclass
    if is_dataclass(data):
        return asdict(data)

    # Primitives, list, dict
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    if isinstance(data, (list, tuple)):
        return [serialize_output(item) for item in data]
    if isinstance(data, dict):
        return {k: serialize_output(v) for k, v in data.items()}

    # Fallback: try to convert to string
    try:
        return str(data)
    except Exception as e:
        raise ValueError(
            f"Cannot serialize output of type {type(data).__name__}: {e}"
        )


class ToolRunner:
    """
    Runner for executing tools with file I/O and manifest generation.

    This runner handles the complete lifecycle:
    1. Build ToolContext (with ALL services - no optionals)
    2. Initialize tool
    3. Load input file(s)
    4. Build request model
    5. Call tool.run(request, ctx)
    6. Translate CapabilityResult → RunManifest
    7. Write outputs (if success, with proper serialization)
    8. Return manifest

    Example:
        >>> from quack_core.tools import BaseQuackTool
        >>> from quack_runner.workflow import ToolRunner
        >>>
        >>> tool = MyTool()
        >>> runner = ToolRunner(tool)
        >>>
        >>> manifest = runner.run_on_file(
        ...     input_path="/data/input.txt",
        ...     request_builder=lambda content: MyRequest(text=content),
        ...     output_dir="/data/output"
        ... )
        >>>
        >>> print(manifest.status)  # CapabilityStatus.success
        >>> print(manifest.outputs)  # [ArtifactRef(...), ...]
    """

    def __init__(
            self,
            tool: "BaseQuackTool",
            logger: Any | None = None
    ):
        """
        Initialize the tool runner.

        Args:
            tool: The tool instance to run
            logger: Optional logger instance
        """
        self.tool = tool
        self.logger = logger or get_logger(f"runner.{tool.name}")

    def build_context(
            self,
            run_id: str,
            work_dir: str,
            output_dir: str,
            metadata: dict[str, Any] | None = None
    ) -> ToolContext:
        """
        Build a ToolContext for tool execution.

        All services are required and provided by runner.

        Args:
            run_id: Run ID (runner-generated)
            work_dir: Working directory (runner-created)
            output_dir: Output directory (runner-created)
            metadata: Optional metadata dict

        Returns:
            Configured ToolContext with all required services
        """
        return ToolContext(
            run_id=run_id,
            tool_name=self.tool.name,
            tool_version=self.tool.version,
            logger=self.logger,
            fs=fs,
            work_dir=work_dir,
            output_dir=output_dir,
            metadata=metadata or {}
        )

    def run_on_file(
            self,
            input_path: str | Path,
            request_builder: Any,  # Callable[[str], BaseModel]
            output_dir: str | Path | None = None,
            work_dir: str | Path | None = None,
            metadata: dict[str, Any] | None = None
    ) -> RunManifest:
        """
        Run tool on a file input.

        This is the main entrypoint for file-based tool execution.

        Args:
            input_path: Path to input file
            request_builder: Function that builds request model from file content
            output_dir: Optional output directory (default: ./output)
            work_dir: Optional working directory (default: temp)
            metadata: Optional metadata

        Returns:
            RunManifest with results and artifacts

        Example:
            >>> manifest = runner.run_on_file(
            ...     input_path="/data/input.txt",
            ...     request_builder=lambda content: EchoRequest(text=content),
            ...     output_dir="/data/output"
            ... )
        """
        input_path = Path(input_path)

        # Ensure output directory exists
        if output_dir is None:
            output_dir = Path("./output")
        else:
            output_dir = Path(output_dir)
        fs.create_directory(str(output_dir), exist_ok=True)

        # Create work directory
        if work_dir is None:
            work_dir = Path(tempfile.mkdtemp(prefix=f"quack_{self.tool.name}_"))
        else:
            work_dir = Path(work_dir)
            fs.create_directory(str(work_dir), exist_ok=True)

        # Generate run ID
        run_id = generate_run_id()

        # Build context with ALL required services
        ctx = self.build_context(
            run_id=run_id,
            work_dir=str(work_dir),
            output_dir=str(output_dir),
            metadata=metadata
        )

        # Track timing
        started_at = utcnow()

        try:
            # Initialize tool
            init_result = self.tool.initialize(ctx)
            if init_result.status != CapabilityStatus.success:
                return self._build_error_manifest(
                    ctx=ctx,
                    started_at=started_at,
                    error_msg=init_result.human_message,
                    error_code=init_result.machine_message or "QC_TOOL_INIT_ERROR"
                )

            # Load input file
            file_info = fs.get_file_info(str(input_path))
            if not file_info.exists:
                return self._build_error_manifest(
                    ctx=ctx,
                    started_at=started_at,
                    error_msg=f"Input file not found: {input_path}",
                    error_code="QC_IO_NOT_FOUND"
                )

            # Read content
            content = Path(input_path).read_text(encoding="utf-8")

            # Build request model
            try:
                request = request_builder(content)
            except Exception as e:
                return self._build_error_manifest(
                    ctx=ctx,
                    started_at=started_at,
                    error_msg=f"Failed to build request: {e}",
                    error_code="QC_VAL_INVALID"
                )

            # Create input artifact reference (use real path, not URI)
            input_artifact = ArtifactRef(
                role=f"{self.tool.name}.input",
                kind=ArtifactKind.intermediate,
                content_type="text/plain",
                storage=StorageRef(
                    scheme=StorageScheme.local,
                    uri=f"file://{input_path.absolute()}"
                )
            )

            # Run tool
            result = self.tool.run(request, ctx)

            # Track timing
            finished_at = utcnow()
            duration_sec = (finished_at - started_at).total_seconds()

            # Build manifest from result
            return self._build_manifest_from_result(
                result=result,
                ctx=ctx,
                input_path=input_path,  # Pass real path, not artifact
                input_artifact=input_artifact,
                started_at=started_at,
                finished_at=finished_at,
                duration_sec=duration_sec,
                output_dir=output_dir
            )

        except Exception as e:
            self.logger.exception(f"Tool execution failed: {e}")
            return self._build_error_manifest(
                ctx=ctx,
                started_at=started_at,
                error_msg=f"Unexpected error: {e}",
                error_code="QC_EXEC_ERROR"
            )

    def _build_manifest_from_result(
            self,
            result: CapabilityResult,
            ctx: ToolContext,
            input_path: Path,  # Real filesystem path
            input_artifact: ArtifactRef,
            started_at: datetime,
            finished_at: datetime,
            duration_sec: float,
            output_dir: Path
    ) -> RunManifest:
        """
        Build RunManifest from CapabilityResult.

        This translates the tool's result into a manifest that orchestrators
        can route and track.
        """
        # Build tool info
        tool_info = ToolInfo(
            name=self.tool.name,
            version=self.tool.version,
            metadata=result.metadata
        )

        # Build input reference
        manifest_input = ManifestInput(
            name="source",
            artifact=input_artifact,
            required=True,
            description="Input file"
        )

        # Handle different statuses
        outputs: list[ArtifactRef] = []

        # Only write outputs on SUCCESS (invariant)
        if result.status == CapabilityStatus.success and result.data is not None:
            # Use input_path.stem for output naming (not URI)
            output_path = output_dir / f"{input_path.stem}.{ctx.run_id}.json"

            # Serialize output with proper error handling
            try:
                serialized = serialize_output(result.data)
            except ValueError as e:
                # Serialization failed - treat as error
                return RunManifest(
                    run_id=ctx.run_id,
                    tool=tool_info,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_sec=duration_sec,
                    status=CapabilityStatus.error,
                    inputs=[manifest_input],
                    outputs=[],  # Empty on error (invariant)
                    intermediates=[],
                    logs=result.logs,
                    error=CapabilityError(
                        code="QC_OUT_SERIALIZE_ERROR",
                        message=str(e)
                    ),
                    metadata=result.metadata
                )

            write_result = fs.write_json(
                str(output_path),
                serialized,
                indent=2
            )

            if write_result.success:
                output_artifact = ArtifactRef(
                    role=f"{self.tool.name}.output",
                    kind=ArtifactKind.final,
                    content_type="application/json",
                    storage=StorageRef(
                        scheme=StorageScheme.local,
                        uri=f"file://{output_path.absolute()}"
                    )
                )
                outputs.append(output_artifact)

        # Build manifest (enforces invariants: skip/error → empty outputs)
        return RunManifest(
            run_id=ctx.run_id,
            tool=tool_info,
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=duration_sec,
            status=result.status,
            inputs=[manifest_input],
            outputs=outputs,  # Empty if skipped/error (invariant enforced)
            intermediates=[],
            logs=result.logs,
            error=result.error,
            metadata=result.metadata
        )

    def _build_error_manifest(
            self,
            ctx: ToolContext,
            started_at: datetime,
            error_msg: str,
            error_code: str
    ) -> RunManifest:
        """Build error manifest."""
        finished_at = utcnow()
        duration_sec = (finished_at - started_at).total_seconds()

        return RunManifest(
            run_id=ctx.run_id,
            tool=ToolInfo(
                name=self.tool.name,
                version=self.tool.version
            ),
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=duration_sec,
            status=CapabilityStatus.error,
            inputs=[],
            outputs=[],  # Empty (error invariant)
            intermediates=[],
            logs=[],
            error=CapabilityError(
                code=error_code,
                message=error_msg
            ),
            metadata={}
        )