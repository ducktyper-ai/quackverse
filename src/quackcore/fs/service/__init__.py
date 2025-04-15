# src/quackcore/fs/service/__init__.py
"""
FileSystemService provides a high-level interface for filesystem operations.

This module exports the FileSystemService class and provides utility functions
for common filesystem operations without requiring a service instance.
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
from quackcore.fs.service.factory import create_service

# Import the complete FileSystemService with all mixins
from quackcore.fs.service.full_class import FileSystemService

# Create a global instance for convenience
service = create_service()


# Define standalone functions at the module level to avoid circular imports


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


def read_text(path: str | Path, encoding: str = "utf-8") -> ReadResult[str]:
    """
    Read text from a file.

    Args:
        path: Path to the file
        encoding: Text encoding

    Returns:
        ReadResult with the file content as text
    """
    return service.read_text(path, encoding)


def write_text(
    path: str | Path,
    content: str,
    encoding: str = "utf-8",
    atomic: bool = True,
) -> WriteResult:
    """
    Write text to a file.

    Args:
        path: Path to the file
        content: Content to write
        encoding: Text encoding
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return service.write_text(path, content, encoding, atomic)


def read_binary(path: str | Path) -> ReadResult[bytes]:
    """
    Read binary data from a file.

    Args:
        path: Path to the file

    Returns:
        ReadResult with the file content as bytes
    """
    return service.read_binary(path)


def write_binary(
    path: str | Path,
    content: bytes,
    atomic: bool = True,
) -> WriteResult:
    """
    Write binary data to a file.

    Args:
        path: Path to the file
        content: Content to write
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return service.write_binary(path, content, atomic)


def write_yaml(
    path: str | Path,
    data: dict,
    atomic: bool = True,
) -> WriteResult:
    """
    Write data to a YAML file.

    Args:
        path: Path to YAML file
        data: Data to write
        atomic: Whether to use atomic writing

    Returns:
        WriteResult with operation status
    """
    return service.write_yaml(path, data, atomic)


def read_json(path: str | Path) -> DataResult[dict]:
    """
    Read a JSON file and parse its contents.

    Args:
        path: Path to JSON file

    Returns:
        DataResult with parsed JSON data
    """
    return service.read_json(path)


def write_json(
    path: str | Path,
    data: dict,
    atomic: bool = True,
    indent: int = 2,
) -> WriteResult:
    """
    Write data to a JSON file.

    Args:
        path: Path to JSON file
        data: Data to write
        atomic: Whether to use atomic writing
        indent: Number of spaces to indent

    Returns:
        WriteResult with operation status
    """
    return service.write_json(path, data, atomic, indent)


def list_directory(
    path: str | Path,
    pattern: str | None = None,
    include_hidden: bool = False,
) -> DirectoryInfoResult:
    """
    List contents of a directory.

    Args:
        path: Path to list
        pattern: Pattern to match files against
        include_hidden: Whether to include hidden files

    Returns:
        DirectoryInfoResult with directory contents
    """
    return service.list_directory(path, pattern, include_hidden)


def find_files(
    path: str | Path,
    pattern: str,
    recursive: bool = True,
    include_hidden: bool = False,
) -> FindResult:
    """
    Find files matching a pattern.

    Args:
        path: Directory to search
        pattern: Pattern to match files against
        recursive: Whether to search recursively
        include_hidden: Whether to include hidden files

    Returns:
        FindResult with matching files
    """
    return service.find_files(path, pattern, recursive, include_hidden)


def copy(src: str | Path, dst: str | Path, overwrite: bool = False) -> WriteResult:
    """
    Copy a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite if destination exists

    Returns:
        WriteResult with operation status
    """
    return service.copy(src, dst, overwrite)


def move(src: str | Path, dst: str | Path, overwrite: bool = False) -> WriteResult:
    """
    Move a file or directory.

    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite if destination exists

    Returns:
        WriteResult with operation status
    """
    return service.move(src, dst, overwrite)


def delete(path: str | Path, missing_ok: bool = True) -> OperationResult:
    """
    Delete a file or directory.

    Args:
        path: Path to delete
        missing_ok: Whether to ignore if the path doesn't exist

    Returns:
        OperationResult with operation status
    """
    return service.delete(path, missing_ok)


def read_lines(path: str | Path, encoding: str = "utf-8") -> ReadResult:
    """
    Read lines from a text file.

    Args:
        path: Path to the file
        encoding: Text encoding

    Returns:
        ReadResult with the file content as a list of lines
    """
    return service.read_lines(path, encoding)


def write_lines(
    path: str | Path,
    lines: list[str],
    encoding: str = "utf-8",
    atomic: bool = True,
    line_ending: str = "\n",
) -> WriteResult:
    """
    Write lines to a text file.

    Args:
        path: Path to the file
        lines: Lines to write
        encoding: Text encoding
        atomic: Whether to write the file atomically
        line_ending: The line ending to use

    Returns:
        WriteResult indicating the outcome of the operation
    """
    return service.write_lines(path, lines, encoding, atomic, line_ending)


def path_exists(path: str | Path) -> DataResult[bool]:
    """
    Check if a path exists using the FileSystemService.

    This function delegates directly to the underlying service instance,
    ensuring consistency with all other filesystem operations.

    Args:
        path: The file or directory path to check.

    Returns:
        DataResult with boolean indicating if the path exists.
    """
    return service.path_exists(path)


def normalize_path_with_info(path: str | Path) -> PathResult:
    """
    Normalize a path and return detailed information.

    Args:
        path: Path to normalize

    Returns:
        PathResult containing the normalized path and status information
    """
    return service.normalize_path_with_info(path)


def get_path_info(path: str | Path) -> PathResult:
    """
    Get information about a path's validity and format.

    Args:
        path: Path to check

    Returns:
        PathResult containing validation results
    """
    return service.get_path_info(path)


def is_valid_path(path: str | Path) -> DataResult[bool]:
    """
    Check if a path has valid syntax.

    Args:
        path: Path to check

    Returns:
        DataResult with boolean indicating if the path has valid syntax
    """
    return service.is_valid_path(path)


# Type variables
T = TypeVar("T")  # Generic type for flexible typing

__all__ = [
    # Main classes
    "FileSystemService",
    "create_service",
    "service",
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
