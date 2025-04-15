# src/quackcore/fs/service/utility_operations.py
"""
Utility operations for the FileSystemService.
"""

from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs.api.public import (
    atomic_write,
    compute_checksum,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    find_files_by_content,
    get_disk_usage,
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
)
from quackcore.fs.operations import FileSystemOperations


class UtilityOperationsMixin:
    """Mixin class for utility operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    # --- Advanced and Utility Operations ---

    @wrap_io_errors
    def ensure_directory(self, path: str | Path, exist_ok: bool = True) -> Path:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure exists
            exist_ok: If False, raise an error when directory exists

        Returns:
            Path object for the directory
        """
        return ensure_directory(path, exist_ok)

    @wrap_io_errors
    def get_unique_filename(self, directory: str | Path, filename: str) -> Path:
        """
        Generate a unique filename in the given directory.

        Args:
            directory: Directory path
            filename: Base filename

        Returns:
            Path object for the unique filename
        """
        return get_unique_filename(directory, filename)

    @wrap_io_errors
    def create_temp_directory(
        self, prefix: str = "quackcore_", suffix: str = ""
    ) -> Path:
        """
        Create a temporary directory.

        Args:
            prefix: Directory name prefix
            suffix: Directory name suffix

        Returns:
            Path to the created temporary directory
        """
        return create_temp_directory(prefix, suffix)

    @wrap_io_errors
    def create_temp_file(
        self,
        suffix: str = ".txt",
        prefix: str = "quackcore_",
        directory: str | Path | None = None,
    ) -> Path:
        """
        Create a temporary file.

        Args:
            suffix: File suffix (e.g., ".txt")
            prefix: File prefix
            directory: Directory to create the file in (default: system temp dir)

        Returns:
            Path to the created temporary file
        """
        return create_temp_file(suffix, prefix, directory)

    @wrap_io_errors
    def find_files_by_content(
        self, directory: str | Path, text_pattern: str, recursive: bool = True
    ) -> list[Path]:
        """
        Find files containing the given text pattern.

        Args:
            directory: Directory to search in
            text_pattern: Text pattern to search for
            recursive: Whether to search recursively

        Returns:
            List of paths to files containing the pattern
        """
        return find_files_by_content(directory, text_pattern, recursive)

    @wrap_io_errors
    def get_disk_usage(self, path: str | Path) -> dict[str, int]:
        """
        Get disk usage information for the given path.

        Args:
            path: Path to get disk usage for

        Returns:
            Dictionary with total, used, and free space in bytes
        """
        return get_disk_usage(path)

    def get_file_type(self, path: str | Path) -> str:
        """
        Get the type of a file.

        Args:
            path: Path to the file

        Returns:
            File type string
        """
        return get_file_type(path)

    def get_file_size_str(self, size_bytes: int) -> str:
        """
        Convert file size in bytes to a human-readable string.

        Args:
            size_bytes: File size in bytes

        Returns:
            Human-readable file size (e.g., "2.5 MB")
        """
        return get_file_size_str(size_bytes)

    def get_mime_type(self, path: str | Path) -> str | None:
        """
        Get the MIME type of a file.

        Args:
            path: Path to the file

        Returns:
            MIME type string or None if not determinable
        """
        return get_mime_type(path)

    def is_path_writeable(self, path: str | Path) -> bool:
        """
        Check if a path is writeable.

        Args:
            path: Path to check

        Returns:
            True if the path is writeable
        """
        return is_path_writeable(path)

    def is_file_locked(self, path: str | Path) -> bool:
        """
        Check if a file is locked by another process.

        Args:
            path: Path to the file

        Returns:
            True if the file is locked
        """
        return is_file_locked(path)

    def get_file_timestamp(self, path: str | Path) -> float:
        """
        Get the latest timestamp (modification time) for a file.

        Args:
            path: Path to the file

        Returns:
            Timestamp as float
        """
        return get_file_timestamp(path)

    def compute_checksum(self, path: str | Path, algorithm: str = "sha256") -> str:
        """
        Compute the checksum of a file.

        Args:
            path: Path to the file.
            algorithm: Hash algorithm to use (default: "sha256").

        Returns:
            Hexadecimal string representing the checksum.
        """
        return compute_checksum(path, algorithm)

    def atomic_write(self, path: str | Path, content: str | bytes) -> Path:
        """
        Write content to a file atomically using a temporary file.

        Args:
            path: Destination file path.
            content: Content to write. Can be either string or bytes.

        Returns:
            Path object pointing to the written file.
        """
        return atomic_write(path, content)
