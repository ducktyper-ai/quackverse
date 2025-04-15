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
        path: Path to split

    Returns:
        List of path components
    """
    parts = list(Path(path).parts)
    if str(path).startswith("./"):
        parts.insert(0, ".")
    logger.debug(f"Split path {path} into {parts}")
    return parts


def _join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    Args:
        *parts: Path parts to join

    Returns:
        Joined Path object
    """
    result = Path(*parts)
    logger.debug(f"Joined path parts {parts} to {result}")
    return result


def _expand_user_vars(path: str | Path) -> Path:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables

    Returns:
        Expanded Path object
    """
    path_str = os.path.expanduser(str(path))
    path_str = os.path.expandvars(path_str)
    result = Path(path_str)

    if str(result) != str(path):
        logger.debug(f"Expanded path variables: {path} -> {result}")

    return result
