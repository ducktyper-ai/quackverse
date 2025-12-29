# === QV-LLM:BEGIN ===
# path: quack-runner/src/quack_runner/workflow/tool_runner.py
# module: quack_runner.workflow.tool_runner
# role: module
# neighbors: __init__.py, results.py, legacy.py
# exports: ToolRunner, serialize_output, get_content_type_from_extension
# git_branch: refactor/toolkitWorkflow
# git_commit: de0fa70
# === QV-LLM:END ===


"""
Tool runner for executing QuackTools with file I/O.

This runner bridges between the pure capability interface (tools returning
CapabilityResult) and file-based workflows (reading inputs, writing outputs).

Responsibilities:
- Build ToolContext with ALL required services
- Load input files (text or binary via fs)
- Invoke lifecycle hooks (validate, pre_run, post_run, cleanup)
- Call tool.run(request, ctx)
- Translate CapabilityResult → RunManifest
- Write output artifacts (with strict JSON serialization)
- Handle errors (with context preservation)
- Cleanup temporary directories

The runner owns all I/O operations. Tools remain pure.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING, Callable
from datetime import datetime
from dataclasses import is_dataclass, asdict
import tempfile
import shutil

from pydantic import BaseModel

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


def serialize_output(
        data: Any,
        logger: Any | None = None,
        allow_string_fallback: bool = False
) -> Any:
    """
    Serialize data to JSON-compatible format with strict constraints (fix #4).

    JSON constraints enforced:
    - Dict keys must be strings
    - Sets converted to lists
    - Recursive serialization
    - Unknown types REJECTED by default (not stringified)

    Args:
        data: Data to serialize
        logger: Optional logger for warnings
        allow_string_fallback: If True, stringify unknown objects (risky)

    Returns:
        JSON-serializable data

    Raises:
        ValueError: If data cannot be serialized to valid JSON
    """
    # Pydantic model
    if hasattr(data, 'model_dump'):
        return data.model_dump()

    # Dataclass
    if is_dataclass(data):
        return asdict(data)

    # Primitives
    if isinstance(data, (str, int, float, bool, type(None))):
        return data

    # Set → list
    if isinstance(data, set):
        if logger:
            logger.debug("Converting set to list for JSON serialization")
        return [serialize_output(item, logger, allow_string_fallback) for item in data]

    # List/tuple
    if isinstance(data, (list, tuple)):
        return [serialize_output(item, logger, allow_string_fallback) for item in data]

    # Dict (enforce string keys)
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if not isinstance(k, str):
                if logger:
                    logger.warning(
                        f"Dict key {k!r} (type {type(k).__name__}) is not a string. "
                        f"Converting to string for JSON serialization."
                    )
                k = str(k)
            result[k] = serialize_output(v, logger, allow_string_fallback)
        return result

    # Unknown type: reject by default (fix #4 - strict)
    if not allow_string_fallback:
        raise ValueError(
            f"Cannot serialize object of type {type(data).__name__} to JSON. "
            f"Use Pydantic model, dataclass, or JSON-compatible types. "
            f"Object: {data!r}"
        )

    # Fallback: stringify (only if explicitly allowed)
    if logger:
        logger.warning(
            f"Serializing complex object of type {type(data).__name__} to string. "
            f"This may lose structure. Consider using Pydantic model or dataclass."
        )
    try:
        return str(data)
    except Exception as e:
        raise ValueError(
            f"Cannot serialize output of type {type(data).__name__} to JSON: {e}."
        )


def get_content_type_from_extension(extension: str) -> str:
    """
    Get MIME type from file extension.

    Args:
        extension: File extension (without dot)

    Returns:
        MIME type string
    """
    type_map = {
        'txt': 'text/plain',
        'json': 'application/json',
        'xml': 'application/xml',
        'html': 'text/html',
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'zip': 'application/zip',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
        'bin': 'application/octet-stream',
    }
    return type_map.get(extension.lower(), 'application/octet-stream')


class ToolRunner:
    """
    Runner for executing tools with file I/O and manifest generation.

    This runner handles the complete lifecycle including temporary directory cleanup.

    Example:
        >>> tool = MyTool()
        >>> runner = ToolRunner(tool, cleanup_work_dir=True)
        >>>
        >>> manifest = runner.run_on_file(
        ...     input_path="/data/input.txt",
        ...     request_builder=lambda content: MyRequest(text=content),
        ...     output_dir="/data/output"
        ... )
    """

    def __init__(
            self,
            tool: "BaseQuackTool",
            logger: Any | None = None,
            cleanup_work_dir: bool = True  # Fix #3 - configurable cleanup
    ):
        """
        Initialize the tool runner.

        Args:
            tool: The tool instance to run
            logger: Optional logger instance
            cleanup_work_dir: If True, delete temp work_dir after execution (default: True)
        """
        self.tool = tool
        self.logger = logger or get_logger(f"runner.{tool.name}")
        self.cleanup_work_dir = cleanup_work_dir

        # Check each lifecycle hook individually
        self._has_validate = hasattr(tool, 'validate') and callable(
            getattr(tool, 'validate'))
        self._has_pre_run = hasattr(tool, 'pre_run') and callable(
            getattr(tool, 'pre_run'))
        self._has_post_run = hasattr(tool, 'post_run') and callable(
            getattr(tool, 'post_run'))
        self._has_cleanup = hasattr(tool, 'cleanup') and callable(
            getattr(tool, 'cleanup'))

    def build_context(
            self,
            run_id: str,
            work_dir: str,
            output_dir: str,
            services: dict[str, Any] | None = None,
            metadata: dict[str, Any] | None = None
    ) -> ToolContext:
        """Build a ToolContext for tool execution."""
        return ToolContext(
            run_id=run_id,
            tool_name=self.tool.name,
            tool_version=self.tool.version,
            logger=self.logger,
            fs=fs,
            work_dir=work_dir,
            output_dir=output_dir,
            services=services or {},
            metadata=metadata or {}
        )

    def run_on_file(
            self,
            input_path: str | Path,
            request_builder: Callable[[str | bytes], BaseModel],
            output_dir: str | Path | None = None,
            work_dir: str | Path | None = None,
            services: dict[str, Any] | None = None,
            metadata: dict[str, Any] | None = None
    ) -> RunManifest:
        """
        Run tool on a file input.

        Args:
            input_path: Path to input file
            request_builder: Function that builds request model from file content
            output_dir: Optional output directory (default: ./output)
            work_dir: Optional working directory (default: temp, auto-deleted if cleanup_work_dir=True)
            services: Optional services to provide to tool
            metadata: Optional metadata

        Returns:
            RunManifest with results and artifacts
        """
        input_path = Path(input_path)

        # Track if we created temp dir (for cleanup - fix #3)
        created_temp_dir = False
        temp_dir_path: Path | None = None

        # Ensure output directory exists
        if output_dir is None:
            output_dir = Path("./output")
        else:
            output_dir = Path(output_dir)

        mkdir_result = fs.create_directory(str(output_dir), exist_ok=True)
        if not mkdir_result.success:
            started_at = utcnow()
            return self._build_error_manifest(
                ctx=None,
                input_path=input_path,
                started_at=started_at,
                error_msg=f"Failed to create output directory: {mkdir_result.error}",
                error_code="QC_IO_MKDIR_ERROR"
            )

        # Create work directory
        safe_tool_name = self.tool.name.replace('.', '_').replace('/', '_')
        if work_dir is None:
            temp_dir_path = Path(tempfile.mkdtemp(prefix=f"quack_{safe_tool_name}_"))
            work_dir = temp_dir_path
            created_temp_dir = True
        else:
            work_dir = Path(work_dir)
            mkdir_result = fs.create_directory(str(work_dir), exist_ok=True)
            if not mkdir_result.success:
                started_at = utcnow()
                return self._build_error_manifest(
                    ctx=None,
                    input_path=input_path,
                    started_at=started_at,
                    error_msg=f"Failed to create work directory: {mkdir_result.error}",
                    error_code="QC_IO_MKDIR_ERROR"
                )

        # Generate run ID
        run_id = generate_run_id()

        # Build context
        ctx = self.build_context(
            run_id=run_id,
            work_dir=str(work_dir),
            output_dir=str(output_dir),
            services=services,
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
                    input_path=input_path,
                    started_at=started_at,
                    error_msg=init_result.human_message,
                    error_code=init_result.machine_message or "QC_TOOL_INIT_ERROR"
                )

            # Check file exists
            file_info = fs.get_file_info(str(input_path))
            if not file_info.success:
                return self._build_error_manifest(
                    ctx=ctx,
                    input_path=input_path,
                    started_at=started_at,
                    error_msg=f"Failed to check file: {file_info.error}",
                    error_code="QC_IO_CHECK_ERROR"
                )

            if not file_info.exists:
                return self._build_error_manifest(
                    ctx=ctx,
                    input_path=input_path,
                    started_at=started_at,
                    error_msg=f"Input file not found: {input_path}",
                    error_code="QC_IO_NOT_FOUND"
                )

            # Detect if binary file (correct extension handling)
            ext_result = fs.get_extension(str(input_path))
            extension = (ext_result.data or "").lower().lstrip(".")

            binary_extensions = {"bin", "pdf", "png", "jpg", "jpeg", "gif", "zip",
                                 "tar", "gz"}
            is_binary = extension in binary_extensions

            # Read content
            content: str | bytes
            content_type: str

            if is_binary:
                read_result = fs.read_binary(str(input_path))
                if not read_result.success:
                    return self._build_error_manifest(
                        ctx=ctx,
                        input_path=input_path,
                        started_at=started_at,
                        error_msg=f"Failed to read binary file: {read_result.error}",
                        error_code="QC_IO_READ_ERROR"
                    )
                content = read_result.content
                content_type = get_content_type_from_extension(extension)
            else:
                read_result = fs.read_text(str(input_path))
                if not read_result.success:
                    return self._build_error_manifest(
                        ctx=ctx,
                        input_path=input_path,
                        started_at=started_at,
                        error_msg=f"Failed to read text file: {read_result.error}",
                        error_code="QC_IO_READ_ERROR"
                    )
                content = read_result.content
                content_type = get_content_type_from_extension(
                    extension) if extension else "text/plain"

            # Build request model
            try:
                request = request_builder(content)
            except Exception as e:
                return self._build_error_manifest(
                    ctx=ctx,
                    input_path=input_path,
                    started_at=started_at,
                    error_msg=f"Failed to build request: {e}",
                    error_code="QC_VAL_INVALID"
                )

            # Create input artifact reference
            input_artifact = ArtifactRef(
                role=f"{self.tool.name}.input",
                kind=ArtifactKind.intermediate,
                content_type=content_type,
                storage=StorageRef(
                    scheme=StorageScheme.local,
                    uri=f"file://{input_path.absolute()}"
                )
            )

            # Lifecycle hooks
            if self._has_validate:
                validate_result = self.tool.validate(request, ctx)  # type: ignore
                if validate_result.status != CapabilityStatus.success:
                    return self._build_error_manifest(
                        ctx=ctx,
                        input_path=input_path,
                        started_at=started_at,
                        error_msg=validate_result.human_message or "Validation failed",
                        error_code=validate_result.machine_message or "QC_VAL_FAILED",
                        input_artifact=input_artifact
                    )

            if self._has_pre_run:
                pre_result = self.tool.pre_run(request, ctx)  # type: ignore
                if pre_result.status != CapabilityStatus.success:
                    return self._build_error_manifest(
                        ctx=ctx,
                        input_path=input_path,
                        started_at=started_at,
                        error_msg=pre_result.human_message or "Pre-run failed",
                        error_code=pre_result.machine_message or "QC_PRE_RUN_FAILED",
                        input_artifact=input_artifact
                    )

            # Run tool
            result = self.tool.run(request, ctx)

            # Post-run hook
            if self._has_post_run:
                result = self.tool.post_run(request, result, ctx)  # type: ignore

            # Track timing
            finished_at = utcnow()
            duration_sec = (finished_at - started_at).total_seconds()

            # Build manifest
            return self._build_manifest_from_result(
                result=result,
                ctx=ctx,
                input_path=input_path,
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
                input_path=input_path,
                started_at=started_at,
                error_msg=f"Unexpected error: {e}",
                error_code="QC_EXEC_ERROR"
            )

        finally:
            # Cleanup hook (always)
            if self._has_cleanup:
                try:
                    self.tool.cleanup(ctx)  # type: ignore
                except Exception as e:
                    self.logger.warning(f"Cleanup failed: {e}")

            # Cleanup temp directory (fix #3)
            if created_temp_dir and self.cleanup_work_dir and temp_dir_path:
                try:
                    shutil.rmtree(temp_dir_path, ignore_errors=True)
                    self.logger.debug(f"Cleaned up temp directory: {temp_dir_path}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to cleanup temp directory {temp_dir_path}: {e}")

    def _build_manifest_from_result(
            self,
            result: CapabilityResult,
            ctx: ToolContext,
            input_path: Path,
            input_artifact: ArtifactRef,
            started_at: datetime,
            finished_at: datetime,
            duration_sec: float,
            output_dir: Path
    ) -> RunManifest:
        """Build RunManifest from CapabilityResult."""
        tool_info = ToolInfo(
            name=self.tool.name,
            version=self.tool.version,
            metadata=result.metadata
        )

        manifest_input = ManifestInput(
            name="source",
            artifact=input_artifact,
            required=True,
            description="Input file"
        )

        outputs: list[ArtifactRef] = []

        # Merge metadata
        manifest_metadata = dict(ctx.metadata, **result.metadata)

        # Handle success with no data (fix #5)
        if result.status == CapabilityStatus.success and result.data is None:
            # Tool returned success but no output - note in metadata
            manifest_metadata["no_output"] = True
            self.logger.info(
                f"Tool {self.tool.name} returned success with no output data")

        # Only write outputs on SUCCESS with data
        if result.status == CapabilityStatus.success and result.data is not None:
            output_path = output_dir / f"{input_path.stem}.{ctx.run_id}.json"

            # Strict serialization (fix #4 - no string fallback by default)
            try:
                serialized = serialize_output(result.data, self.logger,
                                              allow_string_fallback=False)
            except ValueError as e:
                return RunManifest(
                    run_id=ctx.run_id,
                    tool=tool_info,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_sec=duration_sec,
                    status=CapabilityStatus.error,
                    inputs=[manifest_input],
                    outputs=[],
                    intermediates=[],
                    logs=result.logs,
                    error=CapabilityError(
                        code="QC_OUT_SERIALIZE_ERROR",
                        message=str(e)
                    ),
                    metadata=manifest_metadata
                )

            write_result = fs.write_json(str(output_path), serialized, indent=2)

            if not write_result.success:
                return RunManifest(
                    run_id=ctx.run_id,
                    tool=tool_info,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_sec=duration_sec,
                    status=CapabilityStatus.error,
                    inputs=[manifest_input],
                    outputs=[],
                    intermediates=[],
                    logs=result.logs,
                    error=CapabilityError(
                        code="QC_IO_WRITE_ERROR",
                        message=f"Failed to write output: {write_result.error}"
                    ),
                    metadata=manifest_metadata
                )

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

        return RunManifest(
            run_id=ctx.run_id,
            tool=tool_info,
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=duration_sec,
            status=result.status,
            inputs=[manifest_input],
            outputs=outputs,
            intermediates=[],
            logs=result.logs,
            error=result.error,
            metadata=manifest_metadata
        )

    def _build_error_manifest(
            self,
            ctx: ToolContext | None,
            input_path: Path | None,
            started_at: datetime,
            error_msg: str,
            error_code: str,
            input_artifact: ArtifactRef | None = None
    ) -> RunManifest:
        """Build error manifest with context preserved."""
        finished_at = utcnow()
        duration_sec = (finished_at - started_at).total_seconds()

        inputs: list[ManifestInput] = []
        if input_artifact:
            inputs.append(ManifestInput(
                name="source",
                artifact=input_artifact,
                required=True,
                description="Input file"
            ))
        elif input_path:
            file_info = fs.get_file_info(str(input_path))
            if file_info.success and file_info.exists:
                ext_result = fs.get_extension(str(input_path))
                extension = (ext_result.data or "").lower().lstrip(".")
                content_type = get_content_type_from_extension(
                    extension) if extension else "application/octet-stream"

                input_artifact = ArtifactRef(
                    role=f"{self.tool.name}.input",
                    kind=ArtifactKind.intermediate,
                    content_type=content_type,
                    storage=StorageRef(
                        scheme=StorageScheme.local,
                        uri=f"file://{input_path.absolute()}"
                    )
                )
                inputs.append(ManifestInput(
                    name="source",
                    artifact=input_artifact,
                    required=True,
                    description="Input file"
                ))

        metadata = ctx.metadata if ctx else {}

        return RunManifest(
            run_id=ctx.run_id if ctx else generate_run_id(),
            tool=ToolInfo(
                name=self.tool.name,
                version=self.tool.version
            ),
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=duration_sec,
            status=CapabilityStatus.error,
            inputs=inputs,
            outputs=[],
            intermediates=[],
            logs=[],
            error=CapabilityError(
                code=error_code,
                message=error_msg
            ),
            metadata=metadata
        )