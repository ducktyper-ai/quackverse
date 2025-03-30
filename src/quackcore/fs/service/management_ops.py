"""
File management operations for FileSystemService.
"""

from pathlib import Path

from quackcore.fs.results import (
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    WriteResult,
)
from quackcore.logging import get_logger

from .protocols import LoggerProtocol, OperationsProtocol

# Create a local logger for this module
logger = get_logger(__name__)


class ManagementOperationsMixin:
    """Mixin for file management operations."""

    # This tells type checkers that this class requires these properties
    logger: LoggerProtocol  # Will be set by the main class
    operations: OperationsProtocol  # Will be set by the main class

    # --- File Management Operations ---

    def copy(
        self, src: str | Path, dst: str | Path, overwrite: bool = False
    ) -> WriteResult:
        """
        Copy a file or directory.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status
        """
        self.logger.debug(f"Copying from {src} to {dst}")
        return self.operations.copy(src, dst, overwrite)

    def move(
        self, src: str | Path, dst: str | Path, overwrite: bool = False
    ) -> WriteResult:
        """
        Move a file or directory.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status
        """
        self.logger.debug(f"Moving from {src} to {dst}")
        return self.operations.move(src, dst, overwrite)

    def delete(self, path: str | Path, missing_ok: bool = True) -> OperationResult:
        """
        Delete a file or directory.

        Args:
            path: Path to delete
            missing_ok: Whether to ignore if the path doesn't exist

        Returns:
            OperationResult with operation status
        """
        self.logger.debug(f"Deleting {path}")
        return self.operations.delete(path, missing_ok)

    def create_directory(
        self, path: str | Path, exist_ok: bool = True
    ) -> OperationResult:
        """
        Create a directory.

        Args:
            path: Path to create
            exist_ok: Whether to ignore if the directory already exists

        Returns:
            OperationResult with operation status
        """
        self.logger.debug(f"Creating directory {path}")
        return self.operations.create_directory(path, exist_ok)

    # --- Information and Listing Operations ---

    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to get information about

        Returns:
            FileInfoResult with file information
        """
        self.logger.debug(f"Getting file info for {path}")
        return self.operations.get_file_info(path)

    def list_directory(
        self,
        path: str | Path,
        pattern: str | None = None,
        include_hidden: bool = False,
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
        self.logger.debug(f"Listing directory {path}")
        return self.operations.list_directory(path, pattern, include_hidden)

    def find_files(
        self,
        path: str | Path,
        pattern: str,
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> FindResult:
        """
        Find files matching a pattern.

        Args:
            path: Directory to search
            pattern: Pattern to match files against
            recursive: Whether to search recursively
            include_hidden: Whether to include hidden files

        Returns:
            FindResult with matching files
        """
        self.logger.debug(f"Finding files in {path} with pattern {pattern}")
        return self.operations.find_files(path, pattern, recursive, include_hidden)