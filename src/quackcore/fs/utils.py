# src/quackcore/fs/utils.py
"""
Utility functions for filesystem operations.

This module provides helper functions for common filesystem tasks
and utilities for working with file formats.
"""

import hashlib
import logging
import os
import platform
import re
import shutil
import tempfile
from pathlib import Path
from typing import TypeVar

from quackcore.errors import (
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
    wrap_io_errors,
)

T = TypeVar("T")  # Generic type for flexible typing
logger = logging.getLogger(__name__)


def get_extension(path: str | Path) -> str:
    """
    Get the file extension from a path.

    Args:
        path: File path

    Returns:
        File extension without the dot
    """
    return Path(path).suffix.lstrip(".")


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object
    """
    return Path(path).expanduser().resolve()


def is_same_file(path1: str | Path, path2: str | Path) -> bool:
    """
    Check if two paths refer to the same file.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if paths refer to the same file
    """
    try:
        return os.path.samefile(str(path1), str(path2))
    except OSError:
        # If one or both files don't exist, compare normalized paths.
        return normalize_path(path1) == normalize_path(path2)


def is_subdirectory(child: str | Path, parent: str | Path) -> bool:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path
        parent: Potential parent path

    Returns:
        True if child is a subdirectory of parent
    """
    child_path = normalize_path(child)
    parent_path = normalize_path(parent)
    try:
        child_path.relative_to(parent_path)
        return True
    except ValueError:
        return False


def get_file_size_str(size_bytes: int) -> str:
    """
    Convert file size in bytes to human-readable string.

    Args:
        size_bytes: File size in bytes

    Returns:
        Human-readable file size (e.g., "2.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024 or unit == "TB":
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024


@wrap_io_errors
def get_unique_filename(
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
        raise QuackFileNotFoundError(str(directory), message="Directory does not exist")
    if not filename or not filename.strip():
        raise QuackIOError("Filename cannot be empty", str(directory))

    base_name = Path(filename).stem
    extension = Path(filename).suffix
    path = dir_path / filename

    if path.exists():
        if raise_if_exists:
            raise QuackFileExistsError(str(path), message="File already exists")
    else:
        return path

    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        path = dir_path / new_name
        if not path.exists():
            return path
        counter += 1


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
    temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix)
    return Path(temp_dir)


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
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir_path)
    os.close(fd)  # Close the file descriptor
    return Path(path)


@wrap_io_errors
def get_file_timestamp(path: str | Path) -> float:
    """
    Get the latest timestamp (modification time) for a file.

    Args:
        path: Path to the file

    Returns:
        Timestamp as float

    Raises:
        QuackFileNotFoundError: If the file doesn't exist
        QuackIOError: For other IO related issues
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise QuackFileNotFoundError(str(path))
    return path_obj.stat().st_mtime


def is_path_writeable(path: str | Path) -> bool:
    """
    Check if a path is writeable.

    Args:
        path: Path to check

    Returns:
        True if the path is writeable
    """
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
            return True
        except (QuackPermissionError, QuackIOError, OSError):
            return False

    if path_obj.is_file():
        return os.access(path_obj, os.W_OK)

    if path_obj.is_dir():
        try:
            test_file = path_obj / f"test_write_{os.getpid()}.tmp"
            with open(test_file, "w") as _:
                pass
            test_file.unlink()  # Clean up
            return True
        except (QuackPermissionError, QuackIOError, OSError):
            return False

    return False


def get_mime_type(path: str | Path) -> str | None:
    """
    Get the MIME type of the file.

    Args:
        path: Path to the file

    Returns:
        MIME type string or None if not determinable
    """
    import mimetypes

    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type


