"""
Advanced and utility operations for FileSystemService.
"""

from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.fs.results import DataResult, FileInfoResult, OperationResult
from quackcore.fs.utils import (
    atomic_write,
    compute_checksum,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    find_files_by_content,
    get_disk_usage,
    get_file_size_str,
    get_file_timestamp,
    get_mime_type,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
)
from quackcore.logging import get_logger

from .protocols import LoggerProtocol, OperationsProtocol

# Create a local logger for this module
logger = get_logger(__name__)


class UtilityOperationsMixin:
    """Mixin for advanced and utility operations."""

    # This tells type checkers that this class requires these properties
    logger: LoggerProtocol  # Will be set by the main class
    operations: OperationsProtocol  # Will be set by the main class

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

        Raises:
            QuackFileNotFoundError: If the file doesn't exist.
            QuackIOError: For any IO-related issue during checksum computation.
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

        Raises:
            QuackPermissionError: If writing is not permitted.
            QuackIOError: For any IO-related issue during write.
        """
        return atomic_write(path, content)


# Module-level utility functions for backward compatibility
def create_directory(path: str | Path, exist_ok: bool = True) -> OperationResult:
    """
    Create a directory if it doesn't exist.

    Args:
        path: Directory path to create.
        exist_ok: If False, raise an error when the directory exists.

    Returns:
        An OperationResult indicating whether the directory
        was created or already exists.
    """
    try:
        directory = Path(path)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=exist_ok)
        return OperationResult(
            success=True, path=str(directory), message="Directory exists or was created"
        )
    except Exception as e:
        return OperationResult(success=False, error=str(e), path=str(path))


def read_yaml(path: str | Path) -> DataResult[dict]:
    """
    Read a YAML file and parse its contents using the FileSystemService.

    Args:
        path: Path to the YAML file.

    Returns:
        A DataResult containing the parsed YAML data.
    """
    from .base import FileSystemService
    return FileSystemService().read_yaml(path)


def get_file_info(path: str | Path) -> FileInfoResult:
    """
    Get information about a file or directory.

    Args:
        path: Path to get information about

    Returns:
        FileInfoResult with file information
    """
    p = Path(path)
    try:
        exists = p.exists()
        is_file = exists and p.is_file()
        is_dir = exists and p.is_dir()

        size = None
        modified = None
        created = None

        if exists:
            try:
                if is_file:
                    size = p.stat().st_size
                modified = p.stat().st_mtime
                created = p.stat().st_ctime
            except OSError:
                pass

        return FileInfoResult(
            success=True,
            path=str(p),  # Convert to string to match the expected interface
            exists=exists,
            is_file=is_file,
            is_dir=is_dir,
            size=size,
            modified=modified,
            created=created,
            message=f"Got file info for {p}",
        )
    except Exception as e:
        return FileInfoResult(
            success=False,
            path=str(p),  # Convert to string to match the expected interface
            error=str(e),
        )