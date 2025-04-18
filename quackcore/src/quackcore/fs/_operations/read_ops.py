# src/quackcore/fs/_operations/read_ops.py
"""
File reading _operations for the filesystem _operations.

This module provides internal _operations for reading both text and binary
data from files with proper error handling and result formatting.
"""

from pathlib import Path
from typing import TypeVar

from quackcore.fs.results import DataResult, OperationResult, ReadResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Define generic type for ReadResult
T = TypeVar("T")


class ReadOperationsMixin:
    """
    File reading _operations mixin class.

    Provides internal methods for reading text and binary data from files
    with consistent error handling and return types.
    """

    def _resolve_path(self, path: str | Path | DataResult | OperationResult) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve (str, Path, DataResult, or OperationResult)

        Returns:
            Path: Resolved Path object

        Note:
            Internal helper method implemented in the main class.
            Not meant for external consumption.
        """
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _read_text(self, path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[str]:
        """
        Read text from a file.

        Args:
            path: Path to the file (str, Path, DataResult, or OperationResult)
            encoding: Text encoding (default: utf-8)

        Returns:
            ReadResult[str]: Result object containing:
                - success: Whether the operation was successful
                - path: The resolved file path
                - content: The file content as text (empty string on error)
                - encoding: The encoding used
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(f"Reading text from: {resolved_path} with encoding: {encoding}")

        try:
            with open(resolved_path, encoding=encoding) as f:
                content = f.read()

            logger.debug(
                f"Successfully read {len(content)} characters from {resolved_path}"
            )
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

    def _read_binary(self, path: str | Path | DataResult | OperationResult) -> ReadResult[bytes]:
        """
        Read binary data from a file.

        Args:
            path: Path to the file (str, Path, DataResult, or OperationResult)

        Returns:
            ReadResult[bytes]: Result object containing:
                - success: Whether the operation was successful
                - path: The resolved file path
                - content: The file content as bytes (empty bytes on error)
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(f"Reading binary data from: {resolved_path}")

        try:
            with open(resolved_path, "rb") as f:
                content = f.read()

            logger.debug(f"Successfully read {len(content)} bytes from {resolved_path}")
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
