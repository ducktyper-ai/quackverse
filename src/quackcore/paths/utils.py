# src/quackcore/paths/utils.py
"""
Utility functions for path resolution.

This module provides utility functions for path resolution,
including functions for finding project roots and navigating directories.
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field

from quackcore.errors import QuackFileNotFoundError, wrap_io_errors
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Get module-specific logger
logger = get_logger(__name__)


class ProjectConfig(BaseModel):
    """Configuration model for project detection."""

    marker_files: list[str] = Field(
        default_factory=lambda: [
            "pyproject.toml",
            "setup.py",
            ".git",
            ".quack",
            "quack_config.yaml",
        ],
        description="Files that indicate a project root",
    )

    marker_dirs: list[str] = Field(
        default_factory=lambda: [
            "src",
            "quackcore",
            "tests",
        ],
        description="Directories that indicate a project root",
    )

    max_levels: int = Field(
        default=5,
        description="Maximum number of parent directories to check"
    )


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
    if marker_files is None or marker_dirs is None:
        config = ProjectConfig()
        marker_files = marker_files or config.marker_files
        marker_dirs = marker_dirs or config.marker_dirs

    # Safely get the current directory, with fallback to a known directory
    try:
        current_dir = Path(start_dir) if start_dir else Path.cwd()
    except (FileNotFoundError, OSError):
        # Fallback to home directory if current directory doesn't exist
        current_dir = Path.home()
        logger.warning(
            f"Current working directory not found, falling back to {current_dir}"
        )

    for _ in range(max_levels):
        # Check for marker files in the current directory.
        if any((current_dir / marker).exists() for marker in marker_files):
            return current_dir

        # Check for marker directories: if two or more are found, assume project root.
        dir_markers_found = sum(
            1 for marker in marker_dirs if (current_dir / marker).is_dir()
        )
        if dir_markers_found >= 2:
            return current_dir

        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break  # Reached filesystem root.
        current_dir = parent_dir

    raise QuackFileNotFoundError(
        str(start_dir or "unknown"),
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

    # First, search within the current directory and its subdirectories.
    for root, dirs, _ in os.walk(str(current_dir)):
        if name in dirs:
            return Path(root) / name

    # If not found, search upward through parent directories.
    for _ in range(max_levels):
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break  # Reached filesystem root.
        current_dir = parent_dir
        if (current_dir / name).is_dir():
            return current_dir / name

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
    if path_obj.is_absolute():
        return path_obj

    if project_root is None:
        try:
            project_root = find_project_root()
        except QuackFileNotFoundError:
            project_root = Path.cwd()

    return Path(project_root) / path_obj


@wrap_io_errors
def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    This function uses fs.normalize_path to ensure consistent behavior
    with quackcore.fs module.

    Args:
        path: Path to normalize

    Returns:
        Normalized absolute Path object.
    """
    return fs.normalize_path(path)


@wrap_io_errors
def join_path(*parts: str | Path) -> Path:
    """
    Join path components.

    This function uses fs.join_path to ensure consistent behavior
    with quackcore.fs module.

    Args:
        *parts: Path parts to join

    Returns:
        Joined Path object
    """
    return fs.join_path(*parts)


@wrap_io_errors
def split_path(path: str | Path) -> list[str]:
    """
    Split a path into its components.

    This function uses fs.split_path to ensure consistent behavior
    with quackcore.fs module.

    Args:
        path: Path to split

    Returns:
        List of path components
    """
    return fs.split_path(path)


def get_extension(path: str | Path) -> str:
    """
    Get the file extension from a path.

    This function uses fs.get_extension to ensure consistent behavior
    with quackcore.fs module.

    Args:
        path: File path

    Returns:
        File extension without the dot.
        For dotfiles, the extension is the filename without the leading dot.
    """
    return fs.get_extension(path)


def _resolve_project_root(path_obj: Path, project_root: str | Path | None) -> Path:
    """
    Resolve the project root.

    Args:
        path_obj: The path being processed.
        project_root: Provided project root or None.

    Returns:
        A valid project root Path.
    """
    if project_root is not None:
        return Path(project_root)
    try:
        return find_project_root()
    except QuackFileNotFoundError as e:
        logger.error(f"Project root not found: {e}")
        try:
            return Path.cwd()
        except Exception as ex:
            logger.error(f"Error obtaining current working directory: {ex}")
            return path_obj.parent if not path_obj.is_absolute() else Path("/")


def _get_relative_parts(path_obj: Path, base: Path) -> list[str] | None:
    """
    Get relative path parts of path_obj with respect to base.

    Args:
        path_obj: The absolute path.
        base: The base directory to compute the relative path from.

    Returns:
        List of parts if the relative path can be computed, otherwise None.
    """
    try:
        return list(path_obj.relative_to(base).parts)
    except ValueError:
        return None


@wrap_io_errors
def infer_module_from_path(
        path: str | Path,
        project_root: str | Path | None = None,
) -> str:
    """
    Infer a Python module name from a file path.

    Args:
        path: Path to the Python file.
        project_root: Project root directory (default: auto-detected).

    Returns:
        Python module name.
    """
    path_obj = Path(path)
    resolved_root = _resolve_project_root(path_obj, project_root)

    # Ensure the path is absolute.
    if not path_obj.is_absolute():
        path_obj = resolved_root / path_obj
        logger.debug(f"Converted relative path to absolute: {path_obj}")

    # Attempt to find the source directory ("src") within the project.
    try:
        src_dir = find_nearest_directory("src", resolved_root)
        logger.debug(f"Found source directory: {src_dir}")
    except QuackFileNotFoundError:
        src_dir = resolved_root
        logger.debug(f"Source directory not found, using project root: {src_dir}")

    parts = _get_relative_parts(path_obj, src_dir)
    if parts is None:
        parts = _get_relative_parts(path_obj, resolved_root)
    if parts is None:
        logger.debug(
            f"Could not compute relative path, using file stem: {path_obj.stem}"
        )
        return path_obj.stem

    # Remove file extension from the last part if it's a file.
    if parts and "." in parts[-1]:
        parts[-1] = parts[-1].split(".", 1)[0]

    # Filter out parts that are not valid (e.g. parts starting with '__').
    parts = [p for p in parts if p and not p.startswith("__")]

    # Special handling for paths outside the project.
    if "/outside/project/" in str(path_obj):
        result = parts[-1] if parts else path_obj.stem
        logger.debug(f"Path is outside project, using: {result}")
        return result

    result = ".".join(parts)
    logger.debug(f"Inferred module name: {result}")
    return result