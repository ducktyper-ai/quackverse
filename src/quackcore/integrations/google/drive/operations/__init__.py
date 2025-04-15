# src/quackcore/integrations/google/drive/_operations/__init__.py
"""
Operations package for Google Drive integration.

This package contains specialized modules for different Google Drive _operations,
such as uploading, downloading, listing files, and managing permissions.
"""

from quackcore.integrations.google.drive.operations import (
    download,
    folder,
    list_files,
    permissions,
    upload,
)

__all__ = [
    "download",
    "folder",
    "list_files",
    "permissions",
    "upload",
]
