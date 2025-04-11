# tests/test_teaching/test_gamification/test_base.py
"""
Tests for the base functionality of the gamification service.

This module tests initialization and basic event handling in the gamification service.
"""
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.core.models import UserProgress, XPEvent
from quackcore.teaching.core.gamification_service import GamificationResult, GamificationService


class TestGamificationServiceBase:
    """Tests for base functionality of the gamification service."""

    def test_init(self):
        """Test initializing the gamification service."""
        # Setup & Act
        mock_progress = MagicMock(spec=UserProgress)
        service = GamificationService(user_progress=mock_progress)

        # Assert
        assert service.progress == mock_progress
        assert service._changed is False

    @patch("quackcore.teaching.core.gamification_service.utils.load_progress")
    def test_init_default(self, mock_load_progress):
        """Test initializing the service with default progress."""
        # Setup
        mock_progress = MagicMock(spec=UserProgress)
        mock_load_progress.return_value = mock_progress

        # Act
        service = GamificationService()

        # Assert
        assert service.progress == mock_progress
        mock_load_progress.assert_called_once()

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_save(self, mock_save):
        """Test saving changes."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)
        service._changed = True

        # Act
        service.save()

        # Assert
        mock_save.assert_called_with(user)
        assert service._changed is False

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_save_no_changes(self, mock_save):
        """Test saving when no changes have been made."""
        # Setup
        user = UserProgress(github_username="testuser")
        service = GamificationService(user_progress=user)
        service._changed = False

        # Act
        service.save()

        # Assert
        mock_save.assert_not_called()
        assert service._changed is False