# src/quackcore/fs/utils/checksums.py
"""
Utility functions for file checksums.
"""

import hashlib
from pathlib import Path

from quackcore.errors import QuackFileNotFoundError, QuackIOError, wrap_io_errors
from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


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
        logger.error(f"File not found when computing checksum: {path}")
        raise QuackFileNotFoundError(str(path))
    if not path_obj.is_file():
        logger.error(f"Not a file when computing checksum: {path}")
        raise QuackIOError("Not a file", str(path))

    try:
        hash_obj = getattr(hashlib, algorithm)()
        logger.debug(f"Computing {algorithm} checksum for {path}")

        with open(path_obj, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        checksum = hash_obj.hexdigest()
        logger.debug(f"Checksum for {path}: {checksum}")
        return checksum
    except Exception as e:
        logger.error(f"Failed to compute checksum for {path}: {e}")
        raise QuackIOError(
            f"Failed to compute checksum for {path}: {str(e)}",
            str(path),
            original_error=e,
        ) from e
