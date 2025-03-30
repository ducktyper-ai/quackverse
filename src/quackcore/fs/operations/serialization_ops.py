# src/quackcore/fs/operations/serialization_ops.py
"""
Serialization operations (JSON, YAML) for filesystem operations.
"""

import json
from pathlib import Path

from quackcore.errors import (
    QuackFormatError,
    QuackIOError,
    QuackValidationError,
)
from quackcore.fs.results import DataResult, WriteResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    logger.warning("PyYAML library not found. YAML operations will not be available.")
    YAML_AVAILABLE = False


class SerializationOperationsMixin:
    """Serialization operations mixin class."""

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the base directory."""
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def read_text(self, path: str | Path, encoding: str = "utf-8"):
        """Read text from a file."""
        # This method is implemented in ReadOperationsMixin
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def write_text(
            self, path: str | Path, content: str, encoding: str = "utf-8", **kwargs
    ):
        """Write text to a file."""
        # This method is implemented in WriteOperationsMixin
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    # -------------------------------
    # YAML operations
    # -------------------------------
    def read_yaml(self, path: str | Path) -> DataResult[dict]:
        """
        Read YAML file and parse its contents.

        Args:
            path: Path to YAML file

        Returns:
            DataResult with parsed YAML data
        """
        if not YAML_AVAILABLE:
            error_msg = "PyYAML library not available. Cannot read YAML file."
            logger.error(error_msg)
            return DataResult(
                success=False,
                path=self.resolve_path(path),
                data={},
                format="yaml",
                error=error_msg,
            )

        resolved_path = self.resolve_path(path)
        logger.debug(f"Reading YAML from: {resolved_path}")

        try:
            text_result = self.read_text(resolved_path)
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

    def write_yaml(
            self, path: str | Path, data: dict, atomic: bool = True
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
        if not YAML_AVAILABLE:
            error_msg = "PyYAML library not available. Cannot write YAML file."
            logger.error(error_msg)
            return WriteResult(
                success=False,
                path=self.resolve_path(path),
                error=error_msg
            )

        resolved_path = self.resolve_path(path)
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
            return self.write_text(resolved_path, yaml_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing YAML file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing YAML file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))

    # -------------------------------
    # JSON operations
    # -------------------------------
    def read_json(self, path: str | Path) -> DataResult[dict]:
        """
        Read JSON file and parse its contents.

        Args:
            path: Path to JSON file

        Returns:
            DataResult with parsed JSON data
        """
        resolved_path = self.resolve_path(path)
        logger.debug(f"Reading JSON from: {resolved_path}")

        try:
            text_result = self.read_text(resolved_path)
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
        resolved_path = self.resolve_path(path)
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
            return self.write_text(resolved_path, json_content, atomic=atomic)
        except (QuackFormatError, QuackIOError) as e:
            logger.error(f"Error writing JSON file {resolved_path}: {str(e)}")
            return WriteResult(success=False, path=resolved_path, error=str(e))
        except Exception as e:
            logger.error(
                f"Unexpected error writing JSON file {resolved_path}: {str(e)}"
            )
            return WriteResult(success=False, path=resolved_path, error=str(e))