# quackcore/src/quackcore/fs/api/public/path_ops.py
"""
Public API for path _operations.

This module provides safe, result-oriented wrappers around low-level path _operations.
"""

from pathlib import Path

from quackcore.fs._helpers.common import _normalize_path
from quackcore.fs._helpers.comparison import _is_same_file, _is_subdirectory
from quackcore.fs._helpers.path_ops import _expand_user_vars, _split_path
from quackcore.fs._helpers.path_utils import _normalize_path_param
from quackcore.fs.results import DataResult, OperationResult, PathResult
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


def normalize_path(path: str | Path | DataResult | OperationResult) -> PathResult:
    """
    Normalize a path for cross-platform compatibility.

    Args:
        path: Path to normalize (string, Path, DataResult, or OperationResult)

    Returns:
        PathResult with normalized path and metadata
    """
    try:
        # Ensure we have a raw Path or string
        normalized_input = _normalize_path_param(path)
        # Perform the normalization
        normalized = _normalize_path(normalized_input)
        # Gather metadata
        is_abs = normalized.is_absolute()
        exists = normalized.exists()

        return PathResult(
            success=True,
            path=normalized,
            is_absolute=is_abs,
            is_valid=True,
            exists=exists,
            message="Successfully normalized path",
        )
    except Exception as e:
        logger.error(f"Failed to normalize path {path}: {e}")
        # Attempt to normalize input for error reporting
        normalized_input = _normalize_path_param(path)
        return PathResult(
            success=False,
            path=normalized_input,
            is_absolute=False,
            is_valid=False,
            exists=False,
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


def extract_path_from_result(
        path_or_result: str | Path | DataResult | OperationResult) -> DataResult[str]:
    """
    Extract a path string from any result object or path-like object.

    This function handles all types of result objects (PathResult, DataResult,
    OperationResult) and extracts the actual path component for use in path operations.

    Args:
        path_or_result: Any object that might contain a path (string, Path, DataResult,
                        OperationResult, PathResult, or any path-like object)

    Returns:
        DataResult with the extracted path as a string
    """
    try:
        from quackcore.fs._helpers.path_utils import (
            extract_path_from_result as _extract_path_impl,
        )

        extracted_path = _extract_path_impl(path_or_result)
        normalized_path = _normalize_path_param(path_or_result)

        return DataResult(
            success=True,
            path=normalized_path,
            data=str(extracted_path),
            format="path",
            message="Successfully extracted path from result",
        )
    except Exception as e:
        logger.error(f"Failed to extract path from result {path_or_result}: {e}")

        # Try to get a normalized path for the error report
        try:
            normalized_path = _normalize_path_param(path_or_result)
        except:
            normalized_path = Path()

        return DataResult(
            success=False,
            path=normalized_path,
            data=str(path_or_result),
            format="path",
            error=str(e),
            message="Failed to extract path from result",
        )
