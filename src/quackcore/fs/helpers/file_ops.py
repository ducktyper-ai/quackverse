# src/quackcore/fs/helpers/file_ops.py
"""
Utility functions for file operations.
"""

import os
import re
import tempfile
from pathlib import Path

from quackcore.errors import (
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
    wrap_io_errors,
)
from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


@wrap_io_errors
def _get_unique_filename(
    directory: str | Path, filename: str, raise_if_exists: bool = False
) -> Path:
    """
    Generate a unique filename in the given directory.

    If the directory does not exist, raises QuackFileNotFoundError.
    If the provided filename is empty, raises QuackIOError.
    If raise_if_exists is True and the file exists, raises QuackFileExistsError.
    Otherwise, if the filename exists, adds a numeric suffix.

    Args:
        directory: Directory path
        filename: Base filename
        raise_if_exists: If True, raise an error when the file exists

    Returns:
        Unique Path object
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.error(f"Directory does not exist: {directory}")
        raise QuackFileNotFoundError(str(directory), message="Directory does not exist")
    if not filename or not filename.strip():
        logger.error(f"Empty filename provided for directory: {directory}")
        raise QuackIOError("Filename cannot be empty", str(directory))

    base_name = Path(filename).stem
    extension = Path(filename).suffix
    path = dir_path / filename

    if path.exists():
        if raise_if_exists:
            logger.error(f"File already exists: {path}")
            raise QuackFileExistsError(str(path), message="File already exists")
    else:
        logger.debug(f"Using original filename: {path}")
        return path

    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        path = dir_path / new_name
        if not path.exists():
            logger.debug(f"Generated unique filename: {path}")
            return path
        counter += 1


@wrap_io_errors
def _ensure_directory(path: str | Path, exist_ok: bool = True) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        exist_ok: If False, raise an error when directory exists

    Returns:
        Path object for the directory

    Raises:
        QuackFileExistsError: If directory exists and exist_ok is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    path_obj = Path(path)
    try:
        path_obj.mkdir(parents=True, exist_ok=exist_ok)
        logger.debug(f"Ensured directory exists: {path}")
        return path_obj
    except FileExistsError as e:
        logger.error(f"Directory already exists and exist_ok is False: {path}")
        raise QuackFileExistsError(str(path), original_error=e) from e
    except PermissionError as e:
        logger.error(f"Permission denied when creating directory: {path}")
        raise QuackPermissionError(
            str(path), "create directory", original_error=e
        ) from e
    except Exception as e:
        logger.error(f"Failed to create directory: {path}, error: {e}")
        raise QuackIOError(
            f"Failed to create directory: {str(e)}", str(path), original_error=e
        ) from e


@wrap_io_errors
def _atomic_write(path: str | Path, content: str | bytes) -> Path:
    """
    Write content to a file atomically using a temporary file.

    Args:
        path: Destination path
        content: Content to write (string or bytes)

    Returns:
        Path object for the written file

    Raises:
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    path_obj = Path(path)
    _ensure_directory(path_obj.parent)

    temp_dir = path_obj.parent
    temp_file = None

    try:
        fd, temp_path = tempfile.mkstemp(dir=temp_dir)
        temp_file = Path(temp_path)
        logger.debug(f"Created temporary file for atomic write: {temp_path}")

        with os.fdopen(fd, "wb" if isinstance(content, bytes) else "w") as f:
            f.write(content)

        # On Unix-like systems, rename is atomic
        os.replace(temp_path, path_obj)
        logger.debug(f"Successfully wrote content to {path} atomically")
        return path_obj
    except Exception as e:
        logger.error(f"Failed to write file {path} atomically: {e}")
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Cleaned up temporary file after error: {temp_file}")
            except Exception as unlink_error:
                logger.debug(
                    f"Failed to unlink temporary file {temp_file}: {unlink_error}"
                )
        raise QuackIOError(
            f"Failed to write file {path}: {str(e)}", str(path), original_error=e
        ) from e


@wrap_io_errors
def _find_files_by_content(
    directory: str | Path, text_pattern: str, recursive: bool = True
) -> list[Path]:
    """
    Find files containing the given text pattern.

    Args:
        directory: Directory to search in
        text_pattern: Text pattern to search for
        recursive: Whether to search recursively

    Returns:
        List of paths to files containing the pattern

    Raises:
        QuackIOError: If the provided regex pattern is invalid.
    """
    try:
        pattern = re.compile(text_pattern)
        logger.debug(f"Searching for pattern '{text_pattern}' in {directory}")
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        raise QuackIOError(
            f"Invalid regex pattern: {e}", str(directory), original_error=e
        ) from e

    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        logger.warning(f"Directory does not exist or is not a directory: {directory}")
        return []

    matching_files = []
    all_files = (
        list(directory_path.glob("**/*"))
        if recursive
        else list(directory_path.glob("*"))
    )

    logger.debug(f"Found {len(all_files)} files to search through")

    for path in all_files:
        if not path.is_file():
            continue
        try:
            # Remove explicit "r" mode as it is the default for text files.
            with open(path, errors="ignore") as file_obj:
                content = file_obj.read()
                if pattern.search(content):
                    matching_files.append(path)
                    logger.debug(f"Found matching file: {path}")
        except (QuackIOError, OSError):
            # Skip files that raise an error (e.g. permission issues)
            logger.debug(f"Skipping file due to access error: {path}")
            continue

    logger.info(f"Found {len(matching_files)} files matching pattern '{text_pattern}'")
    return matching_files
