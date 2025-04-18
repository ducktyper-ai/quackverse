# quackcore/src/quackcore/fs/service/__init__.py
"""
FileSystemService provides a high-level interface for filesystem _operations.

This module exports the FileSystemService class and provides utility functions
for common filesystem _operations without requiring a service instance.
"""

from pathlib import Path
from typing import TypeVar

from quackcore.fs.results import (
    DataResult,
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    PathResult,
    ReadResult,
    WriteResult,
)

# Import the factory function but defer creating the service
from quackcore.fs.service.factory import create_service

# Import the complete FileSystemService with all mixins for type hints
from quackcore.fs.service.full_class import FileSystemService

# Create a global instance but initialize it lazily
_service = None


def get_service(self=None):
    """
    Get the global filesystem service instance.

    This function initializes the service on first access to avoid circular imports.

    Args:
        self: Unused parameter to satisfy property getter requirements

    Returns:
        FileSystemService: The global filesystem service instance
    """
    global _service
    if _service is None:
        _service = create_service()
    return _service


# Access the service through a property to ensure lazy initialization
service = property(get_service)


# Define standalone functions for direct use
# These are wrappers around the service functions that lazily initialize the service


def create_directory(path: str | Path | DataResult | OperationResult, exist_ok: bool = True) -> OperationResult:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create (string, Path, DataResult, or OperationResult)
        exist_ok: If False, raise an error when the directory exists.

    Returns:
        An OperationResult indicating whether the directory
        was created or already exists.
    """
    return get_service().create_directory(path, exist_ok)


def read_yaml(path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
    """
    Read a YAML file and parse its contents using the FileSystemService.

    Args:
        path: Path to the YAML file (string, Path, DataResult, or OperationResult)

    Returns:
        A DataResult containing the parsed YAML data.
    """
    return get_service().read_yaml(path)


def get_file_info(path: str | Path | DataResult | OperationResult) -> FileInfoResult:
    """
    Get information about a file or directory.

    Args:
        path: Path to get information about (string, Path, DataResult, or OperationResult)

    Returns:
        FileInfoResult with file information
    """
    return get_service().get_file_info(path)


def read_text(path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[str]:
    """
    Read text from a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        encoding: Text encoding

    Returns:
        ReadResult with the file content as text
    """
    return get_service().read_text(path, encoding)


def write_text(
    path: str | Path | DataResult | OperationResult,
    content: str,
    encoding: str = "utf-8",
    atomic: bool = True,
) -> WriteResult:
    """
    Write text to a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        content: Content to write
        encoding: Text encoding
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return get_service().write_text(path, content, encoding, atomic)


def read_binary(path: str | Path | DataResult | OperationResult) -> ReadResult[bytes]:
    """
    Read binary data from a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)

    Returns:
        ReadResult with the file content as bytes
    """
    return get_service().read_binary(path)


def write_binary(
    path: str | Path | DataResult | OperationResult,
    content: bytes,
    atomic: bool = True,
) -> WriteResult:
    """
    Write binary data to a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        content: Content to write
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return get_service().write_binary(path, content, atomic)


def write_yaml(
    path: str | Path | DataResult | OperationResult,
    data: dict,
    atomic: bool = True,
) -> WriteResult:
    """
    Write data to a YAML file.

    Args:
        path: Path to YAML file (string, Path, DataResult, or OperationResult)
        data: Data to write
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return get_service().write_yaml(path, data, atomic)


