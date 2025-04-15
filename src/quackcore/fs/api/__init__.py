# src/quackcore/fs/api/__init__.py
"""
Utility functions for filesystem operations.

This module aggregates ONLY public helper functions for working with the filesystem.
"""

# Re-export all public functions
from quackcore.fs.api.public import (
    atomic_write,
    compute_checksum,
    copy_safely,
    create_temp_directory,
    create_temp_file,
    delete_safely,
    ensure_directory,
    expand_user_vars,
    find_files_by_content,
    get_disk_usage,
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
    is_same_file,
    is_subdirectory,
    move_safely,
    normalize_path,
    split_path,
)

__all__ = [
    # Re-export everything from public
    "atomic_write",
    "compute_checksum",
    "copy_safely",
    "create_temp_directory",
    "create_temp_file",
    "delete_safely",
    "ensure_directory",
    "expand_user_vars",
    "find_files_by_content",
    "get_disk_usage",
    "get_file_size_str",
    "get_file_timestamp",
    "get_file_type",
    "get_mime_type",
    "get_unique_filename",
    "is_file_locked",
    "is_path_writeable",
    "is_same_file",
    "is_subdirectory",
    "move_safely",
    "normalize_path",
    "split_path",
]
