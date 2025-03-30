# src/quackcore/fs/utils/common.py
"""
Common utility functions for filesystem operations.
"""

from pathlib import Path

from quackcore.errors import wrap_io_errors
from quackcore.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)


def get_extension(path: str | Path) -> str:
    """
    Get the file extension from a path.

    Args:
        path: File path

    Returns:
        File extension without the dot
    """
    path_obj = Path(path)
    filename = path_obj.name

    # Special case for dotfiles
    if filename.startswith(".") and "." not in filename[1:]:
        return filename[1:]  # Return everything after the first dot for dotfiles

    return path_obj.suffix.lstrip(".")


@wrap_io_errors
def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path for cross-platform compatibility.

    This does not check if the path exists.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object
    """
    path_obj = Path(path).expanduser()

    # If path is already absolute, no need for getcwd() which might fail
    if path_obj.is_absolute():
        return path_obj

    try:
        # Try to make it absolute or resolve it
        if not path_obj.exists():
            return path_obj.absolute()
        return path_obj.resolve()
    except (FileNotFoundError, OSError) as e:
        # If any OS error occurs (including getcwd() failing),
        # just return the path as is, with a warning
        logger.warning(f"Could not normalize path '{path}': {str(e)}")
        return path_obj