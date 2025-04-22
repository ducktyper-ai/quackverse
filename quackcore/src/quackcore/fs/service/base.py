# quackcore/src/quackcore/fs/service/base.py
"""
Base class for the FileSystemService.

This provides the core functionality and initialization for the service.
"""

from pathlib import Path

from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.results import DataResult, OperationResult
from quackcore.logging import LOG_LEVELS, LogLevel, get_logger


class FileSystemService:
    """
    High-level service for filesystem _operations.

    This service provides a clean, consistent API for all file _operations
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

        # Initialize _operations with base directory
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.operations = FileSystemOperations(self.base_dir)

    def _normalize_input_path(self,
                              path: str | Path | DataResult | OperationResult) -> Path:
        """
        Normalize an input path to a Path object.

        This method handles various input types (str, Path, DataResult, OperationResult)
        and converts them to a standard Path object for internal use.

        Args:
            path: Input path, which can be a string, Path, DataResult, or OperationResult

        Returns:
            A normalized Path object
        """
        # Extract from path attribute first (for PathResult)
        if hasattr(path, "path") and path.path is not None:
            return Path(path.path)

        # Then check for data attribute (for DataResult)
        if hasattr(path, "data") and path.data is not None:
            path_content = path.data
        else:
            path_content = path

        try:
            return Path(path_content)
        except TypeError:
            return Path(str(path_content))
