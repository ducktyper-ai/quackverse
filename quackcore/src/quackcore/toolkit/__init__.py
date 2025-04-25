# quackcore/src/quackcore/toolkit/__init__.py
"""
2. ✅ quackcore.toolkit – NEW MODULE
🧰 Provides abstract base classes and patterns for QuackTool development.
Based on plugins/tool_plugin.py, this becomes:

ToolPluginBase: abstract class for building tools with standard lifecycle.
GoogleDriveEnabledMixin, QuackToolLifecycleMixin, etc.
Enforces init, run(), validate(), upload() pattern.
Optionally: include plugin-style registration if not already in plugins.


```python
# src/quackmetadata/quackcore_candidate/plugins/tool_plugin.py
"""
Base classes for QuackTool plugins.

This module provides base classes for creating QuackTool plugins with
reduced boilerplate and standardized behavior.
"""

import tempfile
from abc import abstractmethod
from logging import Logger
from typing import Any, Dict, Tuple

from quackcore.fs.service import get_service
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.google.drive import GoogleDriveService
from quackcore.logging import get_logger
from quackcore.paths import service as paths
from quackcore.plugins.protocols import QuackPluginMetadata

# Import from the workflow module we created earlier
from quackmetadata.quackcore_candidate.workflow.file_processor import process_file_workflow

# Define the protocol for QuackToolPlugin
class QuackToolPluginProtocol:
    """Protocol for QuackTool plugins."""

    # Add initialization state attribute to the protocol
    _initialized: bool

    @property
    def logger(self) -> Logger:
        """Get the logger for the plugin."""
        ...

    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        ...

    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        ...

    def get_metadata(self) -> QuackPluginMetadata:
        """
        Get metadata for the plugin.

        Returns:
            QuackPluginMetadata: Plugin metadata
        """
        ...

    def initialize(self) -> IntegrationResult:
        """Initialize the plugin."""
        ...

    def is_available(self) -> bool:
        """Check if the plugin is available."""
        ...

    def process_file(
            self,
            file_path: str,
            output_path: str | None = None,
            options: Dict[str, Any] | None = None,
    ) -> IntegrationResult:
        """Process a file using the plugin."""
        ...

# Get filesystem service
fs = get_service()

class BaseQuackToolPlugin(QuackToolPluginProtocol):
    """
    Base class for QuackTool plugins.

    This class implements common functionality for QuackTool plugins,
    reducing boilerplate in concrete implementations.

    Attributes:
        tool_name: Name of the tool (override in subclass)
        tool_version: Version of the tool (override in subclass)
        tool_description: Description of the tool (override in subclass)
        tool_author: Author of the tool (override in subclass)
        tool_capabilities: List of tool capabilities (override in subclass)
    """

    # Override these in subclasses
    tool_name = "base_tool"
    tool_version = "0.1.0"
    tool_description = "Base QuackTool plugin"
    tool_author = "AI Product Engineer Team"
    tool_capabilities = []

    def __init__(self) -> None:
        """Initialize the plugin."""
        self._logger: Logger = get_logger(f"{__name__}.{self.tool_name}")
        self._drive_service = None
        self._initialized: bool = False

        # Create a temporary directory
        temp_result = fs.create_temp_directory(prefix=f"{self.tool_name}_")
        if temp_result.success:
            self._temp_dir: str = str(temp_result.path)
        else:
            self._temp_dir = tempfile.mkdtemp(prefix=f"{self.tool_name}_")

        # Resolve the output directory
        try:
            project_context = paths.detect_project_context()
            output_dir = (
                project_context.get_output_dir()
                if project_context.get_output_dir()
                else fs.normalize_path("./output")
            )
        except Exception:
            output_dir = fs.normalize_path("./output")

        dir_result = fs.create_directory(output_dir, exist_ok=True)
        if dir_result.success:
            self._output_dir = str(dir_result.path)
        else:
            self._logger.warning(
                f"Failed to create output directory: {dir_result.error}")
            self._output_dir = "./output"

    @property
    def logger(self) -> Logger:
        """Get the logger for the plugin."""
        return self._logger

    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        return self.tool_name

    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        return self.tool_version

    def get_metadata(self) -> QuackPluginMetadata:
        """
        Get metadata for the plugin.

        Returns:
            QuackPluginMetadata: Plugin metadata.
        """
        return QuackPluginMetadata(
            name=self.name,
            version=self.version,
            description=self.tool_description,
            author=self.tool_author,
            capabilities=self.tool_capabilities,
        )

    def initialize(self) -> IntegrationResult:
        """
        Initialize the plugin and its dependencies.

        Returns:
            IntegrationResult indicating success or failure.
        """
        if self._initialized:
            return IntegrationResult.success_result(
                message=f"{self.name} plugin already initialized"
            )

        try:
            # Initialize environment
            self._initialize_environment()

            # Initialize Google Drive
            self._drive_service = GoogleDriveService()
            drive_result = self._drive_service.initialize()
            if not drive_result.success:
                self._logger.warning(
                    f"Google Drive integration not available: {drive_result.error}")
                self._drive_service = None

            # Call the concrete initialization method
            init_result = self._initialize_plugin()
            if not init_result.success:
                return init_result

            self._initialized = True
            return IntegrationResult.success_result(
                message=f"{self.name} plugin initialized successfully"
            )
        except Exception as e:
            self.logger.exception(f"Failed to initialize {self.name} plugin")
            return IntegrationResult.error_result(
                f"Failed to initialize {self.name} plugin: {str(e)}"
            )

    def _initialize_environment(self) -> None:
        """
        Initialize environment variables from configuration.
        """
        try:
            # Import the tool's initialize function if available
            module_name = self.tool_name.lower()
            initialize_module = __import__(module_name, fromlist=["initialize"])
            if hasattr(initialize_module, "initialize"):
                initialize_module.initialize()
        except Exception as e:
            self.logger.warning(f"Failed to initialize environment: {e}")

    @abstractmethod
    def _initialize_plugin(self) -> IntegrationResult:
        """
        Initialize plugin-specific functionality.

        This method should be implemented by concrete plugin classes.

        Returns:
            IntegrationResult indicating success or failure.
        """
        pass

    def is_available(self) -> bool:
        """
        Check if the plugin is available.

        Returns:
            True if the plugin is available, False otherwise.
        """
        return self._initialized

    @abstractmethod
    def process_content(
            self,
            content: str,
            options: Dict[str, Any]
    ) -> Tuple[bool, Any, str]:
        """
        Process content with the plugin.

        This method should be implemented by concrete plugin classes.

        Args:
            content: The content to process
            options: Processing options

        Returns:
            Tuple of (success, result, error_message)
        """
        pass

    def process_file(
            self,
            file_path: str,
            output_path: str | None = None,
            options: Dict[str, Any] | None = None,
    ) -> IntegrationResult:
        """
        Process a file using the plugin.

        Args:
            file_path: Path to the file to process
            output_path: Optional path for the output file
            options: Optional processing options

        Returns:
            IntegrationResult containing the processing result
        """
        if not self._initialized:
            init_result = self.initialize()
            if not init_result.success:
                return init_result

        # Use the standard file processing workflow
        return process_file_workflow(
            file_path=file_path,
            processor_func=self.process_content,
            output_path=output_path,
            options=options,
            drive_service=self._drive_service,
            temp_dir=self._temp_dir,
            output_dir=self._output_dir,
            output_extension=self._get_output_extension()
        )

    def _get_output_extension(self) -> str:
        """
        Get the extension for output files.

        Returns:
            Extension string including the dot
        """
        return ".json"
```
"""

