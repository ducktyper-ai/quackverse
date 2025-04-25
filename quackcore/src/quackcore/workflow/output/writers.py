# quackcore/workflow/output/writers.py
"""
Implementation of OutputWriter classes for various file formats.

This module provides concrete implementations of the OutputWriter abstract
base class for writing data to different file formats, such as JSON and YAML.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quackcore.workflow.output.base import OutputWriter
from quackcore.fs.service import get_service

# Try importing yaml, set to None if not available
try:
    import yaml
except ImportError:
    yaml = None


class DefaultOutputWriter(OutputWriter):
    """
    Default output writer that saves data as JSON.

    This writer serializes data to JSON format and ensures the output
    file has the correct extension.
    """

    def __init__(self, indent: int = 2) -> None:
        """
        Initialize a DefaultOutputWriter instance.

        Args:
            indent: Number of spaces for JSON indentation (default: 2)
        """
        self._extension = ".json"
        self._indent = indent

    def get_extension(self) -> str:
        """
        Get the file extension for JSON files.

        Returns:
            The '.json' file extension
        """
        return self._extension

    def validate_data(self, data: Any) -> bool:
        """
        Validate that the data can be serialized to JSON.

        Args:
            data: The data to validate

        Returns:
            True if the data is valid for JSON serialization

        Raises:
            ValueError: If the data cannot be serialized to JSON
        """
        if not isinstance(data, (dict, list)):
            raise ValueError("DefaultOutputWriter expects dict or list data types")

        # Try to serialize to ensure it's JSON-compatible
        try:
            json.dumps(data)
            return True
        except (TypeError, OverflowError, ValueError) as e:
            raise ValueError(
                f"Data cannot be serialized to JSON. Offending type: {type(data)}. Error: {str(e)}")

    def write_output(self, data: Any, output_path: str | Path) -> str:
        """
        Write data to a JSON file at the specified path.

        Args:
            data: The data to write (must be JSON-serializable)
            output_path: The path where the output should be saved

        Returns:
            The actual path where the data was written

        Raises:
            ValueError: If the data is not valid for JSON serialization
            RuntimeError: If the write operation fails
        """
        # Validate the data first
        self.validate_data(data)

        # Convert Path to string if needed
        if isinstance(output_path, Path):
            output_path = str(output_path)

        # Ensure the path has the correct extension
        if not output_path.endswith(self._extension):
            output_path = f"{output_path}{self._extension}"

        # Get the filesystem service
        fs = get_service()

        # Write the data
        result = fs.write_json(output_path, data, indent=self._indent)

        # Check if the write operation was successful
        if not result.success:
            raise RuntimeError(f"Failed to write output: {result.error}")

        return str(result.path)


class YAMLOutputWriter(OutputWriter):
    """
    Output writer that saves data as YAML.

    This writer serializes data to YAML format and ensures the output
    file has the correct extension.
    """

    def __init__(self, default_flow_style: bool = False) -> None:
        """
        Initialize a YAMLOutputWriter instance.

        Args:
            default_flow_style: Use flow style for collections if True (default: False)

        Note:
            This writer requires PyYAML to be installed.
        """
        self._extension = ".yaml"
        self._default_flow_style = default_flow_style

    def get_extension(self) -> str:
        """
        Get the file extension for YAML files.

        Returns:
            The '.yaml' file extension
        """
        return self._extension

    def validate_data(self, data: Any) -> bool:
        """
        Validate that the data can be serialized to YAML.

        Args:
            data: The data to validate

        Returns:
            True if the data is valid for YAML serialization

        Raises:
            ValueError: If the data cannot be serialized to YAML
            ImportError: If PyYAML is not available
        """
        if yaml is None:
            raise ImportError("PyYAML is required for YAMLOutputWriter")

        if not isinstance(data, (dict, list)):
            raise ValueError("YAMLOutputWriter expects dict or list data types")

        # Try to serialize to ensure it's YAML-compatible
        try:
            yaml.dump(data)
            return True
        except yaml.YAMLError as e:
            raise ValueError(
                f"Data cannot be serialized to YAML. Offending type: {type(data)}. Error: {str(e)}")

    def write_output(self, data: Any, output_path: str | Path) -> str:
        """
        Write data to a YAML file at the specified path.

        Args:
            data: The data to write (must be YAML-serializable)
            output_path: The path where the output should be saved

        Returns:
            The actual path where the data was written

        Raises:
            ValueError: If the data is not valid for YAML serialization
            RuntimeError: If the write operation fails
            ImportError: If PyYAML is not available
        """
        # Validate the data first
        self.validate_data(data)

        # Convert Path to string if needed
        if isinstance(output_path, Path):
            output_path = str(output_path)

        # Ensure the path has the correct extension
        if not output_path.endswith(self._extension):
            output_path = f"{output_path}{self._extension}"

        # Get the filesystem service
        fs = get_service()

        # Convert data to YAML
        yaml_text = yaml.dump(data, default_flow_style=self._default_flow_style)

        # Write the data
        result = fs.write_text(output_path, yaml_text)

        # Check if the write operation was successful
        if not result.success:
            raise RuntimeError(f"Failed to write output: {result.error}")

        return str(result.path)