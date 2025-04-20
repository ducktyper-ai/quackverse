# quackcore/src/quackcore/fs/service/standalone.py
"""
Standalone utility functions that are exposed at the package level.

These functions provide direct access to common filesystem _operations
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
    PathResult,
    ReadResult,
    WriteResult,
)

# Import the complete FileSystemService with all mixins
from quackcore.fs.service.full_class import FileSystemService

T = TypeVar("T")  # Generic type for flexible typing

# Create a service instance specifically for standalone functions
_service = FileSystemService()

# File _operations


def read_text(path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[str]:
    """
    Read text from a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        encoding: Text encoding.

    Returns:
        ReadResult with the file content as text.
    """
    return _service.read_text(path, encoding)


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
        content: Content to write.
        encoding: Text encoding.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_text(path, content, encoding, atomic)


def read_binary(path: str | Path | DataResult | OperationResult) -> ReadResult[bytes]:
    """
    Read binary data from a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)

    Returns:
        ReadResult with the file content as bytes.
    """
    return _service.read_binary(path)


def write_binary(
    path: str | Path | DataResult | OperationResult,
    content: bytes,
    atomic: bool = True,
) -> WriteResult:
    """
    Write binary data to a file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        content: Content to write.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_binary(path, content, atomic)


def read_lines(path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[list[str]]:
    """
    Read lines from a text file.

    Args:
        path: Path to the file (string, Path, DataResult, or OperationResult)
        encoding: Text encoding.

    Returns:
        ReadResult with the file content as a list of lines.
    """
    return _service.read_lines(path, encoding)


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
        lines: Lines to write.
        encoding: Text encoding.
        atomic: Whether to write the file atomically.
        line_ending: The line ending to use.

    Returns:
        WriteResult with the outcome of the operation.
    """
    return _service.write_lines(path, lines, encoding, atomic, line_ending)


def create_directory(path: str | Path | DataResult | OperationResult, exist_ok: bool = True) -> OperationResult:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create (string, Path, DataResult, or OperationResult)
        exist_ok: If False, raise an error when the directory exists.

    Returns:
        OperationResult indicating whether the directory was created or already exists.
    """
    return _service.create_directory(path, exist_ok)


def read_yaml(path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
    """
    Read a YAML file and parse its contents.

    Args:
        path: Path to the YAML file (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult containing the parsed YAML data.
    """
    return _service.read_yaml(path)


def write_yaml(
    path: str | Path | DataResult | OperationResult,
    data: dict,
    atomic: bool = True,
) -> WriteResult:
    """
    Write data to a YAML file.

    Args:
        path: Path to the YAML file (string, Path, DataResult, or OperationResult)
        data: Data to write.
        atomic: Whether to use atomic writing.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_yaml(path, data, atomic)


def read_json(path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
    """
    Read a JSON file and parse its contents.

    Args:
        path: Path to the JSON file (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with parsed JSON data.
    """
    return _service.read_json(path)


def write_json(
    path: str | Path | DataResult | OperationResult,
    data: dict,
    atomic: bool = True,
    indent: int = 2,
) -> WriteResult:
    """
    Write data to a JSON file.

    Args:
        path: Path to the JSON file (string, Path, DataResult, or OperationResult)
        data: Data to write.
        atomic: Whether to use atomic writing.
        indent: Number of spaces to indent.

    Returns:
        WriteResult with operation status.
    """
    return _service.write_json(path, data, atomic, indent)


def get_file_info(path: str | Path | DataResult | OperationResult) -> FileInfoResult:
    """
    Get information about a file or directory.

    Args:
        path: Path to get information about (string, Path, DataResult, or OperationResult)

    Returns:
        FileInfoResult with file information.
    """
    return _service.get_file_info(path)


def list_directory(
    path: str | Path | DataResult | OperationResult,
    pattern: str | None = None,
    include_hidden: bool = False,
) -> DirectoryInfoResult:
    """
    List contents of a directory.

    Args:
        path: Directory path to list (string, Path, DataResult, or OperationResult)
        pattern: Pattern to match files against.
        include_hidden: Whether to include hidden files.

    Returns:
        DirectoryInfoResult with directory contents.
    """
    return _service.list_directory(path, pattern, include_hidden)


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
        pattern: Pattern to match files against.
        recursive: Whether to search recursively.
        include_hidden: Whether to include hidden files.

    Returns:
        FindResult with the matching files.
    """
    return _service.find_files(path, pattern, recursive, include_hidden)


def copy(src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False) -> WriteResult:
    """
    Copy a file or directory.

    Args:
        src: Source path (string, Path, DataResult, or OperationResult)
        dst: Destination path (string, Path, DataResult, or OperationResult)
        overwrite: Whether to overwrite if the destination exists.

    Returns:
        WriteResult with operation status.
    """
    return _service.copy(src, dst, overwrite)


def move(src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False) -> WriteResult:
    """
    Move a file or directory.

    Args:
        src: Source path (string, Path, DataResult, or OperationResult)
        dst: Destination path (string, Path, DataResult, or OperationResult)
        overwrite: Whether to overwrite if the destination exists.

    Returns:
        WriteResult with operation status.
    """
    return _service.move(src, dst, overwrite)


def delete(path: str | Path | DataResult | OperationResult, missing_ok: bool = True) -> OperationResult:
    """
    Delete a file or directory.

    Args:
        path: Path to delete (string, Path, DataResult, or OperationResult)
        missing_ok: Whether to ignore if the path doesn't exist.

    Returns:
        OperationResult with operation status.
    """
    return _service.delete(path, missing_ok)


def split_path(path: str | Path | DataResult | OperationResult) -> DataResult[list[str]]:
    """
    Split a path into its components.

    Args:
        path: Path to split (string, Path, DataResult, or OperationResult)

    Returns:
        List of path components.
    """
    return _service.split_path(path)


def join_path(*parts: str | Path | DataResult | OperationResult) -> DataResult[str]:
    """
    Join path components.

    Args:
        *parts: Path parts to join. Each part can be a string, Path, DataResult, or OperationResult.

    Returns:
        Joined Path object.
    """
    return _service.join_path(*parts)


# Updated functions from standalone.py that work with PathValidationMixin


def path_exists(path: str | Path | DataResult | OperationResult) -> DataResult[bool]:
    """
    Check if a path exists using the FileSystemService.

    Args:
        path: The file or directory path to check (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if path exists
    """
    return _service.path_exists(path)


def normalize_path_with_info(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Normalize a path and return detailed information.

    Args:
        path: The path to normalize (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult containing the normalized path and status information.
    """
    return _service.normalize_path_with_info(path)

def normalize_path(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Normalize a path.

    Args:
        path: The path to normalize (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult containing the normalized path and status information.
    """
    return _service.normalize_path(path)


def get_path_info(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Get information about a path's validity and format.

    Args:
        path: The path to check (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult containing validation results.
    """
    return _service.get_path_info(path)


def is_valid_path(path: str | Path | DataResult | OperationResult) -> DataResult[bool]:
    """
    Check if a path has valid syntax.

    Args:
        path: The path to check (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if the path has valid syntax.
    """
    return _service.is_valid_path(path)


def get_extension(path: str | Path | DataResult | OperationResult) -> DataResult[str]:
    """
    Get the file extension from a path.

    Args:
        path: Path to get extension from (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with file extension without the dot
    """
    return _service.get_extension(path)

def expand_user_vars(path: str | Path | DataResult | OperationResult) -> DataResult[
    str]:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables to expand (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with expanded path as string
    """

    return _service.expand_user_vars(path)

def resolve_path(path: str | Path | DataResult | OperationResult) -> \
    PathResult:
        """
        Resolve a path relative to the service's base_dir and return as a string.

        This is a public, safe wrapper around _resolve_path that conforms to
        the DataResult structure used throughout QuackCore.

        Args:
            path: Input path (absolute or relative) (string, Path, DataResult, or OperationResult)

        Returns:
            PathResult with the fully resolved, absolute path as a string.
        """
        return _service.resolve_path(path)
