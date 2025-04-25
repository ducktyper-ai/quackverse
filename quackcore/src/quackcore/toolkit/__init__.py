# quackcore/src/quackcore/toolkit/__init__.py
"""
Developer interface layer for creating QuackTools.

This package provides the foundation for building QuackTool plugins,
including the base class, protocol, and mixins that add optional features.

# Core components
- BaseQuackToolPlugin: Base class that tools can inherit from
- QuackToolPluginProtocol: Protocol that defines the required interface
- Various mixins that add optional features

# Example usage
```python
from quackcore.toolkit import BaseQuackToolPlugin, IntegrationEnabledMixin
from quackcore.integrations.google.drive import GoogleDriveService

class MyTool(IntegrationEnabledMixin[GoogleDriveService], BaseQuackToolPlugin):
    def _initialize_plugin(self):
        self._drive = self.resolve_integration(GoogleDriveService)

    def process_content(self, content, options):
        # Process content here
        return {"result": "processed content"}
```
"""

from .base import BaseQuackToolPlugin
from .mixins.env_init import ToolEnvInitializerMixin
from .mixins.integration_enabled import IntegrationEnabledMixin
from .mixins.lifecycle import QuackToolLifecycleMixin
from .mixins.output_handler import OutputFormatMixin
from .protocol import QuackToolPluginProtocol

__all__ = [
    "BaseQuackToolPlugin",
    "QuackToolPluginProtocol",
    "IntegrationEnabledMixin",
    "OutputFormatMixin",
    "ToolEnvInitializerMixin",
    "QuackToolLifecycleMixin",
]
