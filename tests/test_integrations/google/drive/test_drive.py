# tests/test_integrations/google/drive/test_drive.py
"""
Main entry point for Google Drive integration tests.

This file imports all the specific test modules to ensure they are discovered
by pytest when running the test suite.
"""

# Import test modules to ensure they are discovered by pytest
from tests.test_integrations.google.drive.test_drive_models import TestDriveModels
from tests.test_integrations.google.drive.test_drive_service_delete import (
    TestGoogleDriveServiceDelete,
)
from tests.test_integrations.google.drive.test_drive_service_download import (
    TestGoogleDriveServiceDownload,
)
from tests.test_integrations.google.drive.test_drive_service_files import (
    TestGoogleDriveServiceFiles,
)
from tests.test_integrations.google.drive.test_drive_service_folders import (
    TestGoogleDriveServiceFolders,
)
from tests.test_integrations.google.drive.test_drive_service_init import (
    TestGoogleDriveServiceInit,
)
from tests.test_integrations.google.drive.test_drive_service_list import (
    TestGoogleDriveServiceList,
)
from tests.test_integrations.google.drive.test_drive_service_permissions import (
    TestGoogleDriveServicePermissions,
)
from tests.test_integrations.google.drive.test_drive_service_upload import (
    TestGoogleDriveServiceUpload,
)

# Export the test classes for direct import
__all__ = [
    "TestDriveModels",
    "TestGoogleDriveServiceDelete",
    "TestGoogleDriveServiceDownload",
    "TestGoogleDriveServiceFiles",
    "TestGoogleDriveServiceFolders",
    "TestGoogleDriveServiceInit",
    "TestGoogleDriveServiceList",
    "TestGoogleDriveServicePermissions",
    "TestGoogleDriveServiceUpload",
]
