# src/quackcore/fs/types.py
"""
Type definitions for the FileSystemService.

This module defines the return types and data structures used by the FS module.
"""

from pathlib import Path
from typing import Any
from pydantic import BaseModel


class OperationResult(BaseModel):
    """Base result for file system operations."""

    success: bool
    path: str | None = None
    message: str | None = None
    error: str | None = None


class ReadResult(OperationResult):
    """Result of a read operation."""

    content: str | bytes | None = None
    encoding: str | None = None
    data: Any = None  # For parsed data (JSON, YAML)


class WriteResult(OperationResult):
    """Result of a write operation."""

    bytes_written: int | None = None


class FileInfoResult(OperationResult):
    """Result of a file info operation."""

    exists: bool = False
    is_file: bool = False
    is_directory: bool = False
    size: int | None = None
    modified: float | None = None
    created: float | None = None


class DirectoryListResult(OperationResult):
    """Result of a directory listing operation."""

    directories: list[Path] = []
    files: list[Path] = []


class FileFindResult(OperationResult):
    """Result of a file find operation."""

    files: list[Path] = []


class FileInfo(BaseModel):
    """Information about a file."""

    path: Path
    format: str | None = None
    size: int = 0
    exists: bool = False