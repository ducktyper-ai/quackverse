# src/quackcore/fs/utils/temp.py
"""
Utility functions for temporary files and directories.
"""

import os
import tempfile
from pathlib import Path

from quackcore.errors import QuackIOError, wrap_io_errors
from quackcore.logging import get_logger

# Import from within package
from .file_ops import ensure_directory

# Initialize module logger
logger = get_logger(__name__)


@wrap_io_errors
def create_temp_directory(prefix: str = "quackcore_", suffix: str = "") -> Path:
    """
    Create a temporary directory.

    Args:
        prefix: Directory name prefix
        suffix: Directory name suffix

    Returns:
        Path to the created temporary directory

    Raises:
        QuackIOError: For IO related issues
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix)
        logger.debug(f"Created temporary directory: {temp_dir}")
        return Path(temp_dir)
    except Exception as e:
        logger.error(f"Failed to create temporary directory: {e}")
        raise QuackIOError(f"Failed to create temporary directory: {e}") from e


@wrap_io_errors
def create_temp_file(
    suffix: str = ".txt",
    prefix: str = "quackcore_",
    directory: str | Path | None = None,
) -> Path:
    """
    Create a temporary file.

    Args:
        suffix: File suffix (e.g., ".txt")
        prefix: File prefix
        directory: Directory to create the file in (default: system temp dir)

    Returns:
        Path to the created temporary file

    Raises:
        QuackIOError: For IO related issues
    """
    dir_path = Path(directory) if directory else None
    if dir_path:
        ensure_directory(dir_path)

    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir_path)
        os.close(fd)  # Close the file descriptor
        logger.debug(f"Created temporary file: {path}")
        return Path(path)
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise QuackIOError(f"Failed to create temporary file: {e}") from e