def read_json(path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
    """
    Read a JSON file and parse its contents.

    Args:
        path: Path to JSON file (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with parsed JSON data
    """
    return get_service().read_json(path)


def write_json(
    path: str | Path | DataResult | OperationResult,
    data: dict,
    atomic: bool = True,
    indent: int = 2,
) -> WriteResult:
    """
    Write data to a JSON file.

    Args:
        path: Path to JSON file (string, Path, DataResult, or OperationResult)
        data: Data to write
        atomic: Whether to use atomic writing
        indent: Number of spaces to indent

    Returns:
        WriteResult with operation status
    """
    return get_service().write_json(path, data, atomic, indent)


def list_directory(
    path: str | Path | DataResult | OperationResult,
    pattern: str | None = None,
    include_hidden: bool = False,
) -> DirectoryInfoResult:
    """
    List contents of a directory.

    Args:
        path: Path to list (string, Path, DataResult, or OperationResult)
        pattern: Pattern to match files against
        include_hidden: Whether to include hidden files

    Returns:
        DirectoryInfoResult with directory contents
    """
    return get_service().list_directory(path, pattern, include_hidden)


def find_files(
    path: str | Path | DataResult | OperationResult,
    pattern: str,
    recursive: bool = True,
    include_hidden: bool = False,
) -> FindResult:
    """
    Find files matching a pattern.

    Args:
        path: Directory to search (string, Path, DataResult, or OperationResult)
        pattern: Pattern to match files against
        recursive: Whether to search recursively
        include_hidden: Whether to include hidden files

    Returns:
        FindResult with matching files
    """
    return get_service().find_files(path, pattern, recursive, include_hidden)


def copy(src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False) -> WriteResult:
    """
    Copy a file or directory.

    Args:
        src: Source path (string, Path, DataResult, or OperationResult)
        dst: Destination path (string, Path, DataResult, or OperationResult)
        overwrite: Whether to overwrite if destination exists

    Returns:
        WriteResult with operation status
    """
    return get_service().copy(src, dst, overwrite)


def move(src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False) -> WriteResult:
    """
    Move a file or directory.

    Args:
        src: Source path (string, Path, DataResult, or OperationResult)
        dst: Destination path (string, Path, DataResult, or OperationResult)
        overwrite: Whether to overwrite if destination exists

    Returns:
        WriteResult with operation status
    """
    return get_service().move(src, dst, overwrite)


def delete(path: str | Path | DataResult | OperationResult, missing_ok: bool = True) -> OperationResult:
    """
    Delete a file or directory.

    Args:
        path: Path to delete (string, Path, DataResult, or OperationResult)
        missing_ok: Whether to ignore if the path doesn't exist

    Returns:
        OperationResult with operation status
    """
    return get_service().delete(path, missing_ok)


def read_lines(path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult:
    """
    Read lines from a text file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        encoding: Text encoding

    Returns:
        ReadResult with the file content as a list of lines
    """
    return get_service().read_lines(path, encoding)


def write_lines(
    path: str | Path | DataResult | OperationResult,
    lines: list[str],
    encoding: str = "utf-8",
    atomic: bool = True,
    line_ending: str = "\n",
) -> WriteResult:
    """
    Write lines to a text file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        lines: Lines to write
        encoding: Text encoding
        atomic: Whether to write the file atomically
        line_ending: The line ending to use

    Returns:
        WriteResult indicating the outcome of the operation
    """
    return get_service().write_lines(path, lines, encoding, atomic, line_ending)


def path_exists(path: str | Path | DataResult | OperationResult) -> DataResult[bool]:
    """
    Check if a path exists using the FileSystemService.

    This function delegates directly to the underlying service instance,
    ensuring consistency with all other filesystem _operations.

    Args:
        path: The file or directory path to check (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if the path exists.
    """
    return get_service().path_exists(path)


def normalize_path_with_info(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Normalize a path and return detailed information.

    Args:
        path: Path to normalize (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult containing the normalized path and status information
    """
    return get_service().normalize_path_with_info(path)


def get_path_info(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Get information about a path's validity and format.

    Args:
        path: Path to check (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult containing validation results
    """
    return get_service().get_path_info(path)


def is_valid_path(path: str | Path | DataResult | OperationResult) -> DataResult[bool]:
    """
    Check if a path has valid syntax.

    Args:
        path: Path to check (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if the path has valid syntax
    """
    return get_service().is_valid_path(path)


# Type variables
T = TypeVar("T")  # Generic type for flexible typing

__all__ = [
    # Main classes
    "FileSystemService",
    "create_service",
    "service",
    "get_service",
    # Standalone functions
    "create_directory",
    "get_file_info",
    "read_yaml",
    "read_text",
    "write_text",
    "read_binary",
    "write_binary",
    "write_yaml",
    "read_json",
    "write_json",
    "read_lines",
    "write_lines",
    "list_directory",
    "find_files",
    "copy",
    "move",
    "delete",
    "normalize_path_with_info",
    "get_path_info",
    "is_valid_path",
    "path_exists",
    # Result classes for type hints
    "OperationResult",
    "ReadResult",
    "WriteResult",
    "FileInfoResult",
    "DirectoryInfoResult",
    "FindResult",
    "DataResult",
    "PathResult",
    # Type variables
    "T",
]
