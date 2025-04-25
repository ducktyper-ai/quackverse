# quackcore/src/quackcore/workflow/__init__.py
"""
1. ✅ quackcore.workflow – NEW MODULE
🔁 Standardizes how tools process files (local or Drive), wrap logic in error-handling, and execute workflows.
Inspired by workflow/file_processor.py, but:

Must follow QuackCore conventions (typed *Result objects, no direct CLI printing).
Expose:
FileProcessorService: a public API
Internal logic goes into _internal.workflow_runners, _internal.drive_handlers, etc.


That’s a killer insight, Rod — and exactly the right question to ask.

We **do** want a `workflow/` module in QuackCore, but **not as a DAG framework** or orchestration system like Dagster or Prefect. Instead, we want something **much smaller, composable, and declarative**, built specifically for the **solo dev**, the **CLI-first flow**, and the **QuackTool model**.

---

## 🧠 What Should QuackCore Workflows Be?

> ✨ A "workflow" is just a **well-defined execution pattern** for how a QuackTool runs — it wraps behavior, not logic.

We’re not building a universal orchestrator.
We’re building **tiny workflow contracts** (mixins or base classes) that make tool behaviors predictable, traceable, and safe.

---

## 🧰 🧩 Mental Model: **Workflow = Micro-Orchestration Contract**

- Not a DAG.
- Not a scheduler.
- Not a background job engine.
- Just a **tool-specific execution lifecycle** with support for:
  - Input resolution (local, remote, Drive)
  - Preprocessing
  - Execution
  - Postprocessing (e.g., upload, report)
  - Error handling and logging

---

## ✅ What Goes in `quackcore.workflow`

### 1. **Abstract Base Classes or Protocols**
Let tools define their own steps via interface:

```python
class BaseWorkflow:
    def resolve_input(self, source: str) -> InputResult: ...
    def process(self, input: InputResult) -> OutputResult: ...
    def postprocess(self, output: OutputResult) -> FinalResult: ...
```

Each QuackTool then implements a custom subclass, like:

```python
class MetadataExtractionWorkflow(BaseWorkflow):
    def process(...):  # call OpenAI
    def postprocess(...):  # write YAML
```

### 2. **Prebuilt Mixins / Helpers**
Optional mixins to reduce boilerplate, like:

```python
class DriveInputMixin:
    def resolve_input(self, source: str):
        if source.startswith("gdrive://"):
            return download_from_drive(source)
        return InputResult(path=Path(source))
```

Let devs compose:
```python
class MyWorkflow(DriveInputMixin, BaseWorkflow):
    ...
```

### 3. **Result Types**
Just like `fs`, each step should return a structured `*Result`:
```python
class InputResult(BaseModel):
    path: Path
    metadata: dict

class OutputResult(BaseModel):
    content: Any
    raw_text: Optional[str]
```

### 4. **`run_workflow()` Orchestrator**
Tiny dispatcher that runs a 3-stage lifecycle:

```python
def run_workflow(workflow: BaseWorkflow, source: str) -> FinalResult:
    input = workflow.resolve_input(source)
    output = workflow.process(input)
    return workflow.postprocess(output)
```

DuckTyper could eventually wrap this with inline progress + teaching.

---

## 🧱 Why This Works for Us

| Feature | QuackCore Workflow | Dagster-like Systems |
|--------|---------------------|----------------------|
| Designed for CLI tools | ✅ Yes | ❌ Heavy |
| Plugin-friendly | ✅ Yes | ❌ Often server-based |
| Fast to teach and fork | ✅ Yes | ❌ Complex UI / infra |
| Fits into tool.py | ✅ Yes | ❌ Requires orchestration layer |
| DuckTyper-compatible | ✅ Built-in | ❌ Not integrated |
| Can be tested with mocks | ✅ Easy | ❌ Often brittle |

---

## 🤔 Should We Ever Add DAG Support?

Eventually: **maybe**, via a **plugin**.
For now, we **focus on inline workflows**.

If we ever want long-running jobs or multi-phase tools (e.g., scrape → analyze → publish), we can expose:

```bash
ducktyper run mytool --step scrape
ducktyper run mytool --step analyze
```

Or implement:

```python
class MultiStageWorkflow(BaseWorkflow):
    def process(...):
        self.scrape()
        self.analyze()
        self.summarize()
```

---

## 💡 Recommendation Summary

| Module | Purpose |
|--------|---------|
| `quackcore.workflow.base` | Base classes and interfaces |
| `quackcore.workflow.mixins` | Drop-in step handlers (e.g., Drive input, file output) |
| `quackcore.workflow.runners` | Utilities like `run_workflow()` |
| `quackcore.workflow.results` | `InputResult`, `OutputResult`, etc. |
| `quackcore.workflow._internal` | Hidden helpers for retries, drive caching, etc. |

---

# file_processor.py

Yes, **I absolutely agree with the approach — with some key architectural tweaks to align it with QuackCore’s philosophy** and prevent future coupling or bloat.
```python
# src/quackmetadata/quackcore_candidate/workflow/file_processor.py
"""
Standard file processing workflow for QuackCore tools.

