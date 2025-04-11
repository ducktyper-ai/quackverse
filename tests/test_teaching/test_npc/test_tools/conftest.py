"""
Pytest fixtures for testing quackcore.teaching.npc.tools.

This module provides common fixtures for testing the tools functionality.
"""
from unittest.mock import MagicMock

import pytest

from quackcore.teaching.npc.schema import UserMemory


@pytest.fixture
def basic_user_memory():
    """Create a basic UserMemory object for testing."""
    return UserMemory(
        github_username="testuser",
        xp=150,
        level=2,
        completed_quests=["quest1", "quest2"],
        badges=["badge1"],
        custom_data={"xp_to_next_level": 50},
    )


@pytest.fixture
def advanced_user_memory():
    """Create an advanced UserMemory object for testing."""
    return UserMemory(
        github_username="advanceduser",
        xp=350,
        level=4,
        completed_quests=[
            "quest1",
            "quest2",
            "quest3",
            "open-pr",
            "merged-pr",
        ],
        badges=["badge1", "badge2", "duck-team-player"],
        custom_data={
            "xp_to_next_level": 25,
            "learning_style": "challenge",
            "suggested_quests": [
                {"id": "quest4", "name": "Quest 4", "description": "Fourth quest"},
            ],
            "recent_quests_discussed": ["quest4"],
        },
    )


@pytest.fixture
def new_user_memory():
    """Create a new user with minimal progress."""
    return UserMemory(
        github_username="newuser",
        xp=50,
        level=1,
        completed_quests=[],
        badges=[],
        custom_data={},
    )


@pytest.fixture
def mock_quest():
    """Create a mock quest object."""
    quest = MagicMock()
    quest.id = "test-quest"
    quest.name = "Test Quest"
    quest.description = "A test quest"
    quest.reward_xp = 25
    quest.badge_id = "test-badge"
    return quest


@pytest.fixture
def mock_badge():
    """Create a mock badge object."""
    badge = MagicMock()
    badge.id = "test-badge"
    badge.name = "Test Badge"
    badge.emoji = "🏆"
    badge.description = "A test badge"
    badge.required_xp = 100
    return badge


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.has_completed_quest.return_value = False
    user.has_earned_badge.return_value = False
    return user