# src/quackcore/teaching/npc/tools/common.py
"""
Common utilities for Quackster NPC tools.

This module provides shared functions and utilities used by multiple tools.
"""

from collections.abc import Mapping
from typing import Any, overload

from quackcore.logging import get_logger
from quackcore.teaching.npc.dialogue import DialogueRegistry
from quackcore.teaching.npc.tools.schema import (
    BadgeDetailOutput,
    BadgeInfo,
    BadgeListOutput,
    BadgeListResult,
    CertificateListOutput,
    CertificateListResult,
    ProgressOutput,
    ProgressResult,
    QuestCompletionOutput,
    QuestCompletionResult,
    QuestDetailOutput,
    QuestInfo,
    QuestListOutput,
    QuestListResult,
    ToolOutput,
    ToolType,
    TutorialOutput,
    TutorialResult,
)

logger = get_logger(__name__)


# Define overloaded versions of standardize_tool_output for different tool types
# This allows us to provide precise return type information


@overload
def standardize_tool_output(
    tool_name: str, result: Mapping[str, Any], flavor: bool = True
) -> ToolOutput[Any]: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    tool_type: ToolType = ToolType.META,
) -> ToolOutput[Any]: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[QuestListOutput],
) -> QuestListOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[QuestDetailOutput],
) -> QuestDetailOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[QuestCompletionOutput],
) -> QuestCompletionOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[BadgeListOutput],
) -> BadgeListOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[BadgeDetailOutput],
) -> BadgeDetailOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[ProgressOutput],
) -> ProgressOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[CertificateListOutput],
) -> CertificateListOutput: ...


@overload
def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    *,
    return_type: type[TutorialOutput],
) -> TutorialOutput: ...


def standardize_tool_output(
    tool_name: str,
    result: Mapping[str, Any],
    flavor: bool = True,
    tool_type: ToolType = None,
    *,
    return_type=None,
) -> ToolOutput[Any]:
    """
    Standardize tool output format using Pydantic models.

    This function converts a dictionary result into a properly typed
    Pydantic model based on the tool type.

    Args:
        tool_name: Name of the tool
        result: Tool result data
        flavor: Whether to add Quackster flavor to the text
        tool_type: Optional explicit tool type
        return_type: Optional specific return type class

    Returns:
        A properly typed ToolOutput model instance
    """
    # Create a mutable copy of the result dict to avoid modifying the original
    result_copy = dict(result)

    # Ensure formatted_text exists
    if "formatted_text" not in result_copy:
        result_copy["formatted_text"] = str(result_copy)

    # Add Quackster flavor if requested
    if flavor and "formatted_text" in result_copy:
        result_copy["formatted_text"] = DialogueRegistry.flavor_text(
            tool_name, result_copy["formatted_text"]
        )

    # Extract metadata fields
    badge_awarded = result_copy.pop("badge_awarded", False)
    xp_gained = result_copy.pop("xp_gained", 0)
    quests_completed = result_copy.pop("quests_completed", False)
    level_up = result_copy.pop("level_up", False)

    # Determine tool type based on tool name or explicit parameter
    if tool_type is None:
        tool_type_mapping = {
            "list_badges": ToolType.BADGE,
            "get_badge_details": ToolType.BADGE,
            "get_certificate_info": ToolType.CERTIFICATE,
            "list_xp_and_level": ToolType.PROGRESS,
            "list_quests": ToolType.QUEST,
            "get_quest_details": ToolType.QUEST,
            "suggest_next_quest": ToolType.QUEST,
            "verify_quest_completion": ToolType.QUEST,
            "get_tutorial": ToolType.TUTORIAL,
        }

        # Get tool type from mapping or explicit value in result
        explicit_type = result_copy.pop("type", None)
        if explicit_type is None:
            tool_type = tool_type_mapping.get(tool_name, ToolType.META)
        elif isinstance(explicit_type, str):
            # Convert string to enum if needed
            tool_type = ToolType(explicit_type)
        else:
            tool_type = explicit_type

    # Format the base output data
    base_output = {
        "name": tool_name,
        "formatted_text": result_copy.pop("formatted_text", ""),
        "type": tool_type,
        "badge_awarded": badge_awarded,
        "xp_gained": xp_gained,
        "quests_completed": quests_completed,
        "level_up": level_up,
    }

    # If return_type is explicitly specified, use that to determine the output format
    if return_type is not None:
        if return_type == QuestCompletionOutput:
            result_model = QuestCompletionResult.model_validate(result_copy)
            return QuestCompletionOutput(result=result_model, **base_output)
        elif return_type == QuestDetailOutput:
            result_model = QuestInfo.model_validate(result_copy)
            return QuestDetailOutput(result=result_model, **base_output)
        elif return_type == QuestListOutput:
            result_model = QuestListResult.model_validate(result_copy)
            return QuestListOutput(result=result_model, **base_output)
        elif return_type == BadgeListOutput:
            result_model = BadgeListResult.model_validate(result_copy)
            return BadgeListOutput(result=result_model, **base_output)
        elif return_type == BadgeDetailOutput:
            result_model = BadgeInfo.model_validate(result_copy)
            return BadgeDetailOutput(result=result_model, **base_output)
        elif return_type == ProgressOutput:
            result_model = ProgressResult.model_validate(result_copy)
            return ProgressOutput(result=result_model, **base_output)
        elif return_type == CertificateListOutput:
            result_model = CertificateListResult.model_validate(result_copy)
            return CertificateListOutput(result=result_model, **base_output)
        elif return_type == TutorialOutput:
            result_model = TutorialResult.model_validate(result_copy)
            return TutorialOutput(result=result_model, **base_output)
        else:
            return return_type(result=result_copy, **base_output)

    # Determine the appropriate result model and output model based on tool type and name
    if tool_type == ToolType.BADGE:
        if tool_name == "list_badges":
            result_model = BadgeListResult.model_validate(result_copy)
            return BadgeListOutput(result=result_model, **base_output)
        else:  # get_badge_details
            result_model = BadgeInfo.model_validate(result_copy)
            return BadgeDetailOutput(result=result_model, **base_output)

    elif tool_type == ToolType.QUEST:
        if tool_name == "list_quests":
            result_model = QuestListResult.model_validate(result_copy)
            return QuestListOutput(result=result_model, **base_output)
        elif tool_name == "verify_quest_completion":
            result_model = QuestCompletionResult.model_validate(result_copy)
            return QuestCompletionOutput(result=result_model, **base_output)
        else:  # get_quest_details or suggest_next_quest
            result_model = QuestInfo.model_validate(result_copy)
            return QuestDetailOutput(result=result_model, **base_output)

    elif tool_type == ToolType.PROGRESS:
        result_model = ProgressResult.model_validate(result_copy)
        return ProgressOutput(result=result_model, **base_output)

    elif tool_type == ToolType.CERTIFICATE:
        result_model = CertificateListResult.model_validate(result_copy)
        return CertificateListOutput(result=result_model, **base_output)

    elif tool_type == ToolType.TUTORIAL:
        result_model = TutorialResult.model_validate(result_copy)
        return TutorialOutput(result=result_model, **base_output)

    else:
        # For untyped or META tools, use a generic ToolOutput
        return ToolOutput(result=result_copy, **base_output)
