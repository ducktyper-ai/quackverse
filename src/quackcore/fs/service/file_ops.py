"""
File reading and writing operations for FileSystemService.
"""

from pathlib import Path

from quackcore.fs.results import ReadResult, WriteResult
from quackcore.logging import get_logger

from .protocols import LoggerProtocol, OperationsProtocol

# Create a local logger for this module
logger = get_logger(__name__)


class FileOperationsMixin:
    """Mixin for file reading and writing operations."""

    # This tells type checkers that this class requires these properties
    logger: LoggerProtocol  # Will be set by the main class
    operations: OperationsProtocol  # Will be set by the main class

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
        self.logger.debug(f"Reading text from {path}")
        return self.operations.read_text(path, encoding)

    def read_binary(self, path: str | Path) -> ReadResult[bytes]:
        """
        Read binary data from a file.

        Args:
            path: Path to the file

        Returns:
            ReadResult with the file content as bytes
        """
        self.logger.debug(f"Reading binary from {path}")
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
        self.logger.debug(f"Reading lines from {path}")
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
        self.logger.debug(f"Writing text to {path}")
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
        self.logger.debug(f"Writing binary to {path}")
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
        self.logger.debug(f"Writing lines to {path}")
        content = line_ending.join(lines)

        # For non-default line endings, encode and write in binary mode
        if line_ending != "\n":
            bytes_content = content.encode(encoding)
            return self.operations.write_binary(path, bytes_content, atomic)
        else:
            return self.operations.write_text(path, content, encoding, atomic)