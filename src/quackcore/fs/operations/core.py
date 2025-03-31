# src/quackcore/fs/operations/core.py
"""
Core path resolution and utility functionality for filesystem operations.
"""

import mimetypes
from pathlib import Path

from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


def resolve_path(base_dir: Path, path: str | Path) -> Path:
    """
    Resolve a path relative to the base directory.

    Args:
        base_dir: Base directory for resolution
        path: Path to resolve

    Returns:
        Resolved Path object
    """
    path_obj = Path(path)

    if path_obj.is_absolute():
        logger.debug(f"Using absolute path: {path_obj}")
        return path_obj

    resolved = base_dir / path_obj
    logger.debug(f"Resolved relative path: {path} -> {resolved}")
    return resolved


def initialize_mime_types() -> None:
    """Initialize MIME types database."""
    mimetypes.init()
    logger.debug("MIME types database initialized")
