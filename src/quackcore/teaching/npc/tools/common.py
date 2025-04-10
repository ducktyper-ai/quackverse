# src/quackcore/teaching/npc/tools/common.py
"""
Common utilities for Quackster NPC tools.

This module provides shared functions and utilities used by multiple tools.
"""

from typing import Any

from quackcore.logging import get_logger
from quackcore.teaching.npc.dialogue import DialogueRegistry

logger = get_logger(__name__)


def standardize_tool_output(
    tool_name: str, result: dict[str, Any], flavor: bool = True
) -> dict[str, Any]:
    """
    Standardize tool output format.

    Args:
        tool_name: Name of the tool
        result: Tool result data
        flavor: Whether to add Quackster flavor to the text

    Returns:
        Standardized tool output
    """
    # Ensure formatted_text exists
    if "formatted_text" not in result:
        result["formatted_text"] = str(result)

    # Add Quackster flavor if requested
    if flavor and "formatted_text" in result:
        result["formatted_text"] = DialogueRegistry.flavor_text(
            tool_name, result["formatted_text"]
        )

    # Add standard metadata
    return {
        "name": tool_name,
        "result": result,
        "formatted_text": result.get("formatted_text", ""),
        **result
    }