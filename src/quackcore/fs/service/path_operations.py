# src/quackcore/fs/service/path_operations.py
"""
Path operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for path manipulation.
"""

import os
import tempfile
from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs import DataResult
from quackcore.fs.api.public import (
    expand_user_vars,
    is_same_file,
    is_subdirectory,
)
from quackcore.fs.api.public import normalize_path as utils_normalize_path
from quackcore.fs.api.public import (
    split_path,
)
from quackcore.fs.operations import FileSystemOperations


class PathOperationsMixin:
    """Mixin class for path operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    @wrap_io_errors
    def join_path(self, *parts: str | Path) -> Path:
        """
        Join path components.

        Args:
            *parts: Path parts to join

        Returns:
            Joined Path object
        """
        if not parts:
            return Path()

        base_path = Path(parts[0])
        for part in parts[1:]:
            base_path = base_path / part
        return base_path

    @wrap_io_errors
    def split_path(self, path: str | Path) -> DataResult[list[str]]:
        """
        Split a path into its components.

        Args:
            path: Path to split

        Returns:
            List of path components
        """
        return split_path(path)

    @wrap_io_errors
    def normalize_path(self, path: str | Path) -> DataResult[str]:
        """
        Normalize a path for cross-platform compatibility.

        This does not check if the path exists.

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        return utils_normalize_path(path)

    def expand_user_vars(self, path: str | Path) -> DataResult[str]:
        """
        Expand user variables and environment variables in a path.

        Args:
            path: Path with variables

        Returns:
            Expanded Path object
        """
        return expand_user_vars(path)

    def is_same_file(self, path1: str | Path, path2: str | Path) -> DataResult[bool]:
        """
        Check if two paths refer to the same file.

        Args:
            path1: First path
            path2: Second path

        Returns:
            True if paths refer to the same file
        """
        return is_same_file(path1, path2)

    def is_subdirectory(self, child: str | Path, parent: str | Path) -> DataResult[
        bool]:
        """
        Check if a path is a subdirectory of another path.

        Args:
            child: Potential child path
            parent: Potential parent path

        Returns:
            True if child is a subdirectory of parent
        """
        return is_subdirectory(child, parent)

    @wrap_io_errors
    def create_temp_directory(
        self, prefix: str = "quackcore_", suffix: str = ""
    ) -> Path:
        """
        Create a temporary directory.

        Args:
            prefix: Prefix for the temporary directory name
            suffix: Suffix for the temporary directory name

        Returns:
            Path to the created temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, suffix=suffix))
        return temp_dir

    @wrap_io_errors
    def get_extension(self, path: str | Path) -> str:
        """
        Get the file extension from a path.

        Args:
            path: Path to get extension from

        Returns:
            File extension without the dot, or empty string if no extension
        """
        path_str = str(path)
        _, ext = os.path.splitext(path_str)
        return ext.lstrip(".").lower()
