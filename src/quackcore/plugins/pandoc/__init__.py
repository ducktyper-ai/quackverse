# src/quackcore/plugins/pandoc/__init__.py
"""
Pandoc plugin for QuackCore.

This package provides a plugin for document conversion using Pandoc,
including HTML to Markdown and Markdown to DOCX conversion.
"""

from quackcore.plugins.pandoc.config import ConversionConfig, PandocConfigProvider
from quackcore.plugins.pandoc.converter import DocumentConverter, create_converter
from quackcore.plugins.pandoc.models import (
    BatchConversionResult,
    ConversionMetrics,
    ConversionResult,
    ConversionTask,
    FileInfo,
)
from quackcore.plugins.pandoc.service import PandocService
from quackcore.plugins.protocols import QuackPluginProtocol

__all__ = [
    # Main service class
    "PandocService",
    # Configuration
    "ConversionConfig",
    "PandocConfigProvider",
    # Core converter
    "DocumentConverter",
    "create_converter",
    # Models
    "BatchConversionResult",
    "ConversionMetrics",
    "ConversionResult",
    "ConversionTask",
    "FileInfo",
    # Factory function for plugin discovery
    "create_plugin",
]


def create_plugin() -> QuackPluginProtocol:
    """
    Create and return a Pandoc plugin instance.

    This function is used as an entry point for automatic plugin discovery.

    Returns:
        QuackPluginProtocol: Configured Pandoc service
    """
    return PandocService()