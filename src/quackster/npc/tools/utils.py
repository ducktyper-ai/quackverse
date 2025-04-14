# src/quackster/npc/tools/utils.py
"""
Utility functions for Quackster NPC tools.

This module provides helper functions for tool operations,
including tool discovery and invocation.
"""

import re
from collections.abc import Sequence
from typing import Any, TypeVar

from quackcore.logging import get_logger
from quackster.npc.schema import UserMemory
from quackster.npc.tools import TOOL_REGISTRY
from quackster.npc.tools.schema import ToolOutput

logger = get_logger(__name__)

# Type variable for tool outputs
T = TypeVar("T", bound=ToolOutput[Any])


def detect_tool_triggers(
    user_input: str, user_memory: UserMemory
) -> list[tuple[str, dict[str, Any]]]:
    """
    Detect which tools should be triggered based on user input.

    Args:
        user_input: The user's message
        user_memory: User memory data

    Returns:
        List of (tool_name, tool_args) tuples for tools that should be triggered
    """
    tools_to_run = []

    # Check for XP and level queries
    if re.search(r"\b(xp|level|progress)\b", user_input, re.IGNORECASE):
        tools_to_run.append(("list_xp_and_level", {"user_memory": user_memory}))

    # Check for badge queries
    badge_match = re.search(
        r'badge[s\s]*[\'"]?([\w-]+)[\'"]?', user_input, re.IGNORECASE
    )
    if badge_match:
        badge_id = badge_match.group(1).lower().strip()
        tools_to_run.append(("get_badge_details", {"badge_id": badge_id}))
    elif re.search(r"\bbadges?\b", user_input, re.IGNORECASE):
        tools_to_run.append(("list_badges", {"user_memory": user_memory}))

    # Check for quest queries
    quest_match = re.search(
        r'quest[s\s]*[\'"]?([\w-]+)[\'"]?', user_input, re.IGNORECASE
    )
    if quest_match:
        quest_id = quest_match.group(1).lower().strip()
        tools_to_run.append(("get_quest_details", {"quest_id": quest_id}))
    elif re.search(r"\bquests?\b", user_input, re.IGNORECASE):
        tools_to_run.append(("list_quests", {"user_memory": user_memory}))

    # Check for next quest suggestions
    if re.search(
        r"\b(what next|next quest|suggest|do next)\b", user_input, re.IGNORECASE
    ):
        tools_to_run.append(("suggest_next_quest", {"user_memory": user_memory}))

    # Check for tutorial requests
    tutorial_match = re.search(
        r'tutorial[s\s]*(?:on|about)?\s*[\'"]?([\w-]+)[\'"]?', user_input, re.IGNORECASE
    )
    if tutorial_match:
        topic = tutorial_match.group(1).lower().strip()
        tools_to_run.append(("get_tutorial", {"topic": topic}))

    # Check for certificate queries
    if re.search(r"\bcertificates?\b", user_input, re.IGNORECASE):
        tools_to_run.append(("get_certificate_info", {"user_memory": user_memory}))

    # Check for quest completion verification
    if re.search(r"\b(completed|finished|done|did)\b", user_input, re.IGNORECASE):
        tools_to_run.append(("verify_quest_completion", {"user_memory": user_memory}))

    return tools_to_run


def run_tools(triggers: Sequence[tuple[str, dict[str, Any]]]) -> list[ToolOutput[Any]]:
    """
    Run the specified tools with the given arguments.

    Args:
        triggers: List of (tool_name, tool_args) tuples

    Returns:
        List of tool outputs as Pydantic model instances
    """
    outputs: list[ToolOutput[Any]] = []

    for tool_name, tool_args in triggers:
        try:
            # Look up the tool function
            tool_func = TOOL_REGISTRY.get(tool_name)
            if tool_func:
                # Run the tool and collect output
                output = tool_func(**tool_args)
                # Ensure it's a ToolOutput instance
                if isinstance(output, ToolOutput):
                    outputs.append(output)
                else:
                    logger.warning(
                        f"Tool '{tool_name}' returned non-ToolOutput result: {type(output)}"
                    )
            else:
                logger.warning(f"Tool '{tool_name}' not found in registry")
        except Exception as e:
            logger.error(f"Error running tool '{tool_name}': {e}")

    return outputs
