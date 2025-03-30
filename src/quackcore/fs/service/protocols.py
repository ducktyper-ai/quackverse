"""
Protocol definitions for FileSystemService.

This module defines protocol classes that specify interfaces
required by the various mixins.
"""

from pathlib import Path
from typing import Any, Protocol, TypeVar

from quackcore.fs.results import (
    DataResult,
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    ReadResult,
    WriteResult,
)

T = TypeVar("T")  # Generic type for flexible typing


class LoggerProtocol(Protocol):
    """Protocol defining the logger interface required by mixins."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        ...

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        ...

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        ...

    def setLevel(self, level: int) -> None:
        """Set the logging level."""
        ...


class OperationsProtocol(Protocol):
    """Protocol defining the operations interface required by mixins."""

    def read_text(self, path: str | Path, encoding: str = ...) -> ReadResult[str]:
        """Read text from a file."""
        ...

    def read_binary(self, path: str | Path) -> ReadResult[bytes]:
        """Read binary data from a file."""
        ...

    def write_text(self, path: str | Path, content: str, encoding: str = ...,
                   atomic: bool = ..., calculate_checksum: bool = ...) -> WriteResult:
        """Write text to a file."""
        ...

    def write_binary(self, path: str | Path, content: bytes, atomic: bool = ...,
                     calculate_checksum: bool = ...) -> WriteResult:
        """Write binary data to a file."""
        ...

    def copy(self, src: str | Path, dst: str | Path,
             overwrite: bool = ...) -> WriteResult:
        """Copy a file or directory."""
        ...

    def move(self, src: str | Path, dst: str | Path,
             overwrite: bool = ...) -> WriteResult:
        """Move a file or directory."""
        ...

    def delete(self, path: str | Path, missing_ok: bool = ...) -> OperationResult:
        """Delete a file or directory."""
        ...

    def create_directory(self, path: str | Path,
                         exist_ok: bool = ...) -> OperationResult:
        """Create a directory."""
        ...

    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """Get information about a file or directory."""
        ...

    def list_directory(self, path: str | Path, pattern: str | None = ...,
                       include_hidden: bool = ...) -> DirectoryInfoResult:
        """List contents of a directory."""
        ...

    def find_files(self, path: str | Path, pattern: str, recursive: bool = ...,
                   include_hidden: bool = ...) -> FindResult:
        """Find files matching a pattern."""
        ...

    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """Read YAML file and parse its contents."""
        ...

    def write_yaml(self, path: str | Path, data: dict,
                   atomic: bool = ...) -> WriteResult:
        """Write data to a YAML file."""
        ...

    def read_json(self, path: str | Path) -> DataResult[dict]:
        """Read JSON file and parse its contents."""
        ...

    def write_json(self, path: str | Path, data: dict, atomic: bool = ...,
                   indent: int = ...) -> WriteResult:
        """Write data to a JSON file."""
        ...


class ServiceProtocol(Protocol):
    """Protocol defining the requirements for service mixins."""

    @property
    def logger(self) -> LoggerProtocol:
        """Get the logger for this service."""
        ...

    @property
    def operations(self) -> OperationsProtocol:
        """Get the FileSystemOperations instance."""
        ...

    @property
    def base_dir(self) -> Path:
        """Get the base directory."""
        ...