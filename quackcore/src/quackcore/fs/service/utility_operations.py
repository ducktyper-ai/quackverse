# quackcore/src/quackcore/fs/service/utility_operations.py
"""
Utility _operations for the FileSystemService.
"""

from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs import DataResult, OperationResult, WriteResult
from quackcore.fs._operations import FileSystemOperations
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


class UtilityOperationsMixin:
    """Mixin class for utility _operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have _operations
    operations: FileSystemOperations

    # This method is added in the base class
    def _normalize_input_path(self,
                              path: str | Path | DataResult | OperationResult) -> Path:
        """Normalize an input path to a Path object."""
        raise NotImplementedError("This method should be overridden")

    # --- Advanced and Utility Operations ---

    @wrap_io_errors
    def ensure_directory(
            self, path: str | Path | DataResult | OperationResult, exist_ok: bool = True
    ) -> OperationResult:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure exists (string, Path, DataResult, or OperationResult)
            exist_ok: If False, raise an error when directory exists

        Returns:
            OperationResult with operation status
        """
        normalized_path = self._normalize_input_path(path)
        return ensure_directory(normalized_path, exist_ok)

    @wrap_io_errors
    def get_unique_filename(
            self, directory: str | Path | DataResult | OperationResult, filename: str
    ) -> DataResult[str]:
        """
        Generate a unique filename in the given directory.

        Args:
            directory: Directory path (string, Path, DataResult, or OperationResult)
            filename: Base filename

        Returns:
            Path object for the unique filename
        """
        normalized_directory = self._normalize_input_path(directory)
        return get_unique_filename(normalized_directory, filename)

    @wrap_io_errors
    def create_temp_directory(
            self, prefix: str = "quackcore_", suffix: str = ""
    ) -> DataResult[str]:
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
            directory: str | Path | DataResult | OperationResult | None = None,
    ) -> DataResult[str]:
        """
        Create a temporary file.

        Args:
            suffix: File suffix (e.g., ".txt")
            prefix: File prefix
            directory: Directory to create the file in (string, Path, DataResult, or OperationResult, default: system temp dir)

        Returns:
            Path to the created temporary file
        """
        if directory is not None:
            normalized_directory = self._normalize_input_path(directory)
            return create_temp_file(suffix, prefix, normalized_directory)
        else:
            return create_temp_file(suffix, prefix, None)

    @wrap_io_errors
    def find_files_by_content(
            self, directory: str | Path | DataResult | OperationResult,
            text_pattern: str, recursive: bool = True
    ) -> DataResult[list[str]]:
        """
        Find files containing the given text pattern.

        Args:
            directory: Directory to search in (string, Path, DataResult, or OperationResult)
            text_pattern: Text pattern to search for
            recursive: Whether to search recursively

        Returns:
            List of paths to files containing the pattern
        """
        normalized_directory = self._normalize_input_path(directory)
        return find_files_by_content(normalized_directory, text_pattern, recursive)

    @wrap_io_errors
    def get_disk_usage(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[dict[str, int]]:
        """
        Get disk usage information for the given path.

        Args:
            path: Path to get disk usage for (string, Path, DataResult, or OperationResult)

        Returns:
            Dictionary with total, used, and free space in bytes
        """
        normalized_path = self._normalize_input_path(path)
        return get_disk_usage(normalized_path)

    def get_file_type(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str]:
        """
        Get the type of a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)

        Returns:
            File type string
        """
        normalized_path = self._normalize_input_path(path)
        return get_file_type(normalized_path)

    def get_file_size_str(self, size_bytes: int) -> DataResult[str]:
        """
        Convert file size in bytes to a human-readable string.

        Args:
            size_bytes: File size in bytes

        Returns:
            Human-readable file size (e.g., "2.5 MB")
        """
        return get_file_size_str(size_bytes)

    def get_mime_type(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[str] | None:
        """
        Get the MIME type of a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)

        Returns:
            MIME type string or None if not determinable
        """
        normalized_path = self._normalize_input_path(path)
        return get_mime_type(normalized_path)

    def is_path_writeable(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[bool]:
        """
        Check if a path is writeable.

        Args:
            path: Path to check (string, Path, DataResult, or OperationResult)

        Returns:
            True if the path is writeable
        """
        normalized_path = self._normalize_input_path(path)
        return is_path_writeable(normalized_path)

    def is_file_locked(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[bool]:
        """
        Check if a file is locked by another process.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)

        Returns:
            True if the file is locked
        """
        normalized_path = self._normalize_input_path(path)
        return is_file_locked(normalized_path)

    def get_file_timestamp(self, path: str | Path | DataResult | OperationResult) -> \
    DataResult[float]:
        """
        Get the latest timestamp (modification time) for a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)

        Returns:
            Timestamp as float
        """
        normalized_path = self._normalize_input_path(path)
        return get_file_timestamp(normalized_path)

    def compute_checksum(
            self, path: str | Path | DataResult | OperationResult,
            algorithm: str = "sha256"
    ) -> DataResult[str]:
        """
        Compute the checksum of a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)
            algorithm: Hash algorithm to use (default: "sha256").

        Returns:
            Hexadecimal string representing the checksum.
        """
        normalized_path = self._normalize_input_path(path)
        return compute_checksum(normalized_path, algorithm)

    def atomic_write(self, path: str | Path | DataResult | OperationResult,
                     content: str | bytes) -> WriteResult:
        """
        Write content to a file atomically using a temporary file.

        Args:
            path: Destination file path (string, Path, DataResult, or OperationResult)
            content: Content to write. Can be either string or bytes.

        Returns:
            Path object pointing to the written file.
        """
        normalized_path = self._normalize_input_path(path)
        return atomic_write(normalized_path, content)
