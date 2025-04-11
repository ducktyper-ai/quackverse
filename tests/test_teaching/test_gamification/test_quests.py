# tests/test_teaching/test_gamification/test_quests.py
"""
Tests for quest-related functionality in the gamification service.

This module tests quest completion and management in the gamification service.
"""
from unittest.mock import MagicMock, patch

from quackcore.teaching.core.models import UserProgress
from quackcore.teaching.core.gamification_service import GamificationService


class TestGamificationServiceQuests:
    """Tests for quest-related functionality in the gamification service."""

    @patch("quackcore.teaching.core.gamification_service.quests")
    @patch("quackcore.teaching.core.gamification_service.xp")
    @patch("quackcore.teaching.core.gamification_service.badges")
    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    @patch("quackcore.teaching.core.gamification_service.logger")
    def test_complete_quest(self, mock_logger, mock_save, mock_badges, mock_xp,
                            mock_quests):
        """Test completing a quest."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        quest_id = "test-quest"
        quest_name = "Test Quest"
        reward_xp = 25
        badge_id = "test-badge"

        # Set up quest mock
        mock_quest = MagicMock()
        mock_quest.id = quest_id
        mock_quest.name = quest_name
        mock_quest.reward_xp = reward_xp
        mock_quest.badge_id = badge_id
        mock_quests.get_quest.return_value = mock_quest

        # Mock quest completion to succeed
        mock_quests.complete_quest.return_value = True

        # Mock badge object for message formatting
        mock_badge = MagicMock()
        mock_badge.name = "Test Badge"
        mock_badge.emoji = "🏆"
        mock_badges.get_badge.return_value = mock_badge

        # Act
        result = service.complete_quest(quest_id)

        # Assert
        mock_quests.get_quest.assert_called_with(quest_id)
        mock_quests.complete_quest.assert_called_with(user, quest_id, forced=True)
        mock_xp.add_xp_from_quest.assert_called_with(user, quest_id, reward_xp)
        mock_save.assert_called_with(user)

        assert result.xp_added == reward_xp
        assert result.completed_quests == [quest_id]
        assert result.earned_badges == [badge_id]
        assert quest_name in result.message
        assert "🏆" in result.message
        assert str(reward_xp) in result.message

    @patch("quackcore.teaching.core.gamification_service.quests")
    @patch("quackcore.teaching.core.gamification_service.logger")
    def test_complete_quest_nonexistent(self, mock_logger, mock_quests):
        """Test completing a non-existent quest."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)

        quest_id = "nonexistent-quest"

        # Mock get_quest to return None
        mock_quests.get_quest.return_value = None

        # Act
        result = service.complete_quest(quest_id)

        # Assert
        mock_quests.get_quest.assert_called_with(quest_id)
        mock_logger.warning.assert_called()

        assert result.xp_added == 0
        assert not result.completed_quests
        assert not result.earned_badges
        assert quest_id in result.message
        assert "not found" in result.message

    @patch("quackcore.teaching.core.gamification_service.quests")
    @patch("quackcore.teaching.core.gamification_service.logger")
    def test_complete_quest_already_completed(self, mock_logger, mock_quests):
        """Test completing an already completed quest."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)

        quest_id = "test-quest"

        # Set up quest mock
        mock_quest = MagicMock()
        mock_quest.id = quest_id
        mock_quest.name = "Test Quest"
        mock_quests.get_quest.return_value = mock_quest

        # Mock quest completion to fail (already completed)
        mock_quests.complete_quest.return_value = False

        # Act
        result = service.complete_quest(quest_id)

        # Assert
        mock_quests.complete_quest.assert_called_with(user, quest_id, forced=True)

        assert result.xp_added == 0
        assert not result.completed_quests
        assert not result.earned_badges
        assert "already completed" in result.message