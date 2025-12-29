# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/tool_runner.py
# module: quack_runner.workflow.tool_runner
# role: module
# neighbors: __init__.py, results.py
# exports: ToolRunner
# git_branch: refactor/toolkitWorkflow
# git_commit: 82e6d2b
# === QV-LLM:END ===



"""
Tool runner for executing QuackTools with file I/O.

This runner bridges between the pure capability interface (tools returning
CapabilityResult) and file-based workflows (reading inputs, writing outputs).

Responsibilities:
- Build ToolContext from configuration
- Load input files
- Call tool.run(request, ctx)
- Translate CapabilityResult → RunManifest
- Write output artifacts
- Handle errors and retries (future)

The runner owns all I/O operations. Tools remain pure.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING
from datetime import datetime

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
)
from quack_core.tools.context import ToolContext
from quack_core.lib.logging import get_logger

if TYPE_CHECKING:
    from quack_core.tools import BaseQuackTool


class ToolRunner:
    """
    Runner for executing tools with file I/O and manifest generation.

    This runner handles the complete lifecycle:
    1. Build ToolContext
    2. Initialize tool
    3. Load input file(s)
    4. Build request model
    5. Call tool.run(request, ctx)
    6. Translate CapabilityResult → RunManifest
    7. Write outputs (if success)
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
            run_id: str | None = None,
            work_dir: str | None = None,
            output_dir: str | None = None,
            metadata: dict[str, Any] | None = None
    ) -> ToolContext:
        """
        Build a ToolContext for tool execution.

        Args:
            run_id: Optional run ID (generated if not provided)
            work_dir: Optional working directory
            output_dir: Optional output directory
            metadata: Optional metadata dict

        Returns:
            Configured ToolContext
        """
        from quack_core.lib.fs.service import standalone as fs
        from quack_core.contracts import generate_run_id

        return ToolContext(
            run_id=run_id or generate_run_id(),
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
        from quack_core.lib.fs.service import standalone as fs
        from quack_core.contracts import utcnow

        input_path = Path(input_path)
        output_dir = Path(output_dir or "./output")

        # Ensure output directory exists
        fs.create_directory(str(output_dir), exist_ok=True)

        # Build context
        ctx = self.build_context(
            work_dir=str(work_dir) if work_dir else None,
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

            # Create input artifact reference
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
        from quack_core.lib.fs.service import standalone as fs

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

        if result.status == CapabilityStatus.success and result.data is not None:
            # Write output artifact
            output_path = output_dir / f"{Path(input_artifact.storage.uri).stem}_output.json"

            write_result = fs.write_json(
                str(output_path),
                result.data.model_dump() if hasattr(result.data,
                                                    "model_dump") else result.data,
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
        from quack_core.contracts import utcnow, CapabilityError

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