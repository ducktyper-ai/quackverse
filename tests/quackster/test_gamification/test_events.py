# tests/quackster/test_gamification/test_events.py
"""
Tests for event handling in the gamification service.

This module tests event handling functionality in the gamification service.
"""

from unittest.mock import MagicMock, patch

from quackster.core.gamification_service import (
    GamificationResult,
    GamificationService,
)
from quackster.core.models import UserProgress, XPEvent


class TestGamificationServiceEvents:
    """Tests for event handling in the gamification service."""

    @patch("quackster.core.gamification_service.xp.add_xp")
    @patch("quackster.core.gamification_service.quests.apply_completed_quests")
    @patch("quackster.core.gamification_service.xp._check_xp_badges")
    @patch("quackster.core.gamification_service.utils.save_progress")
    def test_handle_event_new(
        self, mock_save, mock_check_badges, mock_apply_quests, mock_add_xp
    ):
        """Test handling a new XP event."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        event = XPEvent(id="test-event", label="Test Event", points=25)

        # Mock add_xp to return success and old level
        mock_add_xp.return_value = (True, 1)

        # Mock newly completed quests
        mock_quest = MagicMock()
        mock_quest.id = "test-quest"
        mock_quest.name = "Test Quest"
        mock_apply_quests.return_value = [mock_quest]

        # Mock newly earned badges
        mock_check_badges.return_value = ["test-badge"]

        # Act
        result = service.handle_event(event)

        # Assert
        mock_add_xp.assert_called_with(user, event)
        mock_apply_quests.assert_called_with(user)
        mock_check_badges.assert_called_with(user)
        mock_save.assert_called_with(user)

        assert result.xp_added == 25
        assert result.level == 1
        assert result.level_up is False
        assert result.completed_quests == ["test-quest"]
        assert result.earned_badges == ["test-badge"]
        assert result.message is not None
        assert "25 XP" in result.message
        assert "Test Quest" in result.message

    @patch("quackster.core.gamification_service.xp.add_xp")
    @patch("quackster.core.gamification_service.quests.apply_completed_quests")
    @patch("quackster.core.gamification_service.xp._check_xp_badges")
    @patch("quackster.core.gamification_service.utils.save_progress")
    def test_handle_event_level_up(
        self, mock_save, mock_check_badges, mock_apply_quests, mock_add_xp
    ):
        """Test handling an event that causes a level up."""
        # Setup
        user = UserProgress(github_username="testuser", xp=90)
        service = GamificationService(user_progress=user)

        event = XPEvent(id="test-event", label="Test Event", points=20)

        # Mock add_xp to return success and old level
        mock_add_xp.return_value = (True, 1)  # Level 1 before, should be level 2 after

        # No quests or badges for this test
        mock_apply_quests.return_value = []
        mock_check_badges.return_value = []

        # User now has 110 XP, which is level 2
        user.xp = 110

        # Act
        result = service.handle_event(event)

        # Assert
        assert result.xp_added == 20
        assert result.level == 2  # New level
        assert result.level_up is True
        assert "Leveled up to level 2" in result.message

    @patch("quackster.core.gamification_service.xp.add_xp")
    def test_handle_event_already_completed(self, mock_add_xp):
        """Test handling an event that's already been completed."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        event = XPEvent(id="test-event", label="Test Event", points=25)

        # Mock add_xp to return not new and current level
        mock_add_xp.return_value = (False, 1)

        # Act
        result = service.handle_event(event)

        # Assert
        mock_add_xp.assert_called_with(user, event)
        assert result.xp_added == 0
        assert result.level == 1
        assert result.level_up is False
        assert not result.completed_quests
        assert not result.earned_badges
        assert result.message is None

    @patch("quackster.core.gamification_service.utils.save_progress")
    def test_handle_events(self, mock_save):
        """Test handling multiple events."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        event1 = XPEvent(id="event1", label="Event 1", points=10)
        event2 = XPEvent(id="event2", label="Event 2", points=15)

        # Mock the handle_event method to return specific results
        mock_result1 = GamificationResult(
            xp_added=10,
            level=1,
            level_up=False,
            completed_quests=["quest1"],
            earned_badges=[],
            message="Result 1",
        )

        mock_result2 = GamificationResult(
            xp_added=15,
            level=1,
            level_up=False,
            completed_quests=[],
            earned_badges=["badge1"],
            message="Result 2",
        )

        with patch.object(service, "handle_event") as mock_handle_event:
            mock_handle_event.side_effect = [mock_result1, mock_result2]

            # Act
            result = service.handle_events([event1, event2])

            # Assert
            assert mock_handle_event.call_count == 2
            assert result.xp_added == 25
            assert result.level == 1
            assert result.level_up is False
            assert result.completed_quests == ["quest1"]
            assert result.earned_badges == ["badge1"]
            assert "25 total XP" in result.message
