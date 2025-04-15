# src/quackcore/fs/api/public/safe_ops.py
"""
Public API for safe file operations (copy, move, delete).

This module provides safe, result-oriented wrappers around low-level
safe file operations.
"""

from pathlib import Path

from quackcore.fs.helpers.safe_ops import _safe_copy, _safe_delete, _safe_move
from quackcore.fs.results import OperationResult, WriteResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def copy_safely(
    src: str | Path, dst: str | Path, overwrite: bool = False
) -> WriteResult:
    """
    Safely copy a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: If True, overwrite destination if it exists

    Returns:
        WriteResult with operation status
    """
    try:
        result_path = _safe_copy(src, dst, overwrite)

        # Get size if it's a file
        bytes_copied = 0
        if result_path.is_file():
            bytes_copied = result_path.stat().st_size

        return WriteResult(
            success=True,
            path=result_path,
            original_path=Path(src),
            bytes_written=bytes_copied,
            message=f"Successfully copied {src} to {dst}",
        )
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return WriteResult(
            success=False,
            path=Path(dst),
            original_path=Path(src),
            error=str(e),
            message="Failed to copy file or directory",
        )


def move_safely(
    src: str | Path, dst: str | Path, overwrite: bool = False
) -> WriteResult:
    """
    Safely move a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: If True, overwrite destination if it exists

    Returns:
        WriteResult with operation status
    """
    try:
        # Get size before moving if it's a file
        bytes_moved = 0
        src_path = Path(src)
        if src_path.is_file():
            bytes_moved = src_path.stat().st_size

        result_path = _safe_move(src, dst, overwrite)

        return WriteResult(
            success=True,
            path=result_path,
            original_path=src_path,
            bytes_written=bytes_moved,
            message=f"Successfully moved {src} to {dst}",
        )
    except Exception as e:
        logger.error(f"Failed to move {src} to {dst}: {e}")
        return WriteResult(
            success=False,
            path=Path(dst),
            original_path=Path(src),
            error=str(e),
            message="Failed to move file or directory",
        )


def delete_safely(path: str | Path, missing_ok: bool = True) -> OperationResult:
    """
    Safely delete a file or directory.

    Args:
        path: Path to delete
        missing_ok: If True, don't raise error if path doesn't exist

    Returns:
        OperationResult with operation status
    """
    try:
        result = _safe_delete(path, missing_ok)

        if result:
            return OperationResult(
                success=True, path=Path(path), message=f"Successfully deleted {path}"
            )
        else:
            # This branch is hit when the path doesn't exist and missing_ok is True
            return OperationResult(
                success=True,
                path=Path(path),
                message=f"Path {path} does not exist, no action taken",
            )
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return OperationResult(
            success=False,
            path=Path(path),
            error=str(e),
            message="Failed to delete file or directory",
        )
