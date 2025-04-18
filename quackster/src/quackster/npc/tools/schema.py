# src/quackster/npc/tools/schema.py
"""
Pydantic models defining the schema for Quackster NPC tool outputs.

This module provides standardized data models for tool outputs,
ensuring consistency across all tools and enabling validation.
"""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type variable for result data
T = TypeVar("T")


class ToolType(str, Enum):
    """Enumeration of possible tool types."""

    PROGRESS = "progress"
    QUEST = "quest"
    BADGE = "badge"
    CERTIFICATE = "certificate"
    TUTORIAL = "tutorial"
    META = "meta"


class ToolOutput(BaseModel, Generic[T]):
    """
    Standardized tool output model.

    This is the base model that all tool outputs must follow.
    It contains common fields that every tool must provide.
    """

    name: str = Field(description="The tool's function name (e.g., 'list_quests')")
    result: T = Field(description="Raw, structured data returned by the tool")
    formatted_text: str = Field(
        description="Quackster-enhanced string ready for display in terminal or chat"
    )
    type: ToolType = Field(
        default=ToolType.META,
        description="Tool category for UI rendering and context injection",
    )
    badge_awarded: bool = Field(
        default=False, description="If a badge was earned as a result of this tool"
    )
    xp_gained: int = Field(
        default=0, description="XP gained from completing the action"
    )
    quests_completed: bool = Field(
        default=False, description="True if any new quests were completed"
    )
    level_up: bool = Field(default=False, description="True if the user leveled up")


# Specific result models for different tool types


class BadgeInfo(BaseModel):
    """Model for badge information."""

    id: str
    name: str
    emoji: str = "🏆"
    description: str
    is_earned: bool = False
    progress: float = 0.0
    required_xp: int = 0


class BadgeListResult(BaseModel):
    """Model for badge list tool results."""

    earned_badges: list[BadgeInfo] = []
    earned_count: int = 0
    earned_formatted: list[str] = []
    next_badges: list[BadgeInfo] = []
    next_badges_formatted: list[str] = []


class QuestInfo(BaseModel):
    """Model for quest information."""

    id: str
    name: str
    description: str
    reward_xp: int = 0
    badge_id: str | None = None
    is_completed: bool = False
    guidance: str | None = None
    hint: str | None = None


class QuestListResult(BaseModel):
    """Model for quest list tool results."""

    completed: list[QuestInfo] = []
    completed_count: int = 0
    completed_formatted: list[str] = []
    available: list[QuestInfo] = []
    available_count: int = 0
    available_formatted: list[str] = []
    suggested: list[QuestInfo] = []
    suggested_formatted: list[str] = []


class QuestCompletionDetail(BaseModel):
    """Model for completed quest details."""

    id: str
    name: str
    reward_xp: int
    badge: str | None = None
    completion_message: str
    formatted: str


class QuestCompletionResult(BaseModel):
    """Model for quest completion verification results."""

    quests_completed: bool = False
    completed_quests: list[QuestInfo] = []
    completed_details: list[QuestCompletionDetail] = []
    total_completed_count: int = 0
    old_level: int | None = None
    new_level: int | None = None


class ProgressResult(BaseModel):
    """Model for progress and XP information."""

    level: int
    xp: int
    next_level: int
    xp_needed: int
    progress_pct: float
    progress_bar: str


class CertificateInfo(BaseModel):
    """Model for certificate information."""

    id: str
    name: str
    description: str
    earned: bool = False
    requirements: list[str] = []
    progress: float = 0.0
    progress_bar: str = ""
    formatted: str


class CertificateListResult(BaseModel):
    """Model for certificate list tool results."""

    certificates: list[CertificateInfo] = []
    earned_any: bool = False
    certificate_count: int = 0
    earned_count: int = 0


class TutorialResult(BaseModel):
    """Model for tutorial information."""

    topic: str
    title: str
    description: str = ""
    content: str = ""


# Type-specific tool output models


class BadgeListOutput(ToolOutput[BadgeListResult]):
    """Badge list tool output model."""

    type: ToolType = ToolType.BADGE


class BadgeDetailOutput(ToolOutput[BadgeInfo]):
    """Badge detail tool output model."""

    type: ToolType = ToolType.BADGE


class QuestListOutput(ToolOutput[QuestListResult]):
    """Quest list tool output model."""

    type: ToolType = ToolType.QUEST


class QuestDetailOutput(ToolOutput[QuestInfo]):
    """Quest detail tool output model."""

    type: ToolType = ToolType.QUEST


class QuestCompletionOutput(ToolOutput[QuestCompletionResult]):
    """Quest completion verification tool output model."""

    type: ToolType = ToolType.QUEST


class ProgressOutput(ToolOutput[ProgressResult]):
    """Progress information tool output model."""

    type: ToolType = ToolType.PROGRESS


class CertificateListOutput(ToolOutput[CertificateListResult]):
    """Certificate list tool output model."""

    type: ToolType = ToolType.CERTIFICATE


class TutorialOutput(ToolOutput[TutorialResult]):
    """Tutorial tool output model."""

    type: ToolType = ToolType.TUTORIAL
