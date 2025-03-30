"""
Data operations (YAML, JSON) for FileSystemService.
"""

from pathlib import Path

from quackcore.fs.results import DataResult, WriteResult
from quackcore.logging import get_logger

from .protocols import LoggerProtocol, OperationsProtocol

# Create a local logger for this module
logger = get_logger(__name__)


class DataOperationsMixin:
    """Mixin for structured data operations."""

    # This tells type checkers that this class requires these properties
    logger: LoggerProtocol  # Will be set by the main class
    operations: OperationsProtocol  # Will be set by the main class

    # --- Structured Data Operations ---

    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file

        Returns:
            DataResult with parsed YAML data
        """
        self.logger.debug(f"Reading YAML from {path}")
        return self.operations.read_yaml(path)

    def write_yaml(
        self,
        path: str | Path,
        data: dict,
        atomic: bool = True,
    ) -> WriteResult:
        """
        Write data to a YAML file.

        Args:
            path: Path to YAML file
            data: Data to write
            atomic: Whether to use atomic writing

        Returns:
            WriteResult with operation status
        """
        self.logger.debug(f"Writing YAML to {path}")
        return self.operations.write_yaml(path, data, atomic)

    def read_json(self, path: str | Path) -> DataResult[dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file

        Returns:
            DataResult with parsed JSON data
        """
        self.logger.debug(f"Reading JSON from {path}")
        return self.operations.read_json(path)

    def write_json(
        self,
        path: str | Path,
        data: dict,
        atomic: bool = True,
        indent: int = 2,
    ) -> WriteResult:
        """
        Write data to a JSON file.

        Args:
            path: Path to JSON file
            data: Data to write
            atomic: Whether to use atomic writing
            indent: Number of spaces to indent

        Returns:
            WriteResult with operation status
        """
        self.logger.debug(f"Writing JSON to {path}")
        return self.operations.write_json(path, data, atomic, indent)