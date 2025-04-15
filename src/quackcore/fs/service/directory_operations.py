# src/quackcore/fs/service/directory_operations.py
"""
Directory management _operations for the FileSystemService.
"""

from pathlib import Path
from typing import Protocol

from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.results import (
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
)


class HasOperations(Protocol):
    """Protocol for classes that have _operations."""

    operations: FileSystemOperations


class DirectoryOperationsMixin:
    """Mixin class for directory _operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have _operations
    operations: FileSystemOperations

    def create_directory(
        self, path: str | Path, exist_ok: bool = True
    ) -> OperationResult:
        """
        Create a directory.

        Args:
            path: Path to create
            exist_ok: Whether to ignore if the directory already exists

        Returns:
            OperationResult with operation status
        """
        return self.operations._create_directory(path, exist_ok)

    # --- Information and Listing Operations ---

    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to get information about

        Returns:
            FileInfoResult with file information
        """
        return self.operations._get_file_info(path)

    def list_directory(
        self,
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
        return self.operations._list_directory(path, pattern, include_hidden)

    def find_files(
        self,
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
        return self.operations._find_files(path, pattern, recursive, include_hidden)
