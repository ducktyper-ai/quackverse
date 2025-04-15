# src/quackcore/fs/operations/__init__.py
"""
Core filesystem operations implementation.

This module provides the implementation of filesystem operations
with proper error handling and consistent return values.
"""

from typing import TypeVar

# Import utility functions directly into this namespace for backward compatibility
# This will make patching work correctly in tests
from quackcore.fs.helpers import (
    _atomic_write,
    _compute_checksum,
    _ensure_directory,
    _safe_copy,
    _safe_delete,
    _safe_move,
)
from quackcore.logging import get_logger

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
    """Core implementation of filesystem operations."""

    def __init__(self, base_dir=None) -> None:
        """
        Initialize filesystem operations.

        Args:
            base_dir: Optional base directory for relative paths
        """
        from pathlib import Path

        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        logger.debug(f"Initialized FileSystemOperations with base_dir: {self.base_dir}")
        _initialize_mime_types()

    def _resolve_path(self, path):
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve

        Returns:
            Resolved Path object
        """
        return _resolve_path(self.base_dir, path)


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
