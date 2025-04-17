# src/quackcore/fs/_helpers/file_info.py
"""
Utility functions for getting file information.
"""

import platform
from pathlib import Path

from quackcore.errors import QuackFileNotFoundError, QuackIOError, wrap_io_errors
from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


def _get_file_size_str(size_bytes: int) -> str:
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
def _get_file_timestamp(path: str | Path) -> float:
    """
    Get the latest timestamp (modification time) for a file.

    Args:
        path: Path to the file (string or Path)

    Returns:
        Timestamp as float

    Raises:
        QuackFileNotFoundError: If the file doesn't exist
        QuackIOError: For other IO related issues
    """
    # Normalize to Path object
    path_obj = Path(path)

    if not path_obj.exists():
        logger.error(f"File not found when getting timestamp: {path}")
        raise QuackFileNotFoundError(str(path))
    return path_obj.stat().st_mtime


def _get_mime_type(path: str | Path) -> str | None:
    """
    Get the MIME type of the file.

    Args:
        path: Path to the file (string or Path)

    Returns:
        MIME type string or None if not determinable
    """
    import mimetypes

    # Normalize to string for mimetypes.guess_type
    path_str = str(Path(path))

    mime_type, _ = mimetypes.guess_type(path_str)
    if mime_type:
        logger.debug(f"Detected MIME type for {path}: {mime_type}")
    else:
        logger.debug(f"Could not determine MIME type for {path}")
    return mime_type


def _is_file_locked(path: str | Path) -> bool:
    """
    Check if a file is locked by another process.

    Args:
        path: Path to the file (string or Path)

    Returns:
        True if the file is locked
    """
    # Normalize to Path object
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
        logger.debug(f"File {path} is locked by another process")
        return True
    except ImportError:
        logger.warning(
            f"Cannot check lock status for {path}: "
            f"platform-specific modules not available"
        )
        return False


def _get_file_type(path: str | Path) -> str:
    """
    Get the type of the file.

    Args:
        path: Path to the file (string or Path)

    Returns:
        File type string (e.g., "text", "binary", "directory", "symlink")
    """
    # Normalize to Path object
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
