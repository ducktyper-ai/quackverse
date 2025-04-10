"""
Tests for the teaching XP management module.

This module tests the XP management functionality in quackcore.teaching.core.xp.
"""
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.core.models import UserProgress, XPEvent
from quackcore.teaching.core import xp


class TestXPManagement:
    """Tests for XP management functions."""

    @patch("quackcore.teaching.core.xp.badges.get_all_badges")
    @patch("quackcore.teaching.core.xp.logger")
    def test_add_xp_new_event(self, mock_logger, mock_get_all_badges):
        """Test adding XP for a new event."""
        # Setup
        mock_get_all_badges.return_value = []
        user = UserProgress(github_username="testuser", xp=0)
        event = XPEvent(id="test-event", label="Test Event", points=50)

        # Act
        is_new, level_before = xp.add_xp(user, event)

        # Assert
        assert is_new is True
        assert level_before == 1
        assert user.xp == 50
        assert "test-event" in user.completed_event_ids
        mock_logger.info.assert_called_with(
            "Added 50 XP to user from event 'Test Event'"
        )

    @patch("quackcore.teaching.core.xp.badges.get_all_badges")
    @patch("quackcore.teaching.core.xp.logger")
    def test_add_xp_already_completed(self, mock_logger, mock_get_all_badges):
        """Test adding XP for an already completed event."""
        # Setup
        mock_get_all_badges.return_value = []
        user = UserProgress(
            github_username="testuser",
            xp=50,
            completed_event_ids=["test-event"],
        )
        event = XPEvent(id="test-event", label="Test Event", points=50)

        # Act
        is_new, level_before = xp.add_xp(user, event)

        # Assert
        assert is_new is False
        assert level_before == 1
        assert user.xp == 50  # XP should not change
        mock_logger.debug.assert_called_with(
            "User already completed event 'Test Event', no XP added"
        )

    @patch("quackcore.teaching.core.xp.badges.get_all_badges")
    @patch("quackcore.teaching.core.xp.logger")
    @patch("quackcore.teaching.core.xp._handle_level_up")
    def test_add_xp_level_up(self, mock_handle_level_up, mock_logger, mock_get_all_badges):
        """Test adding XP causes a level up."""
        # Setup
        mock_get_all_badges.return_value = []
        user = UserProgress(github_username="testuser", xp=80)
        event = XPEvent(id="test-event", label="Test Event", points=30)

        # Act
        is_new, level_before = xp.add_xp(user, event)

        # Assert
        assert is_new is True
        assert level_before == 1
        assert user.xp == 110
        assert "test-event" in user.completed_event_ids
        mock_handle_level_up.assert_called_once_with(user, 1, 2)
        mock_logger.info.assert_any_call("User leveled up from 1 to 2!")

    @patch("quackcore.teaching.core.xp.logger")
    def test_add_xp_from_quest(self, mock_logger):
        """Test adding XP from completing a quest."""
        # Setup
        user = UserProgress(github_username="testuser", xp=0)
        quest_id = "test-quest"
        xp_amount = 75

        # Mock the add_xp function
        with patch("quackcore.teaching.core.xp.add_xp") as mock_add_xp:
            # Act
            xp.add_xp_from_quest(user, quest_id, xp_amount)

            # Assert
            mock_add_xp.assert_called_once()
            # Verify that an XPEvent with the correct properties was passed
            call_args = mock_add_xp.call_args[0]
            assert call_args[0] is user
            event = call_args[1]
            assert event.id == f"quest-{quest_id}"
            assert "Completed Quest" in event.label
            assert event.points == xp_amount

    def test_handle_level_up(self):
        """Test handling a level-up event."""
        # Setup
        user = UserProgress(github_username="testuser", xp=100)
        old_level = 1
        new_level = 2

        # Mock _check_level_badges to avoid dependencies
        with patch("quackcore.teaching.core.xp._check_level_badges") as mock_check:
            # Act
            xp._handle_level_up(user, old_level, new_level)

            # Assert
            assert f"level-up-{new_level}" in user.completed_event_ids
            mock_check.assert_called_once_with(user, new_level)

    @patch("quackcore.teaching.core.xp.badges.get_all_badges")
    @patch("quackcore.teaching.core.xp.logger")
    def test_check_xp_badges(self, mock_logger, mock_get_all_badges):
        """Test checking for XP-based badges."""
        # Setup
        badge1 = MagicMock()
        badge1.id = "badge1"
        badge1.name = "Badge 1"
        badge1.emoji = "🏆"
        badge1.required_xp = 50

        badge2 = MagicMock()
        badge2.id = "badge2"
        badge2.name = "Badge 2"
        badge2.emoji = "🏅"
        badge2.required_xp = 150

        mock_get_all_badges.return_value = [badge1, badge2]

        user = UserProgress(github_username="testuser", xp=100)

        # Act
        new_badges = xp._check_xp_badges(user)

        # Assert
        assert new_badges == ["badge1"]
        assert "badge1" in user.earned_badge_ids
        assert "badge2" not in user.earned_badge_ids
        mock_logger.info.assert_called_with(
            f"User earned badge: {badge1.name} ({badge1.emoji})"
        )

    @patch("quackcore.teaching.core.xp.badges.get_badge")
    @patch("quackcore.teaching.core.xp.logger")
    def test_check_level_badges(self, mock_logger, mock_get_badge):
        """Test checking for level-based badges."""
        # Setup
        mock_badge = MagicMock()
        mock_badge.name = "Expert Badge"
        mock_badge.emoji = "🌟"
        mock_get_badge.return_value = mock_badge

        user = UserProgress(github_username="testuser", xp=1000)
        level = 10  # This should match "expert" in the level_badges dict

        # Act
        new_badges = xp._check_level_badges(user, level)

        # Assert
        assert new_badges == ["expert"]
        assert "expert" in user.earned_badge_ids
        mock_get_badge.assert_called_with("expert")
        mock_logger.info.assert_called_with(
            f"User earned level badge: {mock_badge.name} ({mock_badge.emoji})"
        )

    def test_calculate_total_possible_xp(self):
        """Test calculating total possible XP."""
        # This is currently a placeholder in the implementation
        # but we should still test the function exists and returns a positive value
        total_xp = xp.calculate_total_possible_xp()
        assert isinstance(total_xp, int)
        assert total_xp > 0