"""
Absolutely — let’s spec out `quackcore.toolkit` properly and explain why it matters.

---

# 🧰 `quackcore.toolkit` — The Developer Enabler Module

---

## ✨ TL;DR

`quackcore.toolkit` is **the scaffolding layer for QuackTools**.

It defines base classes, lifecycle patterns, and optional mixins that make it easy to build tools that:
- Plug into the QuackCore ecosystem
- Are discoverable and testable via `DuckTyper`
- Work with file workflows, logging, config, and cloud integrations
- Feel "batteries-included" for solo devs

If `quackcore.workflow` is about *running logic*, `quackcore.toolkit` is about *organizing tool code into robust, reusable components*.

---

## 🎯 Purpose

`quackcore.toolkit` exists to:

| Goal | Description |
|------|-------------|
| ✅ **Reduce boilerplate** | Tools shouldn’t have to reimplement lifecycle logic like `initialize()`, Drive setup, temp folder creation, etc. |
| 🧩 **Standardize structure** | All tools should follow a consistent interface (`process_content`, `process_file`, `get_metadata`, etc.) |
| 🔌 **Enable plugin discovery** | Through compatibility with `quackcore.plugins`, tools become pluggable and introspectable. |
| 🧪 **Improve testability** | Standard patterns make mocking, dependency injection, and lifecycle testing easier. |
| 🧙 **Empower teaching mode** | DuckTyper can expect a known set of capabilities (`run`, `validate`, `upload`, etc.) |
| 🛠️ **Encourage composition** | Tools can opt into GDrive support, output formats, temp file usage via mixins. |

---

## 🧱 Module Structure

```
quackcore/
└── toolkit/
    ├── base.py                # BaseQuackToolPlugin
    ├── protocol.py            # QuackToolPluginProtocol (inspired by plugins.protocols)
    ├── mixins/
    │   ├── integration_enabled.py   # IntegrationEnabledMixin (opt-in)
    │   ├── output_handler.py  # OutputFormatMixin (json/yaml/md)
    │   ├── lifecycle.py       # QuackToolLifecycleMixin (adds run(), upload(), etc.)
    │   └── env_init.py        # ToolEnvInitializerMixin (import init from tool.py)
```

---

## 🔍 Key Components

---

### 1. `QuackToolPluginProtocol` (`toolkit.protocol`)

A strict interface definition:
```python
class QuackToolPluginProtocol:
    def initialize(self) -> IntegrationResult: ...
    def is_available(self) -> bool: ...
    def get_metadata(self) -> QuackPluginMetadata: ...
    def process_file(self, path: str, ...) -> IntegrationResult: ...
```

🔒 Guarantees plugin compatibility for:
- DuckTyper
- Teaching mode
- Plugin registry

---

### 2. `BaseQuackToolPlugin` (`toolkit.base`)

The base class that implements:

- Logging
- Temp + output dir creation
- Optional Drive integration (delegated to a mixin)
- Common `initialize()` logic
- Hook-based design (`_initialize_plugin()`, `process_content()`)

This becomes the **recommended base class** for all QuackTools.

---

### 3. Mixin Modules

Each mixin adds functionality without forcing it:

#### ✅ `IntegrationEnabledMixin`
We shouldn’t create a separate mixin like GoogleDriveEnabledMixin, GoogleMailEnabledMixin, GitHubEnabledMixin, etc. for every integration. That approach doesn't scale and tightly couples each integration to quackcore.toolkit.

Instead, let’s refactor the pattern you’re seeing into something composable and scalable across all integrations — using the existing architecture in quackcore.integrations.core.

✅ Revised Plan: IntegrationEnabledMixin + Standardized Service Resolution

🧠 Design Principle

🧩 All integrations (Drive, Mail, GitHub, Notion, etc.) should be injected or resolved by type, not hardcoded or per-mixin.
✅ New Design

🔄 Replace GoogleDriveEnabledMixin with:
✅ IntegrationEnabledMixin
# quackcore/toolkit/mixins/integration_enabled.py

from typing import Type, Optional, TypeVar, Generic
from quackcore.integrations.core import get_integration_service
from quackcore.integrations.core.protocols import BaseIntegrationService

T = TypeVar("T", bound=BaseIntegrationService)

class IntegrationEnabledMixin(Generic[T]):
    """
    Mixin that enables integration with a specified service type.
    """
    _integration_service: Optional[T] = None

    def resolve_integration(self, service_type: Type[T]) -> Optional[T]:
        """
        Lazily load the integration service of the given type.
        Stores the result for reuse.
        """
        if self._integration_service is None:
            self._integration_service = get_integration_service(service_type)
            if self._integration_service and hasattr(self._integration_service, "initialize"):
                self._integration_service.initialize()
        return self._integration_service

    def get_integration_service(self) -> Optional[T]:
        return self._integration_service
🔍 How to Use in a Tool
Instead of:

class MyTool(GoogleDriveEnabledMixin, BaseQuackToolPlugin):
You do:

class MyTool(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):

    def _initialize_plugin(self):
        self._drive = self.resolve_integration(GoogleDriveService)
        ...
You now have:

✅ Lazy-loaded, optionally initialized Drive support
✅ The same pattern works for GitHubService, NotionService, etc.
✅ Future-proofed architecture
✅ No bloat in toolkit.mixins
💡 Bonus: You Can Add Shortcuts

If you want more ergonomics in tools using only 1 service, the base class could optionally expose:

@property
def integration(self) -> T:
    return self.get_integration_service()
So the tool can just do self.integration.download().

🛠 Changes to Make


File	Change
quackcore/toolkit/mixins/drive_enabled.py	❌ Delete (won’t be used)
quackcore/toolkit/mixins/integration_enabled.py	✅ Add new generic integration mixin
quackcore/__init__.py	✅ Add IntegrationEnabledMixin to toolkit.__all__
BaseQuackToolPlugin	✅ Stop initializing GoogleDriveService directly
Any tool using Drive	✅ Migrate to resolve_integration(GoogleDriveService)
✅ Benefits of This Approach


Benefit	Why it matters
✅ Scalable	No new mixin per service
✅ DRY	Uses get_integration_service() — centralized
✅ Flexible	Tools can use any combo of services
✅ Explicit	Service type is passed directly — no magic attributes
✅ Consistent	Works with all current and future integrations


#### ✅ `OutputFormatMixin`
- Adds `_get_output_extension()` and `write_output()` logic
- Can be overridden by tools using YAML or Markdown

#### ✅ `ToolEnvInitializerMixin`
- Loads `initialize()` from tool.py if present
- Used to pre-load secrets, models, etc.

#### ✅ `QuackToolLifecycleMixin`
- Adds optional methods like `run()`, `upload()`, `validate()`
- Helps DuckTyper trigger tool steps in teaching mode

You can combine them like:
```python
class MyTool(
    ToolEnvInitializerMixin,
    GoogleDriveEnabledMixin,
    OutputFormatMixin,
    BaseQuackToolPlugin,
):
    ...
```

---

## 🧠 Why `toolkit` is Separate from `plugins`

| Concern | `toolkit` | `plugins` |
|--------|-----------|------------|
| Defines dev-facing abstractions | ✅ | ❌ |
| Contains lifecycle logic and mixins | ✅ | ❌ |
| Handles plugin discovery/registry | ❌ | ✅ |
| Defines system-level protocols for all plugins | ❌ | ✅ |

Think of `toolkit` as the *QuackTool base class suite*, while `plugins` is the *platform glue*.

---

## 🧪 Teaching + CLI Synergy

By adhering to `BaseQuackToolPlugin`, a tool automatically:
- Is discoverable by `ducktyper`
- Is inspectable (via `.get_metadata()`)
- Can participate in XP, badge, and step-based workflows (via `process_file`, `run()`, etc.)

This is what makes QuackTools *“code you can use and learn from.”*

---

## 🛠 Future Additions

### 🧪 `MockableMixin`
- Adds fake file inputs for testing
- Simulates tool behavior in teaching mode

### 📖 `TutorialMetadataMixin`
- Loads and validates `tutorial.yaml`
- Makes the tool introspectable by DuckTyper

---

## 🔄 Usage Pattern

```python
# quackmetadata/tool.py

class QuackMetadataTool(
    ToolEnvInitializerMixin,
    GoogleDriveEnabledMixin,
    OutputFormatMixin,
    BaseQuackToolPlugin,
):

    tool_name = "quackmetadata"
    tool_version = "1.0.0"
    tool_description = "Extract YAML metadata from text using LLMs"

    def _initialize_plugin(self):
        # Load model or setup logic
        return IntegrationResult.success_result("Ready")

    def process_content(self, content: str, options: dict):
        yaml_result = extract_metadata_yaml(content)
        return True, yaml_result, ""
```

This tool is now:

- A QuackPlugin ✅
- A DuckTyper-compatible CLI ✅
- Teaching-mode ready ✅
- Fully testable ✅

---

## ✅ Final Recap

**`quackcore.toolkit` is the developer's ergonomic layer** — the thing that makes writing a QuackTool *feel* great.  
It's structured, predictable, and powerful — but not abstract for its own sake.

It's the foundation for:
- 🧰 Tool creation
- 🧪 Testing and simulation
- 🧠 Teaching workflows
- 🧩 Plugin ecosystem

---
"""



