# QuackCore Integration System

This document explains how the QuackCore integration system works and how to use it in your QuackTool plugins.

## Overview

The integration system in QuackCore allows tools to seamlessly connect with external services like Google Drive, GitHub, or custom APIs. It's designed to be:

- **Type-safe**: Using generics to ensure you get the right service type
- **Lazy-loaded**: Services are only initialized when needed
- **Flexible**: Tools can use any combination of services
- **Extensible**: New integrations can be added without changing the core toolkit

## Key Components

### 1. BaseIntegrationService

This is the foundation for all integration services. Every service that interacts with an external API should inherit from this base class.

```python
from quack_core.integrations.core.base import BaseIntegrationService

class MyCustomService(BaseIntegrationService):
    @property
    def name(self) -> str:
        return "MyCustomService"
    
    # Implementation of service-specific methods
```

### 2. IntegrationRegistry

The registry keeps track of all available integration services. It's initialized automatically when the application starts.

```python
from quack_core.integrations.core import registry

# Get all registered integrations
integration_names = registry.list_integrations()
```

### 3. get_integration_service()

This function retrieves a specific type of integration service from the registry:

```python
from quack_core.integrations.core import get_integration_service
from quack_core.integrations.google.drive import GoogleDriveService

# Get a Google Drive service instance
drive_service = get_integration_service(GoogleDriveService)
```

## Using Integrations in Tools

### The IntegrationEnabledMixin

The easiest way to use integrations in your tools is with the `IntegrationEnabledMixin`:

```python
from quack_core.toolkit import BaseQuackToolPlugin, IntegrationEnabledMixin
from quack_core.integrations.google.drive import GoogleDriveService

class MyTool(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):
    def initialize_plugin(self):
        # Resolve the integration service
        self._drive = self.resolve_integration(GoogleDriveService)
        
        if self._drive:
            self.logger.info("Google Drive integration is available")
        else:
            self.logger.info("Google Drive integration is not available")
    
    def process_content(self, content, options):
        # Use the integration service if available
        if self._drive:
            # Do something with Drive
            pass
        
        return {"result": "processed"}
```

### Using Multiple Integrations

You can use multiple integrations in a single tool by resolving each one separately:

```python
from quack_core.toolkit import BaseQuackToolPlugin
from quack_core.integrations.google.drive import GoogleDriveService
from quack_core.integrations.github import GitHubService
from quack_core.integrations.core import get_integration_service

class MultiIntegrationTool(BaseQuackToolPlugin):
    def initialize_plugin(self):
        # Resolve integration services directly
        self._drive = get_integration_service(GoogleDriveService)
        self._github = get_integration_service(GitHubService)
```

### Using the Integration Property

For convenience, the `IntegrationEnabledMixin` provides an `integration` property:

```python
# Instead of self._drive.upload_file(...)
result = self.integration.upload_file(file_path, destination)
```

## Creating a New Integration

To create a new integration service:

1. Create a new class that inherits from `BaseIntegrationService`
2. Implement the required methods and properties
3. Register it with the integration registry

Example:

```python
from quack_core.integrations.core.base import BaseIntegrationService
from quack_core.integrations.core import IntegrationResult, registry

class MyNewService(BaseIntegrationService):
    @property
    def name(self) -> str:
        return "MyNewService"
    
    def do_something(self) -> IntegrationResult[str]:
        # Implement your service-specific functionality
        return IntegrationResult.success_result(
            content="It worked!",
            message="Operation completed successfully"
        )

# Register with the registry
registry.register(MyNewService())
```

## Best Practices

1. **Lazy Initialization**: Only initialize connections when needed
2. **Error Handling**: Always use `IntegrationResult` for returning results
3. **Fallbacks**: Handle the case when an integration is not available
4. **Logging**: Use the service's logger for debugging
5. **Configuration**: Use the config_provider for service configuration

## Example: File Upload with Google Drive

Here's a complete example of a tool that uploads files to Google Drive:

```python
from quack_core.toolkit import BaseQuackToolPlugin, IntegrationEnabledMixin
from quack_core.integrations.google.drive import GoogleDriveService
from quack_core.integrations.core import IntegrationResult

class DriveUploader(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):
    def __init__(self):
        super().__init__("drive_uploader", "1.0.0")
    
    def initialize_plugin(self):
        self._drive = self.resolve_integration(GoogleDriveService)
        
        if not self._drive:
            self.logger.warning("Google Drive integration not available")
    
    def process_content(self, content, options):
        return {"message": "Use upload method to upload files"}
    
    def upload(self, file_path, destination=None):
        if not self._drive:
            return IntegrationResult.error_result(
                error="Google Drive integration not available"
            )
        
        try:
            self.logger.info(f"Uploading {file_path} to Google Drive")
            result = self._drive.upload_file(file_path, destination)
            return result
        except Exception as e:
            self.logger.error(f"Error uploading to Drive: {e}")
            return IntegrationResult.error_result(str(e))
```