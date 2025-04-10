# src/quackcore/teaching/npc/tools/__init__.py
"""
Tools for the Quackster teaching NPC.

This module provides tool functions that the NPC can use to answer
questions, check progress, and provide guidance.

Tool Categories:
- Badge Tools: Functions for working with badges
- Certificate Tools: Functions for working with certificates
- Progress Tools: Functions for checking user progress and XP
- Quest Tools: Functions for managing quests and quest completion
- Tutorial Tools: Functions for accessing educational content
"""

from quackcore.teaching.npc.tools.badge_tools import get_badge_details, list_badges
from quackcore.teaching.npc.tools.certificate_tools import get_certificate_info
from quackcore.teaching.npc.tools.common import standardize_tool_output
from quackcore.teaching.npc.tools.progress_tools import list_xp_and_level
from quackcore.teaching.npc.tools.quest_tools import (
    get_quest_details,
    list_quests,
    suggest_next_quest,
    verify_quest_completion,
)
from quackcore.teaching.npc.tools.schema import (
    BadgeDetailOutput,
    BadgeListOutput,
    CertificateListOutput,
    ProgressOutput,
    QuestCompletionOutput,
    QuestDetailOutput,
    QuestListOutput,
    ToolOutput,
    ToolType,
    TutorialOutput,
)
from quackcore.teaching.npc.tools.tutorial_tools import get_tutorial

# Tool registry - maps tool names to their function implementations
TOOL_REGISTRY = {
    # Progress tools
    "list_xp_and_level": list_xp_and_level,
    # Badge tools
    "list_badges": list_badges,
    "get_badge_details": get_badge_details,
    # Quest tools
    "list_quests": list_quests,
    "get_quest_details": get_quest_details,
    "suggest_next_quest": suggest_next_quest,
    "verify_quest_completion": verify_quest_completion,
    # Tutorial tools
    "get_tutorial": get_tutorial,
    # Certificate tools
    "get_certificate_info": get_certificate_info,
}

__all__ = [
    # Common utilities
    "standardize_tool_output",
    "TOOL_REGISTRY",
    # Progress tools
    "list_xp_and_level",
    # Badge tools
    "list_badges",
    "get_badge_details",
    # Quest tools
    "list_quests",
    "get_quest_details",
    "suggest_next_quest",
    "verify_quest_completion",
    # Tutorial tools
    "get_tutorial",
    # Certificate tools
    "get_certificate_info",
    # Schemas
    "ToolOutput",
    "ToolType",
    "QuestListOutput",
    "QuestDetailOutput",
    "QuestCompletionOutput",
    "BadgeListOutput",
    "BadgeDetailOutput",
    "ProgressOutput",
    "CertificateListOutput",
    "TutorialOutput",
]
