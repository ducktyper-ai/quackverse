# tests/quackcore/test_integrations/pandoc/operations/__init__.py
"""
Tests for Pandoc conversion _operations.

This package contains test modules for the various operation functions
for the Pandoc integration, including HTML to Markdown and Markdown to DOCX conversion.
"""

from tests.quackcore.test_integrations.pandoc.operations.test_html_to_md import (
    TestHtmlToMarkdownOperations,
)
from tests.quackcore.test_integrations.pandoc.operations.test_md_to_docx import (
    TestMarkdownToDocxOperations,
)
from tests.quackcore.test_integrations.pandoc.operations.test_utils import (
    TestPandocUtilities,
)

__all__ = [
    "TestHtmlToMarkdownOperations",
    "TestMarkdownToDocxOperations",
    "TestPandocUtilities",
]
