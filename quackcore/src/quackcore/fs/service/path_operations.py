# quackcore/src/quackcore/fs/service/path_operations.py
"""
Path _operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for path manipulation.
"""

import os
import tempfile
from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs import DataResult, OperationResult
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

    # This method is added in the base class
    def _normalize_input_path(self,
                              path: str | Path | DataResult | OperationResult) -> Path:
        """Normalize an input path to a Path object."""
        raise NotImplementedError("This method should be overridden")

    @wrap_io_errors
    def join_path(self, *parts: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Join path components.

        Args:
            *parts: Path parts to join (can be string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with the joined path
        """
        try:
            if not parts:
                result_path = Path()
            else:
                # Normalize each part before joining
                normalized_parts = [self._normalize_input_path(part) for part in parts]
                base_path = normalized_parts[0]
                for part in normalized_parts[1:]:
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
            if not parts:
                path_for_error = Path()
            else:
                try:
                    path_for_error = self._normalize_input_path(parts[0])
                except:
                    path_for_error = Path()

            return DataResult(
                success=False,
                path=path_for_error,
                data="",
                format="path",
                error=str(e),
                message="Failed to join path parts",
            )

    @wrap_io_errors
    def split_path(self, path: str | Path | DataResult | OperationResult) -> DataResult[
        list[str]]:
        """
        Split a path into its components.

        Args:
            path: Path to split (string, Path, DataResult, or OperationResult)

        Returns:
            List of path components
        """
        normalized_path = self._normalize_input_path(path)
        return split_path(normalized_path)

    @wrap_io_errors
    def normalize_path(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Normalize a path for cross-platform compatibility.

        This does not check if the path exists.

        Args:
            path: Path to normalize (string, Path, DataResult, or OperationResult)

        Returns:
            Normalized Path object
        """
        normalized_path = self._normalize_input_path(path)
        return utils_normalize_path(normalized_path)

    def expand_user_vars(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Expand user variables and environment variables in a path.

        Args:
            path: Path with variables (string, Path, DataResult, or OperationResult)

        Returns:
            Expanded Path object
        """
        normalized_path = self._normalize_input_path(path)
        return expand_user_vars(normalized_path)

    def is_same_file(self, path1: str | Path | DataResult | OperationResult,
                     path2: str | Path | DataResult | OperationResult) -> DataResult[
        bool]:
        """
        Check if two paths refer to the same file.

        Args:
            path1: First path (string, Path, DataResult, or OperationResult)
            path2: Second path (string, Path, DataResult, or OperationResult)

        Returns:
            True if paths refer to the same file
        """
        normalized_path1 = self._normalize_input_path(path1)
        normalized_path2 = self._normalize_input_path(path2)
        return is_same_file(normalized_path1, normalized_path2)

    def is_subdirectory(
            self, child: str | Path | DataResult | OperationResult,
            parent: str | Path | DataResult | OperationResult
    ) -> DataResult[bool]:
        """
        Check if a path is a subdirectory of another path.

        Args:
            child: Potential child path (string, Path, DataResult, or OperationResult)
            parent: Potential parent path (string, Path, DataResult, or OperationResult)

        Returns:
            True if child is a subdirectory of parent
        """
        normalized_child = self._normalize_input_path(child)
        normalized_parent = self._normalize_input_path(parent)
        return is_subdirectory(normalized_child, normalized_parent)

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
    def get_extension(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Get the file extension from a path.

        Args:
            path: Path to get extension from (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with file extension without the dot
        """
        try:
            normalized_path = self._normalize_input_path(path)
            path_str = str(normalized_path)
            _, ext = os.path.splitext(path_str)
            extension = ext.lstrip(".").lower()

            return DataResult(
                success=True,
                path=normalized_path,
                data=extension,
                format="extension",
                message=f"Successfully extracted extension: {extension}",
            )
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return DataResult(
                success=False,
                path=normalized_path,
                data="",
                format="extension",
                error=str(e),
                message="Failed to extract file extension",
            )

    def resolve_path(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Resolve a path relative to the service's base_dir and return as a string.

        This is a public, safe wrapper around _resolve_path that conforms to
        the DataResult structure used throughout QuackCore.

        Args:
            path: Input path (absolute or relative) (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with the fully resolved, absolute path as a string.
        """
        try:
            normalized_path = self._normalize_input_path(path)
            resolved = self.operations._resolve_path(normalized_path)
            return DataResult(
                success=True,
                path=resolved,
                data=str(resolved),
                format="path",
                message=f"Resolved path to: {resolved}",
            )
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return DataResult(
                success=False,
                path=normalized_path,
                data="",
                format="path",
                error=str(e),
                message="Failed to resolve path",
            )
