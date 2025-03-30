# src/quackcore/fs/utils/__init__.py
"""
Utility functions for filesystem operations.

This module provides helper functions for common filesystem tasks
and utilities for working with file formats.
"""

# Import TypeVar for backward compatibility
from typing import TypeVar

# Import the logger
from quackcore.logging import get_logger

# Import all functions from submodules to maintain backward compatibility
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

# Get module-level logger
logger = get_logger(__name__)

# Re-export TypeVar T for backward compatibility
T = TypeVar("T")  # Generic type for flexible typing

# Re-export everything for backward compatibility
__all__ = [
    # TypeVar
    "T",
    # Common utilities
    "get_extension",
    "normalize_path",
    # Comparison
    "is_same_file",
    "is_subdirectory",
    # Disk operations
    "get_disk_usage",
    "is_path_writeable",
    # File information
    "get_file_size_str",
    "get_file_timestamp",
    "get_file_type",
    "get_mime_type",
    "is_file_locked",
    # File operations
    "atomic_write",
    "ensure_directory",
    "find_files_by_content",
    "get_unique_filename",
    # Path operations
    "expand_user_vars",
    "join_path",
    "split_path",
    # Safe operations
    "safe_copy",
    "safe_delete",
    "safe_move",
    # Temporary files/directories
    "create_temp_directory",
    "create_temp_file",
]