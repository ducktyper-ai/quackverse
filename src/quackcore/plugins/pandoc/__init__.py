# src/quackcore/integrations/pandoc/__init__.py
"""
Pandoc integration for QuackCore.

This package provides integration with pandoc for document conversion,
including HTML to Markdown and Markdown to DOCX conversion.
"""

from quackcore.integrations.pandoc.config import ConversionConfig, PandocConfigProvider
from quackcore.integrations.pandoc.converter import DocumentConverter
from quackcore.integrations.pandoc.models import (
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
    FileInfo,
)
from quackcore.integrations.pandoc.service import PandocService
from quackcore.integrations.protocols import IntegrationProtocol

__all__ = [
    # Main service class
    "PandocService",
    # Configuration
    "ConversionConfig",
    "PandocConfigProvider",
    # Core converter
    "DocumentConverter",
    # Models
    "BatchConversionResult",
    "ConversionMetrics",
    "ConversionResult",
    "ConversionTask",
    "FileInfo",
    # Factory function for integration discovery
    "create_integration",
]


def create_integration() -> IntegrationProtocol:
    """
    Create and initialize a pandoc integration.

    This function is used as an entry point for automatic integration discovery.

    Returns:
        IntegrationProtocol: Configured pandoc service
    """
    return PandocService()