# src/quackcore/fs/service/path_operations.py
"""
Path _operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for path manipulation.
"""

import os
import tempfile
from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs import DataResult
from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.api.public import (
    expand_user_vars,
    is_same_file,
    is_subdirectory,
    split_path,
)
from quackcore.fs.api.public import normalize_path as utils_normalize_path


class PathOperationsMixin:
    """Mixin class for path _operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have _operations
    operations: FileSystemOperations

    @wrap_io_errors
    def join_path(self, *parts: str | Path) -> DataResult[str]:
        """
        Join path components.

        Args:
            *parts: Path parts to join

        Returns:
            DataResult with the joined path
        """
        try:
            if not parts:
                result_path = Path()
            else:
                base_path = Path(parts[0])
                for part in parts[1:]:
                    base_path = base_path / part
                result_path = base_path

            return DataResult(
                success=True,
                path=result_path,
                data=str(result_path),
                format="path",
                message="Successfully joined path parts",
            )
        except Exception as e:
            return DataResult(
                success=False,
                path=Path() if not parts else Path(parts[0]),
                data="",
                format="path",
                error=str(e),
                message="Failed to join path parts",
            )

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

    def is_subdirectory(
        self, child: str | Path, parent: str | Path
    ) -> DataResult[bool]:
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
    ) -> DataResult[str]:
        """
        Create a temporary directory.

        Args:
            prefix: Prefix for the temporary directory name
            suffix: Suffix for the temporary directory name

        Returns:
            DataResult with path to the created temporary directory
        """
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, suffix=suffix))
            return DataResult(
                success=True,
                path=temp_dir,
                data=str(temp_dir),
                format="path",
                message=f"Created temporary directory: {temp_dir}",
            )
        except Exception as e:
            return DataResult(
                success=False,
                path=None,
                data="",
                format="path",
                error=str(e),
                message="Failed to create temporary directory",
            )

    @wrap_io_errors
    def get_extension(self, path: str | Path) -> DataResult[str]:
        """
        Get the file extension from a path.

        Args:
            path: Path to get extension from

        Returns:
            DataResult with file extension without the dot
        """
        try:
            path_obj = Path(path)
            path_str = str(path_obj)
            _, ext = os.path.splitext(path_str)
            extension = ext.lstrip(".").lower()

            return DataResult(
                success=True,
                path=path_obj,
                data=extension,
                format="extension",
                message=f"Successfully extracted extension: {extension}",
            )
        except Exception as e:
            return DataResult(
                success=False,
                path=Path(path) if isinstance(path, (str, Path)) else Path(),
                data="",
                format="extension",
                error=str(e),
                message="Failed to extract file extension",
            )

    def resolve_path(self, path: str | Path) -> DataResult[str]:
        """
        Resolve a path relative to the service's base_dir and return as a string.

        This is a public, safe wrapper around _resolve_path that conforms to
        the DataResult structure used throughout QuackCore.

        Args:
            path: Input path (absolute or relative)

        Returns:
            DataResult with the fully resolved, absolute path as a string.
        """
        try:
            resolved = self.operations._resolve_path(path)
            return DataResult(
                success=True,
                path=resolved,
                data=str(resolved),
                format="path",
                message=f"Resolved path to: {resolved}",
            )
        except Exception as e:
            return DataResult(
                success=False,
                path=Path(path),
                data="",
                format="path",
                error=str(e),
                message="Failed to resolve path",
            )
