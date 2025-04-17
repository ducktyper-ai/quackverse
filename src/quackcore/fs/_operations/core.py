# src/quackcore/fs/_operations/core.py
"""
Core path resolution and utility functionality for filesystem _operations.

This module provides internal helper functions for path resolution and
initialization tasks. These functions are used by the FileSystemOperations
class and its mixins but are not meant to be consumed directly by external code.
"""

import mimetypes
import os
from pathlib import Path

from quackcore.fs import DataResult, OperationResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


def _resolve_path(
    base_dir: str | Path, path: str | os.PathLike | DataResult | OperationResult
) -> str:
    """
    Resolve a path relative to the base directory.

    This function takes a path (string, Path object, DataResult, or OperationResult) and
    resolves it relative to the provided base directory. If the path is absolute, it's
    returned as-is. Otherwise, it's joined with the base directory.

    Args:
        base_dir: Base directory for resolution
        path: Path to resolve (str, Path, DataResult, or OperationResult)

    Returns:
        str: Resolved path as a string

    Note:
        This is an internal helper function not meant for external consumption.
        It's used by the _resolve_path method in FileSystemOperations.
    """
    # If it's a DataResult or OperationResult, extract the path data
    if isinstance(path, (DataResult, OperationResult)) and hasattr(path, "data"):
        path_content = path.data
    # If path is a Path object, convert to string for consistent handling
    elif isinstance(path, Path):
        path_content = str(path)
    else:
        path_content = path

    # Now process the path_content
    try:
        path_obj = Path(path_content)
        if not path_obj.is_absolute():
            logger.debug(f"Resolved relative path: {path} -> {path_obj}")
            return str(Path(base_dir) / path_content)
        return str(path_obj)
    except TypeError:
        # Fallback to string conversion if Path fails
        path_str = str(path_content)
        if os.path.isabs(path_str):
            logger.debug(f"Using absolute path: {path_str}")
            return path_str
        return os.path.join(base_dir, path_str)


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
