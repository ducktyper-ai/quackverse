# src/quackcore/fs/service/standalone.py
"""
Standalone utility functions that are exposed at the package level.

These functions provide direct access to common filesystem operations
without having to create a service instance.
"""

from pathlib import Path
from typing import TypeVar

from quackcore.fs.results import (
    DataResult,
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    ReadResult,
    WriteResult,
)

# Import the complete FileSystemService with all mixins
from quackcore.fs.service.full_class import FileSystemService

# Import PathInfo directly from its module
from quackcore.fs.service.path_validation import PathInfo

T = TypeVar("T")  # Generic type for flexible typing

# Create a service instance specifically for standalone functions
_service = FileSystemService()

# File operations


def read_text(path: str | Path, encoding: str = "utf-8") -> ReadResult[str]:
    """
    Read text from a file.

    Args:
        path: Path to the file.
        encoding: Text encoding.

    Returns:
        ReadResult with the file content as text.
    """
    return _service.read_text(path, encoding)


def write_text(
    path: str | Path,
    content: str,
    encoding: str = "utf-8",
    atomic: bool = True,
) -> WriteResult:
    """
    Write text to a file.

    Args:
        path: Path to the file.
        content: Content to write.
        encoding: Text encoding.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_text(path, content, encoding, atomic)


def read_binary(path: str | Path) -> ReadResult[bytes]:
    """
    Read binary data from a file.

    Args:
        path: Path to the file.

    Returns:
        ReadResult with the file content as bytes.
    """
    return _service.read_binary(path)


def write_binary(
    path: str | Path,
    content: bytes,
    atomic: bool = True,
) -> WriteResult:
    """
    Write binary data to a file.

    Args:
        path: Path to the file.
        content: Content to write.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_binary(path, content, atomic)


def read_lines(path: str | Path, encoding: str = "utf-8") -> ReadResult[list[str]]:
    """
    Read lines from a text file.

    Args:
        path: Path to the file.
        encoding: Text encoding.

    Returns:
        ReadResult with the file content as a list of lines.
    """
    return _service.read_lines(path, encoding)


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
        path: Path to the file.
        lines: Lines to write.
        encoding: Text encoding.
        atomic: Whether to write the file atomically.
        line_ending: The line ending to use.

    Returns:
        WriteResult with the outcome of the operation.
    """
    return _service.write_lines(path, lines, encoding, atomic, line_ending)


def create_directory(path: str | Path, exist_ok: bool = True) -> OperationResult:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create.
        exist_ok: If False, raise an error when the directory exists.

    Returns:
        OperationResult indicating whether the directory was created or already exists.
    """
    return _service.create_directory(path, exist_ok)


def read_yaml(path: str | Path) -> DataResult[dict]:
    """
    Read a YAML file and parse its contents.

    Args:
        path: Path to the YAML file.

    Returns:
        DataResult containing the parsed YAML data.
    """
    return _service.read_yaml(path)


def write_yaml(
    path: str | Path,
    data: dict,
    atomic: bool = True,
) -> WriteResult:
    """
    Write data to a YAML file.

    Args:
        path: Path to the YAML file.
        data: Data to write.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_yaml(path, data, atomic)


def read_json(path: str | Path) -> DataResult[dict]:
    """
    Read a JSON file and parse its contents.

    Args:
        path: Path to the JSON file.

    Returns:
        DataResult with parsed JSON data.
    """
    return _service.read_json(path)


def write_json(
    path: str | Path,
    data: dict,
    atomic: bool = True,
    indent: int = 2,
) -> WriteResult:
    """
    Write data to a JSON file.

    Args:
        path: Path to the JSON file.
        data: Data to write.
        atomic: Whether to use atomic writing.
        indent: Number of spaces to indent.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_json(path, data, atomic, indent)


def get_file_info(path: str | Path) -> FileInfoResult:
    """
    Get information about a file or directory.

    Args:
        path: Path to get information about.

    Returns:
        FileInfoResult with file information.
    """
    return _service.get_file_info(path)


def list_directory(
    path: str | Path,
    pattern: str | None = None,
    include_hidden: bool = False,
) -> DirectoryInfoResult:
    """
    List contents of a directory.

    Args:
        path: Directory path to list.
        pattern: Pattern to match files against.
        include_hidden: Whether to include hidden files.

    Returns:
        DirectoryInfoResult with directory contents.
    """
    return _service.list_directory(path, pattern, include_hidden)


def find_files(
    path: str | Path,
    pattern: str,
    recursive: bool = True,
    include_hidden: bool = False,
) -> FindResult:
    """
    Find files matching a pattern.

    Args:
        path: Directory to search.
        pattern: Pattern to match files against.
        recursive: Whether to search recursively.
        include_hidden: Whether to include hidden files.

    Returns:
        FindResult with the matching files.
    """
    return _service.find_files(path, pattern, recursive, include_hidden)


def copy(src: str | Path, dst: str | Path, overwrite: bool = False) -> WriteResult:
    """
    Copy a file or directory.

    Args:
        src: Source path.
        dst: Destination path.
        overwrite: Whether to overwrite if the destination exists.

    Returns:
        WriteResult with operation status.
    """
    return _service.copy(src, dst, overwrite)


def move(src: str | Path, dst: str | Path, overwrite: bool = False) -> WriteResult:
    """
    Move a file or directory.

    Args:
        src: Source path.
        dst: Destination path.
        overwrite: Whether to overwrite if the destination exists.

    Returns:
        WriteResult with operation status.
    """
    return _service.move(src, dst, overwrite)


def delete(path: str | Path, missing_ok: bool = True) -> OperationResult:
    """
    Delete a file or directory.

    Args:
        path: Path to delete.
        missing_ok: Whether to ignore if the path doesn't exist.

    Returns:
        OperationResult with operation status.
    """
    return _service.delete(path, missing_ok)


def split_path(path: str | Path) -> list[str]:
    """
    Split a path into its components.

    Args:
        path: Path to split.

    Returns:
        List of path components.
    """
    return _service.split_path(path)


def join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    Args:
        *parts: Path parts to join.

    Returns:
        Joined Path object.
    """
    return _service.join_path(*parts)


# NEW: Path utility function for checking existence


def path_exists(path: str | Path) -> bool:
    """
    Check if a path exists using the FileSystemService.

    This function delegates directly to the underlying service instance,
    ensuring consistency with all other filesystem operations.

    Args:
        path: The file or directory path to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    return _service.path_exists(path)


def normalize_path_with_info(path: str | Path) -> PathInfo:
    """
    Normalize a path and return detailed information.

    Args:
        path: The path to normalize.

    Returns:
        PathInfo object with the normalized path and status information.
    """
    return _service.normalize_path_with_info(path)


def get_path_info(path: str | Path) -> PathInfo:
    """
    Get information about a path’s validity and format.

    Args:
        path: The path to check.

    Returns:
        PathInfo object with validation results.
    """
    return _service.get_path_info(path)


def is_valid_path(path: str | Path) -> bool:
    """
    Check if a path has valid syntax.

    Args:
        path: The path to check.

    Returns:
        True if the path has valid syntax.
    """
    return _service.is_valid_path(path)
