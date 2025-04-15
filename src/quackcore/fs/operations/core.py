# src/quackcore/fs/operations/core.py
"""
Core path resolution and utility functionality for filesystem operations.

This module provides internal helper functions for path resolution and
initialization tasks. These functions are used by the FileSystemOperations
class and its mixins but are not meant to be consumed directly by external code.
"""

import mimetypes
from pathlib import Path

from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


def _resolve_path(base_dir: Path, path: str | Path) -> Path:
    """
    Resolve a path relative to the base directory.

    This function takes a path (either string or Path object) and resolves it
    relative to the provided base directory. If the path is absolute, it's
    returned as-is. Otherwise, it's joined with the base directory.

    Args:
        base_dir: Base directory for resolution
        path: Path to resolve

    Returns:
        Path: Resolved Path object

    Note:
        This is an internal helper function not meant for external consumption.
        It's used by the _resolve_path method in FileSystemOperations.
    """
    path_obj = Path(path)

    if path_obj.is_absolute():
        logger.debug(f"Using absolute path: {path_obj}")
        return path_obj

    resolved = base_dir / path_obj
    logger.debug(f"Resolved relative path: {path} -> {resolved}")
    return resolved


def _initialize_mime_types() -> None:
    """
    Initialize MIME types database.

    This function ensures the MIME types database is properly initialized
    for file type detection.

    Note:
        This is an internal helper function not meant for external consumption.
        It's called during FileSystemOperations initialization.
    """
    mimetypes.init()
    logger.debug("MIME types database initialized")
