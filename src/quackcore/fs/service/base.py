"""
Base implementation of the FileSystemService.
"""

from pathlib import Path

from quackcore.fs.operations import FileSystemOperations
from quackcore.logging import get_logger
from quackcore.logging.config import LogLevel, LOG_LEVELS

# Import all mixins
from .core import CoreServiceMixin
from .data_ops import DataOperationsMixin
from .file_ops import FileOperationsMixin
from .management_ops import ManagementOperationsMixin
from .path_utils import PathUtilsMixin
from .utility_ops import UtilityOperationsMixin


class FileSystemService(
    CoreServiceMixin,
    FileOperationsMixin,
    ManagementOperationsMixin,
    DataOperationsMixin,
    PathUtilsMixin,
    UtilityOperationsMixin,
):
    """
    High-level service for filesystem operations.

    This service provides a clean, consistent API for all file operations
    in QuackCore, with proper error handling and result objects.
    """

    def __init__(
        self, base_dir: str | Path | None = None, log_level: int = LOG_LEVELS[LogLevel.INFO]
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