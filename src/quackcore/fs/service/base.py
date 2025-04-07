# src/quackcore/fs/service/base.py
"""
Base class for the FileSystemService.

This provides the core functionality and initialization for the service.
"""

from pathlib import Path

from quackcore.fs.operations import FileSystemOperations
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