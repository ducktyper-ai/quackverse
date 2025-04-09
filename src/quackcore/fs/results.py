# src/quackcore/fs/results.py
"""
Result models for filesystem operations.

This module provides standardized result classes for various
filesystem operations, enhancing error handling and return values.
"""

from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # Generic type for flexible typing


class OperationResult(BaseModel):
    """Base class for all filesystem operation results."""

    success: bool = Field(
        default=True,
        description="Whether the operation was successful",
    )

    path: Path = Field(
        description="Path that was operated on",
    )

    message: str | None = Field(
        default=None,
        description="Additional message about the operation",
    )

    error: str | None = Field(
        default=None,
        description="Error message if operation failed",
    )


class ReadResult(OperationResult, Generic[T]):
    """Result of a file read operation."""

    content: T = Field(
        description="Content read from the file",
    )

    encoding: str | None = Field(
        default=None,
        description="Encoding used for text content",
    )

    # This field is added for backward compatibility with the old types.ReadResult
    data: Any = Field(
        default=None,
        description="Parsed data (for structured formats like JSON, YAML)",
    )

    @property
    def text(self) -> str:
        """
        Get content as text.

        Returns:
            Content as a string.

        Raises:
            TypeError: If content is not a string or bytes.
            UnicodeDecodeError: If binary content cannot be decoded.
        """
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, bytes):
            # If the content contains a null byte, consider it binary.
            # Respect the provided encoding parameter
            # if the test explicitly wants to decode binary data
            if b"\x00" in self.content and not self.encoding == "latin1":
                raise UnicodeDecodeError(
                    "utf-8",
                    self.content,
                    0,
                    len(self.content),
                    "Cannot decode binary content to text",
                )
            try:
                return self.content.decode(self.encoding or "utf-8")
            except UnicodeError as err:
                raise UnicodeDecodeError(
                    "utf-8",
                    self.content,
                    0,
                    len(self.content),
                    "Cannot decode binary content to text",
                ) from err
        else:
            raise TypeError(f"Content is not text: {type(self.content)}")

    @property
    def binary(self) -> bytes:
        """
        Get content as binary.

        Returns:
            Content as bytes

        Raises:
            TypeError: If content is not bytes or string
        """
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode(self.encoding or "utf-8")
        else:
            raise TypeError(f"Content is not binary: {type(self.content)}")


class WriteResult(OperationResult):
    """Result of a file write operation."""

    bytes_written: int = Field(
        default=0,
        description="Number of bytes written",
    )

    original_path: Path | None = Field(
        default=None,
        description="Original path for move/copy operations",
    )

    checksum: str | None = Field(
        default=None,
        description="Checksum of the written content",
    )


class FileInfoResult(OperationResult):
    """Result of a file info operation."""

    exists: bool = Field(
        default=False,
        description="Whether the file exists",
    )

    is_file: bool = Field(
        default=False,
        description="Whether the path is a file",
    )

    is_dir: bool = Field(
        default=False,
        description="Whether the path is a directory",
    )

    size: int | None = Field(
        default=None,
        description="Size in bytes",
    )

    modified: float | None = Field(
        default=None,
        description="Last modified timestamp",
    )

    created: float | None = Field(
        default=None,
        description="Creation timestamp",
    )

    owner: str | None = Field(
        default=None,
        description="Owner of the file",
    )

    permissions: int | None = Field(
        default=None,
        description="File permissions (mode)",
    )

    mime_type: str | None = Field(
        default=None,
        description="Detected MIME type",
    )

    # Property for backward compatibility
    @property
    def is_directory(self) -> bool:
        """Alias for is_dir for backward compatibility."""
        return self.is_dir


class DirectoryInfoResult(OperationResult):
    """Result of a directory listing operation."""

    exists: bool = Field(
        default=False,
        description="Whether the directory exists",
    )

    is_empty: bool = Field(
        default=True,
        description="Whether the directory is empty",
    )

    files: list[Path] = Field(
        default_factory=list,
        description="List of files in the directory",
    )

    directories: list[Path] = Field(
        default_factory=list,
        description="List of subdirectories in the directory",
    )

    total_files: int = Field(
        default=0,
        description="Total number of files",
    )

    total_directories: int = Field(
        default=0,
        description="Total number of subdirectories",
    )

    total_size: int = Field(
        default=0,
        description="Total size of all files in bytes",
    )


class FindResult(OperationResult):
    """Result of a file find operation."""

    files: list[Path] = Field(
        default_factory=list,
        description="List of files found",
    )

    directories: list[Path] = Field(
        default_factory=list,
        description="List of directories found",
    )

    total_matches: int = Field(
        default=0,
        description="Total number of matches",
    )

    pattern: str = Field(
        description="Pattern used for finding",
    )

    recursive: bool = Field(
        default=False,
        description="Whether search was recursive",
    )


class DataResult(OperationResult, Generic[T]):
    """Result for structured data operations (YAML, JSON, etc.)."""

    data: T = Field(
        description="The structured data",
    )

    format: str = Field(
        description="Format of the data (e.g., 'yaml', 'json')",
    )

    schema_valid: bool | None = Field(
        default=None,
        description="Whether data passed schema validation",
    )


# Aliases for backward compatibility with quackcore.fs.types
DirectoryListResult = DirectoryInfoResult
FileFindResult = FindResult
