# src/quackcore/fs/api/public/file_ops.py
"""
Public API for file _operations.

This module provides safe, result-oriented wrappers around low-level file _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.file_ops import (
    _atomic_write,
    _ensure_directory,
    _find_files_by_content,
    _get_unique_filename,
)
from quackcore.fs.results import DataResult, OperationResult, WriteResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def atomic_write(path: str | Path, content: str | bytes) -> WriteResult:
    """
    Write content to a file atomically using a temporary file.

    Args:
        path: Destination path
        content: Content to write (string or bytes)

    Returns:
        WriteResult with operation status
    """
    try:
        path_obj = Path(path)
        result_path = _atomic_write(path, content)
        bytes_written = len(content.encode() if isinstance(content, str) else content)

        return WriteResult(
            success=True,
            path=result_path,
            bytes_written=bytes_written,
            message=f"Successfully wrote {bytes_written} bytes to {result_path} atomically",
        )
    except Exception as e:
        logger.error(f"Failed to write file {path} atomically: {e}")
        return WriteResult(
            success=False,
            path=Path(path),
            error=str(e),
            message="Failed to write file atomically",
        )


def ensure_directory(path: str | Path, exist_ok: bool = True) -> OperationResult:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        exist_ok: If False, raise an error when directory exists

    Returns:
        OperationResult with operation status
    """
    try:
        created_path = _ensure_directory(path, exist_ok)
        return OperationResult(
            success=True,
            path=created_path,
            message=f"Directory {created_path} {'exists' if created_path.exists() else 'created'}",
        )
    except Exception as e:
        logger.error(f"Failed to ensure directory {path}: {e}")
        return OperationResult(
            success=False,
            path=Path(path),
            error=str(e),
            message="Failed to ensure directory exists",
        )


def find_files_by_content(
    directory: str | Path, text_pattern: str, recursive: bool = True
) -> DataResult[list[str]]:
    """
    Find files containing the given text pattern.

    Args:
        directory: Directory to search in
        text_pattern: Text pattern to search for
        recursive: Whether to search recursively

    Returns:
        DataResult with list of matching file paths
    """
    try:
        matches = _find_files_by_content(directory, text_pattern, recursive)
        str_matches = [str(p) for p in matches]

        return DataResult(
            success=True,
            path=Path(directory),
            data=str_matches,
            format="file_list",
            message=f"Found {len(matches)} files matching pattern '{text_pattern}'",
        )
    except Exception as e:
        logger.error(f"Failed to find files by content in {directory}: {e}")
        return DataResult(
            success=False,
            path=Path(directory),
            data=[],
            format="file_list",
            error=str(e),
            message="Failed to search for files by content",
        )


def get_unique_filename(
    directory: str | Path, filename: str, raise_if_exists: bool = False
) -> DataResult[str]:
    """
    Generate a unique filename in the given directory.

    Args:
        directory: Directory path
        filename: Base filename
        raise_if_exists: If True, raise an error when the file exists

    Returns:
        DataResult with the unique filename
    """
    try:
        result_path = _get_unique_filename(directory, filename, raise_if_exists)

        return DataResult(
            success=True,
            path=Path(directory),
            data=str(result_path),
            format="path",
            message=f"Generated unique filename: {result_path}",
        )
    except Exception as e:
        logger.error(f"Failed to get unique filename in {directory}: {e}")
        return DataResult(
            success=False,
            path=Path(directory),
            data="",
            format="path",
            error=str(e),
            message="Failed to generate unique filename",
        )
