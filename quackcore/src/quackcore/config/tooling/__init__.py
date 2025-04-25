# quackcore/src/quackcore/config/tooling/__init__.py
"""
4. ✅ quackcore.config.tooling – EXTENSION MODULE
⚙️ Add helper classes to reduce boilerplate in QuackTool configs.
We can expose:

load_tool_config()
A QuackToolConfigModel base class
Defaults for logging, credential location, environment

```python
# src/quackmetadata/quackcore_candidate/config/config.py
"""
Configuration management for QuackMetadata.

This module uses QuackCore's configuration system to manage settings
for the QuackMetadata application.
"""

import atexit
import logging
import os
from typing import Any

from pydantic import BaseModel, Field
from quackcore.config import load_config
from quackcore.config.models import QuackConfig

# Import QuackCore FS service and helper function.
from quackcore.fs.service import get_service

fs = get_service()

# Keep track of open file handlers to ensure they get closed.
_file_handlers: list[logging.FileHandler] = []

@atexit.register
def _close_file_handlers() -> None:
    """
    Close all file handlers when the program exits.

    This helps avoid resource warnings during test runs.
    """
    for handler in _file_handlers:
        if handler:
            handler.close()
    _file_handlers.clear()

class QuackMetadataConfig(BaseModel):
    """
    QuackMetadata-specific configuration model.

    This model defines the configuration structure specific to QuackMetadata,
    which will be stored in the 'custom' section of the QuackCore config.
    """

    default_prompt_template: str = Field(
        default="generic",
        description="Default prompt template for metadata extraction",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum retries for LLM calls",
        ge=1,
        le=10,
    )

    output_format: str = Field(
        default="json",
        description="Default output format for metadata",
    )

    temp_dir: str = Field(
        default="./temp",
        description="Directory for temporary files",
    )

    output_dir: str = Field(
        default="./output",
        description="Default directory for output files",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level for QuackMetadata",
    )

def initialize_config(config_path: str | None = None) -> QuackConfig:
    """
    Initialize configuration from a file and set up defaults.

    Args:
        config_path: Optional path to configuration file

    Returns:
        QuackConfig object with QuackMetadata-specific configuration
    """
    global _config
    _config = None

    # Load configuration from file or defaults.
    quack_config = load_config(config_path)

    # Initialize QuackMetadata-specific configuration if not present.
    if hasattr(quack_config.custom, "get"):
        if "quackmetadata" not in quack_config.custom:
            quack_config.custom["quackmetadata"] = QuackMetadataConfig().model_dump()
        metadata_config = quack_config.custom.get("quackmetadata", {})
    else:
        if not hasattr(quack_config.custom, "quackmetadata"):
            quack_config.custom.quackmetadata = QuackMetadataConfig().model_dump()
        metadata_config = getattr(quack_config.custom, "quackmetadata", {})

    # Get the log level from metadata_config.
    log_level_name = (
        metadata_config.get("log_level", "INFO")
        if isinstance(metadata_config, dict)
        else getattr(metadata_config, "log_level", "INFO")
    )
    log_level = getattr(logging, log_level_name, logging.INFO)

    # When running tests, use minimal logging configuration to avoid file handle issues.
    if "PYTEST_CURRENT_TEST" in os.environ:
        logging.basicConfig(level=log_level, force=True)
        logs_dir = "./logs"  # Default value
        fs.create_directory(logs_dir, exist_ok=True)
        return quack_config

    # In normal operation, use full logging configuration.
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    has_console_handler = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root_logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            root_logger.removeHandler(handler)
            handler.close()

    global _file_handlers

    # Use default fallback for logs_dir.
    logs_dir = "./logs"
    if hasattr(quack_config.paths, "logs_dir"):
        logs_dir = quack_config.paths.logs_dir

    # Ensure the logs directory exists using FS.
    fs.create_directory(logs_dir, exist_ok=True)

    try:
        log_file = fs.join_path(logs_dir, "quackmetadata.log")
        file_handler = logging.FileHandler(str(log_file), mode="a")
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
        _file_handlers.append(file_handler)  # Track for cleanup.
    except (OSError, PermissionError):
        pass

    return quack_config

_config = None

def get_config() -> QuackConfig:
    """
    Get the QuackMetadata configuration.

    Uses lazy initialization to avoid resource issues during testing.

    Returns:
        QuackConfig instance
    """
    global _config
    if _config is None:
        _config = initialize_config()
    return _config

def get_tool_config() -> dict[str, Any]:
    """
    Get the QuackMetadata-specific configuration.

    Returns:
        Dictionary containing QuackMetadata configuration
    """
    config = get_config()
    if hasattr(config.custom, "get"):
        metadata_config = config.custom.get("quackmetadata", {})
    else:
        metadata_config = getattr(config.custom, "quackmetadata", {})
    return metadata_config

def update_tool_config(new_config: dict[str, Any]) -> None:
    """
    Update the QuackMetadata-specific configuration.

    Args:
        new_config: Dictionary containing new configuration values
    """
    config = get_config()
    tool_config = get_tool_config()

    if isinstance(tool_config, dict):
        updated_config = dict(tool_config)
        updated_config.update(new_config)
    else:
        updated_config = new_config

    if hasattr(config.custom, "get"):
        config.custom["quackmetadata"] = updated_config
    else:
        config.custom.quackmetadata = updated_config

def get_logger() -> logging.Logger:
    """
    Get the QuackMetadata logger.

    Returns:
        Logger instance for QuackMetadata
    """
    from quackcore.logging import get_logger

    return get_logger("quackmetadata")

```

Absolutely — let’s spec out `quackcore.config.tooling` as a formal extension module that unlocks **clean, minimal, and idiomatic configuration for QuackTools**, without tool-specific logic leaking into core modules.

---

# ⚙️ `quackcore.config.tooling` — Tool Config Made Simple

---

## 🎯 Purpose

`quackcore.config.tooling` exists to:

| Goal | Description |
|------|-------------|
| ✅ Reduce boilerplate | Avoid every QuackTool reinventing `get_config()`, `update_config()`, and logger setup |
| 🧱 Enforce a pattern | Ensure tools define their own `ConfigModel`, live under `custom.tool_name` in YAML |
| 🧼 Separate concerns | Keep `quackcore.config` focused on generic config resolution |
| 🧰 Enable toolkit plug-and-play | Used by `BaseQuackToolPlugin` and friends in `quackcore.toolkit` |
| 🧪 Improve testability | Standardized config makes mocking, resetting, and injecting config state trivial |

---

## 🔍 What Problem Does It Solve?

Almost every QuackTool needs:

- A typed Pydantic model for tool settings
- A way to inject default config values into `quack_config.custom`
- Consistent logging setup (especially during testing)
- A way to override config via YAML or programmatically

We want this to be **declarative** and **automatic**, not re-coded for every tool.

---

## ✅ Responsibilities of `config.tooling`

| Function | Description |
|---------|-------------|
| `load_tool_config()` | Loads the full `QuackConfig`, injects defaults, returns `(quack_config, tool_config)` |
| `QuackToolConfigModel` | Abstract base Pydantic model for tool-specific config |
| `setup_tool_logging()` | Handles log level, console/file output, test-friendly atexit handling |
| `update_tool_config()` | Programmatically updates the config in memory |
| `get_logger(tool_name)` | Returns a scoped logger (without re-importing `logging`) |

---

## 🧱 Module Layout

```
quackcore/
└── config/
    └── tooling/
        ├── __init__.py            # Public API
        ├── base.py                # Base config model
        ├── loader.py              # load_tool_config, update_tool_config
        ├── logger.py              # setup_tool_logging, get_logger
```

---

## 🧠 Design Philosophy

- All config is stored under: `quack_config.custom.<tool_slug>`
- Tool config model is declared in each tool (not in QuackCore)
- Tool config is lazily injected at load time if missing
- Logging is consistent across tools
- Test runs auto-clean file handlers using `atexit`

---

## 🧰 How to Use in a Tool

### In `tool_config.py` (inside a QuackTool repo):

```python
from pydantic import BaseModel, Field
from quackcore.config.tooling.base import QuackToolConfigModel

class QuackMetadataConfig(QuackToolConfigModel):
    default_prompt_template: str = Field(default="generic")
    max_retries: int = Field(default=3)
    output_format: str = Field(default="json")
    temp_dir: str = Field(default="./temp")
    output_dir: str = Field(default="./output")
    log_level: str = Field(default="INFO")
```

### In `tool.py`:

```python
from quackcore.config.tooling import load_tool_config, setup_tool_logging
from .tool_config import QuackMetadataConfig

quack_config, metadata_config = load_tool_config(
    tool_name="quackmetadata",
    config_model=QuackMetadataConfig,
)

setup_tool_logging(tool_name="quackmetadata", log_level=metadata_config.log_level)
```

You now have:
- A `quack_config` with full access
- A typed `metadata_config`
- Logging ready to go

No need for custom `_config = None` globals.  
No hand-written `initialize_config()` per tool.  
And during testing, all logs clean up automatically.

---

## 📘 Example: `load_tool_config`

```python
def load_tool_config(
    tool_name: str,
    config_model: Type[QuackToolConfigModel],
    config_path: str | None = None
) -> tuple[QuackConfig, QuackToolConfigModel]:
    """
    Load and inject tool-specific config into QuackConfig.

    Returns:
        Tuple of (quack_config, typed tool_config)
    """
    config = load_config(config_path)

    # Insert default if missing
    if tool_name not in config.custom:
        config.custom[tool_name] = config_model().model_dump()

    tool_data = config.custom.get(tool_name, {})
    tool_config = config_model(**tool_data)

    return config, tool_config
```

---

## 📘 Example: `setup_tool_logging`

```python
def setup_tool_logging(tool_name: str, log_level: str = "INFO") -> None:
    """
    Set up logging for a tool, using console and file output.
    """
    import logging, atexit
    from quackcore.fs.service import get_service

    fs = get_service()
    level = getattr(logging, log_level.upper(), logging.INFO)
    logs_dir = fs.normalize_path("./logs")

    fs.create_directory(logs_dir, exist_ok=True)
    file_path = fs.join_path(logs_dir, f"{tool_name}.log")

    logger = logging.getLogger()
    logger.setLevel(level)

    # Clean console handler
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        logger.addHandler(handler)

    # Clean file handler
    fh = logging.FileHandler(str(file_path))
    fh.setLevel(level)
    logger.addHandler(fh)

    @atexit.register
    def _cleanup_log_handlers():
        fh.close()
        logger.removeHandler(fh)
```

---

## 🚫 What *Doesn't* Belong in `config.tooling`

| Feature | Where it should go |
|---------|--------------------|
| Tool-specific config classes | ✅ Tool repo (`tool_config.py`) |
| Logging to remote services | ❌ Plugin layer or integrations |
| CLI-based config overrides | ❌ `ducktyper` or the CLI layer |
| Teaching metadata config | ❌ `quackcore.teaching` |

---

## ✅ Summary

`quackcore.config.tooling` provides:

- Declarative, idiomatic config loading for tools
- Safe defaults and runtime injection
- Seamless logging setup
- Boilerplate-free experience for tool developers

It complements `quackcore.toolkit` and is foundational for the smooth developer and learner experience promised by QuackVerse.
"""

