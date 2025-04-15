# tests/quackster/test_gamification/test_badges.py
"""
Tests for badge-related functionality in the gamification service.

This module tests badge award and management in the gamification service.
"""

from unittest.mock import MagicMock, patch

from quackster.core.gamification_service import GamificationService
from quackster.core.models import UserProgress


class TestGamificationServiceBadges:
    """Tests for badge-related functionality in the gamification service."""

    @patch("quackster.core.gamification_service.badges")
    @patch("quackster.core.gamification_service.api.save_progress")
    def test_award_badge(self, mock_save, mock_badges):
        """Test awarding a badge."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)

        badge_id = "test-badge"

        # Set up badge mock
        mock_badge = MagicMock()
        mock_badge.id = badge_id
        mock_badge.name = "Test Badge"
        mock_badge.emoji = "🏆"
        mock_badges.get_badge.return_value = mock_badge

        # Mock award_badge to succeed
        mock_badges.award_badge.return_value = True

        # Act
        result = service.award_badge(badge_id)

        # Assert
        mock_badges.get_badge.assert_called_with(badge_id)
        mock_badges.award_badge.assert_called_with(user, badge_id)
        mock_save.assert_called_with(user)

        assert result.earned_badges == [badge_id]
        assert "Test Badge" in result.message
        assert "🏆" in result.message

    @patch("quackster.core.gamification_service.badges")
    @patch("quackster.core.gamification_service.logger")
    def test_award_badge_nonexistent(self, mock_logger, mock_badges):
        """Test awarding a non-existent badge."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)

        badge_id = "nonexistent-badge"

        # Mock get_badge to return None
        mock_badges.get_badge.return_value = None

        # Act
        result = service.award_badge(badge_id)

        # Assert
        mock_badges.get_badge.assert_called_with(badge_id)
        mock_logger.warning.assert_called()

        assert not result.earned_badges
        assert badge_id in result.message
        assert "not found" in result.message

    @patch("quackster.core.gamification_service.badges")
    def test_award_badge_already_earned(self, mock_badges):
        """Test awarding an already earned badge."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)

        badge_id = "test-badge"

        # Set up badge mock
        mock_badge = MagicMock()
        mock_badge.id = badge_id
        mock_badge.name = "Test Badge"
        mock_badges.get_badge.return_value = mock_badge

        # Mock award_badge to fail (already earned)
        mock_badges.award_badge.return_value = False

        # Act
        result = service.award_badge(badge_id)

        # Assert
        mock_badges.award_badge.assert_called_with(user, badge_id)

        assert not result.earned_badges
        assert "already earned" in result.message
