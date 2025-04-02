# src/quackcore/fs/service/__init__.py
"""
FileSystemService provides a high-level interface for filesystem operations.

This module exports the FileSystemService class and provides a factory function
for creating instances of it.
"""

from quackcore.fs.service.base import FileSystemService
from quackcore.fs.service.factory import create_service

# Create a global instance for convenience - this will be imported
# in the main fs/__init__.py to maintain backward compatibility
service = create_service()

__all__ = [
    "FileSystemService",
    "create_service",
    "service",
]