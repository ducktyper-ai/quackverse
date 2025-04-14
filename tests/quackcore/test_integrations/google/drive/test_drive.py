# tests/quackcore/test_integrations/google/drive/test_drive.py
"""
Main entry point for Google Drive integration tests.

This file imports all the specific test modules to ensure they are discovered
by pytest when running the test suite.
"""

# Import test classes from operations submodules
from tests.quackcore.test_integrations.google.drive.operations.test_operations_download import (
    TestDriveOperationsDownload,
)
from tests.quackcore.test_integrations.google.drive.operations.test_operations_folder import (
    TestDriveOperationsFolder,
)
from tests.quackcore.test_integrations.google.drive.operations.test_operations_list_files import (
    TestDriveOperationsListFiles,
)
from tests.quackcore.test_integrations.google.drive.operations.test_operations_permissions import (
    TestDriveOperationsPermissions,
)
from tests.quackcore.test_integrations.google.drive.operations.test_operations_upload import (
    TestDriveOperationsUpload,
)

# Import test modules to ensure they are discovered by pytest
from tests.quackcore.test_integrations.google.drive.test_drive_models import (
    TestDriveModels,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_delete import (
    TestGoogleDriveServiceDelete,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_download import (
    TestGoogleDriveServiceDownload,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_files import (
    TestGoogleDriveServiceFiles,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_folders import (
    TestGoogleDriveServiceFolders,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_init import (
    TestGoogleDriveServiceInit,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_list import (
    TestGoogleDriveServiceList,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_permissions import (
    TestGoogleDriveServicePermissions,
)
from tests.quackcore.test_integrations.google.drive.test_drive_service_upload import (
    TestGoogleDriveServiceUpload,
)
from tests.quackcore.test_integrations.google.drive.test_protocols import (
    TestDriveProtocols,
)
from tests.quackcore.test_integrations.google.drive.utils.test_utils_api import (
    TestDriveUtilsApi,
)
from tests.quackcore.test_integrations.google.drive.utils.test_utils_query import (
    TestDriveUtilsQuery,
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
    "TestDriveOperationsDownload",
    "TestDriveOperationsFolder",
    "TestDriveOperationsListFiles",
    "TestDriveOperationsPermissions",
    "TestDriveOperationsUpload",
    "TestDriveProtocols",
    "TestDriveUtilsApi",
    "TestDriveUtilsQuery",
]
