# quack-core/tests/test_integrations/google/drive/mocks.py
"""
Mock objects for Google Drive service testing.

This module provides mock implementations of Google Drive service objects
that can be used across different test modules.

Note: This file now re-exports from the mocks/ package for backward compatibility.
      New imports should use the mocks/ package directly.
"""

# Re-export all mock classes and functions from the mocks package
from tests.test_integrations.google.drive.mocks import (  # Base mocks; Request mocks; Resource mocks; Service mocks; Credential mocks; Media mocks
    GenericApiRequestMock,
    MockDownloadStatus,
    MockDriveFilesResource,
    MockDrivePermissionsResource,
    MockDriveRequest,
    MockDriveService,
    MockGoogleCredentials,
    MockMediaDownloader,
    create_credentials,
    create_error_drive_service,
    create_mock_drive_service,
    create_mock_media_io_base_download,
)

# Export all symbols
__all__ = [
    # Base mocks
    "GenericApiRequestMock",
    # Request mocks
    "MockDriveRequest",
    # Resource mocks
    "MockDrivePermissionsResource",
    "MockDriveFilesResource",
    # Service mocks
    "MockDriveService",
    "create_mock_drive_service",
    "create_error_drive_service",
    # Credential mocks
    "MockGoogleCredentials",
    "create_credentials",
    # Media mocks
    "MockDownloadStatus",
    "MockMediaDownloader",
    "create_mock_media_io_base_download",
]
