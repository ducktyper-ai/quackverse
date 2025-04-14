# src/quackcore/fs/utils/__init__.py
"""
Utility functions for filesystem operations.

This module aggregates helper functions for working with the filesystem.
"""

from typing import TypeVar

# Instead of importing get_logger via the top-level logging package,
# we import it directly from our dedicated logger module.
from quackcore.logging.logger import get_logger

# Import all utility function submodules to preserve backward compatibility.
from .checksums import compute_checksum
from .common import get_extension, normalize_path
from .comparison import is_same_file, is_subdirectory
from .disk import get_disk_usage, is_path_writeable
from .file_info import (
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    is_file_locked,
)
from .file_ops import (
    atomic_write,
    ensure_directory,
    find_files_by_content,
    get_unique_filename,
)
from .path_ops import expand_user_vars, join_path, split_path
from .safe_ops import safe_copy, safe_delete, safe_move
from .temp import create_temp_directory, create_temp_file

# Lazily create module-level logger using our refactored get_logger.
logger = get_logger(__name__)

# Re-export TypeVar for backward compatibility.
T = TypeVar("T")

__all__ = [
    "T",
    "get_extension",
    "normalize_path",
    "is_same_file",
    "is_subdirectory",
    "get_disk_usage",
    "is_path_writeable",
    "get_file_size_str",
    "get_file_timestamp",
    "get_file_type",
    "get_mime_type",
    "is_file_locked",
    "atomic_write",
    "ensure_directory",
    "find_files_by_content",
    "get_unique_filename",
    "expand_user_vars",
    "join_path",
    "split_path",
    "safe_copy",
    "safe_delete",
    "safe_move",
    "create_temp_directory",
    "create_temp_file",
    "compute_checksum",
]
