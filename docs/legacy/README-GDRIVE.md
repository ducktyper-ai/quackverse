# Google Drive Integration for QuackCore

This integration allows QuackCore to interact with Google Drive, providing a simple interface for uploading, downloading, and managing files and folders.

## Features

- **Authentication**: OAuth2 authentication with credential caching
- **File Operations**: Upload, download, list, and delete files
- **Folder Management**: Create folders and manage permissions
- **Configuration**: Flexible configuration through files or parameters

## Installation

To use the Google Drive integration, you need to install QuackCore with the Google Drive dependencies:

```bash
pip install "quackcore[drive]"
```

## Prerequisites

1. You need a Google Cloud project with the Drive API enabled
2. You need to create OAuth2 credentials in the Google Cloud Console
3. You need to download the client secrets JSON file

## Usage

### Basic Usage

```python
from quack_core.integrations.google.drive import GoogleDriveService

# Initialize the service
drive = GoogleDriveService(
    client_secrets_file="path/to/client_secrets.json",
    credentials_file="path/to/credentials.json",
)

# First time use will open a browser for authentication
drive.initialize()

# Upload a file
result = drive.upload_file("path/to/local/file.txt")
if result.success:
    print(f"File uploaded, sharing link: {result.content}")

# List files
list_result = drive.list_files()
if list_result.success:
    for file in list_result.content:
        print(f"{file['name']} ({file['id']})")

# Create a folder
folder_result = drive.create_folder("My Folder")
if folder_result.success:
    folder_id = folder_result.content
    print(f"Created folder with ID: {folder_id}")

# Download a file
download_result = drive.download_file(file_id, "path/to/save/file.txt")
if download_result.success:
    print(f"File downloaded to {download_result.content}")
```

### Configuration File

You can also use a configuration file to avoid hardcoding credentials:

```yaml
# config/quack_config.yaml
google_drive:
  client_secrets_file: "path/to/client_secrets.json"
  credentials_file: "path/to/credentials.json"
  shared_folder_id: "optional_shared_folder_id"
  public_sharing: true
  default_share_access: "reader"
```

Then initialize the service without parameters:

```python
from quack_core.integrations.google.drive import GoogleDriveService

drive = GoogleDriveService()
drive.initialize()
```

## Environment Variables

You can also configure the integration using environment variables:

- `QUACK_GOOGLE_CONFIG` - Path to a configuration file
- `QUACK_GOOGLE_CLIENT_SECRETS_FILE` - Path to client secrets file
- `QUACK_GOOGLE_CREDENTIALS_FILE` - Path to credentials file
- `QUACK_GOOGLE_DRIVE_SHARED_FOLDER_ID` - Shared folder ID

## Best Practices

1. Store your client secrets and credentials files outside of your code repository
2. Use a configuration file rather than hardcoded paths
3. Handle result objects properly by checking the `success` attribute
4. Use `try/except` blocks to catch any exceptions

## Adding to Custom Applications

If you're building a custom application with QuackCore, you can register the Google Drive integration:

```python
from quack_core.integrations import registry
from quack_core.integrations.google.drive import GoogleDriveService

# Register the integration
drive_service = GoogleDriveService()
registry.register(drive_service)

# Later, get it from the registry
drive = registry.get_integration("GoogleDrive")
```

## OAuth Scopes

By default, the integration requests the following scopes:

- `https://www.googleapis.com/auth/drive.file` - View and manage files created by the application
- `https://www.googleapis.com/auth/drive.metadata.readonly` - View metadata for files

If you need different scopes, you can specify them when creating the service:

```python
drive = GoogleDriveService(
    client_secrets_file="path/to/client_secrets.json",
    scopes=["https://www.googleapis.com/auth/drive"],
)
```

## Contributing

If you'd like to extend or improve the Google Drive integration, please see the QuackCore contribution guidelines.