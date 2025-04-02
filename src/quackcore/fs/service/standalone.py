# src/quackcore/fs/service/standalone.py
"""
Standalone utility functions that are exposed at the package level.

These functions provide direct access to common filesystem operations
without having to create a service instance.
"""

from pathlib import Path

from quackcore.fs.results import (
    DataResult,
    FileInfoResult,
    OperationResult,
)
from quackcore.fs.service import service


def create_directory(path: str | Path, exist_ok: bool = True) -> OperationResult:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create.
        exist_ok: If False, raise an error when the directory exists.

    Returns:
        An OperationResult indicating whether the directory
        was created or already exists.
    """
    return service.create_directory(path, exist_ok)


def read_yaml(path: str | Path) -> DataResult[dict]:
    """
    Read a YAML file and parse its contents using the FileSystemService.

    Args:
        path: Path to the YAML file.

    Returns:
        A DataResult containing the parsed YAML data.
    """
    return service.read_yaml(path)


def get_file_info(path: str | Path) -> FileInfoResult:
    """
    Get information about a file or directory.

    Args:
        path: Path to get information about

    Returns:
        FileInfoResult with file information
    """
    return service.get_file_info(path)