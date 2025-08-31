# quack-core/src/quack-core/integrations/pandoc/operations/__init__.py
"""
Operations package for pandoc integration.

This package contains specialized modules for different pandoc _operations,
such as HTML to Markdown and Markdown to DOCX conversion.
"""

from quack_core.integrations.pandoc.operations.html_to_md import (
    convert_html_to_markdown,
    post_process_markdown,
)
from quack_core.integrations.pandoc.operations.html_to_md import (
    validate_conversion as validate_html_conversion,
)
from quack_core.integrations.pandoc.operations.md_to_docx import (
    convert_markdown_to_docx,
)
from quack_core.integrations.pandoc.operations.md_to_docx import (
    validate_conversion as validate_docx_conversion,
)
from quack_core.integrations.pandoc.operations.utils import (
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
    "post_process_markdown",
    "validate_html_conversion",
    "validate_docx_conversion",
    "check_conversion_ratio",
    "check_file_size",
    "get_file_info",
    "prepare_pandoc_args",
    "track_metrics",
    "validate_docx_structure",
    "validate_html_structure",
    "verify_pandoc",
]
