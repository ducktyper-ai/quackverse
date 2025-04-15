# src/quackcore/fs/api/public/file_info.py
"""
Public API for file information operations.

This module provides safe, result-oriented wrappers around low-level file info operations.
"""

from pathlib import Path

from quackcore.fs.helpers.file_info import (
    _get_file_size_str,
    _get_file_timestamp,
    _get_file_type,
    _get_mime_type,
    _is_file_locked,
)
from quackcore.fs.results import DataResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def get_file_type(path: str | Path) -> DataResult[str]:
    """
    Get the type of a file.

    Args:
        path: Path to the file

    Returns:
        DataResult with file type string (e.g., "text", "binary", "directory", "symlink")
    """
    try:
        file_type = _get_file_type(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=file_type,
            format="file_type",
            message=f"File {path} is of type: {file_type}",
        )
    except Exception as e:
        logger.error(f"Failed to get file type for {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data="unknown",
            format="file_type",
            error=str(e),
            message="Failed to determine file type",
        )


def get_file_size_str(size_bytes: int) -> DataResult[str]:
    """
    Convert file size in bytes to a human-readable string.

    Args:
        size_bytes: File size in bytes

    Returns:
        DataResult with human-readable file size (e.g., "2.5 MB")
    """
    try:
        size_str = _get_file_size_str(size_bytes)

        return DataResult(
            success=True,
            path=None,  # Not applicable for this function
            data=size_str,
            format="file_size",
            message=f"Converted {size_bytes} bytes to human-readable format: {size_str}",
        )
    except Exception as e:
        logger.error(f"Failed to convert size {size_bytes} to string: {e}")
        return DataResult(
            success=False,
            path=None,
            data=f"{size_bytes} B",
            format="file_size",
            error=str(e),
            message="Failed to format file size",
        )


def get_file_timestamp(path: str | Path) -> DataResult[float]:
    """
    Get the latest timestamp (modification time) for a file.

    Args:
        path: Path to the file

    Returns:
        DataResult with timestamp as float
    """
    try:
        timestamp = _get_file_timestamp(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=timestamp,
            format="timestamp",
            message=f"Retrieved file timestamp: {timestamp}",
        )
    except Exception as e:
        logger.error(f"Failed to get file timestamp for {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data=0.0,
            format="timestamp",
            error=str(e),
            message="Failed to get file timestamp",
        )


def get_mime_type(path: str | Path) -> DataResult[str | None]:
    """
    Get the MIME type of a file.

    Args:
        path: Path to the file

    Returns:
        DataResult with MIME type string or None if not determinable
    """
    try:
        mime_type = _get_mime_type(path)

        message = (
            f"MIME type for {path}: {mime_type}"
            if mime_type
            else f"Could not determine MIME type for {path}"
        )

        return DataResult(
            success=True,
            path=Path(path),
            data=mime_type,
            format="mime_type",
            message=message,
        )
    except Exception as e:
        logger.error(f"Failed to get MIME type for {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data=None,
            format="mime_type",
            error=str(e),
            message="Failed to determine MIME type",
        )


def is_file_locked(path: str | Path) -> DataResult[bool]:
    """
    Check if a file is locked by another process.

    Args:
        path: Path to the file

    Returns:
        DataResult with boolean indicating if file is locked
    """
    try:
        is_locked = _is_file_locked(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=is_locked,
            format="boolean",
            message=f"File {path} is {'locked' if is_locked else 'not locked'}",
        )
    except Exception as e:
        logger.error(f"Failed to check if file is locked {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check if file is locked",
        )
