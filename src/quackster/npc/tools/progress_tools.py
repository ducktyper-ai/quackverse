# src/quackster/npc/tools/progress_tools.py
"""
Tools for checking user progress, XP, and level information.

This module provides functions for retrieving and displaying user progress metrics.
"""

from quackster.npc.schema import UserMemory
from quackster.npc.tools import ProgressOutput, standardize_tool_output


def list_xp_and_level(user_memory: UserMemory) -> ProgressOutput:
    """
    Get information about a user's XP and level.

    Args:
        user_memory: User memory data

    Returns:
        ProgressOutput with XP and level information
    """
    level = user_memory.level
    xp = user_memory.xp
    xp_to_next = user_memory.custom_data.get("xp_to_next_level", 100)
    next_level = level + 1

    # Calculate percentage progress to next level
    progress_pct = int(100 - (xp_to_next / (next_level * 100) * 100))

    # Create progress bar
    progress_bar = "█" * (progress_pct // 5) + "░" * ((100 - progress_pct) // 5)

    # Format text with duck-like enthusiasm
    formatted_text = (
        f"Level {level} ({xp} XP)\n"
        f"{progress_bar} {progress_pct}%\n"
        f"{xp_to_next} XP needed for Level {next_level}"
    )

    return standardize_tool_output(
        "list_xp_and_level",
        {
            "level": level,
            "xp": xp,
            "next_level": next_level,
            "xp_needed": xp_to_next,
            "progress_pct": progress_pct,
            "progress_bar": progress_bar,
            "formatted_text": formatted_text,
        },
        return_type=ProgressOutput,
    )
