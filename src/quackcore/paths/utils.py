# src/quackcore/paths/utils.py
"""
Utility functions for path resolution.

This module provides utility functions for path resolution,
including functions for finding project roots and navigating directories.
"""

import os
from pathlib import Path
from typing import TypeVar

from quackcore.errors import QuackFileNotFoundError, wrap_io_errors

T = TypeVar("T")  # Generic type for flexible typing


@wrap_io_errors
def find_project_root(
    start_dir: str | Path | None = None,
    marker_files: list[str] | None = None,
    marker_dirs: list[str] | None = None,
    max_levels: int = 5,
) -> Path:
    """
    Find the project root directory by looking for marker files or directories.

    Args:
        start_dir: Directory to start searching from (default: current directory)
        marker_files: List of filenames that indicate a project root
        marker_dirs: List of directory names that indicate a project root
        max_levels: Maximum number of parent directories to check

    Returns:
        Path to the project root directory

    Raises:
        QuackFileNotFoundError: If project root cannot be found
    """
    if marker_files is None:
        marker_files = [
            "pyproject.toml",
            "setup.py",
            ".git",
            ".quack",
            "quack_config.yaml",
        ]

    if marker_dirs is None:
        marker_dirs = ["src", "quackcore", "tests"]

    # Start from current directory if not specified
    current_dir = Path(start_dir) if start_dir else Path.cwd()

    # Search up to max_levels parent directories
    for _ in range(max_levels):
        # Check if any marker files exist in this directory
        for marker in marker_files:
            if (current_dir / marker).exists():
                return current_dir

        # Check if any marker directories exist in this directory
        dir_markers_found = 0
        for marker in marker_dirs:
            if (current_dir / marker).is_dir():
                dir_markers_found += 1

        # If multiple directory markers are found, this is likely the project root
        if dir_markers_found >= 2:
            return current_dir

        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            # Reached filesystem root without finding project root
            break

        current_dir = parent_dir

    # Could not find project root
    raise QuackFileNotFoundError(
        str(start_dir or Path.cwd()),
        "Could not find project root directory. Please specify it explicitly.",
    )


@wrap_io_errors
def find_nearest_directory(
    name: str,
    start_dir: str | Path | None = None,
    max_levels: int = 5,
) -> Path:
    """
    Find the nearest directory with the given name.

    Args:
        name: Name of the directory to find
        start_dir: Directory to start searching from (default: current directory)
        max_levels: Maximum number of parent directories to check

    Returns:
        Path to the nearest directory with the given name

    Raises:
        QuackFileNotFoundError: If directory cannot be found
    """
    current_dir = Path(start_dir) if start_dir else Path.cwd()

    # First, check if the directory exists at or below the start directory
    for root, dirs, _ in os.walk(str(current_dir)):
        if name in dirs:
            return Path(root) / name

    # If not found, check parent directories
    for _ in range(max_levels):
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            # Reached filesystem root
            break

        current_dir = parent_dir

        if (current_dir / name).is_dir():
            return current_dir / name

    # Could not find directory
    raise QuackFileNotFoundError(
        str(name),
        f"Could not find directory '{name}' in or near {start_dir or Path.cwd()}",
    )


@wrap_io_errors
def resolve_relative_to_project(
    path: str | Path,
    project_root: str | Path | None = None,
) -> Path:
    """
    Resolve a path relative to the project root.

    Args:
        path: Path to resolve
        project_root: Project root directory (default: auto-detected)

    Returns:
        Resolved absolute path

    Raises:
        QuackFileNotFoundError: If project root cannot be found and path is relative
    """
    path_obj = Path(path)

    # If path is absolute, return it as is
    if path_obj.is_absolute():
        return path_obj

    # If project root is not specified, try to find it
    if project_root is None:
        try:
            project_root = find_project_root()
        except QuackFileNotFoundError:
            # If project root cannot be found, use current directory
            project_root = Path.cwd()

    # Resolve path relative to project root
    return Path(project_root) / path_obj


@wrap_io_errors
def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object
    """
    return Path(path).expanduser().resolve()


@wrap_io_errors
def join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    Args:
        *parts: Path parts to join

    Returns:
        Joined Path object
    """
    return Path(*parts)


@wrap_io_errors
def split_path(path: str | Path) -> list[str]:
    """
    Split a path into its components.

    Args:
        path: Path to split

    Returns:
        List of path components
    """
    parts = list(Path(path).parts)
    if str(path).startswith("./"):
        parts.insert(0, ".")
    return parts


def get_extension(path: str | Path) -> str:
    """
    Get the file extension from a path.

    Args:
        path: File path

    Returns:
        File extension without the dot
    """
    return Path(path).suffix.lstrip(".")


def infer_module_from_path(
    path: str | Path,
    project_root: str | Path | None = None,
) -> str:
    """
    Infer a Python module name from a file path.

    Args:
        path: Path to the Python file
        project_root: Project root directory (default: auto-detected)

    Returns:
        Python module name
    """
    path_obj = Path(path)

    # Get project root if not specified
    if project_root is None:
        try:
            project_root = find_project_root()
        except QuackFileNotFoundError:
            # If project root cannot be found, use current directory
            project_root = Path.cwd()

    project_root = Path(project_root)

    # Make path absolute if it's not already
    if not path_obj.is_absolute():
        path_obj = project_root / path_obj

    # Try to find the source directory
    try:
        src_dir = find_nearest_directory("src", project_root)
    except QuackFileNotFoundError:
        # If source directory cannot be found, use the path's directory
        src_dir = path_obj.parent

    # Check if the path is within the source directory
    try:
        rel_path = path_obj.relative_to(src_dir)
    except ValueError:
        # If path is not within the source directory,
        # use the path relative to project root
        try:
            rel_path = path_obj.relative_to(project_root)
        except ValueError:
            # If path is not within the project root,
            # use the path's name without extension
            return path_obj.stem

    # Create module name from path
    parts = list(rel_path.parts)

    # Remove file extension from the last part if it's a file
    if parts and "." in parts[-1]:
        parts[-1] = parts[-1].split(".", 1)[0]

    # Filter out parts that are not valid Python identifiers
    parts = [p for p in parts if p and not p.startswith("__")]

    # Join parts with dots to create a module name
    return ".".join(parts)
