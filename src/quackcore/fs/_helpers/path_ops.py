# src/quackcore/fs/_helpers/path_ops.py
"""
Utility functions for path _operations.
"""

import os
from pathlib import Path

from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


def _split_path(path: str | Path) -> list[str]:
    """
    Split a path into its components.

    Args:
        path: Path to split (string or Path)

    Returns:
        List of path components
    """
    # Normalize to Path object
    path_obj = Path(path)

    parts = list(path_obj.parts)
    if str(path).startswith("./"):
        parts.insert(0, ".")
    logger.debug(f"Split path {path} into {parts}")
    return parts


def _join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    Args:
        *parts: Path parts to join (strings or Paths)

    Returns:
        Joined Path object
    """
    # Normalize all parts to strings before joining
    normalized_parts = [str(part) for part in parts]
    result = Path(*normalized_parts)
    logger.debug(f"Joined path parts {parts} to {result}")
    return result


def _expand_user_vars(path: str | Path) -> Path:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables (string or Path)

    Returns:
        Expanded Path object
    """
    # Normalize to string first
    path_str = str(path)

    # Expand user and environment variables
    path_str = os.path.expanduser(path_str)
    path_str = os.path.expandvars(path_str)

    # Convert back to Path object
    result = Path(path_str)

    if str(result) != str(path):
        logger.debug(f"Expanded path variables: {path} -> {result}")

    return result
