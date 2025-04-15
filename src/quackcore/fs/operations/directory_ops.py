# src/quackcore/fs/operations/directory_ops.py
"""
Directory operations.
"""

from pathlib import Path

from quackcore.errors import (
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
)
from quackcore.fs.results import DirectoryInfoResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class DirectoryOperationsMixin:
    """Directory operations mixin class."""

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the base directory."""
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _list_directory(
        self, path: str | Path, pattern: str | None = None, include_hidden: bool = False
    ) -> DirectoryInfoResult:
        """
        List contents of a directory.

        Args:
            path: Path to list
            pattern: Pattern to match files against
            include_hidden: Whether to include hidden files

        Returns:
            DirectoryInfoResult with directory contents
        """
        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Listing directory {resolved_path}, "
            f"pattern={pattern}, include_hidden={include_hidden}"
        )

        try:
            if not resolved_path.exists():
                logger.error(f"Directory does not exist: {resolved_path}")
                return DirectoryInfoResult(
                    success=False,
                    path=resolved_path,
                    exists=False,
                    error=f"Directory does not exist: {resolved_path}",
                )

            if not resolved_path.is_dir():
                logger.error(f"Path is not a directory: {resolved_path}")
                return DirectoryInfoResult(
                    success=False,
                    path=resolved_path,
                    exists=True,
                    error=f"Path is not a directory: {resolved_path}",
                )

            files = []
            directories = []
            total_size = 0

            for item in resolved_path.iterdir():
                # Skip hidden files if needed
                if not include_hidden and item.name.startswith("."):
                    logger.debug(f"Skipping hidden item: {item}")
                    continue

                # Skip items that don't match the pattern
                if pattern and not item.match(pattern):
                    logger.debug(f"Skipping item not matching pattern: {item}")
                    continue

                if item.is_file():
                    files.append(item)
                    item_size = item.stat().st_size
                    total_size += item_size
                    logger.debug(f"Found file: {item}, size: {item_size}")
                elif item.is_dir():
                    directories.append(item)
                    logger.debug(f"Found directory: {item}")

            logger.info(
                f"Found {len(files)} files and {len(directories)} directories in {resolved_path}"
            )

            return DirectoryInfoResult(
                success=True,
                path=resolved_path,
                exists=True,
                is_empty=(len(files) == 0 and len(directories) == 0),
                files=files,
                directories=directories,
                total_files=len(files),
                total_directories=len(directories),
                total_size=total_size,
                message=(
                    f"Found {len(files)} files and {len(directories)} directories "
                    f"matching '{pattern}'"
                ),
            )
        except (QuackFileNotFoundError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error listing directory {resolved_path}: {str(e)}")
            return DirectoryInfoResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error listing directory {resolved_path}: {str(e)}"
            )
            return DirectoryInfoResult(success=False, path=resolved_path, error=str(e))
