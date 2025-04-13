# src/quackcore/fs/service/path_validation.py
"""
Path validation utilities for the FileSystemService.

These utilities extend the FileSystemService with methods to validate
and inspect paths, primarily used for configuration validation.
"""

import os
from pathlib import Path

from pydantic import BaseModel

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.logging import get_logger

logger = get_logger(__name__)


class PathInfo(BaseModel):
    """Result of a path validation operation."""

    success: bool = True
    path: str | None = None
    is_absolute: bool = False
    is_valid: bool = False
    exists: bool = False
    message: str | None = None
    error: str | None = None


class PathValidationMixin:
    """
    Mixin class for path validation operations in the FileSystemService.

    This mixin "dogfoods" our existing implementation from FileInfoOperationsMixin
    (or any compatible implementation exposed via `self.operations`) to check if a path exists.
    """

    # This ensures the mixin will only be used with classes that have an 'operations' attribute.
    operations: FileSystemOperations

    def path_exists(self, path: str | Path) -> bool:
        """
        Check if a path exists in the filesystem by leveraging the existing
        FileInfoOperationsMixin implementation via self.operations.

        Args:
            path: Path to check for existence

        Returns:
            bool: True if the path exists, False otherwise
        """
        try:
            # Delegate to the file_info's path_exists implementation
            return self.operations.path_exists(path)
        except Exception as exc:
            logger.error(f"Error checking if path exists using operations: {exc}")
            # Fallback: use the standard pathlib.Path.exists() check
            try:
                result = Path(path).exists()
                logger.debug(f"Fallback check for {path} returned: {result}")
                return result
            except Exception as fallback_exc:
                logger.error(f"Fallback direct check failed for {path}: {fallback_exc}")
                return False

    def get_path_info(self, path: str | Path) -> PathInfo:
        """
        Get information about a path's validity and format.

        This method checks whether a path is valid and provides information
        without requiring the path to exist.

        Args:
            path: Path to check

        Returns:
            PathInfo object with validation results
        """
        try:
            path_obj = Path(path)
            is_absolute = path_obj.is_absolute()

            # Check if the path syntax is valid without requiring existence
            is_valid = self._is_path_syntax_valid(str(path))

            # Check for existence (optional info)
            exists = self.path_exists(path_obj)

            return PathInfo(
                success=True,
                path=str(path_obj),
                is_absolute=is_absolute,
                is_valid=is_valid,
                exists=exists,
                message="Path validation successful",
            )
        except Exception as e:
            return PathInfo(
                success=False,
                path=str(path) if isinstance(path, (str, Path)) else None,
                is_valid=False,
                error=f"Path validation failed: {str(e)}",
            )

    def is_valid_path(self, path: str | Path) -> bool:
        """
        Check if a path has valid syntax.

        This method checks only the syntax validity of a path,
        not whether it exists or is accessible.

        Args:
            path: Path to check

        Returns:
            True if the path has valid syntax
        """
        return self._is_path_syntax_valid(str(path))

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
    def normalize_path_with_info(self, path: str | Path) -> PathInfo:
        """
        Normalize a path and return detailed information.

        This enhanced version of normalize_path returns a PathInfo object
        with success status and additional information.

        Args:
            path: Path to normalize

        Returns:
            PathInfo with the normalized path and status information
        """
        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                try:
                    path_obj = path_obj.resolve()
                except FileNotFoundError:
                    # When resolution fails (for non-existent paths),
                    # fall back to the original path.
                    pass

            exists = self.path_exists(path_obj)

            return PathInfo(
                success=True,
                path=str(path_obj),
                is_absolute=path_obj.is_absolute(),
                is_valid=True,
                exists=exists,
                message="Path normalized successfully",
            )
        except Exception as e:
            return PathInfo(
                success=False,
                path=str(path) if isinstance(path, (str, Path)) else None,
                is_valid=False,
                error=f"Path normalization failed: {e}",
            )