def get_disk_usage(path: str | Path) -> dict[str, int]:
    """
    Get disk usage information for the given path.

    Args:
        path: Path to get disk usage for

    Returns:
        Dictionary with total, used, and free space in bytes

    Raises:
        QuackIOError: If disk usage cannot be determined.
    """
    try:
        total, used, free = shutil.disk_usage(str(path))
        return {"total": total, "used": used, "free": free}
    except Exception as e:
        raise QuackIOError(
            f"Error getting disk usage for {path}: {e}", str(path)
        ) from e


def is_file_locked(path: str | Path) -> bool:
    """
    Check if a file is locked by another process.

    Args:
        path: Path to the file

    Returns:
        True if the file is locked
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return False
    try:
        with open(path_obj, "r+") as f:
            if platform.system() == "Windows":
                import msvcrt

                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return False
    except (OSError, QuackIOError):
        return True
    except ImportError:
        logger.warning(
            f"Cannot check lock status for {path}: "
            f"platform-specific modules not available"
        )
        return False


def get_file_type(path: str | Path) -> str:
    """
    Get the type of the file.

    Args:
        path: Path to the file

    Returns:
        File type string (e.g., "text", "binary", "directory", "symlink")
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return "nonexistent"
    if path_obj.is_dir():
        return "directory"
    if path_obj.is_symlink():
        return "symlink"
    try:
        with open(path_obj, errors="ignore") as f:
            chunk = f.read(1024)
            # If for some reason we get a str, encode it to bytes.
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            if b"\0" in chunk:
                return "binary"
            return "text"
    except (QuackIOError, OSError) as e:
        logger.error(f"Error determining file type for {path}: {e}")
        return "unknown"


