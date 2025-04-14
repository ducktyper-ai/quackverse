# src/quackster/core/models.py
"""
Core models for the QuackCore quackster module's gamification system.

This module defines the Pydantic models for XP events, badges, quests,
and user progress tracking.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class XPEvent(BaseModel):
    """
    An event that awards XP to a user.

    XP events represent activities or accomplishments that users
    can complete to earn experience points.
    """

    id: str = Field(description="Unique identifier for the event")
    label: str = Field(description="Human-readable label for the event")
    points: int = Field(description="Number of XP points this event awards")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the event"
    )


class Badge(BaseModel):
    """
    A badge that can be earned by a user.

    Badges are awarded automatically when users reach certain
    XP thresholds or complete specific quests.
    """

    id: str = Field(description="Unique identifier for the badge")
    name: str = Field(description="Display name of the badge")
    description: str = Field(description="Description of what the badge represents")
    required_xp: int = Field(description="XP threshold required to earn this badge")
    emoji: str = Field(description="Emoji representing this badge")


class Quest(BaseModel):
    """
    A quest that can be completed by a user.

    Quests are specific challenges that users can complete
    to earn XP and badges.
    """

    id: str = Field(description="Unique identifier for the quest")
    name: str = Field(description="Display name of the quest")
    description: str = Field(description="Description of what the quest involves")
    reward_xp: int = Field(description="Amount of XP awarded for completing this quest")
    badge_id: str | None = Field(
        default=None,
        description="ID of the badge awarded for completing this quest, if any",
    )
    github_check: dict[str, Any] | None = Field(
        default=None,
        description="GitHub check parameters (repo, action, etc.) to verify",
    )

    # This field is defined as Optional but will be set after model creation
    # as Pydantic doesn't support storing callables directly in the model
    verify_func: Callable[["UserProgress"], bool] | None = Field(
        default=None,
        exclude=True,
        description="Function to verify if this quest is completed",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserProgress(BaseModel):
    """
    User progress tracking.

    Tracks a user's XP, completed events, quests, and earned badges.
    This data is stored locally in the user's home directory.
    """

    github_username: str | None = Field(
        default=None, description="GitHub username of the user"
    )
    completed_event_ids: list[str] = Field(
        default_factory=list, description="IDs of XP events the user has completed"
    )
    completed_quest_ids: list[str] = Field(
        default_factory=list, description="IDs of quests the user has completed"
    )
    earned_badge_ids: list[str] = Field(
        default_factory=list, description="IDs of badges the user has earned"
    )
    xp: int = Field(default=0, description="Total XP points earned by the user")

    def has_completed_event(self, event_id: str) -> bool:
        """
        Check if the user has completed a specific XP event.

        Args:
            event_id: ID of the event to check

        Returns:
            True if the user has completed the event, False otherwise
        """
        return event_id in self.completed_event_ids

    def has_completed_quest(self, quest_id: str) -> bool:
        """
        Check if the user has completed a specific quest.

        Args:
            quest_id: ID of the quest to check

        Returns:
            True if the user has completed the quest, False otherwise
        """
        return quest_id in self.completed_quest_ids

    def has_earned_badge(self, badge_id: str) -> bool:
        """
        Check if the user has earned a specific badge.

        Args:
            badge_id: ID of the badge to check

        Returns:
            True if the user has earned the badge, False otherwise
        """
        return badge_id in self.earned_badge_ids

    def get_level(self) -> int:
        """
        Calculate the user's current level based on XP.

        Returns:
            User's current level (1-based)
        """
        # Simple level calculation: 1 level per 100 XP, starting at level 1
        return self.xp // 100 + 1

    def get_xp_to_next_level(self) -> int:
        """
        Calculate XP needed to reach the next level.

        Returns:
            XP needed to reach the next level
        """
        next_level = self.get_level() + 1
        xp_needed = next_level * 100
        return xp_needed - self.xp
