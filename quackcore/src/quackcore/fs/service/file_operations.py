# quackcore/src/quackcore/fs/service/file_operations.py
"""
File _operations utilities for the FileSystemService.

These utilities extend the FileSystemService with methods for file manipulation.
"""

import json
from pathlib import Path

import yaml

from quackcore.errors import wrap_io_errors
from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.results import DataResult, OperationResult, ReadResult, WriteResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


class FileOperationsMixin:
    """Mixin class for file _operations in the FileSystemService."""

    # This mixin expects the implementing class to have an attribute '_operations'
    # that is an instance of FileSystemOperations.
    operations: FileSystemOperations

    # This method is added in the base class
    def _normalize_input_path(self, path: str | Path | DataResult | OperationResult) -> Path:
        """Normalize an input path to a Path object."""
        raise NotImplementedError("This method should be overridden")

    @wrap_io_errors
    def read_text(self, path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[str]:
        """
        Read text content from a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)
            encoding: Text encoding to use (default: utf-8).

        Returns:
            ReadResult with the file content as text.
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._read_text(normalized_path, encoding)

    @wrap_io_errors
    def write_text(
        self,
        path: str | Path | DataResult | OperationResult,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = False,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write text content to a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)
            content: Text content to write.
            encoding: Text encoding to use (default: utf-8).
            atomic: Whether to use atomic write (default: False).
            calculate_checksum: Whether to calculate a checksum (default: False).

        Returns:
            WriteResult with operation status.
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._write_text(
            normalized_path, content, encoding, atomic, calculate_checksum
        )

    @wrap_io_errors
    def read_binary(self, path: str | Path | DataResult | OperationResult) -> ReadResult[bytes]:
        """
        Read binary content from a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)

        Returns:
            ReadResult with the file content as bytes.
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._read_binary(normalized_path)

    @wrap_io_errors
    def write_binary(
        self,
        path: str | Path | DataResult | OperationResult,
        content: bytes,
        atomic: bool = False,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write binary content to a file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)
            content: Binary content to write.
            atomic: Whether to use atomic write (default: False).
            calculate_checksum: Whether to calculate a checksum (default: False).

        Returns:
            WriteResult with operation status.
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._write_binary(normalized_path, content, atomic, calculate_checksum)

    @wrap_io_errors
    def read_lines(
        self, path: str | Path | DataResult | OperationResult, encoding: str = "utf-8"
    ) -> ReadResult[list[str]]:
        """
        Read lines from a text file.

        Args:
            path: Path to the file (string, Path, DataResult, or OperationResult)
            encoding: Text encoding

        Returns:
            ReadResult with the file content as a list of lines
        """
        normalized_path = self._normalize_input_path(path)
        result = self.operations._read_text(normalized_path, encoding)

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
            path=normalized_path,
            content=[],
            encoding=encoding,
            error=result.error,
            message=f"Failed to read lines: {result.error}",
        )

    @wrap_io_errors
    def write_lines(
        self,
        path: str | Path | DataResult | OperationResult,
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
            path: Path to the file (string, Path, DataResult, or OperationResult)
            lines: Lines to write.
            encoding: Text encoding to use.
            atomic: Whether to write the file atomically.
            line_ending: The line ending to use.

        Returns:
            WriteResult indicating the outcome of the write operation.
        """
        normalized_path = self._normalize_input_path(path)
        content = line_ending.join(lines)
        # For non-default line endings, encode and write in binary mode.
        if line_ending != "\n":
            bytes_content = content.encode(encoding)
            return self.operations._write_binary(normalized_path, bytes_content, atomic)
        else:
            return self.operations._write_text(normalized_path, content, encoding, atomic)

    @wrap_io_errors
    def read_yaml(self, path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
        """
        Read and parse YAML content from a file.

        Args:
            path: Path to the YAML file (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with parsed YAML data.
        """
        try:
            normalized_path = self._normalize_input_path(path)
            result = self.read_text(normalized_path)
            if not result.success:
                return DataResult(
                    success=False,
                    path=result.path,
                    data={},
                    format="yaml",
                    error=result.error,
                )
            try:
                parsed_data = yaml.safe_load(result.content)
                if parsed_data is None:
                    parsed_data = {}
                result.data = parsed_data  # For backward compatibility.
                return DataResult(
                    success=True,
                    path=result.path,
                    data=parsed_data,
                    format="yaml",
                    message="Successfully parsed YAML data",
                )
            except yaml.YAMLError as e:
                error_msg = f"Invalid YAML format: {str(e)}"
                return DataResult(
                    success=False,
                    path=normalized_path,
                    data={},
                    format="yaml",
                    error=error_msg,
                )
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return DataResult(
                success=False,
                path=normalized_path,
                data={},
                format="yaml",
                error=f"Error reading YAML format: {str(e)}",
            )

    @wrap_io_errors
    def write_yaml(
        self,
        path: str | Path | DataResult | OperationResult,
        data: dict,
        atomic: bool = True,
    ) -> WriteResult:
        """
        Write data to a YAML file.

        Args:
            path: Path to the YAML file (string, Path, DataResult, or OperationResult)
            data: Data to write.
            atomic: Whether to use atomic writing.

        Returns:
            WriteResult with operation status.
        """
        try:
            normalized_path = self._normalize_input_path(path)
            content = yaml.dump(data, default_flow_style=False, sort_keys=False)
            return self.write_text(normalized_path, content, atomic=atomic)
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return WriteResult(
                success=False,
                path=normalized_path,
                error=f"Failed to write YAML: {str(e)}",
            )

    @wrap_io_errors
    def read_json(self, path: str | Path | DataResult | OperationResult) -> DataResult[dict]:
        """
        Read a JSON file and parse its contents.

        Args:
            path: Path to the JSON file (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with parsed JSON data.
        """
        try:
            normalized_path = self._normalize_input_path(path)
            result = self.read_text(normalized_path)
            if not result.success:
                return DataResult(
                    success=False,
                    path=result.path,
                    data={},
                    format="json",
                    error=result.error,
                )
            try:
                parsed_data = json.loads(result.content)
                result.data = parsed_data  # For backward compatibility.
                return DataResult(
                    success=True,
                    path=result.path,
                    data=parsed_data,
                    format="json",
                    message="Successfully parsed JSON data",
                )
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format: {str(e)}"
                return DataResult(
                    success=False,
                    path=normalized_path,
                    data={},
                    format="json",
                    error=error_msg,
                )
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return DataResult(
                success=False,
                path=normalized_path,
                data={},
                format="json",
                error=f"Error reading JSON format: {str(e)}",
            )

    @wrap_io_errors
    def write_json(
        self,
        path: str | Path | DataResult | OperationResult,
        data: dict,
        atomic: bool = True,
        indent: int = 2,
    ) -> WriteResult:
        """
        Write data to a JSON file.

        Args:
            path: Path to the JSON file (string, Path, DataResult, or OperationResult)
            data: Data to write.
            atomic: Whether to use atomic writing.
            indent: Number of spaces to indent.

        Returns:
            WriteResult with operation status.
        """
        try:
            normalized_path = self._normalize_input_path(path)
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.write_text(normalized_path, content, atomic=atomic)
        except Exception as e:
            normalized_path = self._normalize_input_path(path)
            return WriteResult(
                success=False,
                path=normalized_path,
                error=f"Failed to write JSON: {str(e)}",
            )

    # File management _operations
    def copy(
        self, src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False
    ) -> WriteResult:
        """
        Copy a file or directory.

        Args:
            src: Source path (string, Path, DataResult, or OperationResult)
            dst: Destination path (string, Path, DataResult, or OperationResult)
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status
        """
        normalized_src = self._normalize_input_path(src)
        normalized_dst = self._normalize_input_path(dst)
        return self.operations._copy(normalized_src, normalized_dst, overwrite)

    def move(
        self, src: str | Path | DataResult | OperationResult, dst: str | Path | DataResult | OperationResult, overwrite: bool = False
    ) -> WriteResult:
        """
        Move a file or directory.

        Args:
            src: Source path (string, Path, DataResult, or OperationResult)
            dst: Destination path (string, Path, DataResult, or OperationResult)
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status
        """
        normalized_src = self._normalize_input_path(src)
        normalized_dst = self._normalize_input_path(dst)
        return self.operations._move(normalized_src, normalized_dst, overwrite)

    def delete(self, path: str | Path | DataResult | OperationResult, missing_ok: bool = True) -> OperationResult:
        """
        Delete a file or directory.

        Args:
            path: Path to delete (string, Path, DataResult, or OperationResult)
            missing_ok: Whether to ignore if the path doesn't exist

        Returns:
            OperationResult with operation status
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._delete(normalized_path, missing_ok)
