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
        path1: First path (string or Path)
        path2: Second path (string or Path)

    Returns:
        True if paths refer to the same file
    """
    # Normalize inputs to Path objects
    path1_obj = Path(path1)
    path2_obj = Path(path2)

    try:
        return os.path.samefile(str(path1_obj), str(path2_obj))
    except OSError:
        # If one or both files don't exist, compare normalized paths.
        return _normalize_path(path1_obj) == _normalize_path(path2_obj)


def _is_subdirectory(child: str | Path, parent: str | Path) -> bool:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path (string or Path)
        parent: Potential parent path (string or Path)

    Returns:
        True if child is a subdirectory of parent
    """
    # Normalize inputs to Path objects
    child_path = _normalize_path(Path(child))
    parent_path = _normalize_path(Path(parent))

    # A directory cannot be a subdirectory of itself
    if child_path == parent_path:
        return False

    try:
        child_path.relative_to(parent_path)
        return True
    except ValueError:
        return False
