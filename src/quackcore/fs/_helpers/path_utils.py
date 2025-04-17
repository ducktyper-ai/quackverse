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
