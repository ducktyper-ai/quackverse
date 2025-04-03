# src/quackcore/fs/service/path_operations.py
"""
Path operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for path manipulation.
"""

import os
import tempfile
from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.logging import get_logger


class PathOperationsMixin:
    """Mixin class for path operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    @wrap_io_errors
    def join_path(self, base: str | Path, *parts: str | Path) -> Path:
        """
        Join base path with additional parts.

        Args:
            base: Base path
            *parts: Additional path parts to join

        Returns:
            Joined path as a Path object
        """
        base_path = Path(base)
        for part in parts:
            base_path = base_path / part
        return base_path

    @wrap_io_errors
    def normalize_path(self, path: str | Path) -> Path:
        """
        Normalize a path to an absolute path.

        Args:
            path: Path to normalize

        Returns:
            Normalized absolute Path
        """
        path_obj = Path(path)
        if not path_obj.is_absolute():
            try:
                path_obj = path_obj.resolve()
            except FileNotFoundError as e:
                # Log the error but don't fail completely
                get_logger(__name__).warning(f"Could not normalize path '{path}': {str(e)}")
                # Return the original path if resolution fails
                return Path(path)
        return path_obj

    @wrap_io_errors
    def create_temp_directory(self, prefix: str = "quackcore_") -> Path:
        """
        Create a temporary directory.

        Args:
            prefix: Prefix for the temporary directory name

        Returns:
            Path to the created temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
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