# src/quackcore/fs/service/path_validation.py
"""
Path validation utilities for the FileSystemService.

These utilities extend the FileSystemService with methods to validate
and inspect paths, primarily used for configuration validation.
"""

import os
from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.results import DataResult, PathResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


class PathValidationMixin:
    """
    Mixin class for path validation operations in the FileSystemService.

    This mixin "dogfoods" our existing implementation from FileInfoOperationsMixin
    (or any compatible implementation exposed via `self.operations`) to check if a path exists.
    """

    # This ensures the mixin will only be used with classes that have an 'operations' attribute.
    operations: FileSystemOperations

    def path_exists(self, path: str | Path) -> DataResult[bool]:
        """
        Check if a path exists in the filesystem by leveraging the existing
        FileInfoOperationsMixin implementation via self.operations.

        Args:
            path: Path to check for existence

        Returns:
            DataResult with boolean indicating if the path exists
        """
        path_obj = Path(path)  # Normalize early
        try:
            # Delegate to the file_info's path_exists implementation
            exists = self.operations._path_exists(path_obj)

            return DataResult(
                success=True,
                path=path_obj,
                data=exists,
                format="boolean",
                message=f"Path {path_obj} {'exists' if exists else 'does not exist'}",
            )
        except Exception as exc:
            logger.error(f"Error checking if path exists using operations: {exc}")
            # Fallback: use the standard pathlib.Path.exists() check
            try:
                exists = path_obj.exists()
                logger.debug(f"Fallback check for {path_obj} returned: {exists}")

                return DataResult(
                    success=True,
                    path=path_obj,
                    data=exists,
                    format="boolean",
                    message=f"Path {path_obj} {'exists' if exists else 'does not exist'} (fallback check)",
                )
            except Exception as fallback_exc:
                logger.error(
                    f"Fallback direct check failed for {path_obj}: {fallback_exc}"
                )

                return DataResult(
                    success=False,
                    path=path_obj,
                    data=False,
                    format="boolean",
                    error=f"Failed to check if path exists: {str(fallback_exc)}",
                )

    def get_path_info(self, path: str | Path) -> PathResult:
        """
        Get information about a path's validity and format.

        This method checks whether a path is valid and provides information
        without requiring the path to exist.

        Args:
            path: Path to check

        Returns:
            PathResult with validation results
        """
        try:
            path_obj = Path(path)  # Normalize early
            is_absolute = path_obj.is_absolute()

            # Check if the path syntax is valid without requiring existence
            is_valid = self._is_path_syntax_valid(str(path_obj))

            # Check for existence (optional info)
            exists_result = self.path_exists(path_obj)
            exists = exists_result.data if exists_result.success else False

            return PathResult(
                success=True,
                path=path_obj,
                is_absolute=is_absolute,
                is_valid=is_valid,
                exists=exists,
                message="Path validation successful",
            )
        except Exception as e:
            return PathResult(
                success=False,
                path=Path(path) if isinstance(path, (str, Path)) else Path(),
                is_valid=False,
                error=f"Path validation failed: {str(e)}",
            )

    def is_valid_path(self, path: str | Path) -> DataResult[bool]:
        """
        Check if a path has valid syntax.

        This method checks only the syntax validity of a path,
        not whether it exists or is accessible.

        Args:
            path: Path to check

        Returns:
            DataResult with boolean indicating if the path has valid syntax
        """
        path_obj = Path(path)  # Normalize early
        try:
            is_valid = self._is_path_syntax_valid(str(path_obj))

            return DataResult(
                success=True,
                path=path_obj,
                data=is_valid,
                format="boolean",
                message=f"Path {path_obj} {'has valid' if is_valid else 'has invalid'} syntax",
            )
        except Exception as e:
            logger.error(f"Error checking path validity for {path_obj}: {e}")

            return DataResult(
                success=False,
                path=path_obj,
                data=False,
                format="boolean",
                error=f"Failed to check path validity: {str(e)}",
            )

    def _is_path_syntax_valid(self, path_str: str) -> bool:
        """
        Check if a path string has valid syntax.

        Args:
            path_str: Path string to check

        Returns:
            True if the path has valid syntax
        """
        try:
            # Attempt to create a Path object from the string
            path_obj = Path(path_str)

            # Windows-specific checks for reserved characters and names
            if os.name == "nt":
                reserved_chars = '<>:"|?*'
                if any(char in path_obj.name for char in reserved_chars):
                    return False

                reserved_names = [
                    "CON",
                    "PRN",
                    "AUX",
                    "NUL",
                    "COM1",
                    "COM2",
                    "COM3",
                    "COM4",
                    "COM5",
                    "COM6",
                    "COM7",
                    "COM8",
                    "COM9",
                    "LPT1",
                    "LPT2",
                    "LPT3",
                    "LPT4",
                    "LPT5",
                    "LPT6",
                    "LPT7",
                    "LPT8",
                    "LPT9",
                ]
                if any(part.upper() in reserved_names for part in path_obj.parts):
                    return False

            return True
        except Exception:
            return False

    @wrap_io_errors
    def normalize_path_with_info(self, path: str | Path) -> PathResult:
        """
        Normalize a path and return detailed information.

        This enhanced version of normalize_path returns a PathResult object
        with success status and additional information.

        Args:
            path: Path to normalize

        Returns:
            PathResult with the normalized path and status information
        """
        try:
            path_obj = Path(path)  # Normalize early
            if not path_obj.is_absolute():
                try:
                    path_obj = path_obj.resolve()
                except FileNotFoundError:
                    # When resolution fails (for non-existent paths),
                    # fall back to the original path.
                    pass

            exists_result = self.path_exists(path_obj)
            exists = exists_result.data if exists_result.success else False

            return PathResult(
                success=True,
                path=path_obj,
                is_absolute=path_obj.is_absolute(),
                is_valid=True,
                exists=exists,
                message="Path normalized successfully",
            )
        except Exception as e:
            return PathResult(
                success=False,
                path=Path(path) if isinstance(path, (str, Path)) else Path(),
                is_valid=False,
                error=f"Path normalization failed: {e}",
            )
