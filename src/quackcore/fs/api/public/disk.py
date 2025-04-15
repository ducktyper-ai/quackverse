# src/quackcore/fs/api/public/disk.py
"""
Public API for disk _operations.

This module provides safe, result-oriented wrappers around low-level disk _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.disk import _get_disk_usage, _is_path_writeable
from quackcore.fs.results import DataResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def get_disk_usage(path: str | Path) -> DataResult[dict[str, int]]:
    """
    Get disk usage information for the given path.

    Args:
        path: Path to get disk usage for

    Returns:
        DataResult with total, used, and free space in bytes
    """
    try:
        usage_data = _get_disk_usage(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=usage_data,
            format="disk_usage",
            message=f"Successfully retrieved disk usage for {path}",
        )
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data={},
            format="disk_usage",
            error=str(e),
            message="Failed to get disk usage",
        )


def is_path_writeable(path: str | Path) -> DataResult[bool]:
    """
    Check if a path is writeable.

    Args:
        path: Path to check

    Returns:
        DataResult with boolean indicating if path is writeable
    """
    try:
        is_writeable = _is_path_writeable(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=is_writeable,
            format="boolean",
            message=f"Path {path} is {'writeable' if is_writeable else 'not writeable'}",
        )
    except Exception as e:
        logger.error(f"Failed to check if path is writeable {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check if path is writeable",
        )
