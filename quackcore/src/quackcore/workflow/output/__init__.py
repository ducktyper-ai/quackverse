# quackcore/src/quackcore/workflow/output/__init__.py
"""
Output writing functionality for QuackCore workflows.

This module provides a flexible system for writing workflow outputs in various formats.
It defines a common interface (OutputWriter) and provides concrete implementations
for common formats like JSON and YAML.

The OutputWriter interface is designed to be extensible, allowing for additional
output formats to be added in the future. The current implementations focus on
text-based output formats.

Future extensions:
- TextWriter family: JSON, YAML, CSV, Markdown, HTML
- BinaryWriter family: PDF, Excel, PNG, JPEG
"""

from quackcore.workflow.output.base import OutputWriter
from quackcore.workflow.output.writers import DefaultOutputWriter, YAMLOutputWriter

__all__ = [
    "OutputWriter",
    "DefaultOutputWriter",
    "YAMLOutputWriter",
]
