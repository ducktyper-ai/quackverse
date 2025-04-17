# src/quackcore/fs/_operations/__init__.py
"""
Core filesystem _operations implementation.

This module provides the implementation of filesystem _operations
with proper error handling and consistent return values. It assembles
all the operation mixins into the FileSystemOperations class,
which is the primary internal implementation used by the public API.

The _operations package follows this contract:
- Internal methods (with '_' prefix) can return basic types like Path
- All public methods return Result objects (WriteResult, ReadResult, etc.)
- Input types are flexible (str | Path) and resolved early
- Comprehensive error handling and logging throughout
"""

import os
from pathlib import Path
from typing import TypeVar

# Import utility functions directly into this namespace for backward compatibility
# This will make patching work correctly in tests
from quackcore.fs._helpers import (
    _atomic_write,
    _compute_checksum,
    _ensure_directory,
    _safe_copy,
    _safe_delete,
    _safe_move,
)
from quackcore.logging import get_logger

from .. import DataResult, OperationResult

# Set up module-level logger
logger = get_logger(__name__)

# Import all the mixins we need
from .core import _initialize_mime_types, _resolve_path
from .directory_ops import DirectoryOperationsMixin
from .file_info import FileInfoOperationsMixin
from .find_ops import FindOperationsMixin
from .read_ops import ReadOperationsMixin
from .serialization_ops import SerializationOperationsMixin
from .write_ops import WriteOperationsMixin


# Define the FileSystemOperations class properly with all mixins
class FileSystemOperations(
    ReadOperationsMixin,
    WriteOperationsMixin,
    FileInfoOperationsMixin,
    DirectoryOperationsMixin,
    FindOperationsMixin,
    SerializationOperationsMixin,
):
    """
    Core implementation of filesystem _operations.

    This class combines all operation mixins to provide a complete
    filesystem _operations implementation with consistent error handling,
    logging, and return types. It serves as the internal implementation
    layer used by the public API in quackcore.fs.service.

    All methods follow this contract:
    - Internal methods (with '_' prefix) can return basic types like Path
    - External methods return Result objects (WriteResult, ReadResult, etc.)
    - All methods accept flexible input paths (str | Path)
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """
        Initialize filesystem _operations.

        Args:
            base_dir: Optional base directory for relative paths.
                     If not provided, the current working directory is used.
        """
        from pathlib import Path

        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        logger.debug(f"Initialized FileSystemOperations with base_dir: {self.base_dir}")
        _initialize_mime_types()

    def _resolve_path(
        self, path: str | os.PathLike | DataResult | OperationResult
    ) -> Path:
        """
        Resolve a path relative to the base directory.

        This method normalizes all path inputs to Path objects and resolves them
        relative to the base directory set during initialization.

        Args:
            path: Path to resolve (str, Path, DataResult, or OperationResult)

        Returns:
            Path: Resolved Path object

        Note:
            This is an internal helper method called by all other methods.
            It implements the abstract method defined in the mixins.
        """
        resolved = _resolve_path(self.base_dir, path)
        return Path(resolved)


# Re-export the FileSystemOperations class and utility functions for backward compatibility
__all__ = [
    "FileSystemOperations",
    "_atomic_write",
    "_compute_checksum",
    "_ensure_directory",
    "_safe_copy",
    "_safe_delete",
    "_safe_move",
]

# Export TypeVar T for backward compatibility
T = TypeVar("T")  # Generic type for flexible typing
