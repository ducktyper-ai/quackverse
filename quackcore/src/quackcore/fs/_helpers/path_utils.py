# quackcore/src/quackcore/fs/_helpers/path_utils.py
"""
Path utility functions that don't introduce circular dependencies.
"""

from pathlib import Path
from typing import Any

from quackcore.logging import get_logger

logger = get_logger(__name__)

def _normalize_path_param(path: Any) -> Path:
    """
    Normalize a path parameter to a Path object.
    
    Helper function to consistently handle different path input types,
    including DataResult and OperationResult objects.
    
    Args:
        path: Path parameter (string, Path, or any object with a 'data' attribute)
        
    Returns:
        Normalized Path object
    """
    # Check if it's a DataResult-like object with a data attribute
    if hasattr(path, "data"):
        path_content = path.data
    else:
        path_content = path

    try:
        return Path(path_content)
    except TypeError:
        return Path(str(path_content))


def extract_path_from_result(result_obj: Any) -> str | Path:
    """
    Extract a path from any result object or path-like object.

    This function handles all types of result objects (PathResult, DataResult,
    OperationResult) and extracts the actual path component for use in path operations.

    Args:
        result_obj: Any object that might contain a path

    Returns:
        The extracted path as a string or Path object
    """
    # Handle PathResult objects (with 'path' attribute)
    if hasattr(result_obj, "path") and result_obj.path is not None:
        return result_obj.path

    # Handle DataResult objects (with 'data' attribute)
    if hasattr(result_obj, "data") and result_obj.data is not None:
        data_content = result_obj.data
        # If data itself is a path-like, return it
        if hasattr(data_content, "__fspath__") or isinstance(data_content, str):
            return data_content

    # Handle path-like objects directly
    if hasattr(result_obj, "__fspath__"):
        return result_obj

    # Handle string paths
    if isinstance(result_obj, str):
        return result_obj

    # Last resort: try string conversion
    return str(result_obj)
