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
    """Mixin class for path validation operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

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

            # Check if the path format is valid
            # This doesn't check if the path exists, just if it's valid syntax
            is_valid = self._is_path_syntax_valid(str(path))

            # Check if the path exists (optional info)
            exists = path_obj.exists()

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
            # Try to create a Path object
            path_obj = Path(path_str)

            # Check for invalid characters in the path
            # This varies by platform, but here are some common checks
            if os.name == 'nt':  # Windows
                # Check for reserved characters in Windows
                reserved_chars = '<>:"|?*'
                if any(c in str(path_obj.name) for c in reserved_chars):
                    return False

                # Check for reserved names in Windows
                reserved_names = [
                    'CON', 'PRN', 'AUX', 'NUL',
                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8',
                    'COM9',
                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8',
                    'LPT9'
                ]
                if any(part.upper() in reserved_names for part in path_obj.parts):
                    return False

            # If we're still here, the path syntax is valid
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
            # Implement path normalization directly here instead of calling self.normalize_path
            path_obj = Path(path)
            if not path_obj.is_absolute():
                try:
                    path_obj = path_obj.resolve()
                except FileNotFoundError:
                    # If resolution fails, just use the original path
                    # This prevents test failures when resolving non-existent paths
                    pass

            return PathInfo(
                success=True,
                path=str(path_obj),
                is_absolute=path_obj.is_absolute(),
                is_valid=True,
                exists=path_obj.exists(),
                message="Path normalized successfully",
            )
        except Exception as e:
            return PathInfo(
                success=False,
                path=str(path) if isinstance(path, (str, Path)) else None,
                is_valid=False,
                error=f"Path normalization failed: {str(e)}",
            )