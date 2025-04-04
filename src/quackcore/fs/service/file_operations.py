# src/quackcore/fs/service/file_operations.py
"""
File operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for file manipulation.
"""

import json
import yaml
from pathlib import Path
from typing import Any

from quackcore.errors import wrap_io_errors
from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.results import ReadResult, WriteResult, FileInfoResult, OperationResult


class FileOperationsMixin:
    """Mixin class for file operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    @wrap_io_errors
    def read_text(self, path: str | Path, encoding: str = "utf-8") -> ReadResult:
        """
        Read text content from a file.

        Args:
            path: Path to the file
            encoding: Text encoding to use (default: utf-8)

        Returns:
            ReadResult with the file content
        """
        return self.operations.read_text(path, encoding)

    @wrap_io_errors
    def write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = False,
    ) -> WriteResult:
        """
        Write text content to a file.

        Args:
            path: Path to the file
            content: Text content to write
            encoding: Text encoding to use (default: utf-8)
            atomic: Whether to use atomic write (default: False)

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_text(path, content, encoding, atomic)

    @wrap_io_errors
    def read_binary(self, path: str | Path) -> ReadResult:
        """
        Read binary content from a file.

        Args:
            path: Path to the file

        Returns:
            ReadResult with the file content
        """
        return self.operations.read_binary(path)

    @wrap_io_errors
    def write_binary(
        self, path: str | Path, content: bytes, atomic: bool = False
    ) -> WriteResult:
        """
        Write binary content to a file.

        Args:
            path: Path to the file
            content: Binary content to write
            atomic: Whether to use atomic write (default: False)

        Returns:
            WriteResult with operation status
        """
        return self.operations.write_binary(path, content, atomic)

    @wrap_io_errors
    def read_yaml(self, path: str | Path) -> ReadResult:
        """
        Read and parse YAML content from a file.

        Args:
            path: Path to the YAML file

        Returns:
            ReadResult with parsed YAML data
        """
        result = self.read_text(path)
        if not result.success:
            return result

        try:
            data = yaml.safe_load(result.content)
            return ReadResult(
                success=True,
                path=str(path),
                content=result.content,
                data=data,
                encoding=result.encoding,
            )
        except Exception as e:
            return ReadResult(
                success=False,
                path=str(path),
                error=f"Failed to parse YAML: {str(e)}",
            )

    @wrap_io_errors
    def write_yaml(
        self, path: str | Path, data: Any, encoding: str = "utf-8", atomic: bool = False
    ) -> WriteResult:
        """
        Convert data to YAML and write to a file.

        Args:
            path: Path to the file
            data: Data to convert to YAML
            encoding: Text encoding to use (default: utf-8)
            atomic: Whether to use atomic write (default: False)

        Returns:
            WriteResult with operation status
        """
        try:
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
            return self.write_text(path, content, encoding, atomic)
        except Exception as e:
            return WriteResult(
                success=False,
                path=str(path),
                error=f"Failed to convert data to YAML: {str(e)}",
            )

    @wrap_io_errors
    def read_json(self, path: str | Path) -> ReadResult:
        """
        Read and parse JSON content from a file.

        Args:
            path: Path to the JSON file

        Returns:
            ReadResult with parsed JSON data
        """
        result = self.read_text(path)
        if not result.success:
            return result

        try:
            data = json.loads(result.content)
            return ReadResult(
                success=True,
                path=str(path),
                content=result.content,
                data=data,
                encoding=result.encoding,
            )
        except Exception as e:
            return ReadResult(
                success=False,
                path=str(path),
                error=f"Failed to parse JSON: {str(e)}",
            )

    @wrap_io_errors
    def write_json(
        self,
        path: str | Path,
        data: Any,
        encoding: str = "utf-8",
        atomic: bool = False,
        indent: int = 2,
    ) -> WriteResult:
        """
        Convert data to JSON and write to a file.

        Args:
            path: Path to the file
            data: Data to convert to JSON
            encoding: Text encoding to use (default: utf-8)
            atomic: Whether to use atomic write (default: False)
            indent: JSON indentation level (default: 2)

        Returns:
            WriteResult with operation status
        """
        try:
            content = json.dumps(data, indent=indent)
            return self.write_text(path, content, encoding, atomic)
        except Exception as e:
            return WriteResult(
                success=False,
                path=str(path),
                error=f"Failed to convert data to JSON: {str(e)}",
            )

    @wrap_io_errors
    def get_file_info(self, path: str | Path) -> FileInfoResult:
        """
        Get information about a file or directory.

        Args:
            path: Path to the file or directory

        Returns:
            FileInfoResult with the file information
        """
        return self.operations.get_file_info(path)

    @wrap_io_errors
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

    @wrap_io_errors
    def write_lines(
            self,
            path: str | Path,
            lines: list[str],
            encoding: str = "utf-8",
            atomic: bool = True,
            line_ending: str = "\n",
    ) -> WriteResult:
        """
        Write lines to a text file.

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

    # File management operations
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