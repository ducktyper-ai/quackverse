# src/quackcore/fs/operations.py
"""
Core filesystem operations implementation.

This module provides the implementation of filesystem operations
with proper error handling and consistent return values.
"""

import json
import logging
import mimetypes
from pathlib import Path
from typing import TypeVar

import yaml

from quackcore.errors import (
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackFormatError,
    QuackIOError,
    QuackPermissionError,
    QuackValidationError,
)
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
    ensure_directory,
    safe_copy,
    safe_delete,
    safe_move,
)

T = TypeVar("T")  # Generic type for flexible typing
logger = logging.getLogger(__name__)


class FileSystemOperations:
    """Core implementation of filesystem operations."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """
        Initialize filesystem operations.

        Args:
            base_dir: Optional base directory for relative paths
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        mimetypes.init()

    def resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve

        Returns:
            Resolved Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.base_dir / path_obj

    # -------------------------------
    # Reading operations
    # -------------------------------
    def read_text(self, path: str | Path, encoding: str = "utf-8") -> ReadResult[str]:
        """
        Read text from a file.

        Args:
            path: Path to the file
            encoding: Text encoding

        Returns:
            ReadResult with the file content as text
        """
        resolved_path = self.resolve_path(path)
        try:
            with open(resolved_path, encoding=encoding) as f:
                content = f.read()
            return ReadResult(
                success=True,
                path=resolved_path,
                content=content,
                encoding=encoding,
                message=f"Successfully read {len(content)} characters",
            )
        except FileNotFoundError as e:
            logger.error(f"File not found: {resolved_path}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content="",
                encoding=encoding,
                error=f"File not found: {e}",
            )
        except PermissionError as e:
            logger.error(f"Permission denied for file: {resolved_path}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content="",
                encoding=encoding,
                error=f"Permission denied: {e}",
            )
        except Exception as e:
            logger.error(f"Error reading file {resolved_path}: {str(e)}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content="",
                encoding=encoding,
                error=str(e),
            )

    def read_binary(self, path: str | Path) -> ReadResult[bytes]:
        """
        Read binary data from a file.

        Args:
            path: Path to the file

        Returns:
            ReadResult with the file content as bytes
        """
        resolved_path = self.resolve_path(path)
        try:
            with open(resolved_path, "rb") as f:
                content = f.read()
            return ReadResult(
                success=True,
                path=resolved_path,
                content=content,
                message=f"Successfully read {len(content)} bytes",
            )
        except FileNotFoundError as e:
            logger.error(f"File not found: {resolved_path}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content=b"",
                error=f"File not found: {e}",
            )
        except PermissionError as e:
            logger.error(f"Permission denied for file: {resolved_path}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content=b"",
                error=f"Permission denied: {e}",
            )
        except Exception as e:
            logger.error(f"Error reading binary file {resolved_path}: {str(e)}")
            return ReadResult(
                success=False,
                path=resolved_path,
                content=b"",
                error=str(e),
            )

    # -------------------------------
    # Writing operations
    # -------------------------------
    # Fixed write_text method for FileSystemOperations

    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = True,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write text to a file.

        Args:
            path: Path to the file
            content: Text content to write
            encoding: Text encoding
            atomic: Whether to use atomic writing
            calculate_checksum: Whether to calculate a checksum

        Returns:
            WriteResult with operation status
        """
        resolved_path = self.resolve_path(path)
        try:
            ensure_directory(resolved_path.parent)

            # For UTF-16, we need to ensure a BOM is written
            if encoding.lower().startswith("utf-16"):
                # Convert to bytes first with proper BOM
                if encoding.lower() == "utf-16":
                    # Default to UTF-16-LE with BOM on most platforms
                    bytes_content = content.encode("utf-16")
                elif encoding.lower() == "utf-16-le":
                    # Explicitly use little-endian with BOM
                    bytes_content = content.encode("utf-16-le")
                elif encoding.lower() == "utf-16-be":
                    # Explicitly use big-endian with BOM
                    bytes_content = content.encode("utf-16-be")
                else:
                    bytes_content = content.encode(encoding)

                if atomic:
                    atomic_write(resolved_path, bytes_content)
                else:
                    with open(resolved_path, "wb") as f:
                        f.write(bytes_content)
            else:
                # For other encodings, use text mode
                if atomic:
                    atomic_write(resolved_path, content)
                else:
                    with open(resolved_path, "w", encoding=encoding) as f:
                        f.write(content)

            bytes_written = len(content.encode(encoding))
            checksum = compute_checksum(resolved_path) if calculate_checksum else None
            return WriteResult(
                success=True,
                path=resolved_path,
                bytes_written=bytes_written,
                checksum=checksum,
                message=f"Successfully wrote {bytes_written} bytes",
            )
        except (QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error writing to file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error writing to file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))

    def write_binary(
        self,
        path: str | Path,
        content: bytes,
        atomic: bool = True,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write binary data to a file.

        Args:
            path: Path to the file
            content: Binary content to write
            atomic: Whether to use atomic writing
            calculate_checksum: Whether to calculate a checksum

        Returns:
            WriteResult with operation status
        """
        resolved_path = self.resolve_path(path)
        try:
            ensure_directory(resolved_path.parent)
            if atomic:
                atomic_write(resolved_path, content)
            else:
                with open(resolved_path, "wb") as f:
                    f.write(content)
            checksum = compute_checksum(resolved_path) if calculate_checksum else None
            return WriteResult(
                success=True,
                path=resolved_path,
                bytes_written=len(content),
                checksum=checksum,
                message=f"Successfully wrote {len(content)} bytes",
            )
        except (QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error writing binary to file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing binary to file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))

    # -------------------------------
    # Copy and move
    # -------------------------------
    def copy(
        self,
        src: str | Path,
        dst: str | Path,
        overwrite: bool = False,
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
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        try:
            copied_path = safe_copy(src_path, dst_path, overwrite=overwrite)
            bytes_copied = copied_path.stat().st_size if copied_path.is_file() else 0
            return WriteResult(
                success=True,
                path=dst_path,
                original_path=src_path,
                bytes_written=bytes_copied,
                message=f"Successfully copied {src_path} to {dst_path}",
            )
        except (
            QuackFileNotFoundError,
            QuackFileExistsError,
            QuackPermissionError,
            QuackIOError,
        ) as e:
            logger.error(f"Error copying {src_path} to {dst_path}: {str(e)}")
            return WriteResult(
                success=False,
                path=dst_path,
                original_path=src_path,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error copying {src_path} to {dst_path}: {str(e)}")
            return WriteResult(
                success=False,
                path=dst_path,
                original_path=src_path,
                error=str(e),
            )

    def move(
        self,
        src: str | Path,
        dst: str | Path,
        overwrite: bool = False,
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
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        try:
            bytes_moved = src_path.stat().st_size if src_path.is_file() else 0
            moved_path = safe_move(src_path, dst_path, overwrite=overwrite)
            return WriteResult(
                success=True,
                path=moved_path,
                original_path=src_path,
                bytes_written=bytes_moved,
                message=f"Successfully moved {src_path} to {moved_path}",
            )
        except (
            QuackFileNotFoundError,
            QuackFileExistsError,
            QuackPermissionError,
            QuackIOError,
        ) as e:
            logger.error(f"Error moving {src_path} to {dst_path}: {str(e)}")
            return WriteResult(
                success=False,
                path=dst_path,
                original_path=src_path,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error moving {src_path} to {dst_path}: {str(e)}")
            return WriteResult(
                success=False,
                path=dst_path,
                original_path=src_path,
                error=str(e),
            )

    def delete(self, path: str | Path, missing_ok: bool = True) -> OperationResult:
        """
        Delete a file or directory.

        Args:
            path: Path to delete
            missing_ok: Whether to ignore if the path doesn't exist

        Returns:
            OperationResult with operation status
        """
        resolved_path = self.resolve_path(path)
        try:
            result = safe_delete(resolved_path, missing_ok=missing_ok)
            if not result and not missing_ok:
                return OperationResult(
                    success=False,
                    path=resolved_path,
                    error=f"Path not found: {resolved_path}",
                )
            return OperationResult(
                success=True,
                path=resolved_path,
                message=f"Successfully deleted {resolved_path}",
            )
        except (QuackFileNotFoundError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error deleting {resolved_path}: {str(e)}")
            return OperationResult(
                success=False,
                path=resolved_path,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error deleting {resolved_path}: {str(e)}")
            return OperationResult(
                success=False,
                path=resolved_path,
                error=str(e),
            )

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
        resolved_path = self.resolve_path(path)
        try:
            dir_path = ensure_directory(resolved_path, exist_ok=exist_ok)
            return OperationResult(
                success=True,
                path=dir_path,
                message=f"Successfully created directory {dir_path}",
            )
        except (QuackFileExistsError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error creating directory {resolved_path}: {str(e)}")
            return OperationResult(
                success=False,
                path=resolved_path,
                error=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error creating directory {resolved_path}: {str(e)}"
            )
            return OperationResult(
                success=False,
                path=resolved_path,
                error=str(e),
            )

    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to get information about

        Returns:
            FileInfoResult with file information
        """
        resolved_path = self.resolve_path(path)
        try:
            if not resolved_path.exists():
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
            owner = None
            try:
                import pwd

                owner = pwd.getpwuid(stats.st_uid).pw_name
            except (ImportError, KeyError):
                pass
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

    def list_directory(
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
        resolved_path = self.resolve_path(path)
        try:
            if not resolved_path.exists():
                return DirectoryInfoResult(
                    success=False,
                    path=resolved_path,
                    exists=False,
                    error=f"Directory does not exist: {resolved_path}",
                )
            if not resolved_path.is_dir():
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
                if not include_hidden and item.name.startswith("."):
                    continue
                if pattern and not item.match(pattern):
                    continue
                if item.is_file():
                    files.append(item)
                    total_size += item.stat().st_size
                elif item.is_dir():
                    directories.append(item)
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
        resolved_path = self.resolve_path(path)
        try:
            # Early validation of the path
            if not self._validate_search_path(resolved_path):
                return FindResult(
                    success=False,
                    path=resolved_path,
                    pattern=pattern,
                    recursive=recursive,
                    error=f"Directory does not exist or "
                    f"is not a directory: {resolved_path}",
                )

            # Perform the search
            files, directories = self._perform_pattern_search(
                resolved_path, pattern, recursive, include_hidden
            )

            # Create the result
            total_matches = len(files) + len(directories)
            return FindResult(
                success=True,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                files=files,
                directories=directories,
                total_matches=total_matches,
                message=f"Found {len(files)} files and {len(directories)} "
                f"directories matching '{pattern}'",
            )
        except (QuackFileNotFoundError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error finding files in {resolved_path}: {str(e)}")
            return FindResult(
                success=False,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error finding files in {resolved_path}: {str(e)}")
            return FindResult(
                success=False,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                error=str(e),
            )

    def _validate_search_path(self, path: Path) -> bool:
        """
        Validate that a path exists and is a directory.

        Args:
            path: Path to validate

        Returns:
            True if the path exists and is a directory, False otherwise
        """
        return path.exists() and path.is_dir()

    def _perform_pattern_search(
        self, directory: Path, pattern: str, recursive: bool, include_hidden: bool
    ) -> tuple[list[Path], list[Path]]:
        """
        Perform the actual search for files and directories matching a pattern.

        Args:
            directory: Directory to search in.
            pattern: Pattern to match against.
            recursive: Whether to search recursively.
            include_hidden: Whether to include hidden files.

        Returns:
            Tuple of (matching files, matching directories)
        """
        files: list[Path] = []
        directories: list[Path] = []

        # Choose the appropriate search method explicitly
        if recursive:
            items = directory.rglob(pattern)
        else:
            items = directory.glob(pattern)

        for item in items:
            # Skip hidden items if not requested
            if not include_hidden and item.name.startswith("."):
                continue

            if item.is_file():
                files.append(item)
            elif item.is_dir():
                directories.append(item)

        return files, directories

    # -------------------------------
    # YAML operations
    # -------------------------------
    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file

        Returns:
            DataResult with parsed YAML data
        """
        resolved_path = self.resolve_path(path)
        try:
            text_result = self.read_text(resolved_path)
            if not text_result.success:
                raise QuackIOError(text_result.error, resolved_path)
            try:
                data = yaml.safe_load(text_result.content)
            except yaml.YAMLError as e:
                raise QuackFormatError(
                    resolved_path,
                    "YAML",
                    message=f"Invalid YAML format: {str(e)}",
                    original_error=e,
                ) from e
            if data is None:
                data = {}
            elif not isinstance(data, dict):
                raise QuackValidationError(
                    f"YAML content is not a dictionary: {type(data)}", resolved_path
                )
            return DataResult(
                success=True,
                path=resolved_path,
                data=data,
                format="yaml",
                message=f"Successfully parsed YAML data "
                f"with {len(data)} top-level keys",
            )
        except (QuackFormatError, QuackValidationError, QuackIOError) as e:
            logger.error(f"Error reading YAML file {resolved_path}: {str(e)}")
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="yaml",
                error=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error reading YAML file {resolved_path}: {str(e)}"
            )
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="yaml",
                error=str(e),
            )

    def write_yaml(
        self, path: str | Path, data: dict, atomic: bool = True
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
        resolved_path = self.resolve_path(path)
        try:
            try:
                yaml_content = yaml.safe_dump(
                    data,
                    default_flow_style=False,
                    sort_keys=False,
                )
            except yaml.YAMLError as e:
                raise QuackFormatError(
                    resolved_path,
                    "YAML",
                    message=f"Error converting data to YAML: {str(e)}",
                    original_error=e,
                ) from e
            return self.write_text(resolved_path, yaml_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing YAML file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing YAML file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))

    # -------------------------------
    # JSON operations
    # -------------------------------
    def read_json(self, path: str | Path) -> DataResult[dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file

        Returns:
            DataResult with parsed JSON data
        """
        resolved_path = self.resolve_path(path)
        try:
            text_result = self.read_text(resolved_path)
            if not text_result.success:
                raise QuackIOError(text_result.error, resolved_path)
            try:
                data = json.loads(text_result.content)
            except json.JSONDecodeError as e:
                raise QuackFormatError(
                    resolved_path,
                    "JSON",
                    message=f"Invalid JSON format: {str(e)}",
                    original_error=e,
                ) from e
            if not isinstance(data, dict):
                raise QuackValidationError(
                    f"JSON content is not an object: {type(data)}", resolved_path
                )
            return DataResult(
                success=True,
                path=resolved_path,
                data=data,
                format="json",
                message=f"Successfully parsed JSON data "
                f"with {len(data)} top-level keys",
            )
        except (QuackFormatError, QuackValidationError, QuackIOError) as e:
            logger.error(f"Error reading JSON file {resolved_path}: {str(e)}")
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="json",
                error=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error reading JSON file {resolved_path}: {str(e)}"
            )
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="json",
                error=str(e),
            )

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
        resolved_path = self.resolve_path(path)
        try:
            try:
                json_content = json.dumps(
                    data,
                    indent=indent,
                    ensure_ascii=False,
                )
            except TypeError as e:
                raise QuackFormatError(
                    resolved_path,
                    "JSON",
                    message=f"Error converting data to JSON: {str(e)}",
                    original_error=e,
                ) from e
            return self.write_text(resolved_path, json_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing JSON file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing JSON file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))
