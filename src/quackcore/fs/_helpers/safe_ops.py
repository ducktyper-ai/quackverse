# src/quackcore/fs/_helpers/safe_ops.py
"""
Utility functions for safe file _operations (copy, move, delete).
"""

import shutil
from pathlib import Path

from quackcore.errors import (
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
    wrap_io_errors,
)

# Import from within package
from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


@wrap_io_errors
def _safe_copy(src: str | Path, dst: str | Path, overwrite: bool = False) -> Path:
    """
    Safely copy a file or directory.

    Args:
        src: Source path (string or Path)
        dst: Destination path (string or Path)
        overwrite: If True, overwrite destination if it exists

    Returns:
        Path object for the destination

    Raises:
        QuackFileNotFoundError: If source doesn't exist
        QuackFileExistsError: If destination exists and overwrite is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    # Normalize inputs to Path objects
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        logger.error(f"Source does not exist: {src}")
        raise QuackFileNotFoundError(str(src))

    if dst_path.exists() and not overwrite:
        logger.error(f"Destination exists and overwrite is False: {dst}")
        raise QuackFileExistsError(str(dst))

    try:
        if src_path.is_dir():
            logger.info(f"Copying directory {src} to {dst}")
            if dst_path.exists() and overwrite:
                logger.debug(f"Removing existing destination directory: {dst}")
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            logger.info(f"Copying file {src} to {dst}")
            # Use a locally imported ensure_directory to avoid circular imports
            from quackcore.fs._helpers.file_ops import _ensure_directory
            _ensure_directory(dst_path.parent)
            shutil.copy2(src_path, dst_path)
        return dst_path
    except PermissionError as e:
        logger.error(f"Permission denied when copying {src} to {dst}: {e}")
        raise QuackPermissionError(str(dst), "copy", original_error=e) from e
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        raise QuackIOError(
            f"Failed to copy {src} to {dst}: {str(e)}", str(dst), original_error=e
        ) from e


@wrap_io_errors
def _safe_move(src: str | Path, dst: str | Path, overwrite: bool = False) -> Path:
    """
    Safely move a file or directory.

    Args:
        src: Source path (string or Path)
        dst: Destination path (string or Path)
        overwrite: If True, overwrite destination if it exists

    Returns:
        Path object for the destination

    Raises:
        QuackFileNotFoundError: If source doesn't exist
        QuackFileExistsError: If destination exists and overwrite is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    # Normalize inputs to Path objects
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        logger.error(f"Source does not exist: {src}")
        raise QuackFileNotFoundError(str(src))

    if dst_path.exists() and not overwrite:
        logger.error(f"Destination exists and overwrite is False: {dst}")
        raise QuackFileExistsError(str(dst))

    try:
        logger.info(f"Moving {src} to {dst}")
        # Use a locally imported ensure_directory to avoid circular imports
        from quackcore.fs._helpers.file_ops import _ensure_directory
        _ensure_directory(dst_path.parent)

        if dst_path.exists() and overwrite:
            if dst_path.is_dir():
                logger.debug(f"Removing existing destination directory: {dst}")
                shutil.rmtree(dst_path)
            else:
                logger.debug(f"Removing existing destination file: {dst}")
                dst_path.unlink()
        shutil.move(str(src_path), str(dst_path))
        return dst_path
    except PermissionError as e:
        logger.error(f"Permission denied when moving {src} to {dst}: {e}")
        raise QuackPermissionError(str(dst), "move", original_error=e) from e
    except Exception as e:
        logger.error(f"Failed to move {src} to {dst}: {e}")
        raise QuackIOError(
            f"Failed to move {src} to {dst}: {str(e)}", str(dst), original_error=e
        ) from e


@wrap_io_errors
def _safe_delete(path: str | Path, missing_ok: bool = True) -> bool:
    """
    Safely delete a file or directory.

    Args:
        path: Path to delete (string or Path)
        missing_ok: If True, don't raise error if path doesn't exist

    Returns:
        True if deletion was successful,
        False if path didn't exist and missing_ok is True

    Raises:
        QuackFileNotFoundError: If path doesn't exist and missing_ok is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    # Normalize to Path object
    path_obj = Path(path)

    if not path_obj.exists():
        if missing_ok:
            logger.debug(f"Path does not exist but missing_ok is True: {path}")
            return False
        logger.error(f"Path does not exist and missing_ok is False: {path}")
        raise QuackFileNotFoundError(str(path))

    try:
        if path_obj.is_dir():
            logger.info(f"Deleting directory: {path}")
            shutil.rmtree(path_obj)
        else:
            logger.info(f"Deleting file: {path}")
            path_obj.unlink()
        return True
    except PermissionError as e:
        logger.error(f"Permission denied when deleting {path}: {e}")
        raise QuackPermissionError(str(path), "delete", original_error=e) from e
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        raise QuackIOError(
            f"Failed to delete {path}: {str(e)}", str(path), original_error=e
        ) from e
