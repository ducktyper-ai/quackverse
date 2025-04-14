# tests/quackster/test_core/test_models.py
"""
Tests for the core quackster models.

This module tests the core models in quackster.core.models.
"""

import pytest
from pydantic import ValidationError

from quackster.core.models import Badge, Quest, UserProgress, XPEvent


class TestXPEvent:
    """Tests for the XPEvent model."""

    def test_create_xp_event(self):
        """Test creating an XPEvent."""
        event = XPEvent(id="test-event", label="Test Event", points=10)
        assert event.id == "test-event"
        assert event.label == "Test Event"
        assert event.points == 10
        assert event.metadata == {}

    def test_create_xp_event_with_metadata(self):
        """Test creating an XPEvent with metadata."""
        metadata = {"category": "test", "difficulty": "easy"}
        event = XPEvent(
            id="test-event", label="Test Event", points=10, metadata=metadata
        )
        assert event.metadata == metadata

    def test_xp_event_validation(self):
        """Test XPEvent validation."""
        with pytest.raises(ValidationError):
            XPEvent(id="test-event", label="Test Event", points="invalid")

        with pytest.raises(ValidationError):
            XPEvent(id=None, label="Test Event", points=10)


class TestBadge:
    """Tests for the Badge model."""

    def test_create_badge(self):
        """Test creating a Badge."""
        badge = Badge(
            id="test-badge",
            name="Test Badge",
            description="A test badge",
            required_xp=100,
            emoji="🏆",
        )
        assert badge.id == "test-badge"
        assert badge.name == "Test Badge"
        assert badge.description == "A test badge"
        assert badge.required_xp == 100
        assert badge.emoji == "🏆"

    def test_badge_validation(self):
        """Test Badge validation."""
        with pytest.raises(ValidationError):
            Badge(
                id="test-badge",
                name="Test Badge",
                description="A test badge",
                required_xp="invalid",
                emoji="🏆",
            )

        with pytest.raises(ValidationError):
            Badge(
                id=None,
                name="Test Badge",
                description="A test badge",
                required_xp=100,
                emoji="🏆",
            )


class TestQuest:
    """Tests for the Quest model."""

    def test_create_quest(self):
        """Test creating a Quest."""
        quest = Quest(
            id="test-quest",
            name="Test Quest",
            description="A test quest",
            reward_xp=50,
        )
        assert quest.id == "test-quest"
        assert quest.name == "Test Quest"
        assert quest.description == "A test quest"
        assert quest.reward_xp == 50
        assert quest.badge_id is None
        assert quest.github_check is None
        assert quest.verify_func is None

    def test_create_quest_with_badge(self):
        """Test creating a Quest with a badge."""
        quest = Quest(
            id="test-quest",
            name="Test Quest",
            description="A test quest",
            reward_xp=50,
            badge_id="test-badge",
        )
        assert quest.badge_id == "test-badge"

    def test_create_quest_with_github_check(self):
        """Test creating a Quest with a GitHub check."""
        github_check = {"repo": "test/repo", "action": "star"}
        quest = Quest(
            id="test-quest",
            name="Test Quest",
            description="A test quest",
            reward_xp=50,
            github_check=github_check,
        )
        assert quest.github_check == github_check

    def test_create_quest_with_verify_func(self):
        """Test creating a Quest with a verify function."""

        def verify_func(user: UserProgress) -> bool:
            return True

        quest = Quest(
            id="test-quest",
            name="Test Quest",
            description="A test quest",
            reward_xp=50,
            verify_func=verify_func,
        )
        assert quest.verify_func is verify_func

    def test_quest_validation(self):
        """Test Quest validation."""
        with pytest.raises(ValidationError):
            Quest(
                id="test-quest",
                name="Test Quest",
                description="A test quest",
                reward_xp="invalid",
            )

        with pytest.raises(ValidationError):
            Quest(
                id=None,
                name="Test Quest",
                description="A test quest",
                reward_xp=50,
            )


class TestUserProgress:
    """Tests for the UserProgress model."""

    def test_create_user_progress(self):
        """Test creating a UserProgress."""
        progress = UserProgress(github_username="testuser")
        assert progress.github_username == "testuser"
        assert progress.completed_event_ids == []
        assert progress.completed_quest_ids == []
        assert progress.earned_badge_ids == []
        assert progress.xp == 0

    def test_create_user_progress_with_data(self):
        """Test creating a UserProgress with data."""
        progress = UserProgress(
            github_username="testuser",
            completed_event_ids=["event1", "event2"],
            completed_quest_ids=["quest1"],
            earned_badge_ids=["badge1", "badge2"],
            xp=100,
        )
        assert progress.github_username == "testuser"
        assert progress.completed_event_ids == ["event1", "event2"]
        assert progress.completed_quest_ids == ["quest1"]
        assert progress.earned_badge_ids == ["badge1", "badge2"]
        assert progress.xp == 100

    def test_has_completed_event(self):
        """Test checking if an event has been completed."""
        progress = UserProgress(
            github_username="testuser",
            completed_event_ids=["event1", "event2"],
        )
        assert progress.has_completed_event("event1") is True
        assert progress.has_completed_event("event3") is False

    def test_has_completed_quest(self):
        """Test checking if a quest has been completed."""
        progress = UserProgress(
            github_username="testuser",
            completed_quest_ids=["quest1", "quest2"],
        )
        assert progress.has_completed_quest("quest1") is True
        assert progress.has_completed_quest("quest3") is False

    def test_has_earned_badge(self):
        """Test checking if a badge has been earned."""
        progress = UserProgress(
            github_username="testuser",
            earned_badge_ids=["badge1", "badge2"],
        )
        assert progress.has_earned_badge("badge1") is True
        assert progress.has_earned_badge("badge3") is False

    def test_get_level(self):
        """Test calculating the user's level."""
        progress = UserProgress(github_username="testuser", xp=0)
        assert progress.get_level() == 1

        progress = UserProgress(github_username="testuser", xp=50)
        assert progress.get_level() == 1

        progress = UserProgress(github_username="testuser", xp=100)
        assert progress.get_level() == 2

        progress = UserProgress(github_username="testuser", xp=250)
        assert progress.get_level() == 3

        progress = UserProgress(github_username="testuser", xp=1050)
        assert progress.get_level() == 11

    def test_get_xp_to_next_level(self):
        """Test calculating XP needed for the next level."""
        progress = UserProgress(github_username="testuser", xp=0)
        assert progress.get_xp_to_next_level() == 100

        progress = UserProgress(github_username="testuser", xp=50)
        assert progress.get_xp_to_next_level() == 50

        progress = UserProgress(github_username="testuser", xp=150)
        assert progress.get_xp_to_next_level() == 50

        progress = UserProgress(github_username="testuser", xp=1050)
        assert progress.get_xp_to_next_level() == 150
