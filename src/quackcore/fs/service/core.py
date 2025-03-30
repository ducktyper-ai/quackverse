"""
Core functionality for the FileSystemService.
"""

from pathlib import Path

from quackcore.logging import get_logger

from .protocols import LoggerProtocol, OperationsProtocol

# Create a local logger for this module
logger = get_logger(__name__)


class CoreServiceMixin:
    """Core functionality mixin for FileSystemService."""

    # Internal storage for properties
    _base_dir: Path
    _operations: OperationsProtocol
    _logger: LoggerProtocol

    # These properties and methods will be available to all mixins
    @property
    def base_dir(self) -> Path:
        """Get the base directory."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value: Path):
        """Set the base directory."""
        self._base_dir = value

    @property
    def operations(self) -> OperationsProtocol:
        """Get the FileSystemOperations instance."""
        return self._operations

    @operations.setter
    def operations(self, value: OperationsProtocol):
        """Set the FileSystemOperations instance."""
        self._operations = value

    @property
    def logger(self) -> LoggerProtocol:
        """Get the logger."""
        return self._logger

    @logger.setter
    def logger(self, value: LoggerProtocol):
        """Set the logger."""
        self._logger = value