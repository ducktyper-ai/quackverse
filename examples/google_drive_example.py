# examples/google_drive_example.py
"""
Example usage of the Google Drive integration in QuackCore.

This example demonstrates how to use the Google Drive integration
to upload, download, and manage files on Google Drive.
"""

import logging
import sys
from pathlib import Path

from quackcore.integrations import registry
from quackcore.integrations.google.drive import GoogleDriveService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google_drive_example")


def main():
    """
    Run the Google Drive integration example.
    """
    # Check if required arguments are provided
    if len(sys.argv) < 2:
        print(
            "Usage: python google_drive_example.py [client_secrets_file] [file_to_upload]"
        )
        return

    client_secrets_file = sys.argv[1]

    # File to upload (optional)
    file_to_upload = sys.argv[2] if len(sys.argv) > 2 else None

    # Method 1: Create the service directly
    logger.info("Creating Google Drive service...")
    drive_service = GoogleDriveService(
        client_secrets_file=client_secrets_file,
        credentials_file="google_credentials.json",
    )

    # Initialize the service
    init_result = drive_service.initialize()
    if not init_result.success:
        logger.error(f"Failed to initialize drive service: {init_result.error}")
        return

    logger.info("Google Drive service initialized successfully")

    # Method 2: Get the service from the registry (if registered)
    # Uncomment to use this method instead
    """
    logger.info("Getting Google Drive service from registry...")
    drive_integration = registry.get_integration("GoogleDrive")
    if not drive_integration:
        # If not found, try to load it
        registry.load_integration_module("quackcore.integrations.google.drive")
        drive_integration = registry.get_integration("GoogleDrive")

    if not drive_integration:
        logger.error("Google Drive integration not found in registry")
        return

    drive_service = drive_integration
    """

    # List files in the shared folder
    logger.info("Listing files in Drive...")
    list_result = drive_service.list_files()
    if list_result.success:
        files = list_result.content
        logger.info(f"Found {len(files)} files")
        for file in files:
            print(f"  - {file['name']} ({file['id']})")
    else:
        logger.error(f"Failed to list files: {list_result.error}")

    # Create a folder
    logger.info("Creating a test folder...")
    folder_result = drive_service.create_folder("QuackCore Test Folder")
    if folder_result.success:
        folder_id = folder_result.content
        logger.info(f"Created folder with ID: {folder_id}")
    else:
        logger.error(f"Failed to create folder: {folder_result.error}")
        folder_id = None

    # Upload a file if provided
    if file_to_upload and folder_id:
        file_path = Path(file_to_upload)
        if file_path.exists():
            logger.info(f"Uploading file {file_path}...")
            upload_result = drive_service.upload_file(
                file_path=file_path,
                parent_folder_id=folder_id,
            )
            if upload_result.success:
                logger.info(f"File uploaded successfully: {upload_result.content}")
            else:
                logger.error(f"Failed to upload file: {upload_result.error}")


if __name__ == "__main__":
    main()
