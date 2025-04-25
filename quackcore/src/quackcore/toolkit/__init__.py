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

### 🔨 2. `toolkit/base.py (BaseQuackToolPlugin)`

#### 🔧 Ensure the following are implemented:

- `__init__` creates `_temp_dir`, `_output_dir`, logger
- `_initialize_plugin()` is abstract
- `process_content()` is abstract
- `process_file()` calls into `workflow` module (eventually updated to use `FileWorkflowRunner`)
- `_get_output_extension()` connect it to output writing by providing DefaultOutputWriter with a hint.
- Call setup_tool_logging() automatically inside BaseQuackToolPlugin.__init__() with the tool’s name.

Use FileWorkflowRunner internally for process_file(). Something like:
```python
def process_file(self, file_path: str, output_path: str | None = None, options: dict[str, Any] | None = None) -> IntegrationResult:
    try:
        runner = FileWorkflowRunner(
            processor=self.process_content,
            remote_handler=self.get_remote_handler(),   # optional
            output_writer=self.get_output_writer(),     # optional
        )
        result = runner.run(file_path, options or {})

        if result.success:
            return IntegrationResult.success_result(
                content=result,
                message="File processed successfully"
            )
        else:
            return IntegrationResult.error_result(
                error=result.metadata.get("error_message", "Unknown error"),
                message="File processing failed"
            )
    except Exception as e:
        self.logger.exception("Failed to process file")
        return IntegrationResult.error_result(str(e))
```

➡️ This way, tool authors don't have to think about input detection, output writing, errors, dry run — they just focus on process_content().

✅ Also: Call setup_tool_logging() automatically inside BaseQuackToolPlugin.__init__() with the tool’s name.

✅ _initialize_plugin() and process_content() still abstract methods → good.

✅ _get_output_extension() can stay, but ideally connect it to output writing by providing DefaultOutputWriter with a hint.

→ FileWorkflowRunner
- Handles local/remote files automatically
- Handles dry runs, temp dirs
- Better structured metadata
- Customizable writers
- More consistent error handling
- Future-proof with arazzo conventions

---

### 🧬 3. `toolkit/mixins/integration_enabled.py`

**Task:** Create `IntegrationEnabledMixin`.

We **shouldn’t** create a separate mixin like `GoogleDriveEnabledMixin`, `GoogleMailEnabledMixin`, `GitHubEnabledMixin`, etc. for every integration. That approach doesn't scale and tightly couples each integration to `quackcore.toolkit`.

Instead, let’s **refactor the pattern** we’re seeing into something composable and scalable across all integrations — using the existing architecture in `quackcore.integrations.core`.

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
Lazily load the integration service of the given type. Stores the result for reuse.
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

## 💡 Bonus: Let's Add Shortcuts

We want more ergonomics in tools using only 1 service, the base class should optionally expose:

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

Instead of only _get_output_extension(), also offer:
```python

def get_output_writer(self) -> OutputWriter | None:
    """Override to return a custom OutputWriter if the tool wants."""
    return None
```
➡️ So in BaseQuackToolPlugin, it can check:
```python

self.output_writer = self.get_output_writer()
```
This makes outputting in different formats (YAML, XML, Markdown) possible if a tool wants it later — without hardcoding anything today.

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

Also add optional pre_run() and post_run() hooks, like:

```python
def pre_run(self) -> IntegrationResult:
    """Prepare before running (e.g., check prerequisites)."""
    return IntegrationResult.success_result()

def post_run(self) -> IntegrationResult:
    """Clean up or finalize after running."""
    return IntegrationResult.success_result()
```
➡️ Modern workflows often need this separation.

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

## 🧠 Tips:

- Use `quackcore.fs.service.get_service()` for all file ops.
- Do **not** import directly from `plugins` — toolkit should be independent.
- Use type hints (`str | None`, `IntegrationResult`, `dict[str, Any]`) throughout.

---
