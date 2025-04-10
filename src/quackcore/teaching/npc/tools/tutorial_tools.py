# src/quackcore/teaching/npc/tools/tutorial_tools.py
"""
Tools for tutorial-related information and guidance.

This module provides functions for retrieving and displaying tutorial content
on various topics related to the QuackVerse ecosystem.
"""

from typing import Any

from quackcore.logging import get_logger
from quackcore.teaching.npc import rag
from quackcore.teaching.npc.dialogue import DialogueRegistry
from quackcore.teaching.npc.tools.common import standardize_tool_output

logger = get_logger(__name__)


def get_tutorial(topic: str) -> dict[str, Any]:
    """
    Get tutorial information for a specific topic.

    Args:
        topic: Topic to get tutorial for

    Returns:
        Dictionary with tutorial information
    """
    # Get tutorial from RAG
    tutorial = rag.get_tutorial_topic(topic)

    # Prepare tutorial data for template
    tutorial_data = {
        "topic": topic,
        "title": tutorial.get("title", f"Tutorial on {topic}"),
        "description": tutorial.get("description", ""),
        "content": tutorial.get(
            "content", "No tutorial content available for this topic."
        ),
    }

    # Use template to generate formatted text
    try:
        formatted_text = DialogueRegistry.render_template(
            "tutorial_intro.md.j2", tutorial_data
        )
    except Exception as e:
        logger.error(f"Error rendering tutorial template: {e}")
        # Fallback formatted text
        formatted_text = (
            f"# {tutorial_data['title']}\n\n"
            f"{tutorial_data['description']}\n\n"
            f"{tutorial_data['content']}"
        )

    tutorial_data["formatted_text"] = formatted_text
    return standardize_tool_output("get_tutorial", tutorial_data)
