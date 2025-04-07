# src/quackcore/fs/deprecated_service.py
"""
FileSystemService provides a high-level interface for filesystem operations.

This service layer abstracts underlying filesystem operations and provides
a clean, consistent API for all file operations in QuackCore.
"""

from pathlib import Path
from typing import TypeVar

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.results import (
    DataResult,
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    ReadResult,
    WriteResult,
)
from quackcore.fs.utils import (
    atomic_write,
    compute_checksum,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    expand_user_vars,
    find_files_by_content,
    get_disk_usage,
    get_extension,
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
    is_same_file,
    is_subdirectory,
    join_path,
    normalize_path,
    split_path,
)

T = TypeVar("T")  # Generic type for flexible typing

from quackcore.logging import LOG_LEVELS, LogLevel, get_logger


class FileSystemService:
    """
    High-level service for filesystem operations.

    This service provides a clean, consistent API for all file operations
    in QuackCore, with proper error handling and result objects.
    """

    def __init__(
        self,
        base_dir: str | Path | None = None,
        log_level: int = LOG_LEVELS[LogLevel.INFO],
    ) -> None:
        """
        Initialize the filesystem service.

        Args:
            base_dir: Optional base directory for relative paths
                        (default: current working directory)
            log_level: Logging level for the service
        """
        self.logger = get_logger(__name__)
        self.logger.setLevel(log_level)

        # Initialize operations with base directory
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.operations = FileSystemOperations(self.base_dir)

    # --- File Reading Operations ---

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> ReadResult[str]:
        """
        Read text from a file.

        Args:
            path: Path to the file
            encoding: Text encoding

        Returns:
            ReadResult with the file content as text
        """
        return self.operations.read_text(path, encoding)

    def read_binary(self, path: str | Path) -> ReadResult[bytes]:
        """
        Read binary data from a file.

        Args:
            path: Path to the file

        Returns:
            ReadResult with the file content as bytes
        """
        return self.operations.read_binary(path)

    def read_lines(
        self, path: str | Path, encoding: str = "utf-8"
    ) -> ReadResult[list[str]]:
        """
        Read lines from a text file.

        Args:
            path: Path to the file
            encoding: Text encoding

        Returns:
            ReadResult with the file content as a list of lines
        """
        result = self.operations.read_text(path, encoding)
        if result.success:
            lines = result.content.splitlines()
            return ReadResult(
                success=True,
                path=result.path,
                content=lines,
                encoding=encoding,
                message=f"Successfully read {len(lines)} lines",
            )
        return ReadResult(
            success=False,
            path=result.path,
            content=[],
            encoding=encoding,
            error=result.error,
        )

    # --- File Writing Operations ---

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = True,
    ) -> WriteResult:
        """
        Write text to a file.

        Args:
            path: Path to the file
            content: Content to write
            encoding: Text encoding
            atomic: Whether to use atomic writing

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_text(path, content, encoding, atomic)

    def write_binary(
        self,
        path: str | Path,
        content: bytes,
        atomic: bool = True,
    ) -> WriteResult:
        """
        Write binary data to a file.

        Args:
            path: Path to the file
            content: Content to write
            atomic: Whether to use atomic writing

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_binary(path, content, atomic)

    def write_lines(
        self,
        path: str | Path,
        lines: list[str],
        encoding: str = "utf-8",
        atomic: bool = True,
        line_ending: str = "\n",
    ) -> WriteResult:
        """Write lines to a text file.

        This method explicitly joins the lines using the specified line ending.
        When a non-default line ending is provided, the content is encoded and written
        in binary mode to prevent any unwanted normalization.

        Args:
            path: Path to the file.
            lines: Lines to write.
            encoding: Text encoding to use.
            atomic: Whether to write the file atomically.
            line_ending: The line ending to use.

        Returns:
            WriteResult indicating the outcome of the write operation.
        """
        content = line_ending.join(lines)

        # For non-default line endings, encode and write in binary mode
        if line_ending != "\n":
            bytes_content = content.encode(encoding)
            return self.operations.write_binary(path, bytes_content, atomic)
        else:
            return self.operations.write_text(path, content, encoding, atomic)

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
        return self.operations.find_files(path, pattern, recursive, include_hidden)

    # --- Structured Data Operations ---

    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file

        Returns:
            DataResult with parsed YAML data
        """
        return self.operations.read_yaml(path)

    def write_yaml(
        self,
        path: str | Path,
        data: dict,
        atomic: bool = True,
    ) -> WriteResult:
        """
        Write data to a YAML file.

        Args:
            path: Path to YAML file
            data: Data to write
            atomic: Whether to use atomic writing

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_yaml(path, data, atomic)

    def read_json(self, path: str | Path) -> DataResult[dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file

        Returns:
            DataResult with parsed JSON data
        """
        return self.operations.read_json(path)

    def write_json(
        self,
        path: str | Path,
        data: dict,
        atomic: bool = True,
        indent: int = 2,
    ) -> WriteResult:
        """
        Write data to a JSON file.

        Args:
            path: Path to JSON file
            data: Data to write
            atomic: Whether to use atomic writing
            indent: Number of spaces to indent

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_json(path, data, atomic, indent)

    # --- Advanced and Utility Operations ---
    # For the following utility methods, we directly use the utility functions
    # instead of delegating to the operations instance.

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

    # --- Path Manipulation and Introspection Utilities ---

    @wrap_io_errors
    def join_path(self, *parts: str | Path) -> Path:
        """
        Join path components.

        Args:
            *parts: Path parts to join

        Returns:
            Joined Path object
        """
        return join_path(*parts)

    @wrap_io_errors
    def split_path(self, path: str | Path) -> list[str]:
        """
        Split a path into its components.

        Args:
            path: Path to split

        Returns:
            List of path components
        """
        return split_path(path)

    @wrap_io_errors
    def normalize_path(self, path: str | Path) -> Path:
        """
        Normalize a path for cross-platform compatibility.

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        return normalize_path(path)

    def expand_user_vars(self, path: str | Path) -> Path:
        """
        Expand user variables and environment variables in a path.

        Args:
            path: Path with variables

        Returns:
            Expanded Path object
        """
        return expand_user_vars(path)

    def is_same_file(self, path1: str | Path, path2: str | Path) -> bool:
        """
        Check if two paths refer to the same file.

        Args:
            path1: First path
            path2: Second path

        Returns:
            True if paths refer to the same file
        """
        return is_same_file(path1, path2)

    def is_subdirectory(self, child: str | Path, parent: str | Path) -> bool:
        """
        Check if a path is a subdirectory of another path.

        Args:
            child: Potential child path
            parent: Potential parent path

        Returns:
            True if child is a subdirectory of parent
        """
        return is_subdirectory(child, parent)

    def get_extension(self, path: str | Path) -> str:
        """
        Get the file extension from a path.

        Args:
            path: File path

        Returns:
            File extension without the dot
        """
        return get_extension(path)

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


# --- Module-Level Utility Functions ---
# These functions are exposed at the module level so that external code or tests
# (which patch these names) can find and override them as needed.


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
