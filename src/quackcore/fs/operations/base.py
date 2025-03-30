# src/quackcore/fs/operations/base.py
"""
Base implementation of the FileSystemOperations class.
"""

from pathlib import Path

from quackcore.logging import get_logger

# Import all the specialized operations
from .core import initialize_mime_types, resolve_path
from .directory_ops import DirectoryOperationsMixin
from .file_info import FileInfoOperationsMixin
from .find_ops import FindOperationsMixin
from .read_ops import ReadOperationsMixin
from .serialization_ops import SerializationOperationsMixin
from .write_ops import WriteOperationsMixin

# Set up logger
logger = get_logger(__name__)


class FileSystemOperations(
    ReadOperationsMixin,
    WriteOperationsMixin,
    FileInfoOperationsMixin,
    DirectoryOperationsMixin,
    FindOperationsMixin,
    SerializationOperationsMixin,
):
    """Core implementation of filesystem operations."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """
        Initialize filesystem operations.

        Args:
            base_dir: Optional base directory for relative paths
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        logger.debug(f"Initialized FileSystemOperations with base_dir: {self.base_dir}")
        initialize_mime_types()

    def resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve

        Returns:
            Resolved Path object
        """
        return resolve_path(self.base_dir, path)