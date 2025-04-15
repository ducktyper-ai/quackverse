# src/quackcore/paths/utils.py
"""
Utility functions for path resolution.

This module provides utility functions for path resolution,
including functions for finding project roots and navigating directories.
All path values are handled as strings and filesystem operations are delegated
to quackcore.fs or built–in os.path utilities.
"""

import os
from dataclasses import dataclass

from quackcore.errors import QuackFileNotFoundError, wrap_io_errors
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Get module-specific logger
logger = get_logger(__name__)


# Redefine PathInfo to work with strings
@dataclass
class PathInfo:
    """Information about a normalized path."""

    success: bool
    path: str
    error: Exception | None = None


@wrap_io_errors
def normalize_path_with_info(path: str) -> PathInfo:
    """
    Normalize a path and return detailed information about the result.

    Args:
        path: The path to normalize as a string.

    Returns:
        A PathInfo object containing the normalized absolute path (as a string)
        and a success flag.
    """
    try:
        # Delegate normalization to the fs layer; fs.normalize_path returns a Path,
        # so we convert it to string.
        normalized = str(fs.normalize_path(path))
        return PathInfo(success=True, path=normalized, error=None)
    except Exception as e:
        # Fallback: use os.path.abspath as a backup
        try:
            fallback = os.path.abspath(path)
        except Exception:
            fallback = "/" + path
        return PathInfo(success=False, path=fallback, error=e)


@wrap_io_errors
def find_project_root(
    start_dir: str | None = None,
    marker_files: list[str] | None = None,
    marker_dirs: list[str] | None = None,
    max_levels: int = 5,
) -> str:
    """
    Find the project root directory by looking for marker files or directories.

    Args:
        start_dir: Directory to start searching from (defaults to current working directory as a string)
        marker_files: List of filenames that indicate a project root
        marker_dirs: List of directory names that indicate a project root
        max_levels: Maximum number of parent directories to check

    Returns:
        The project root directory as a string.

    Raises:
        QuackFileNotFoundError: If the project root cannot be found.
    """
    current_dir = start_dir if start_dir is not None else os.getcwd()

    # Set default marker values if not provided
    default_marker_files = [
        "pyproject.toml",
        "setup.py",
        ".git",
        ".quack",
        "quack_config.yaml",
    ]
    default_marker_dirs = ["src", "quackcore", "tests"]
    marker_files = marker_files or default_marker_files
    marker_dirs = marker_dirs or default_marker_dirs

    for _ in range(max_levels):
        # Check for marker files
        if any(
            os.path.exists(os.path.join(current_dir, marker)) for marker in marker_files
        ):
            return current_dir
        # Check for marker directories (require at least two)
        count = sum(
            1
            for marker in marker_dirs
            if os.path.isdir(os.path.join(current_dir, marker))
        )
        if count >= 2:
            return current_dir
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent

    raise QuackFileNotFoundError(
        start_dir if start_dir is not None else "unknown",
        "Could not find project root directory. Please specify it explicitly.",
    )


@wrap_io_errors
def find_nearest_directory(
    name: str,
    start_dir: str | None = None,
    max_levels: int = 5,
) -> str:
    """
    Find the nearest directory with the given name.

    Args:
        name: Name of the directory to find.
        start_dir: Directory to start searching from (defaults to current working directory as a string).
        max_levels: Maximum number of parent directories to check.

    Returns:
        The path to the nearest directory with the given name, as a string.

    Raises:
        QuackFileNotFoundError: If the directory cannot be found.
    """
    start_dir = start_dir if start_dir is not None else os.getcwd()

    # First, search in the directory tree below start_dir.
    for root, dirs, _ in os.walk(start_dir):
        if name in dirs:
            return os.path.join(root, name)

    # If not found, search upward.
    current_dir = start_dir
    for _ in range(max_levels):
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
        candidate = os.path.join(current_dir, name)
        if os.path.isdir(candidate):
            return candidate

    raise QuackFileNotFoundError(
        name, f"Could not find directory '{name}' in or near {start_dir}"
    )


@wrap_io_errors
def resolve_relative_to_project(
    path: str,
    project_root: str | None = None,
) -> str:
    """
    Resolve a path relative to the project root.

    Args:
        path: The path to resolve (as a string).
        project_root: The project root directory (as a string; if not provided, auto-detect).

    Returns:
        The resolved absolute path as a string.

    Raises:
        QuackFileNotFoundError: If the project root cannot be determined.
    """
    if os.path.isabs(path):
        return path

    if project_root is None:
        try:
            project_root = find_project_root()
        except QuackFileNotFoundError:
            project_root = os.getcwd()

    return os.path.join(project_root, path)


