# src/quackcore/fs/api/public/temp.py
"""
Public API for temporary file and directory _operations.

This module provides safe, result-oriented wrappers around low-level temporary
file and directory _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.temp import _create_temp_directory, _create_temp_file
from quackcore.fs.results import DataResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def create_temp_directory(
    prefix: str = "quackcore_", suffix: str = ""
) -> DataResult[str]:
    """
    Create a temporary directory.

    Args:
        prefix: Directory name prefix
        suffix: Directory name suffix

    Returns:
        DataResult with path to the created temporary directory
    """
    try:
        temp_dir = _create_temp_directory(prefix, suffix)

        return DataResult(
            success=True,
            path=temp_dir,
            data=str(temp_dir),
            format="path",
            message=f"Created temporary directory: {temp_dir}",
        )
    except Exception as e:
        logger.error(f"Failed to create temporary directory: {e}")
        return DataResult(
            success=False,
            path=None,
            data="",
            format="path",
            error=str(e),
            message="Failed to create temporary directory",
        )


def create_temp_file(
    suffix: str = ".txt",
    prefix: str = "quackcore_",
    directory: str | Path | None = None,
) -> DataResult[str]:
    """
    Create a temporary file.

    Args:
        suffix: File suffix (e.g., ".txt")
        prefix: File prefix
        directory: Directory to create the file in (default: system temp dir)

    Returns:
        DataResult with path to the created temporary file
    """
    try:
        temp_file = _create_temp_file(suffix, prefix, directory)

        dir_msg = f" in directory {directory}" if directory else ""
        return DataResult(
            success=True,
            path=temp_file,
            data=str(temp_file),
            format="path",
            message=f"Created temporary file: {temp_file}{dir_msg}",
        )
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        return DataResult(
            success=False,
            path=Path(directory) if directory else None,
            data="",
            format="path",
            error=str(e),
            message="Failed to create temporary file",
        )
