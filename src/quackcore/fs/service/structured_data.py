# src/quackcore/fs/service/structured_data.py
"""
Structured data operations (JSON, YAML) for the FileSystemService.
"""

from pathlib import Path

from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.results import DataResult, WriteResult


class StructuredDataMixin:
    """Mixin class for structured data operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have operations
    operations: FileSystemOperations

    # --- Structured Data Operations ---

    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file

        Returns:
            DataResult with parsed YAML data
        """
        return self.operations._read_yaml(path)

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
        return self.operations._write_yaml(path, data, atomic)

    def read_json(self, path: str | Path) -> DataResult[dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file

        Returns:
            DataResult with parsed JSON data
        """
        return self.operations._read_json(path)

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
        return self.operations._write_json(path, data, atomic, indent)
