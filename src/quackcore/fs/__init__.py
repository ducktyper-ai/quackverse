# src/quackcore/fs/__init__.py
"""
Filesystem package for QuackCore.

This package provides a robust filesystem abstraction with proper error handling,
standardized result objects, and comprehensive file operation capabilities.
"""

# Import core components
from quackcore.fs.operations import FileSystemOperations
from quackcore.fs.results import (
    DataResult,
    DirectoryInfoResult,
    FileInfoResult,
    FindResult,
    OperationResult,
    ReadResult,
    WriteResult,
)
from quackcore.fs.service import (
    FileSystemService,
    PathInfo,
    atomic_write,
    compute_checksum,
    copy,
    create_directory,
    create_service,
    create_temp_directory,
    create_temp_file,
    delete,
    ensure_directory,
    expand_user_vars,
    find_files,
    find_files_by_content,
    get_disk_usage,
    get_extension,
    get_file_info,
    get_file_size_str,
    get_file_timestamp,
    get_file_type,
    get_mime_type,
    get_path_info,
    get_unique_filename,
    is_file_locked,
    is_path_writeable,
    is_same_file,
    is_subdirectory,
    is_valid_path,
    join_path,
    list_directory,
    move,
    normalize_path,
    normalize_path_with_info,
    read_binary,
    read_json,
    read_text,
    read_yaml,
    service,
    split_path,
    write_binary,
    write_json,
    write_text,
    write_yaml,
)

# Import utility functions
from quackcore.fs.utils import (
    safe_copy,
    safe_delete,
    safe_move,
)

# Define path validation functions directly here for backward compatibility
def get_path_info(path):
    """Get information about a path's validity and format."""
    return service.get_path_info(path)

def is_valid_path(path):
    """Check if a path has valid syntax."""
    return service.is_valid_path(path)

def normalize_path_with_info(path):
    """Normalize a path and return detailed information."""
    return service.normalize_path_with_info(path)

__all__ = [
    # Main service class
    "FileSystemService",
    # Factory function
    "create_service",
    # Global instance
    "service",
    # Core operations class
    "FileSystemOperations",
    # Result classes
    "OperationResult",
    "ReadResult",
    "WriteResult",
    "FileInfoResult",
    "DirectoryInfoResult",
    "FindResult",
    "DataResult",
    # Utility functions
    "normalize_path",
    "is_same_file",
    "is_subdirectory",
    "get_file_size_str",
    "get_unique_filename",
    "create_temp_directory",
    "create_temp_file",
    "get_file_timestamp",
    "is_path_writeable",
    "get_mime_type",
    "get_disk_usage",
    "is_file_locked",
    "get_file_type",
    "find_files_by_content",
    "split_path",
    "join_path",
    "expand_user_vars",
    "get_extension",
    "ensure_directory",
    "compute_checksum",
    "atomic_write",
    "safe_copy",
    "safe_move",
    "safe_delete",
    "get_file_info",
    "create_directory",
    "read_yaml",
    "read_text",
    "write_text",
    "read_binary",
    "write_binary",
    "write_yaml",
    "read_json",
    "write_json",
    "list_directory",
    "find_files",
    "copy",
    "move",
    "delete",
    # Compatibility methods
    "PathInfo",
    "get_path_info",
    "is_valid_path",
    "normalize_path_with_info",
]