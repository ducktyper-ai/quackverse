# src/quackcore/fs/api/public/path_ops.py
"""
Public API for path _operations.

This module provides safe, result-oriented wrappers around low-level path _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.common import _normalize_path, _normalize_path_param
from quackcore.fs._helpers.comparison import _is_same_file, _is_subdirectory
from quackcore.fs._helpers.path_ops import _expand_user_vars, _split_path
from quackcore.fs.results import DataResult, OperationResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


def split_path(path: str | Path | DataResult | OperationResult) -> DataResult[
    list[str]]:
    """
    Split a path into its components.

    Args:
        path: Path to split (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with list of path components
    """
    try:
        normalized_path = _normalize_path_param(path)
        components = _split_path(normalized_path)

        return DataResult(
            success=True,
            path=normalized_path,
            data=components,
            format="path_components",
            message=f"Successfully split path into {len(components)} components",
        )
    except Exception as e:
        logger.error(f"Failed to split path {path}: {e}")
        normalized_path = _normalize_path_param(path)
        return DataResult(
            success=False,
            path=normalized_path,
            data=[],
            format="path_components",
            error=str(e),
            message="Failed to split path",
        )


def expand_user_vars(path: str | Path | DataResult | OperationResult) -> DataResult[
    str]:
    """
    Expand user variables and environment variables in a path.

    Args:
        path: Path with variables to expand (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with expanded path as string
    """
    try:
        normalized_path = _normalize_path_param(path)
        expanded_path = _expand_user_vars(normalized_path)

        return DataResult(
            success=True,
            path=normalized_path,
            data=str(expanded_path),
            format="path",
            message="Successfully expanded path variables",
        )
    except Exception as e:
        logger.error(f"Failed to expand user vars in path {path}: {e}")
        normalized_path = _normalize_path_param(path)
        return DataResult(
            success=False,
            path=normalized_path,
            data=str(path),
            format="path",
            error=str(e),
            message="Failed to expand path variables",
        )


def normalize_path(path: str | Path | DataResult | OperationResult) -> DataResult[str]:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path to normalize (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with normalized path as string
    """
    try:
        normalized_path = _normalize_path_param(path)
        normalized_result = _normalize_path(normalized_path)

        return DataResult(
            success=True,
            path=normalized_path,
            data=str(normalized_result),
            format="path",
            message="Successfully normalized path",
        )
    except Exception as e:
        logger.error(f"Failed to normalize path {path}: {e}")
        normalized_path = _normalize_path_param(path)
        return DataResult(
            success=False,
            path=normalized_path,
            data=str(path),
            format="path",
            error=str(e),
            message="Failed to normalize path",
        )


def is_same_file(path1: str | Path | DataResult | OperationResult,
                 path2: str | Path | DataResult | OperationResult) -> DataResult[bool]:
    """
    Check if two paths refer to the same file.

    Args:
        path1: First path (string, Path, DataResult, or OperationResult)
        path2: Second path (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if paths refer to the same file
    """
    try:
        normalized_path1 = _normalize_path_param(path1)
        normalized_path2 = _normalize_path_param(path2)
        result = _is_same_file(normalized_path1, normalized_path2)

        return DataResult(
            success=True,
            path=normalized_path1,  # Use path1 as the primary path in the result
            data=result,
            format="boolean",
            message=f"Paths {normalized_path1} and {normalized_path2} {'refer to the same file' if result else 'refer to different files'}",
        )
    except Exception as e:
        logger.error(
            f"Failed to check if paths refer to the same file {path1}, {path2}: {e}"
        )
        normalized_path1 = _normalize_path_param(path1)
        return DataResult(
            success=False,
            path=normalized_path1,
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check if paths refer to the same file",
        )


def is_subdirectory(child: str | Path | DataResult | OperationResult,
                    parent: str | Path | DataResult | OperationResult) -> DataResult[
    bool]:
    """
    Check if a path is a subdirectory of another path.

    Args:
        child: Potential child path (string, Path, DataResult, or OperationResult)
        parent: Potential parent path (string, Path, DataResult, or OperationResult)

    Returns:
        DataResult with boolean indicating if child is a subdirectory of parent
    """
    try:
        normalized_child = _normalize_path_param(child)
        normalized_parent = _normalize_path_param(parent)
        result = _is_subdirectory(normalized_child, normalized_parent)

        return DataResult(
            success=True,
            path=normalized_child,  # Use child as the primary path in the result
            data=result,
            format="boolean",
            message=f"Path {normalized_child} {'is' if result else 'is not'} a subdirectory of {normalized_parent}",
        )
    except Exception as e:
        logger.error(f"Failed to check if {child} is a subdirectory of {parent}: {e}")
        normalized_child = _normalize_path_param(child)
        return DataResult(
            success=False,
            path=normalized_child,
            data=False,
            format="boolean",
            error=str(e),
            message="Failed to check subdirectory relationship",
        )
