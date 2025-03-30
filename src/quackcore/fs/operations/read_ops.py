# src/quackcore/fs/operations/read_ops.py
"""
File reading operations for the filesystem operations.
"""

from pathlib import Path

from quackcore.fs.results import ReadResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class ReadOperationsMixin:
    """File reading operations mixin class."""

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the base directory."""
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

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
        logger.debug(f"Reading text from: {resolved_path} with encoding: {encoding}")

        try:
            with open(resolved_path, encoding=encoding) as f:
                content = f.read()

            logger.debug(
                f"Successfully read {len(content)} characters from {resolved_path}")
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