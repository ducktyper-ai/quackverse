# src/quackcore/fs/api/public/checksums.py
"""
Public API for file checksum _operations.

This module provides safe, result-oriented wrappers around low-level checksum _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.checksums import _compute_checksum
from quackcore.fs.results import DataResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def compute_checksum(path: str | Path, algorithm: str = "sha256") -> DataResult[str]:
    """
    Compute the checksum of a file.

    Args:
        path: Path to the file
        algorithm: Hash algorithm to use (default: "sha256")

    Returns:
        DataResult with hexadecimal checksum string
    """
    try:
        checksum = _compute_checksum(path, algorithm)

        return DataResult(
            success=True,
            path=Path(path),
            data=checksum,
            format="checksum",
            message=f"Computed {algorithm} checksum for {path}: {checksum}",
        )
    except Exception as e:
        logger.error(f"Failed to compute checksum for {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path),
            data="",
            format="checksum",
            error=str(e),
            message=f"Failed to compute {algorithm} checksum",
        )
