# tests/quackcore/test_integrations/pandoc/test_pandoc_integration.py
"""
Main entry point for Pandoc integration tests.

This file imports all the specific test modules to ensure they are discovered
by pytest when running the test suite.
"""

from tests.test_integrations.pandoc.test_config import TestPandocConfig
from tests.test_integrations.pandoc.test_converter import TestDocumentConverter
from tests.test_integrations.pandoc.test_models import TestPandocModels
from tests.test_integrations.pandoc.test_operations import (
    TestHtmlToMarkdownOperations,
    TestMarkdownToDocxOperations,
    TestPandocUtilities,
)
from tests.test_integrations.pandoc.test_service import TestPandocService

# Export the test classes for direct import
__all__ = [
    "TestPandocConfig",
    "TestDocumentConverter",
    "TestPandocModels",
    "TestPandocService",
    "TestHtmlToMarkdownOperations",
    "TestMarkdownToDocxOperations",
    "TestPandocUtilities",
]
