# quackcore/src/quackcore/fs/_operations/core.py
"""
Core path resolution and utility functionality for filesystem _operations.

This module provides internal helper functions for path resolution and
initialization tasks. These functions are used by the FileSystemOperations
class and its mixins but are not meant to be consumed directly by external code.
"""

import mimetypes
import os
from pathlib import Path
from typing import Any

from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


def _resolve_path(
    base_dir: str | Path, path: Any
) -> Path:
    """
    Resolve a path relative to the base directory.

    This function takes a path (string, Path object, or any object with a 'data' attribute)
    and resolves it relative to the provided base directory. If the path is absolute, it's
    returned as-is. Otherwise, it's joined with the base directory.

    Args:
        base_dir: Base directory for resolution
        path: Path to resolve (str, Path, or any object with a 'data' attribute)

    Returns:
        Path: Resolved Path object

    Note:
        This is an internal helper function not meant for external consumption.
        It's used by the _resolve_path method in FileSystemOperations.
    """
    # If it's a DataResult or OperationResult, extract the path data
    if hasattr(path, "data"):
        path_content = path.data
    # If path is a Path object, use it directly
    elif isinstance(path, Path):
        path_content = path
    else:
        path_content = path

    # Now process the path_content
    try:
        path_obj = Path(path_content)
        if not path_obj.is_absolute():
            logger.debug(f"Resolved relative path: {path} -> {path_obj}")
            return Path(base_dir) / path_content
        return path_obj
    except TypeError:
        # Fallback to string conversion if Path fails
        path_str = str(path_content)
        if os.path.isabs(path_str):
            logger.debug(f"Using absolute path: {path_str}")
            return Path(path_str)
        return Path(base_dir) / path_str


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