"""
---

## 🦆 Project Goal

You’re going to build a new module inside `quackcore` called:

```
quackcore.config.tooling
```

This module helps all QuackTools load their config and setup logging the same way, so every tool doesn’t have to copy the same code.

---

## 🧱 Folder Structure to Create

You’ll be working inside this folder:

```
quackcore/src/quackcore/config/tooling/
```

Create these 4 files:

```
tooling/
├── __init__.py       ✅ Public API
├── base.py           ✅ Defines base config model
├── loader.py         ✅ Loads and updates config
├── logger.py         ✅ Sets up log handling
```

---

## 1. 🧩 `base.py` – Base Class for Tool Config

This defines a Pydantic base class that all QuackTools should inherit from.

```python
# quackcore/config/tooling/base.py

from pydantic import BaseModel

class QuackToolConfigModel(BaseModel):
    """
    Base class for QuackTool-specific config models.

    Tools should subclass this with their own fields.
    This base class exists so tooling can type-check config models.
    """
    pass
```

✅ You’re done with this file. Super short and simple.

---

## 2. 📦 `loader.py` – Load and Update Config

This file gives tools the `load_tool_config()` and `update_tool_config()` helpers.

Start with this:

```python
# quackcore/config/tooling/loader.py

from typing import Type, Tuple
from quackcore.config import load_config
from quackcore.config.models import QuackConfig
from .base import QuackToolConfigModel


def load_tool_config(
    tool_name: str,
    config_model: Type[QuackToolConfigModel],
    config_path: str | None = None
) -> Tuple[QuackConfig, QuackToolConfigModel]:
    """
    Load and inject tool-specific config into QuackConfig.

    If the tool doesn't already have config stored in quack_config.custom,
    this function will add the default values from config_model.

    Returns:
        Tuple of (QuackConfig object, tool-specific config model)
    """
    config = load_config(config_path)

    if tool_name not in config.custom:
        config.custom[tool_name] = config_model().model_dump()

    tool_data = config.custom.get(tool_name, {})
    tool_config = config_model(**tool_data)

    return config, tool_config


def update_tool_config(
    config: QuackConfig,
    tool_name: str,
    new_data: dict
) -> None:
    """
    Update a tool's config section in the QuackConfig.

    Args:
        config: The QuackConfig object
        tool_name: e.g. "quackmetadata"
        new_data: New dictionary to merge into config.custom[tool_name]
    """
    old_data = config.custom.get(tool_name, {})
    if isinstance(old_data, dict):
        updated = {**old_data, **new_data}
    else:
        updated = new_data
    config.custom[tool_name] = updated
```

✅ This file is done.

---

## 3. 🔊 `logger.py` – Set Up Console and File Logging

This part takes care of logging to terminal and file with safe cleanup during tests.

```python
# quackcore/config/tooling/logger.py

import logging
import atexit
from quackcore.fs.service import get_service

_file_handlers = []


def setup_tool_logging(tool_name: str, log_level: str = "INFO") -> None:
    """
    Set up logging for a QuackTool.

    This sets the global log level, adds a console logger and a file logger,
    and ensures log files are cleaned up during tests.
    """
    fs = get_service()
    level = getattr(logging, log_level.upper(), logging.INFO)

    logs_dir = fs.normalize_path("./logs")
    fs.create_directory(logs_dir, exist_ok=True)
    log_file = fs.join_path(logs_dir, f"{tool_name}.log")

    logger = logging.getLogger()
    logger.setLevel(level)

    # Console handler (prints to screen)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        logger.addHandler(ch)

    # File handler (saves to file)
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(level)
    logger.addHandler(fh)
    _file_handlers.append(fh)

    @atexit.register
    def _cleanup_handlers():
        for h in _file_handlers:
            h.close()
            logger.removeHandler(h)


def get_logger(tool_name: str) -> logging.Logger:
    """
    Get a named logger for the given tool.

    Args:
        tool_name: The tool name, e.g. 'quackmetadata'
    """
    return logging.getLogger(tool_name)
```

✅ Now logging works in tests and production with no surprises.

---

## 4. 🌐 `__init__.py` – What Tools Will Import

Your job is to make the import clean. Put this in:

```python
# quackcore/config/tooling/__init__.py

from .base import QuackToolConfigModel
from .loader import load_tool_config, update_tool_config
from .logger import setup_tool_logging, get_logger

__all__ = [
    "QuackToolConfigModel",
    "load_tool_config",
    "update_tool_config",
    "setup_tool_logging",
    "get_logger",
]
```

✅ Now tools can just do:

```python
from quackcore.config.tooling import load_tool_config
```

---

## ✅ Testing Plan

You can test it with this scratch script:

```python
# test_tool.py (not in quackcore, just for local testing)

from pydantic import Field
from quackcore.config.tooling import (
    QuackToolConfigModel,
    load_tool_config,
    update_tool_config,
    setup_tool_logging,
    get_logger,
)

class MyConfig(QuackToolConfigModel):
    name: str = Field("demo")
    log_level: str = Field("DEBUG")

config, tool_config = load_tool_config("testtool", MyConfig)
print(tool_config)

update_tool_config(config, "testtool", {"name": "updated"})

setup_tool_logging("testtool", tool_config.log_level)
logger = get_logger("testtool")
logger.debug("This should print and go to file.")
```

---

## 🧠 What NOT To Do

| Don't do this | Why |
|---------------|-----|
| Add `QuackMetadataConfig` inside `quackcore` | Each tool should own its own model |
| Assume a fixed config key like `quackmetadata` | Use `tool_name` argument instead |
| Copy all `quackmetadata/config.py` into quackcore | We’re modularizing it now 💪 |

---
"""