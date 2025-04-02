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
from quackcore.fs.service.full_class import FileSystemService
from quackcore.fs.service import service, create_service

# Import utility functions
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
    safe_copy,
    safe_delete,
    safe_move,
    split_path,
)

# Import standalone functions from service package
from quackcore.fs.service.standalone import create_directory, get_file_info, read_yaml

# Import path validation components
from quackcore.fs.service.path_validation import PathInfo

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
    # Compatibility methods
    "PathInfo",
    "get_path_info",
    "is_valid_path",
    "normalize_path_with_info",
]