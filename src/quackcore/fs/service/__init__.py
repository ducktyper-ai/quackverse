"""
FileSystemService provides a high-level interface for filesystem operations.

This service layer abstracts underlying filesystem operations and provides
a clean, consistent API for all file operations in QuackCore.
"""

from typing import TypeVar

# Import the main service class
from .base import FileSystemService

# Import utility functions to re-export for backward compatibility
from quackcore.fs.utils import (
    atomic_write,
    compute_checksum,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    expand_user_vars,
    find_files_by_content,
    get_disk_usage,
    get_extension,
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
    is_same_file,
    is_subdirectory,
    join_path,
    normalize_path,
    split_path,
)

# Re-export module-level functions from the original service module
from .utility_ops import create_directory, get_file_info, read_yaml

T = TypeVar("T")  # Generic type for flexible typing

# Re-export everything for backward compatibility
__all__ = [
    # Main class
    "FileSystemService",

    # Module-level utility functions
    "create_directory",
    "get_file_info",
    "read_yaml",

    # Re-exported utility functions from quackcore.fs.utils
    "atomic_write",
    "compute_checksum",
    "create_temp_directory",
    "create_temp_file",
    "ensure_directory",
    "expand_user_vars",
    "find_files_by_content",
    "get_disk_usage",
    "get_extension",
    "get_file_size_str",
    "get_file_timestamp",
    "get_file_type",
    "get_mime_type",
    "get_unique_filename",
    "is_file_locked",
    "is_path_writeable",
    "is_same_file",
    "is_subdirectory",
    "join_path",
    "normalize_path",
    "split_path",
]