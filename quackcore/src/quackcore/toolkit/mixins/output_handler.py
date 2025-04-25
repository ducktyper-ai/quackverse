# quackcore/src/quackcore/toolkit/mixins/output_handler.py
"""
Output format mixin for QuackTool plugins.

This module provides a mixin that allows QuackTool plugins to customize
how their output is formatted and written.
"""

from quackcore.workflow.output import OutputWriter


class OutputFormatMixin:
    """
    Mixin that provides customization of output format for QuackTool plugins.

    This mixin allows tools to specify the output format and customize
    how their output is written.
    """

    def _get_output_extension(self) -> str:
        """
        Get the file extension for output files.

        Override this method to return a different extension if needed.

        Returns:
            str: File extension (with leading dot) for output files
        """
        return ".json"

    def get_output_writer(self) -> OutputWriter | None:
        """
        Get the output writer for this tool.

        Override this method to return a custom OutputWriter if the tool wants.
        By default, returns None which means the default writer will be used
        with the extension from _get_output_extension().

        Returns:
            OutputWriter | None: The output writer to use, or None for default
        """
        return None