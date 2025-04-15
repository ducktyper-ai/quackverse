# src/quackcore/fs/_operations/file_info.py
"""
File information _operations.

This module provides internal _operations for retrieving metadata and information
about files and paths in the filesystem. These _operations are used by the public
API but are not meant to be consumed directly.
"""

import mimetypes
from pathlib import Path

from quackcore.errors import QuackIOError, QuackPermissionError
from quackcore.fs.results import FileInfoResult, PathResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class FileInfoOperationsMixin:
    """
    File information _operations mixin class.

    Provides internal methods for retrieving metadata about files and paths,
    including existence checks, permissions, size, and MIME types.
    """

    def _resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve, can be string or Path object

        Returns:
            Path: Resolved Path object

        Note:
            Internal helper method implemented in the main class.
            Not meant for external consumption.
        """
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _path_exists(self, path: str | Path) -> PathResult:
        """
        Check if a path exists.

        Args:
            path: Path to check

        Returns:
            PathResult with existence information

        Note:
            Internal helper method not meant for external consumption.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(f"Checking if path exists: {resolved_path}")

        try:
            exists = resolved_path.exists()
            logger.debug(f"Path {resolved_path} exists: {exists}")

            return PathResult(
                success=True,
                path=resolved_path,
                exists=exists,
                is_valid=True,
                is_absolute=resolved_path.is_absolute(),
                message=f"Path {'exists' if exists else 'does not exist'}: {resolved_path}",
            )
        except Exception as e:
            logger.error(f"Error checking if path exists for {resolved_path}: {str(e)}")
            return PathResult(
                success=False,
                path=resolved_path,
                exists=False,
                is_valid=False,
                is_absolute=resolved_path.is_absolute(),
                error=f"Error checking path: {str(e)}",
            )

    def _get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get comprehensive information about a file or directory.

        This method retrieves metadata including basic properties,
        timestamps, ownership, permissions, and MIME type.

        Args:
            path: Path to get information about

        Returns:
            FileInfoResult with detailed file information

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(f"Getting file info for: {resolved_path}")

        try:
            # Use our _path_exists method to check existence
            exists_result = self._path_exists(resolved_path)
            if not exists_result.success:
                logger.error(f"Error checking path existence: {exists_result.error}")
                return FileInfoResult(
                    success=False,
                    path=resolved_path,
                    exists=False,
                    error=f"Error checking path existence: {exists_result.error}",
                )

            if not exists_result.exists:
                logger.info(f"Path does not exist: {resolved_path}")
                return FileInfoResult(
                    success=True,
                    path=resolved_path,
                    exists=False,
                    message=f"Path does not exist: {resolved_path}",
                )

            # Gather file stats
            stats = resolved_path.stat()
            mime_type = None

            # Get MIME type for files
            if resolved_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(resolved_path))
                logger.debug(f"Determined MIME type for {resolved_path}: {mime_type}")

            # Try to get owner information
            owner = None
            try:
                import pwd

                owner = pwd.getpwuid(stats.st_uid).pw_name
                logger.debug(f"Determined file owner for {resolved_path}: {owner}")
            except (ImportError, KeyError) as e:
                logger.debug(f"Could not determine owner for {resolved_path}: {str(e)}")
                # Continue without owner info

            logger.info(f"Successfully retrieved file info for {resolved_path}")
            return FileInfoResult(
                success=True,
                path=resolved_path,
                exists=True,
                is_file=resolved_path.is_file(),
                is_dir=resolved_path.is_dir(),
                size=stats.st_size,
                modified=stats.st_mtime,
                created=stats.st_ctime,
                owner=owner,
                permissions=stats.st_mode,
                mime_type=mime_type,
                message=f"Got file info for {resolved_path}",
            )
        except (QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error getting file info for {resolved_path}: {str(e)}")
            return FileInfoResult(
                success=False, path=resolved_path, exists=False, error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Unexpected error getting file info for {resolved_path}: {str(e)}"
            )
            return FileInfoResult(
                success=False, path=resolved_path, exists=False, error=str(e)
            )
