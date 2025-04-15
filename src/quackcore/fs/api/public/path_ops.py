# src/quackcore/fs/api/public/path_ops.py
"""
Public API for path _operations.

This module provides safe, result-oriented wrappers around low-level path _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.common import _normalize_path
from quackcore.fs._helpers.comparison import _is_same_file, _is_subdirectory
from quackcore.fs._helpers.path_ops import _expand_user_vars, _split_path
from quackcore.fs.results import DataResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def split_path(path: str | Path) -> DataResult[list[str]]:
    """
    Split a path into its components.

    Args:
        path: Path to split

    Returns:
        DataResult with list of path components
    """
    try:
        components = _split_path(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=components,
            format="path_components",
            message=f"Successfully split path into {len(components)} components",
        )
    except Exception as e:
        logger.error(f"Failed to split path {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path) if isinstance(path, (str, Path)) else Path("."),
            data=[],
            format="path_components",
            error=str(e),
            message="Failed to split path",
        )


def expand_user_vars(path: str | Path) -> DataResult[str]:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables to expand

    Returns:
        DataResult with expanded path as string
    """
    try:
        expanded_path = _expand_user_vars(path)

        return DataResult(
            success=True,
            path=Path(path),
            data=str(expanded_path),
            format="path",
            message="Successfully expanded path variables",
        )
    except Exception as e:
        logger.error(f"Failed to expand user vars in path {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path) if isinstance(path, (str, Path)) else Path("."),
            data=str(path),
            format="path",
            error=str(e),
            message="Failed to expand path variables",
        )


def normalize_path(path: str | Path) -> DataResult[str]:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path to normalize

    Returns:
        DataResult with normalized path as string
    """
    try:
        path_obj = Path(path)  # Normalize early
        normalized_path = _normalize_path(path_obj)

        return DataResult(
            success=True,
            path=path_obj,
            data=str(normalized_path),
            format="path",
            message="Successfully normalized path",
        )
    except Exception as e:
        logger.error(f"Failed to normalize path {path}: {e}")
        return DataResult(
            success=False,
            path=Path(path) if isinstance(path, (str, Path)) else Path("."),
            data=str(path),
            format="path",
            error=str(e),
            message="Failed to normalize path",
        )


def is_same_file(path1: str | Path, path2: str | Path) -> DataResult[bool]:
    """
    Check if two paths refer to the same file.

    Args:
        path1: First path
        path2: Second path

    Returns:
        DataResult with boolean indicating if paths refer to the same file
    """
    try:
        result = _is_same_file(path1, path2)

        return DataResult(
            success=True,
            path=Path(path1),  # Use path1 as the primary path in the result
            data=result,
            format="boolean",
            message=f"Paths {path1} and {path2} {'refer to the same file' if result else 'refer to different files'}",
        )
    except Exception as e:
        logger.error(
            f"Failed to check if paths refer to the same file {path1}, {path2}: {e}"
        )
        return DataResult(
            success=False,
            path=Path(path1) if isinstance(path1, (str, Path)) else Path("."),
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check if paths refer to the same file",
        )


def is_subdirectory(child: str | Path, parent: str | Path) -> DataResult[bool]:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path
        parent: Potential parent path

    Returns:
        DataResult with boolean indicating if child is a subdirectory of parent
    """
    try:
        result = _is_subdirectory(child, parent)

        return DataResult(
            success=True,
            path=Path(child),  # Use child as the primary path in the result
            data=result,
            format="boolean",
            message=f"Path {child} {'is' if result else 'is not'} a subdirectory of {parent}",
        )
    except Exception as e:
        logger.error(f"Failed to check if {child} is a subdirectory of {parent}: {e}")
        return DataResult(
            success=False,
            path=Path(child) if isinstance(child, (str, Path)) else Path("."),
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check subdirectory relationship",
        )
