# src/quackcore/fs/_helpers/disk.py
"""
Utility functions for disk _operations.
"""

import os
import shutil
from pathlib import Path

from quackcore.errors import QuackIOError
from quackcore.logging import get_logger

# Import from within package

# Initialize module logger
logger = get_logger(__name__)


def _get_disk_usage(path: str | Path) -> dict[str, int]:
    """
    Get disk usage information for the given path.

    Args:
        path: Path to get disk usage for (string or Path)

    Returns:
        Dictionary with total, used, and free space in bytes

    Raises:
        QuackIOError: If disk usage cannot be determined.
    """
    # Normalize to Path object and convert to string for shutil.disk_usage
    path_str = str(Path(path))

    try:
        total, used, free = shutil.disk_usage(path_str)
        logger.debug(f"Disk usage for {path}: total={total}, used={used}, free={free}")
        return {"total": total, "used": used, "free": free}
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {e}")
        raise QuackIOError(
            f"Error getting disk usage for {path}: {e}", path_str
        ) from e


def _is_path_writeable(path: str | Path) -> bool:
    """
    Check if a path is writeable.

    Args:
        path: Path to check (string or Path)

    Returns:
        True if the path is writeable
    """
    # Normalize to Path object early
    path_obj = Path(path)

    if not path_obj.exists():
        try:
            if path_obj.suffix:
                with open(path_obj, "w") as _:
                    pass
                path_obj.unlink()  # Clean up
            else:
                path_obj.mkdir(parents=True)
                path_obj.rmdir()  # Clean up
            logger.debug(f"Path {path} is writeable (created and removed test objects)")
            return True
        except Exception as e:
            logger.debug(f"Path {path} is not writeable: {e}")
            return False

    if path_obj.is_file():
        result = os.access(path_obj, os.W_OK)
        logger.debug(f"File {path} writeable check result: {result}")
        return result

    if path_obj.is_dir():
        try:
            test_file = path_obj / f"test_write_{os.getpid()}.tmp"
            with open(test_file, "w") as _:
                pass
            test_file.unlink()  # Clean up
            logger.debug(
                f"Directory {path} is writeable (created and removed test file)"
            )
            return True
        except Exception as e:
            logger.debug(f"Directory {path} is not writeable: {e}")
            return False

    return False