This module provides a standardized workflow for processing files that
handles both local files and files from Google Drive, reducing boilerplate
in tool implementations.
"""

import os
from typing import Any, Callable, Dict, Protocol, Tuple, TypeVar

from quackcore.fs.service import get_service
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.google.drive import GoogleDriveService
from quackcore.logging import get_logger

T = TypeVar('T')  # Return type for processor functions

# Get filesystem service and logger
fs = get_service()
logger = get_logger(__name__)

class FileProcessor(Protocol):
    """
    Protocol for file content processor functions.

    This protocol defines the expected signature for functions that process
    file content and return a tuple with success status, result, and error message.
    """

    def __call__(self, content: str, options: Dict[str, Any]) -> Tuple[bool, T, str]:
        """
        Process file content and return results.

        Args:
            content: File content to process
            options: Processing options

        Returns:
            Tuple containing:
              - success: Boolean indicating success or failure
              - result: Processing result (if successful)
              - error_message: Error message (if failed)
        """
        ...

def is_likely_drive_id(path: str) -> bool:
    """
    Check if a string is likely to be a Google Drive file ID.

    Args:
        path: The string to check

    Returns:
        True if the string looks like a Drive ID, False otherwise
    """
    if not isinstance(path, str):
        return False

    # Drive IDs are typically 25-45 chars and don't contain path separators or dots
    return (len(path) >= 25 and len(path) <= 45 and
            "/" not in path and "\\" not in path and
            "." not in path)

def ensure_clean_path(path_or_result: Any) -> str:
    """
    Extract a clean path string from various input types.

    Args:
        path_or_result: Can be a string, Path, PathResult, or any other Result object

    Returns:
        A clean path string
    """
    if hasattr(path_or_result, "path") and path_or_result.path is not None:
        # Handle PathResult and similar objects
        return str(path_or_result.path)
    elif hasattr(path_or_result, "data") and path_or_result.data is not None:
        # Handle DataResult objects
        return str(path_or_result.data)
    elif hasattr(path_or_result, "content") and path_or_result.content is not None:
        # Handle ContentResult objects
        return str(path_or_result.content)
    else:
        # For strings and Path objects
        return str(path_or_result)

def extract_path_from_path_result_string(path_string: str) -> str:
    """
    Extract a path from a string representation of a PathResult.

    Args:
        path_string: A string that may be a string representation of a PathResult

    Returns:
        The extracted path if found, or the original string
    """
    import re
    if isinstance(path_string, str) and path_string.startswith("success="):
        # Try to extract the path using regex
        match = re.search(r"path=PosixPath\('([^']+)'\)", path_string)
        if match:
            return match.group(1)
    return path_string

def process_file_workflow(
        file_path: str,
        processor_func: FileProcessor,
        output_path: str | None = None,
        options: Dict[str, Any] | None = None,
        drive_service: GoogleDriveService | None = None,
        temp_dir: str | None = None,
        output_dir: str | None = None,
        output_extension: str = ".json"
) -> IntegrationResult:
    """
    Process a file with standard workflow handling.

    This function handles both local files and Google Drive files, downloading
    if needed and optionally uploading results back to Google Drive.

    Args:
        file_path: Path to the file or Google Drive ID
        processor_func: Function to process the file content
        output_path: Optional path to save the output
        options: Optional processing options
        drive_service: Optional Google Drive service to use
        temp_dir: Optional temporary directory for downloads
        output_dir: Optional directory for output files
        output_extension: Extension for output files

    Returns:
        IntegrationResult containing the processing result
    """
    options = options or {}

    # Extract the raw input string
    raw_input = str(file_path)
    logger.debug(f"Raw input: {raw_input}")

    # Check if it looks like a Drive ID first
    is_drive_id_val = is_likely_drive_id(raw_input)

    # Process output path
    output_path_str = ensure_clean_path(
        output_path) if output_path is not None else None

    # If it looks like a Drive ID, process as Google Drive file
    if is_drive_id_val:
        logger.info(f"Detected Google Drive file ID: {raw_input}")
        return _process_drive_file(
            file_id=raw_input,
            processor_func=processor_func,
            output_path=output_path_str,
            options=options,
            drive_service=drive_service,
            temp_dir=temp_dir,
            output_extension=output_extension
        )

    # Process as local file, with fallback to Drive ID if not found
    try:
        # Extract the path from various input types
        file_path_str = extract_path_from_path_result_string(raw_input)

        # Check if file exists
        file_info = fs.get_file_info(file_path_str)

        # If file not found, check if it might be a Drive ID
        if not file_info.success or not file_info.exists:
            secondary_drive_check = (
                    "/" not in file_path_str and
                    "\\" not in file_path_str and
                    len(file_path_str) >= 25 and
                    len(file_path_str) <= 45
            )

            if secondary_drive_check and drive_service:
                potential_id = os.path.basename(file_path_str)

                if is_likely_drive_id(potential_id):
                    logger.info(
                        f"File not found locally, extracted Drive ID: {potential_id}")
                    return _process_drive_file(
                        file_id=potential_id,
                        processor_func=processor_func,
                        output_path=output_path_str,
                        options=options,
                        drive_service=drive_service,
                        temp_dir=temp_dir,
                        output_extension=output_extension
                    )
                else:
                    logger.info(
                        f"File not found locally, trying as Drive ID: {file_path_str}")
                    return _process_drive_file(
                        file_id=file_path_str,
                        processor_func=processor_func,
                        output_path=output_path_str,
                        options=options,
                        drive_service=drive_service,
                        temp_dir=temp_dir,
                        output_extension=output_extension
                    )

        # Process as local file
        logger.info(f"Processing as local file: {file_path_str}")
        return _process_local_file(
            file_path=file_path_str,
            processor_func=processor_func,
            output_path=output_path_str,
            options=options,
            output_dir=output_dir,
            output_extension=output_extension
        )

    except Exception as e:
        logger.exception(f"Failed to process file: {e}")
        return IntegrationResult.error_result(f"Failed to process file: {str(e)}")

def _process_drive_file(
        file_id: str,
        processor_func: FileProcessor,
        output_path: str | None,
        options: Dict[str, Any],
        drive_service: GoogleDriveService | None,
        temp_dir: str | None,
        output_extension: str = ".json"
) -> IntegrationResult:
    """
    Process a file from Google Drive.

    Args:
        file_id: Google Drive file ID
        processor_func: Function to process the file content
        output_path: Optional path for output file
        options: Processing options
        drive_service: Google Drive service
        temp_dir: Temporary directory for downloads
        output_extension: Extension for output files

    Returns:
        IntegrationResult containing the processing result
    """
    # Check if Drive service is available
    if not drive_service:
        return IntegrationResult.error_result(
            "Google Drive integration is not available. Please configure it in quack_config.yaml."
        )

    import tempfile
    logger.info(f"Downloading file from Google Drive with ID: {file_id}")

    # Create a temporary directory if none is provided
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="quacktool_")
        should_cleanup = True
    else:
        should_cleanup = False

    try:
        # Download the file
        download_result = drive_service.download_file(
            remote_id=file_id,
            local_path=temp_dir
        )
        if not download_result.success:
            return IntegrationResult.error_result(
                f"Failed to download file from Google Drive: {download_result.error}"
            )

        # Get the local path
        local_path = ensure_clean_path(download_result.content)
        logger.info(f"Downloaded file to: {local_path}")

        # Get file info from Drive
        file_info_result = drive_service.get_file_info(remote_id=file_id)
        if not file_info_result.success:
            return IntegrationResult.error_result(
                f"Failed to get file info from Google Drive: {file_info_result.error}"
            )

        file_info = file_info_result.content
        file_name = file_info.get("name", "unknown")

        # Process the downloaded file
        result = _process_local_file(
            file_path=local_path,
            processor_func=processor_func,
            output_path=output_path,
            options=options,
            output_extension=output_extension
        )

        # Upload result if successful and not in dry run mode
        if result.success and not options.get("dry_run", False):
            try:
                result_path = result.content.get("result_path")
                if result_path:
                    parent_id = file_info.get("parents", [None])[0]
                    upload_result = drive_service.upload_file(
                        file_path=result_path,
                        parent_folder_id=parent_id
                    )
                    if upload_result.success:
                        result.content["drive_file_id"] = upload_result.content
                        logger.info(
                            f"Uploaded result to Google Drive with ID: {upload_result.content}")
                    else:
                        logger.error(
                            f"Failed to upload to Google Drive: {upload_result.error}")
            except Exception as e:
                logger.error(f"Error during upload to Google Drive: {e}")

        # Add original filename to result
        if result.success:
            result.content["original_file_name"] = file_name

        return result

    except Exception as e:
        logger.exception(f"Error processing Google Drive file: {e}")
        return IntegrationResult.error_result(
            f"Failed to process Google Drive file: {str(e)}")

    finally:
        # Clean up the temporary directory if we created it
        if should_cleanup and temp_dir:
            try:
                fs.delete_directory(temp_dir, recursive=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")

def _process_local_file(
        file_path: str,
        processor_func: FileProcessor,
        output_path: str | None,
        options: Dict[str, Any],
        output_dir: str | None = None,
        output_extension: str = ".json"
) -> IntegrationResult:
    """
    Process a local file.

    Args:
        file_path: Path to the local file
        processor_func: Function to process the file content
        output_path: Optional path for output file
        options: Processing options
        output_dir: Output directory
        output_extension: Extension for output files

    Returns:
        IntegrationResult containing the processing result
    """
    # Ensure we're using a clean string path
    file_path_str = str(file_path)

    # Check if file exists
    file_info = fs.get_file_info(file_path_str)
    if not file_info.success or not file_info.exists:
        return IntegrationResult.error_result(f"File not found: {file_path_str}")
    if not file_info.is_file:
        return IntegrationResult.error_result(f"Not a file: {file_path_str}")

    try:
        # Read the file
        logger.info(f"Reading file: {file_path_str}")
        read_result = fs.read_text(file_path_str, encoding="utf-8")
        if not read_result.success:
            return IntegrationResult.error_result(
                f"Failed to read file: {read_result.error}")

        content = read_result.content

        # Process the content
        success, result, error = processor_func(content, options)
        if not success:
            return IntegrationResult.error_result(f"Failed to process content: {error}")

        # Determine output path
        result_path = output_path
        if not result_path:
            basename = os.path.basename(file_path_str)
            stem = os.path.splitext(basename)[0]
            result_path = os.path.join(output_dir or ".", f"{stem}{output_extension}")

        # Create the output directory if it doesn't exist
        output_parent = os.path.dirname(result_path)
        if output_parent:
            fs.create_directory(output_parent, exist_ok=True)

        # Write the result
        logger.info(f"Writing result to: {result_path}")

        # The write method depends on the result type
        if hasattr(result, "model_dump"):
            # Pydantic model
            result_dict = result.model_dump()
            write_result = fs.write_json(result_path, result_dict, atomic=True,
                                         indent=2)
        elif isinstance(result, dict):
            # Dictionary
            write_result = fs.write_json(result_path, result, atomic=True, indent=2)
        else:
            # String or other type
            write_result = fs.write_text(result_path, str(result), encoding="utf-8",
                                         atomic=True)

        if not write_result.success:
            return IntegrationResult.error_result(
                f"Failed to write result: {write_result.error}")

        # Get the filename for the message
        filename = os.path.basename(file_path_str)

        # Return success result
        return IntegrationResult.success_result(
            content={
                "result": result,
                "result_path": result_path,
            },
            message=f"Successfully processed {filename}"
        )

    except Exception as e:
        logger.exception(f"Failed to process local file: {e}")
        return IntegrationResult.error_result(f"Failed to process file: {str(e)}")
```
This `file_processor.py` is **a fantastic MVP**, but as you correctly flagged earlier, we don’t want a **“one workflow to rule them all.”** The challenge is not the logic — it’s **the abstraction level.** So here’s how I’d evolve it from *“hardcoded pipeline”* to *“modular building blocks.”*

---

## ✅ Why This Is a Great Starting Point

- 🔁 Clean, reusable contract (`processor_func`)
- 💡 Smart fallback logic (Drive ID fallback is practical)
- 🔧 Built-in GDrive support without enforcing dependency
- 📦 Returns `IntegrationResult`, keeping with QuackCore’s typed result conventions
- 📂 Handles real-world cases: file not found, output dir creation, temp cleanup

You can ship 10 tools with this tomorrow. But if we **bake it into QuackCore** as-is, we risk two problems:

- ❌ Too much magic (hidden Drive logic for every tool)
- ❌ One-size-fits-all logic path (no hooks, no overrides, no "just read it and go")

---

## 🧠 Evolution Plan: From Monolithic to Composable

### 🔹 Rename It: From `file_processor` → `FileWorkflowRunner`
To make clear it’s a *runner*, not a central pipeline.

---

### 🔹 Split Into 3 Composable Services

| New Module | Purpose |
|------------|---------|
| `workflow.runners.file_runner` | Core `run_file_workflow()` with hooks |
| `workflow.helpers.drive_handler` | Optional mixin for Drive-aware file resolution |
| `workflow.mixins.output_writer` | Reusable content writing logic (JSON, string, model) |

---

### 🔹 Use Hookable Lifecycle

Turn this…

```python
process_file_workflow(file_path, processor_func, ...)
```

Into this:

```python
runner = FileWorkflowRunner(processor=processor_func)
result = runner.run(source=file_path, options={"dry_run": True})
```

And internally:
```python
class FileWorkflowRunner:
    def resolve_input(self, source): ...
    def load_content(self, path): ...
    def run_processor(self, content): ...
    def write_output(self, result): ...
    def run():  # orchestrates those steps
```

This lets tools override:
```python
class QuackMetadataRunner(FileWorkflowRunner):
    def run_processor(self, content):
        return my_custom_llm(content)
```

Or even:
```python
class DriveOnlyWorkflow(DriveHandlerMixin, FileWorkflowRunner):
    ...
```

---

### 🔹 Don’t Assume Google Drive

Instead:
- Define a `QuackRemoteFileHandlerProtocol`
- Implement `GoogleDriveFileHandler`, optionally injected

That way:
```python
runner = FileWorkflowRunner(processor, remote_handler=GoogleDriveHandler())
```

And we can later add:
- `S3Handler`
- `GitHubHandler`
- `URLDownloaderHandler`

---

### 🔹 Output Writers Should Be Swappable

Make result-writing pluggable:

```python
class JsonOutputWriter:
    def write(path, result): ...
```

Let tools provide their own:

```python
runner = FileWorkflowRunner(processor, writer=CustomYamlWriter())
```

---

## 🦆 Where It Lives in QuackCore

Proposed file structure:

```
quackcore/
├── workflow/
│   ├── runners/
│   │   └── file_runner.py           # FileWorkflowRunner class
│   ├── mixins/
│   │   ├── drive_handler.py         # Optional Drive-aware fallback logic
│   │   └── output_writer.py         # Writers: JSON, text, model
│   ├── protocols/
│   │   └── remote_handler.py        # Interface for remote file providers
```

---

## ✨ Final Verdict

This implementation is **exactly** what we want *as a starting point* — it’s a battle-tested draft that has proven its value in QuackMetadata.

**But for QuackCore**, let’s:
- 🧩 Modularize it
- 🪶 De-magic the assumptions
- 🧱 Let each QuackTool override or mix in behavior

---

## ✅ Next Steps

Would you like me to:

- ✍️ Draft a `FileWorkflowRunner` class with lifecycle hooks?
- 🧪 Convert this into unit-tested modules in a `workflow/` folder layout?
- 📘 Document the `processor_func` protocol, result format, and override options for tool devs?

Let’s build workflows that *feel like Lego, not legacy*. 🧱🦆
"""


