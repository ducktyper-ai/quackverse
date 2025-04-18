# quackcore/src/quackcore/fs/_operations/serialization_ops.py
"""
Serialization _operations (JSON, YAML) for filesystem _operations.

This module provides internal _operations for reading and writing
structured data formats (JSON, YAML) with proper error handling
and validation.
"""

import json
from pathlib import Path
from typing import Any, TypeVar

from quackcore.errors import (
    QuackFormatError,
    QuackIOError,
    QuackValidationError,
)
from quackcore.fs.results import DataResult, OperationResult, ReadResult, WriteResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Try to import YAML library
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    logger.warning("PyYAML library not found. YAML _operations will not be available.")
    YAML_AVAILABLE = False

# Define type variable for generic typing
T = TypeVar("T")


class SerializationOperationsMixin:
    """
    Serialization _operations mixin class.

    Provides internal methods for serializing and deserializing structured
    data formats (JSON, YAML) with proper validation and error handling.
    """

    def _resolve_path(self, path: str | Path | DataResult | OperationResult) -> Path:
        """
        Resolve a path relative to the base directory.

        Args:
            path: Path to resolve (str, Path, DataResult, or OperationResult)

        Returns:
            Path: Resolved Path object

        Note:
            Internal helper method implemented in the main class.
            Not meant for external consumption.
        """
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _read_text(self, path: str | Path | DataResult | OperationResult, encoding: str = "utf-8") -> ReadResult[str]:
        """
        Read text from a file.

        Args:
            path: Path to file (str, Path, DataResult, or OperationResult)
            encoding: Text encoding

        Returns:
            ReadResult[str]: Result containing the file content

        Note:
            Method implemented in ReadOperationsMixin.
            Defined here for type checking.
        """
        # This method is implemented in ReadOperationsMixin
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _write_text(
        self, path: str | Path | DataResult | OperationResult, content: str, encoding: str = "utf-8", **kwargs
    ) -> WriteResult:
        """
        Write text to a file.

        Args:
            path: Path to file (str, Path, DataResult, or OperationResult)
            content: Text content
            encoding: Text encoding
            **kwargs: Additional arguments

        Returns:
            WriteResult: Result of the write operation

        Note:
            Method implemented in WriteOperationsMixin.
            Defined here for type checking.
        """
        # This method is implemented in WriteOperationsMixin
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    # -------------------------------
    # YAML _operations
    # -------------------------------
    def _read_yaml(self, path: str | Path | DataResult | OperationResult) -> DataResult[dict[str, Any]]:
        """
        Read YAML file and parse its contents.

        This method reads a YAML file, parses it, and validates that
        it contains a dictionary. Empty YAML files are treated as
        empty dictionaries.

        Args:
            path: Path to YAML file (str, Path, DataResult, or OperationResult)

        Returns:
            DataResult[dict[str, Any]]: Result object containing:
                - success: Whether the operation was successful
                - path: The resolved file path
                - data: The parsed YAML data as a dictionary
                - format: "yaml"
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        if not YAML_AVAILABLE:
            error_msg = "PyYAML library not available. Cannot read YAML file."
            logger.error(error_msg)
            resolved_path = self._resolve_path(path)
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="yaml",
                error=error_msg,
            )

        resolved_path = self._resolve_path(path)
        logger.debug(f"Reading YAML from: {resolved_path}")

        try:
            text_result = self._read_text(resolved_path)
            if not text_result.success:
                logger.error(f"Failed to read YAML file: {text_result.error}")
                raise QuackIOError(text_result.error, resolved_path)

            try:
                logger.debug("Parsing YAML content")
                data = yaml.safe_load(text_result.content)
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML format in {resolved_path}: {e}")
                raise QuackFormatError(
                    resolved_path,
                    "YAML",
                    message=f"Invalid YAML format: {str(e)}",
                    original_error=e,
                ) from e

            if data is None:
                logger.debug("YAML content is empty, using empty dict")
                data = {}
            elif not isinstance(data, dict):
                logger.error(
                    f"YAML content is not a dictionary: {type(data)} in {resolved_path}"
                )
                raise QuackValidationError(
                    f"YAML content is not a dictionary: {type(data)}", resolved_path
                )

            logger.info(
                f"Successfully parsed YAML data from {resolved_path} "
                f"with {len(data)} top-level keys"
            )

            # For backward compatibility with ReadResult.data
            # Create both a DataResult and update the original text_result
            text_result.data = data
            return DataResult(
                success=True,
                path=resolved_path,
                data=data,
                format="yaml",
                message=f"Successfully parsed YAML data "
                f"with {len(data)} top-level keys",
            )
        except (QuackFormatError, QuackValidationError, QuackIOError) as e:
            logger.error(f"Error reading YAML file {resolved_path}: {str(e)}")
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="yaml",
                error=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error reading YAML file {resolved_path}: {str(e)}"
            )
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="yaml",
                error=str(e),
            )

    def _write_yaml(
        self, path: str | Path | DataResult | OperationResult, data: dict[str, Any], atomic: bool = True
    ) -> WriteResult:
        """
        Write data to a YAML file.

        This method serializes a dictionary to YAML format and writes
        it to the specified file.

        Args:
            path: Path to YAML file (str, Path, DataResult, or OperationResult)
            data: Dictionary data to write
            atomic: Whether to use atomic writing (safer but slower)

        Returns:
            WriteResult: Result of the write operation

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        if not YAML_AVAILABLE:
            error_msg = "PyYAML library not available. Cannot write YAML file."
            logger.error(error_msg)
            resolved_path = self._resolve_path(path)
            return WriteResult(
                success=False, path=resolved_path, error=error_msg
            )

        resolved_path = self._resolve_path(path)
        logger.debug(f"Writing YAML to: {resolved_path}, atomic={atomic}")

        try:
            try:
                logger.debug("Converting data to YAML format")
                yaml_content = yaml.safe_dump(
                    data,
                    default_flow_style=False,
                    sort_keys=False,
                )
            except yaml.YAMLError as e:
                logger.error(f"Error converting data to YAML: {e}")
                raise QuackFormatError(
                    resolved_path,
                    "YAML",
                    message=f"Error converting data to YAML: {str(e)}",
                    original_error=e,
                ) from e

            logger.debug(f"Writing YAML content to {resolved_path}")
            return self._write_text(resolved_path, yaml_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing YAML file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing YAML file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))

    # -------------------------------
    # JSON _operations
    # -------------------------------
    def _read_json(self, path: str | Path | DataResult | OperationResult) -> DataResult[dict[str, Any]]:
        """
        Read JSON file and parse its contents.

        This method reads a JSON file, parses it, and validates that
        it contains a dictionary (JSON object).

        Args:
            path: Path to JSON file (str, Path, DataResult, or OperationResult)

        Returns:
            DataResult[dict[str, Any]]: Result object containing:
                - success: Whether the operation was successful
                - path: The resolved file path
                - data: The parsed JSON data as a dictionary
                - format: "json"
                - error: Error message if operation failed

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(f"Reading JSON from: {resolved_path}")

        try:
            text_result = self._read_text(resolved_path)
            if not text_result.success:
                logger.error(f"Failed to read JSON file: {text_result.error}")
                raise QuackIOError(text_result.error, resolved_path)

            try:
                logger.debug("Parsing JSON content")
                data = json.loads(text_result.content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in {resolved_path}: {e}")
                raise QuackFormatError(
                    resolved_path,
                    "JSON",
                    message=f"Invalid JSON format: {str(e)}",
                    original_error=e,
                ) from e

            if not isinstance(data, dict):
                logger.error(
                    f"JSON content is not an object: {type(data)} in {resolved_path}"
                )
                raise QuackValidationError(
                    f"JSON content is not an object: {type(data)}", resolved_path
                )

            logger.info(
                f"Successfully parsed JSON data from {resolved_path} "
                f"with {len(data)} top-level keys"
            )

            # For backward compatibility with ReadResult.data
            # Create both a DataResult and update the original text_result
            text_result.data = data
            return DataResult(
                success=True,
                path=resolved_path,
                data=data,
                format="json",
                message=f"Successfully parsed JSON data "
                f"with {len(data)} top-level keys",
            )
        except (QuackFormatError, QuackValidationError, QuackIOError) as e:
            logger.error(f"Error reading JSON file {resolved_path}: {str(e)}")
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="json",
                error=str(e),
            )
        except Exception as e:
            logger.error(
                f"Unexpected error reading JSON file {resolved_path}: {str(e)}"
            )
            return DataResult(
                success=False,
                path=resolved_path,
                data={},
                format="json",
                error=str(e),
            )

    def _write_json(
        self,
        path: str | Path | DataResult | OperationResult,
        data: dict[str, Any],
        atomic: bool = True,
        indent: int = 2,
    ) -> WriteResult:
        """
        Write data to a JSON file.

        This method serializes a dictionary to JSON format and writes
        it to the specified file with optional formatting options.

        Args:
            path: Path to JSON file (str, Path, DataResult, or OperationResult)
            data: Dictionary data to write
            atomic: Whether to use atomic writing (safer but slower)
            indent: Number of spaces to indent (for readability)

        Returns:
            WriteResult: Result of the write operation

        Note:
            Internal helper method not meant for external consumption.
            Used by public-facing methods in the service layer.
        """
        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Writing JSON to: {resolved_path}, atomic={atomic}, indent={indent}"
        )

        try:
            try:
                logger.debug("Converting data to JSON format")
                json_content = json.dumps(
                    data,
                    indent=indent,
                    ensure_ascii=False,
                )
            except TypeError as e:
                logger.error(f"Error converting data to JSON: {e}")
                raise QuackFormatError(
                    resolved_path,
                    "JSON",
                    message=f"Error converting data to JSON: {str(e)}",
                    original_error=e,
                ) from e

            logger.debug(f"Writing JSON content to {resolved_path}")
            return self._write_text(resolved_path, json_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing JSON file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing JSON file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))
