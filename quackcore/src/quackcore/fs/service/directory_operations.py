# quackcore/src/quackcore/fs/service/directory_operations.py
"""
Directory management _operations for the FileSystemService.
"""

from pathlib import Path
from typing import Protocol

from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.results import (
    DataResult,
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

    # This method is added in the base class
    def _normalize_input_path(self,
                              path: str | Path | DataResult | OperationResult) -> Path:
        """Normalize an input path to a Path object."""
        raise NotImplementedError("This method should be overridden")

    def create_directory(
            self, path: str | Path | DataResult | OperationResult, exist_ok: bool = True
    ) -> OperationResult:
        """
        Create a directory.

        Args:
            path: Path to create (string, Path, DataResult, or OperationResult)
            exist_ok: Whether to ignore if the directory already exists

        Returns:
            OperationResult with operation status
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._create_directory(normalized_path, exist_ok)

    # --- Information and Listing Operations ---

    def get_file_info(self,
                      path: str | Path | DataResult | OperationResult) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to get information about (string, Path, DataResult, or OperationResult)

        Returns:
            FileInfoResult with file information
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._get_file_info(normalized_path)

    def list_directory(
            self,
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
        normalized_path = self._normalize_input_path(path)
        return self.operations._list_directory(normalized_path, pattern, include_hidden)

    def find_files(
            self,
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
        normalized_path = self._normalize_input_path(path)
        return self.operations._find_files(normalized_path, pattern, recursive,
                                           include_hidden)