"""
Perfect. Below is a super detailed implementation plan for a junior developer to implement the **`quackcore.workflow` module**, based on the `file_processor.py` MVP but modularized, override-friendly, and aligned with QuackCore architecture.

---

# ✅ QuackCore Workflow Module – Implementation Plan

### 📁 Target directory:
```
quackcore/
└── workflow/
    ├── __init__.py
    ├── runners/
    │   └── file_runner.py
    ├── mixins/
    │   ├── drive_handler.py
    │   └── output_writer.py
    ├── results.py
    └── protocols/
        └── remote_handler.py
```

---

## 🧩 Purpose

Create a modular and overrideable workflow runner for QuackTools that:

- Supports file input (local or remote like Google Drive)
- Processes the file using a tool-specific processor
- Writes output in a flexible format
- Wraps all steps with structured logging and typed result objects

---

## ✅ Step-by-Step Tasks

---

### 1. **Create Result Models in `workflow/results.py`**

These are returned at each stage of the workflow.

```python
from pydantic import BaseModel
from pathlib import Path
from typing import Any, Optional

class InputResult(BaseModel):
    path: Path
    metadata: dict[str, Any] = {}

class OutputResult(BaseModel):
    content: Any
    raw_text: Optional[str] = None

class FinalResult(BaseModel):
    result_path: Optional[Path]
    metadata: dict[str, Any]
```

---

### 2. **Define `FileWorkflowRunner` in `workflow/runners/file_runner.py`**

```python
from pathlib import Path
from typing import Callable, Optional
from quackcore.workflow.results import InputResult, OutputResult, FinalResult
from quackcore.logging import get_logger

class FileWorkflowRunner:
    def __init__(
        self,
        processor: Callable[[str, dict], tuple[bool, Any, str]],
        remote_handler: Optional[Any] = None,
        output_writer: Optional[Any] = None,
    ):
        self.logger = get_logger(__name__)
        self.processor = processor
        self.remote_handler = remote_handler
        self.output_writer = output_writer

    def resolve_input(self, source: str) -> InputResult:
        if self.remote_handler and self.remote_handler.is_remote(source):
            return self.remote_handler.download(source)
        return InputResult(path=Path(source))

    def load_content(self, input_result: InputResult) -> str:
        from quackcore.fs.service import get_service
        fs = get_service()
        read_result = fs.read_text(str(input_result.path))
        if not read_result.success:
            raise RuntimeError(read_result.error)
        return read_result.content

    def run_processor(self, content: str, options: dict) -> OutputResult:
        success, result, error = self.processor(content, options)
        if not success:
            raise RuntimeError(error)
        return OutputResult(content=result)

    def write_output(self, result: OutputResult, input_path: Path, options: dict) -> FinalResult:
        if self.output_writer:
            return self.output_writer.write(result, input_path, options)
        else:
            # Default JSON writer
            from quackcore.fs.service import get_service
            fs = get_service()
            out_dir = options.get("output_dir", "./output")
            fs.create_directory(out_dir, exist_ok=True)
            out_path = Path(out_dir) / f"{input_path.stem}.json"
            fs.write_json(str(out_path), result.content, indent=2)
            return FinalResult(result_path=out_path, metadata={})

    def run(self, source: str, options: dict) -> FinalResult:
        input_result = self.resolve_input(source)
        content = self.load_content(input_result)
        output = self.run_processor(content, options)
        return self.write_output(output, input_result.path, options)
```

---

### 3. **Build `DriveHandlerMixin` in `workflow/mixins/drive_handler.py`**

```python
from quackcore.workflow.results import InputResult
from quackcore.fs.service import get_service
from quackcore.integrations.google.drive import GoogleDriveService

class GoogleDriveHandler:
    def __init__(self):
        self.drive = GoogleDriveService()

    def is_remote(self, source: str) -> bool:
        return len(source) >= 25 and "/" not in source and "." not in source

    def download(self, source: str) -> InputResult:
        result = self.drive.download_file(remote_id=source)
        if not result.success:
            raise RuntimeError(result.error)
        path = result.content.path if hasattr(result.content, "path") else result.content
        return InputResult(path=path, metadata={"remote_source": "gdrive"})
```

---

### 4. **Build `OutputWriterMixin` in `workflow/mixins/output_writer.py`**

```python
from quackcore.workflow.results import OutputResult, FinalResult
from pathlib import Path
from quackcore.fs.service import get_service

class DefaultOutputWriter:
    def write(self, result: OutputResult, input_path: Path, options: dict) -> FinalResult:
        fs = get_service()
        out_dir = options.get("output_dir", "./output")
        fs.create_directory(out_dir, exist_ok=True)
        out_path = Path(out_dir) / f"{input_path.stem}.json"

        if hasattr(result.content, "model_dump"):
            data = result.content.model_dump()
        elif isinstance(result.content, dict):
            data = result.content
        else:
            data = str(result.content)

        write_result = fs.write_json(str(out_path), data, indent=2) if isinstance(data, dict) \
            else fs.write_text(str(out_path), data)

        if not write_result.success:
            raise RuntimeError(write_result.error)

        return FinalResult(result_path=out_path, metadata={})
```

---

### 5. **Define `RemoteFileHandlerProtocol` in `workflow/protocols/remote_handler.py`**

```python
from quackcore.workflow.results import InputResult
from typing import Protocol

class RemoteFileHandler(Protocol):
    def is_remote(self, source: str) -> bool:
        ...

    def download(self, source: str) -> InputResult:
        ...
```

---

### 6. **Initialize the Module in `workflow/__init__.py`**

```python
"""
quackcore.workflow – Provides modular runners and mixins for tool workflows.
"""

from .runners.file_runner import FileWorkflowRunner
```

---

## ✅ Deliverables for the Junior Dev

| File | Description |
|------|-------------|
| `file_runner.py` | Full implementation of the `FileWorkflowRunner` lifecycle |
| `drive_handler.py` | Optional Google Drive fallback |
| `output_writer.py` | Output logic (JSON by default) |
| `results.py` | Typed result models for inputs/outputs |
| `remote_handler.py` | Protocol for pluggable remote file systems |

---

## 🧪 How to Test

In `tests/workflow/test_file_runner.py`:

```python
def dummy_processor(content: str, options: dict):
    return True, {"length": len(content)}, ""

def test_file_runner_with_local_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    runner = FileWorkflowRunner(processor=dummy_processor)
    result = runner.run(str(test_file), options={"output_dir": str(tmp_path)})

    assert result.result_path.exists()
```

---

## 🎓 Mentoring Notes

- Stick to QuackCore conventions: `IntegrationResult` or Pydantic models
- Don’t print to console — use `get_logger(__name__)`
- Avoid tool-specific logic (e.g., prompt templates)
- Always clean up temp files
- Ask for help if unsure about `Path`, `Optional`, or type hints
"""