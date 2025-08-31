# quack-core/src/quack-core/integrations/google/drive/__init__.py
"""
Google Drive integration for quack_core.

This module provides integration with Google Drive for storing and sharing
files, with a consistent interface for uploading, downloading, and managing content.
"""

from quack_core.integrations.core.protocols import StorageIntegrationProtocol
from quack_core.integrations.google.drive.models import DriveFile, DriveFolder
from quack_core.integrations.google.drive.service import GoogleDriveService

__all__ = [
    "GoogleDriveService",
    "DriveFile",
    "DriveFolder",
    "create_integration",
]


def create_integration() -> StorageIntegrationProtocol:
    """
    Create and configure a Google Drive integration.

    This function is used as an entry point for automatic integration discovery.

    Returns:
        StorageIntegrationProtocol: Configured Google Drive service
    """
    return GoogleDriveService()
