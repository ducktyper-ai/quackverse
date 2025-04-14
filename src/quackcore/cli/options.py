# src/quackcore/cli/options.py
"""
CLI options and argument processing utilities.

This module provides data models and utilities for handling command-line
arguments and options in a consistent way across QuackCore CLI tools.
"""

from collections.abc import Sequence
from typing import Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # Generic type for flexible typing

# Define LogLevel type for better type checking
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class CliOptions(BaseModel):
    """
    CLI options that can affect bootstrapping behavior.

    This model represents command-line options that can override configuration
    and control runtime behavior like logging and debugging.
    """

    # Instead of using pathlib.Path, we use str here.
    config_path: str | None = Field(
        default=None, description="Path to configuration file"
    )
    log_level: LogLevel | None = Field(default=None, description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress non-error output")
    environment: str | None = Field(
        default=None, description="Override the environment"
    )
    base_dir: str | None = Field(
        default=None, description="Override the base directory"
    )
    no_color: bool = Field(default=False, description="Disable colored output")

    model_config = {
        "frozen": True,
        "extra": "ignore",
    }


def resolve_cli_args(args: Sequence[str]) -> dict[str, object]:
    """
    Parse common CLI arguments into a dictionary.

    This function is useful for libraries that want to handle standard
    QuackCore CLI arguments without using a full argument parser.

    Args:
        args: Sequence of command-line arguments

    Returns:
        Dictionary of parsed arguments
    """
    result: dict[str, object] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            name = arg[2:]
            if "=" in name:
                name, value = name.split("=", 1)
                result[name] = value
                i += 1
                continue
            if name in ("debug", "verbose", "quiet", "no-color"):
                result[name] = True
                i += 1
                continue
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                result[name] = args[i + 1]
                i += 2
                continue
            result[name] = True
            i += 1
            continue
        elif arg.startswith("-") and len(arg) == 2:
            flag_map = {"d": "debug", "v": "verbose", "q": "quiet"}
            name = flag_map.get(arg[1], arg[1])
            result[name] = True
            i += 1
            continue
        i += 1
    return result
