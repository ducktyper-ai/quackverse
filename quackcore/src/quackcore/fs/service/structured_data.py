# quackcore/src/quackcore/fs/service/structured_data.py
"""
Structured data _operations (JSON, YAML) for the FileSystemService.
"""

from pathlib import Path

from quackcore.fs._operations import FileSystemOperations
from quackcore.fs.results import DataResult, OperationResult, WriteResult


class StructuredDataMixin:
    """Mixin class for structured data _operations in the FileSystemService."""

    # This ensures the mixin will only be used with classes that have _operations
    operations: FileSystemOperations

    # This method is added in the base class
    def _normalize_input_path(self,
                              path: str | Path | DataResult | OperationResult) -> Path:
        """Normalize an input path to a Path object."""
        raise NotImplementedError("This method should be overridden")

    # --- Structured Data Operations ---

    def read_yaml(self, path: str | Path | DataResult | OperationResult) -> DataResult[
        dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with parsed YAML data
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._read_yaml(normalized_path)

    def write_yaml(
            self,
            path: str | Path | DataResult | OperationResult,
            data: dict,
            atomic: bool = True,
    ) -> WriteResult:
        """
        Write data to a YAML file.

        Args:
            path: Path to YAML file (string, Path, DataResult, or OperationResult)
            data: Data to write
            atomic: Whether to use atomic writing

        Returns:
            WriteResult with operation status
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._write_yaml(normalized_path, data, atomic)

    def read_json(self, path: str | Path | DataResult | OperationResult) -> DataResult[
        dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file (string, Path, DataResult, or OperationResult)

        Returns:
            DataResult with parsed JSON data
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._read_json(normalized_path)

    def write_json(
            self,
            path: str | Path | DataResult | OperationResult,
            data: dict,
            atomic: bool = True,
            indent: int = 2,
    ) -> WriteResult:
        """
        Write data to a JSON file.

        Args:
            path: Path to JSON file (string, Path, DataResult, or OperationResult)
            data: Data to write
            atomic: Whether to use atomic writing
            indent: Number of spaces to indent

        Returns:
            WriteResult with operation status
        """
        normalized_path = self._normalize_input_path(path)
        return self.operations._write_json(normalized_path, data, atomic, indent)