"""
# ✅ Work Plan for `quackcore.toolkit`

---

## 🧠 What You’re Building

`quackcore.toolkit` is the **developer interface layer** for creating QuackTools. It provides:

- 🔨 A base class (`BaseQuackToolPlugin`) that tools can inherit from.
- 🧩 Mixins that add optional features (Drive support, file output, lifecycle methods).
- 📐 Protocols to enforce structure and enable plugin discovery.
- 📚 Clean separation from core workflow and plugin registry logic.

---

## 📁 Target Folder Structure

```bash
quackcore/
└── toolkit/
    ├── __init__.py
    ├── base.py                     # BaseQuackToolPlugin
    ├── protocol.py                 # QuackToolPluginProtocol
    └── mixins/
        ├── integration_enabled.py        # GoogleDriveEnabledMixin
        ├── output_handler.py       # OutputFormatMixin
        ├── lifecycle.py            # QuackToolLifecycleMixin
        └── env_init.py             # ToolEnvInitializerMixin
```

Each file should be well-documented and include type annotations, Pydantic if needed, and no CLI printing — use `IntegrationResult` and logging only.

---

## 1️⃣ Step-by-Step Tasks

---

### 🧩 1. `toolkit/protocol.py`

**Task:** Define `QuackToolPluginProtocol`.

#### ✅ What to Include:

- All properties and methods listed below:

```python
class QuackToolPluginProtocol(Protocol):
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    @property
    def logger(self) -> Logger: ...
    
    def get_metadata(self) -> QuackPluginMetadata: ...
    
    def initialize(self) -> IntegrationResult: ...
    
    def is_available(self) -> bool: ...
    
    def process_file(
        self,
        file_path: str,
        output_path: str | None = None,
        options: Dict[str, Any] | None = None
    ) -> IntegrationResult: ...
```

**Why:** This lets us enforce structure and enable plugin discovery via `plugins`.

---

### 🔨 2. `toolkit/base.py`

**Task:** Move the core `BaseQuackToolPlugin` from `tool_plugin.py` into here, refactor it to:

- **Inherit from `QuackToolPluginProtocol`**
- **Remove any hardcoded logic for GDrive or environment** — move those to mixins.

#### 🔧 Ensure the following are implemented:

- `__init__` creates `_temp_dir`, `_output_dir`, logger
- `_initialize_plugin()` is abstract
- `process_content()` is abstract
- `process_file()` calls into `workflow` module (eventually updated to use `FileWorkflowRunner`)
- `_get_output_extension()` returns `.json` (default)

---

### 🧬 3. `toolkit/mixins/integration_enabled.py`

**Task:** Create `IntegrationEnabledMixin`.

💯 Excellent observation, Rod — and you're absolutely right to pause here.

We **shouldn’t** create a separate mixin like `GoogleDriveEnabledMixin`, `GoogleMailEnabledMixin`, `GitHubEnabledMixin`, etc. for every integration. That approach doesn't scale and tightly couples each integration to `quackcore.toolkit`.

Instead, let’s **refactor the pattern** you’re seeing into something composable and scalable across all integrations — using the existing architecture in `quackcore.integrations.core`.

---

# ✅ Revised Plan: `IntegrationEnabledMixin` + Standardized Service Resolution

---

## 🧠 Design Principle

> 🧩 All integrations (Drive, Mail, GitHub, Notion, etc.) should be **injected** or **resolved by type**, not hardcoded or per-mixin.

---

## ✅ New Design

### 🔄 Replace `GoogleDriveEnabledMixin` with:

### ✅ `IntegrationEnabledMixin`

```python
# quackcore/toolkit/mixins/integration_enabled.py

from typing import Type, Optional, TypeVar, Generic
from quackcore.integrations.core import get_integration_service
from quackcore.integrations.core.protocols import BaseIntegrationService

T = TypeVar("T", bound=BaseIntegrationService)

class IntegrationEnabledMixin(Generic[T]):
    """
    Mixin that enables integration with a specified service type.
    """
    _integration_service: Optional[T] = None

    def resolve_integration(self, service_type: Type[T]) -> Optional[T]:
        """
        Lazily load the integration service of the given type.
        Stores the result for reuse.
        """
        if self._integration_service is None:
            self._integration_service = get_integration_service(service_type)
            if self._integration_service and hasattr(self._integration_service, "initialize"):
                self._integration_service.initialize()
        return self._integration_service

    def get_integration_service(self) -> Optional[T]:
        return self._integration_service
```

---

### 🔍 How to Use in a Tool

Instead of:

```python
class MyTool(GoogleDriveEnabledMixin, BaseQuackToolPlugin):
```

You do:

```python
class MyTool(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):

    def _initialize_plugin(self):
        self._drive = self.resolve_integration(GoogleDriveService)
        ...
```

You now have:
- ✅ Lazy-loaded, optionally initialized Drive support
- ✅ The same pattern works for GitHubService, NotionService, etc.
- ✅ Future-proofed architecture
- ✅ No bloat in `toolkit.mixins`

---

## 💡 Bonus: You Can Add Shortcuts

If you want more ergonomics in tools using only 1 service, the base class could optionally expose:

```python
@property
def integration(self) -> T:
    return self.get_integration_service()
```

So the tool can just do `self.integration.download()`.

---

## 🛠 Changes to Make

| File | Change |
|------|--------|
| `quackcore/toolkit/mixins/integration_enabled.py` | ✅ **Add** new generic integration mixin |
| `quackcore/__init__.py` | ✅ Add `IntegrationEnabledMixin` to `toolkit.__all__` |
| `BaseQuackToolPlugin` | ✅ Stop initializing `GoogleDriveService` directly |
| Any tool using Drive | ✅ Migrate to `resolve_integration(GoogleDriveService)` |

---

## ✅ Benefits of This Approach

| Benefit | Why it matters |
|--------|----------------|
| ✅ Scalable | No new mixin per service |
| ✅ DRY | Uses `get_integration_service()` — centralized |
| ✅ Flexible | Tools can use any combo of services |
| ✅ Explicit | Service type is passed directly — no magic attributes |
| ✅ Consistent | Works with all current and future integrations |

---

### 🧱 4. `toolkit/mixins/output_handler.py`

**Task:** Create `OutputFormatMixin`.

#### 🔧 Responsibilities:

- Implement `_get_output_extension()`
- Default to `.json`
- Allow override in tools (e.g., `.yaml`, `.md`)
- Later can be extended with a `write_output()` method if tools want to write manually

---

### 🧪 5. `toolkit/mixins/env_init.py`

**Task:** Create `ToolEnvInitializerMixin`.

#### 🔧 Responsibilities:

- Implement `_initialize_environment()` method
- This method should:
  - Dynamically `import tool_name`
  - Call `initialize()` if present
- Handle `ImportError` or `AttributeError` safely

---

### 🧩 6. `toolkit/mixins/lifecycle.py`

**Task:** Create `QuackToolLifecycleMixin`.

#### 🔧 Responsibilities:

- Add optional methods:
  - `run()` → full logic runner
  - `upload()` → post-run uploader
  - `validate()` → input/output checker
- These should all:
  - Use logging
  - Return `IntegrationResult`
  - Default to no-op if not overridden

---

### 📦 7. `toolkit/__init__.py`

**Task:** Public API surface.

```python
from .base import BaseQuackToolPlugin
from .protocol import QuackToolPluginProtocol
from .mixins.integration_enabled import IntegrationEnabledMixin
from .mixins.output_handler import OutputFormatMixin
from .mixins.env_init import ToolEnvInitializerMixin
from .mixins.lifecycle import QuackToolLifecycleMixin

__all__ = [
    "BaseQuackToolPlugin",
    "QuackToolPluginProtocol",
    "IntegrationEnabledMixin",
    "OutputFormatMixin",
    "ToolEnvInitializerMixin",
    "QuackToolLifecycleMixin",
]
```

---

## 🧪 Testing and Linting

- Ensure each mixin can be unit tested in isolation.
- Add a `tests/toolkit/test_base.py` to instantiate a dummy tool and call `initialize()`, `process_file()` etc.
- Use `pytest` and `mypy` to validate structure and compatibility with Protocols.

---

## ✅ Summary Table for the Developer

| File | Purpose | Key Interfaces |
|------|---------|----------------|
| `base.py` | Core plugin class | `BaseQuackToolPlugin` |
| `protocol.py` | Plugin interface | `QuackToolPluginProtocol` |
| `mixins/integration_enabled.py` | Adds Integration support | `IntegrationEnabledMixin` |
| `mixins/output_handler.py` | Output format hooks | `OutputFormatMixin` |
| `mixins/env_init.py` | Dynamic init() import | `ToolEnvInitializerMixin` |
| `mixins/lifecycle.py` | Adds `run/validate/upload()` | `QuackToolLifecycleMixin` |

---

## 🧠 Bonus: Optional Dev Tips

- Use `quackcore.fs.service.get_service()` for all file ops.
- Do **not** import directly from `plugins` — toolkit should be independent.
- Use type hints (`str | None`, `IntegrationResult`, `Dict[str, Any]`) throughout.

---
"""