@wrap_io_errors
def find_files_by_content(
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
    except re.error as e:
        raise QuackIOError(
            f"Invalid regex pattern: {e}", str(directory), original_error=e
        ) from e

    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        return []
    matching_files = []
    all_files = (
        list(directory_path.glob("**/*"))
        if recursive
        else list(directory_path.glob("*"))
    )
    for path in all_files:
        if not path.is_file():
            continue
        try:
            # Remove explicit "r" mode as it is the default for text files.
            with open(path, errors="ignore") as file_obj:
                content = file_obj.read()
                if pattern.search(content):
                    matching_files.append(path)
        except (QuackIOError, OSError):
            # Skip files that raise an error (e.g. permission issues)
            continue
    return matching_files


def split_path(path: str | Path) -> list[str]:
    """
    Split a path into its components.

    Args:
        path: Path to split

    Returns:
        List of path components
    """
    parts = list(Path(path).parts)
    if str(path).startswith("./"):
        parts.insert(0, ".")
    return parts


def join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    Args:
        *parts: Path parts to join

    Returns:
        Joined Path object
    """
    return Path(*parts)


def expand_user_vars(path: str | Path) -> Path:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables

    Returns:
        Expanded Path object
    """
    path_str = os.path.expanduser(str(path))
    path_str = os.path.expandvars(path_str)
    return Path(path_str)


@wrap_io_errors
def ensure_directory(path: str | Path, exist_ok: bool = True) -> Path:
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
        return path_obj
    except FileExistsError as e:
        raise QuackFileExistsError(str(path), original_error=e) from e
    except PermissionError as e:
        raise QuackPermissionError(
            str(path), "create directory", original_error=e
        ) from e
    except Exception as e:
        raise QuackIOError(
            f"Failed to create directory: {str(e)}", str(path), original_error=e
        ) from e


@wrap_io_errors
def compute_checksum(path: str | Path, algorithm: str = "sha256") -> str:
    """
    Compute checksum of a file.

    Args:
        path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal checksum string

    Raises:
        QuackFileNotFoundError: If file doesn't exist
        QuackIOError: For other IO related issues
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise QuackFileNotFoundError(str(path))
    if not path_obj.is_file():
        raise QuackIOError("Not a file", str(path))

    try:
        hash_obj = getattr(hashlib, algorithm)()
        with open(path_obj, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        raise QuackIOError(
            f"Failed to compute checksum for {path}: {str(e)}",
            str(path),
            original_error=e,
        ) from e


@wrap_io_errors
def atomic_write(path: str | Path, content: str | bytes) -> Path:
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
    ensure_directory(path_obj.parent)

    temp_dir = path_obj.parent
    temp_file = None

    try:
        fd, temp_path = tempfile.mkstemp(dir=temp_dir)
        temp_file = Path(temp_path)
        with os.fdopen(fd, "wb" if isinstance(content, bytes) else "w") as f:
            f.write(content)

        # On Unix-like systems, rename is atomic
        os.replace(temp_path, path_obj)
        return path_obj
    except Exception as e:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as unlink_error:
                logger.debug(
                    f"Failed to unlink temporary file {temp_file}: {unlink_error}"
                )
        raise QuackIOError(
            f"Failed to write file {path}: {str(e)}", str(path), original_error=e
        ) from e


@wrap_io_errors
def safe_copy(src: str | Path, dst: str | Path, overwrite: bool = False) -> Path:
    """
    Safely copy a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: If True, overwrite destination if it exists

    Returns:
        Path object for the destination

    Raises:
        QuackFileNotFoundError: If source doesn't exist
        QuackFileExistsError: If destination exists and overwrite is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise QuackFileNotFoundError(str(src))

    if dst_path.exists() and not overwrite:
        raise QuackFileExistsError(str(dst))

    try:
        if src_path.is_dir():
            if dst_path.exists() and overwrite:
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            ensure_directory(dst_path.parent)
            shutil.copy2(src_path, dst_path)
        return dst_path
    except PermissionError as e:
        raise QuackPermissionError(str(dst), "copy", original_error=e) from e
    except Exception as e:
        raise QuackIOError(
            f"Failed to copy {src} to {dst}: {str(e)}", str(dst), original_error=e
        ) from e


@wrap_io_errors
def safe_move(src: str | Path, dst: str | Path, overwrite: bool = False) -> Path:
    """
    Safely move a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: If True, overwrite destination if it exists

    Returns:
        Path object for the destination

    Raises:
        QuackFileNotFoundError: If source doesn't exist
        QuackFileExistsError: If destination exists and overwrite is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise QuackFileNotFoundError(str(src))

    if dst_path.exists() and not overwrite:
        raise QuackFileExistsError(str(dst))

    try:
        ensure_directory(dst_path.parent)
        if dst_path.exists() and overwrite:
            if dst_path.is_dir():
                shutil.rmtree(dst_path)
            else:
                dst_path.unlink()
        shutil.move(str(src_path), str(dst_path))
        return dst_path
    except PermissionError as e:
        raise QuackPermissionError(str(dst), "move", original_error=e) from e
    except Exception as e:
        raise QuackIOError(
            f"Failed to move {src} to {dst}: {str(e)}", str(dst), original_error=e
        ) from e


@wrap_io_errors
def safe_delete(path: str | Path, missing_ok: bool = True) -> bool:
    """
    Safely delete a file or directory.

    Args:
        path: Path to delete
        missing_ok: If True, don't raise error if path doesn't exist

    Returns:
        True if deletion was successful,
        False if path didn't exist and missing_ok is True

    Raises:
        QuackFileNotFoundError: If path doesn't exist and missing_ok is False
        QuackPermissionError: If permission is denied
        QuackIOError: For other IO related issues
    """
    path_obj = Path(path)

    if not path_obj.exists():
        if missing_ok:
            return False
        raise QuackFileNotFoundError(str(path))

    try:
        if path_obj.is_dir():
            shutil.rmtree(path_obj)
        else:
            path_obj.unlink()
        return True
    except PermissionError as e:
        raise QuackPermissionError(str(path), "delete", original_error=e) from e
    except Exception as e:
        raise QuackIOError(
            f"Failed to delete {path}: {str(e)}", str(path), original_error=e
        ) from e
