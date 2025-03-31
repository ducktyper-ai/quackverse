# src/quackcore/fs/operations/file_info.py
"""
File information operations.
"""

import mimetypes
from pathlib import Path

from quackcore.errors import QuackIOError, QuackPermissionError
from quackcore.fs.results import FileInfoResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class FileInfoOperationsMixin:
    """File information operations mixin class."""

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the base directory."""
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to get information about

        Returns:
            FileInfoResult with file information
        """
        resolved_path = self.resolve_path(path)
        logger.debug(f"Getting file info for: {resolved_path}")

        try:
            if not resolved_path.exists():
                logger.info(f"Path does not exist: {resolved_path}")
                return FileInfoResult(
                    success=True,
                    path=resolved_path,
                    exists=False,
                    message=f"Path does not exist: {resolved_path}",
                )

            stats = resolved_path.stat()
            mime_type = None

            if resolved_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(resolved_path))
                logger.debug(f"Determined MIME type for {resolved_path}: {mime_type}")

            owner = None
            try:
                import pwd

                owner = pwd.getpwuid(stats.st_uid).pw_name
                logger.debug(f"Determined file owner for {resolved_path}: {owner}")
            except (ImportError, KeyError) as e:
                logger.debug(f"Could not determine owner for {resolved_path}: {str(e)}")
                pass

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
            return FileInfoResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error getting file info for {resolved_path}: {str(e)}"
            )
            return FileInfoResult(success=False, path=resolved_path, error=str(e))
