# src/quackcore/fs/service/path_operations.py
"""
Path manipulation utilities for the FileSystemService.
"""

from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.utils import (
    expand_user_vars,
    get_extension,
    is_same_file,
    is_subdirectory,
    join_path,
    normalize_path,
    split_path,
)


class PathOperationsMixin:
    """Mixin class for path operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    # --- Path Manipulation and Introspection Utilities ---

    @wrap_io_errors
    def join_path(self, *parts: str | Path) -> Path:
        """
        Join path components.

        Args:
            *parts: Path parts to join

        Returns:
            Joined Path object
        """
        return join_path(*parts)

    @wrap_io_errors
    def split_path(self, path: str | Path) -> list[str]:
        """
        Split a path into its components.

        Args:
            path: Path to split

        Returns:
            List of path components
        """
        return split_path(path)

    @wrap_io_errors
    def normalize_path(self, path: str | Path) -> Path:
        """
        Normalize a path for cross-platform compatibility.

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        return normalize_path(path)

    def expand_user_vars(self, path: str | Path) -> Path:
        """
        Expand user variables and environment variables in a path.

        Args:
            path: Path with variables

        Returns:
            Expanded Path object
        """
        return expand_user_vars(path)

    def is_same_file(self, path1: str | Path, path2: str | Path) -> bool:
        """
        Check if two paths refer to the same file.

        Args:
            path1: First path
            path2: Second path

        Returns:
            True if paths refer to the same file
        """
        return is_same_file(path1, path2)

    def is_subdirectory(self, child: str | Path, parent: str | Path) -> bool:
        """
        Check if a path is a subdirectory of another path.

        Args:
            child: Potential child path
            parent: Potential parent path

        Returns:
            True if child is a subdirectory of parent
        """
        return is_subdirectory(child, parent)

    def get_extension(self, path: str | Path) -> str:
        """
        Get the file extension from a path.

        Args:
            path: File path

        Returns:
            File extension without the dot
        """
        return get_extension(path)