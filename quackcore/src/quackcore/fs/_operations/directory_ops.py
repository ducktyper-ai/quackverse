# quackcore/src/quackcore/fs/_operations/directory_ops.py
"""
Directory _operations.

This module provides internal _operations for working with directories, including
listing contents, getting directory information, and filtering by patterns.
"""

from pathlib import Path

from quackcore.errors import (
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
)
from quackcore.fs.results import DataResult, DirectoryInfoResult, OperationResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class DirectoryOperationsMixin:
    """
    Directory _operations mixin class.

    Provides internal methods for working with directories, listing their contents,
    and filtering by patterns.
    """

    def _resolve_path(self, path: str | Path | DataResult | OperationResult) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve (str, Path, DataResult, or OperationResult)

        Returns:
            Path: Resolved Path object

        Note:
            This method is implemented in the main class.
            It's defined here for type checking.
            Internal helper method not meant for external consumption.
        """
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _list_directory(
        self, path: str | Path | DataResult | OperationResult, pattern: str | None = None, include_hidden: bool = False
    ) -> DirectoryInfoResult:
        """
        List contents of a directory with optional pattern filtering.

        This method scans a directory and returns information about its contents,
        including files and subdirectories. Results can be filtered using
        a glob pattern and hidden files can be optionally included.

        Args:
            path: Path to the directory to list (str, Path, DataResult, or OperationResult)
            pattern: Optional glob pattern to match files and directories against
                     (e.g., "*.py", "data*", etc.)
            include_hidden: Whether to include hidden files/directories
                           (those starting with ".")

        Returns:
            DirectoryInfoResult with directory contents information

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Listing directory {resolved_path}, "
            f"pattern={pattern}, include_hidden={include_hidden}"
        )

        try:
            # Check if the path exists and is a directory
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
                    try:
                        item_size = item.stat().st_size
                        total_size += item_size
                        files.append(item)
                        logger.debug(f"Found file: {item}, size: {item_size}")
                    except (PermissionError, OSError) as e:
                        # Skip files we can't access but log the issue
                        logger.warning(f"Skipping inaccessible file {item}: {str(e)}")
                elif item.is_dir():
                    directories.append(item)
                    logger.debug(f"Found directory: {item}")

            logger.info(
                f"Found {len(files)} files and {len(directories)} directories in {resolved_path}"
            )

            # Ensure pattern is displayed correctly in message
            pattern_msg = f"matching '{pattern}'" if pattern else ""

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
                    f"{pattern_msg}".strip()
                ),
            )
        except (QuackFileNotFoundError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error listing directory {resolved_path}: {str(e)}")
            return DirectoryInfoResult(
                success=False, path=resolved_path, exists=False, error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Unexpected error listing directory {resolved_path}: {str(e)}"
            )
            return DirectoryInfoResult(
                success=False, path=resolved_path, exists=False, error=str(e)
            )
