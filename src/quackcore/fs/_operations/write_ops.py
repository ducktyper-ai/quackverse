# src/quackcore/fs/_operations/write_ops.py
"""
File writing, copying, moving and deleting _operations.

This module provides internal _operations for modifying the filesystem,
including writing files, copying, moving, deleting files and directories,
and directory creation with proper error handling.
"""

from pathlib import Path

from quackcore.errors import (
    QuackFileExistsError,
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
)
from quackcore.fs.results import DataResult, OperationResult, WriteResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class WriteOperationsMixin:
    """
    File writing _operations mixin class.

    Provides internal methods for writing, copying, moving, and deleting
    files and directories with consistent error handling and return types.
    """

    def _resolve_path(self, path: str | Path | DataResult | OperationResult) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve (str, Path, DataResult, or OperationResult)

        Returns:
            Path: Resolved Path object

        Note:
            Internal helper method that must be implemented in the concrete class.
            Not meant for external consumption.
        """
        raise NotImplementedError("This method should be overridden")

    def _write_text(
        self,
        path: str | Path,
        content: str,
        encoding: str = "utf-8",
        atomic: bool = True,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write text content to a file.

        This method handles various text encodings and can perform atomic writes
        for safer file _operations. It can also calculate checksums for data integrity.

        Args:
            path: Path to the file
            content: Text content to write
            encoding: Text encoding (default: utf-8)
            atomic: Whether to use atomic writing (safer but slower)
            calculate_checksum: Whether to calculate a checksum for verification

        Returns:
            WriteResult with operation status including:
                - success: Whether the operation was successful
                - path: The actual path where the file was written
                - bytes_written: Number of bytes written
                - checksum: File checksum if requested
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        # Import necessary utility functions
        from quackcore.fs._operations import (
            _atomic_write,
            _compute_checksum,
            _ensure_directory,
        )

        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Writing text to {resolved_path} with encoding {encoding}, "
            f"atomic={atomic}, calculate_checksum={calculate_checksum}"
        )

        try:
            _ensure_directory(resolved_path.parent)
            logger.debug(f"Ensured parent directory exists: {resolved_path.parent}")

            # Handle special encoding (UTF-16 variants)
            if encoding.lower().startswith("utf-16"):
                if encoding.lower() == "utf-16":
                    bytes_content = content.encode("utf-16")
                elif encoding.lower() == "utf-16-le":
                    bytes_content = content.encode("utf-16-le")
                elif encoding.lower() == "utf-16-be":
                    bytes_content = content.encode("utf-16-be")
                else:
                    bytes_content = content.encode(encoding)
                logger.debug(f"Encoded text to UTF-16 variant: {encoding}")

                if atomic:
                    logger.debug("Using atomic write for binary content (UTF-16)")
                    # Capture the return value from atomic_write
                    written_path = _atomic_write(resolved_path, bytes_content)
                    actual_path = written_path
                else:
                    logger.debug("Using direct write for binary content (UTF-16)")
                    with open(resolved_path, "wb") as f:
                        f.write(bytes_content)
                    actual_path = resolved_path
            else:
                # For other encodings, use text mode
                if atomic:
                    logger.debug("Using atomic write for text content")
                    # Capture the return value from atomic_write (a Path object)
                    written_path = _atomic_write(resolved_path, content)
                    actual_path = written_path
                else:
                    logger.debug("Using direct write for text content")
                    with open(resolved_path, "w", encoding=encoding) as f:
                        f.write(content)
                    actual_path = resolved_path

            bytes_written = len(content.encode(encoding))
            logger.info(f"Successfully wrote {bytes_written} bytes to {actual_path}")

            checksum = None
            if calculate_checksum:
                logger.debug(f"Calculating checksum for {actual_path}")
                checksum = _compute_checksum(actual_path)

            return WriteResult(
                success=True,
                path=actual_path,
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

    def _write_binary(
        self,
        path: str | Path,
        content: bytes,
        atomic: bool = True,
        calculate_checksum: bool = False,
    ) -> WriteResult:
        """
        Write binary data to a file.

        This method writes raw binary data to a file with optional atomic
        writing and checksum calculation.

        Args:
            path: Path to the file
            content: Binary content to write
            atomic: Whether to use atomic writing (safer but slower)
            calculate_checksum: Whether to calculate a checksum for verification

        Returns:
            WriteResult with operation status including:
                - success: Whether the operation was successful
                - path: The actual path where the file was written
                - bytes_written: Number of bytes written
                - checksum: File checksum if requested
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        from quackcore.fs._operations import (
            _atomic_write,
            _compute_checksum,
            _ensure_directory,
        )

        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Writing binary data to {resolved_path}, "
            f"atomic={atomic}, calculate_checksum={calculate_checksum}"
        )

        try:
            _ensure_directory(resolved_path.parent)
            logger.debug(f"Ensured parent directory exists: {resolved_path.parent}")

            if atomic:
                logger.debug("Using atomic write for binary data")
                written_path = _atomic_write(resolved_path, content)
                actual_path = written_path
            else:
                logger.debug("Using direct write for binary data")
                with open(resolved_path, "wb") as f:
                    f.write(content)
                actual_path = resolved_path

            logger.info(f"Successfully wrote {len(content)} bytes to {actual_path}")

            checksum = None
            if calculate_checksum:
                logger.debug(f"Calculating checksum for {actual_path}")
                checksum = _compute_checksum(actual_path)

            return WriteResult(
                success=True,
                path=actual_path,
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

    def _copy(
        self,
        src: str | Path,
        dst: str | Path,
        overwrite: bool = False,
    ) -> WriteResult:
        """
        Copy a file or directory.

        This method copies a file or directory to a new location with
        optional overwriting of existing files.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status including:
                - success: Whether the operation was successful
                - path: The destination path
                - original_path: The source path
                - bytes_written: Number of bytes copied (for files)
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        from quackcore.fs._operations import _safe_copy

        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        logger.debug(f"Copying from {src_path} to {dst_path}, overwrite={overwrite}")

        try:
            copied_path = _safe_copy(src_path, dst_path, overwrite=overwrite)
            bytes_copied = copied_path.stat().st_size if copied_path.is_file() else 0
            logger.info(f"Successfully copied {src_path} to {dst_path}")

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

    def _move(
        self,
        src: str | Path,
        dst: str | Path,
        overwrite: bool = False,
    ) -> WriteResult:
        """
        Move a file or directory.

        This method moves a file or directory to a new location with
        optional overwriting of existing files.

        Args:
            src: Source path
            dst: Destination path
            overwrite: Whether to overwrite if destination exists

        Returns:
            WriteResult with operation status including:
                - success: Whether the operation was successful
                - path: The destination path where the file was moved
                - original_path: The source path
                - bytes_written: Size of the moved file (for files)
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        from quackcore.fs._operations import _safe_move

        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        logger.debug(f"Moving from {src_path} to {dst_path}, overwrite={overwrite}")

        try:
            # Get file size before moving (if it's a file)
            try:
                bytes_moved = src_path.stat().st_size if src_path.is_file() else 0
            except (FileNotFoundError, PermissionError):
                bytes_moved = 0
                logger.warning(f"Could not determine size of {src_path} before moving")

            moved_path = _safe_move(src_path, dst_path, overwrite=overwrite)
            logger.info(f"Successfully moved {src_path} to {moved_path}")

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

    def _delete(self, path: str | Path, missing_ok: bool = True) -> OperationResult:
        """
        Delete a file or directory.

        This method safely removes a file or directory with configurable
        behavior for handling missing files.

        Args:
            path: Path to delete
            missing_ok: Whether to ignore if the path doesn't exist

        Returns:
            OperationResult with operation status including:
                - success: Whether the operation was successful
                - path: The path that was deleted (or attempted to delete)
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        from quackcore.fs._operations import _safe_delete

        resolved_path = self._resolve_path(path)
        logger.debug(f"Deleting {resolved_path}, missing_ok={missing_ok}")

        try:
            result = _safe_delete(resolved_path, missing_ok=missing_ok)

            if not result and not missing_ok:
                logger.error(f"Path not found and missing_ok is False: {resolved_path}")
                return OperationResult(
                    success=False,
                    path=resolved_path,
                    error=f"Path not found: {resolved_path}",
                )

            logger.info(f"Successfully deleted {resolved_path}")
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

    def _create_directory(
        self, path: str | Path, exist_ok: bool = True
    ) -> OperationResult:
        """
        Create a directory.

        This method creates a directory with configurable behavior
        for handling existing directories.

        Args:
            path: Path to create
            exist_ok: Whether to ignore if the directory already exists

        Returns:
            OperationResult with operation status including:
                - success: Whether the operation was successful
                - path: The path of the created directory
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        from quackcore.fs._operations import _ensure_directory

        resolved_path = self._resolve_path(path)
        logger.debug(f"Creating directory {resolved_path}, exist_ok={exist_ok}")

        try:
            dir_path = _ensure_directory(resolved_path, exist_ok=exist_ok)
            logger.info(f"Successfully created directory {dir_path}")

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
