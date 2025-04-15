# src/quackcore/fs/_helpers/comparison.py
"""
Utility functions for comparing files and paths.
"""

import os
from pathlib import Path

from quackcore.logging import get_logger

# Import from within package
from .common import _normalize_path

# Initialize module logger
logger = get_logger(__name__)


def _is_same_file(path1: str | Path, path2: str | Path) -> bool:
    """
    Check if two paths refer to the same file.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if paths refer to the same file
    """
    try:
        return os.path.samefile(str(path1), str(path2))
    except OSError:
        # If one or both files don't exist, compare normalized paths.
        return _normalize_path(path1) == _normalize_path(path2)


def _is_subdirectory(child: str | Path, parent: str | Path) -> bool:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path
        parent: Potential parent path

    Returns:
        True if child is a subdirectory of parent
    """
    child_path = _normalize_path(child)
    parent_path = _normalize_path(parent)

    # A directory cannot be a subdirectory of itself
    if child_path == parent_path:
        return False

    try:
        child_path.relative_to(parent_path)
        return True
    except ValueError:
        return False
