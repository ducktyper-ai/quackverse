# src/quackcore/integrations/pandoc/operations/__init__.py
"""
Operations package for pandoc integration.

This package contains specialized modules for different pandoc operations,
such as HTML to Markdown and Markdown to DOCX conversion.
"""

from quackcore.integrations.pandoc.operations.html_to_md import convert_html_to_markdown
from quackcore.integrations.pandoc.operations.md_to_docx import convert_markdown_to_docx
from quackcore.integrations.pandoc.operations.utils import (
    check_conversion_ratio,
    check_file_size,
    get_file_info,
    prepare_pandoc_args,
    track_metrics,
    validate_docx_structure,
    validate_html_structure,
    verify_pandoc,
)

__all__ = [
    "convert_html_to_markdown",
    "convert_markdown_to_docx",
    "check_conversion_ratio",
    "check_file_size",
    "get_file_info",
    "prepare_pandoc_args",
    "track_metrics",
    "validate_docx_structure",
    "validate_html_structure",
    "verify_pandoc",
]