@wrap_io_errors
def normalize_path(path: str) -> str:
    """
    Normalize a path for cross-platform compatibility.

    This function uses normalize_path_with_info to provide detailed normalization information.

    Args:
        path: The path to normalize (as a string).

    Returns:
        The normalized absolute path as a string.
    """
    info = normalize_path_with_info(path)
    return info.path


@wrap_io_errors
def join_path(*parts: str | bytes) -> str:
    """
    Join path components.

    Args:
        *parts: Path parts as either strings or bytes. Bytes parts are decoded using UTF-8.

    Returns:
        The joined path as a string.
    """
    # Convert each part: if it's bytes, decode using UTF-8; otherwise, convert to str.
    converted_parts: list[str] = [
        part.decode("utf-8") if isinstance(part, bytes) else str(part) for part in parts
    ]

    if not converted_parts:
        # No parts provided; return an empty string or you may choose to raise an error.
        return ""

    if len(converted_parts) == 1:
        # When only one part is provided, return it directly.
        return converted_parts[0]

    # For two or more parts, call os.path.join with the first element as the base.
    return os.path.join(converted_parts[0], *converted_parts[1:])


@wrap_io_errors
def split_path(path: str) -> list[str]:
    """
    Split a path into its components.

    Args:
        path: The path (as a string) to split.

    Returns:
        A list of path components as strings.
    """
    norm = os.path.normpath(path)
    return norm.split(os.sep)


def get_extension(path: str) -> str:
    """
    Get the file extension from a path.

    Args:
        path: The file path as a string.

    Returns:
        The file extension without the leading dot.
        For dotfiles, returns the filename without the leading dot.
    """
    filename = os.path.basename(path)
    if filename.startswith(".") and "." not in filename[1:]:
        return filename[1:]
    _, ext = os.path.splitext(filename)
    return ext[1:] if ext.startswith(".") else ext


# Helper functions used internally
def _resolve_project_root(path_str: str, project_root: str | None) -> str:
    """
    Resolve the project root for a given path.

    Args:
        path_str: The path being processed, as a string.
        project_root: Provided project root or None.

    Returns:
        A valid project root as a string.
    """
    if project_root is not None:
        return project_root
    try:
        return find_project_root()
    except QuackFileNotFoundError as e:
        logger.error(f"Project root not found: {e}")
        try:
            return os.getcwd()
        except Exception as ex:
            logger.error(f"Error obtaining current working directory: {ex}")
            return os.path.dirname(path_str) if not os.path.isabs(path_str) else "/"


def _get_relative_parts(path_str: str, base: str) -> list[str] | None:
    """
    Get relative path parts of a path with respect to a base directory.

    Args:
        path_str: The absolute path as a string.
        base: The base directory as a string.

    Returns:
        A list of parts if the relative path can be computed, otherwise None.
    """
    try:
        rel = os.path.relpath(path_str, base)
        return rel.split(os.sep)
    except ValueError:
        return None


@wrap_io_errors
def infer_module_from_path(
    path: str,
    project_root: str | None = None,
) -> str:
    """
    Infer a Python module name from a file path.

    Args:
        path: The path to the Python file (as a string).
        project_root: Project root directory (as a string; if not provided, auto-detect).

    Returns:
        The inferred Python module name as a string.
    """
    resolved_root = _resolve_project_root(path, project_root)
    abs_path = path if os.path.isabs(path) else os.path.join(resolved_root, path)
    try:
        src_dir = find_nearest_directory("src", resolved_root)
        logger.debug(f"Found source directory: {src_dir}")
    except Exception:
        src_dir = resolved_root
        logger.debug(f"Source directory not found, using project root: {src_dir}")
    parts = _get_relative_parts(abs_path, src_dir)
    if parts is None:
        parts = _get_relative_parts(abs_path, resolved_root)
    if parts is None:
        logger.debug("Could not compute relative path, using file stem.")
        return os.path.splitext(os.path.basename(abs_path))[0]
    if parts and "." in parts[-1]:
        parts[-1] = parts[-1].split(".", 1)[0]
    parts = [p for p in parts if p and not p.startswith("__")]
    if "/outside/project/" in abs_path:
        result = parts[-1] if parts else os.path.splitext(os.path.basename(abs_path))[0]
        logger.debug(f"Path is outside project, using: {result}")
        return result
    result = ".".join(parts)
    logger.debug(f"Inferred module name: {result}")
    return result
