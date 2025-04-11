# tests/test_teaching/test_npc/test_memory.py
"""
Tests for the Quackster NPC memory management.

This module tests the memory management functionality in quackcore.teaching.npc.memory.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.core.models import UserProgress
from quackcore.teaching.npc import memory
from quackcore.teaching.npc.schema import UserMemory


class TestNPCMemory:
    """Tests for NPC memory functionality."""

    def test_get_memory_file_path(self):
        """Test getting the memory file path."""
        # Setup
        mock_data_dir = Path("/test/data/dir")

        with patch("quackcore.teaching.npc.memory.get_user_data_dir",
                   return_value=mock_data_dir):
            # Act
            result = memory._get_memory_file_path()

            # Assert
            assert result == mock_data_dir / "quackster_memory.json"

    @patch("quackcore.teaching.npc.memory.fs.get_file_info")
    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    @patch("quackcore.teaching.npc.memory.logger")
    def test_load_persistent_memory_not_found(self, mock_logger, mock_get_path,
                                              mock_get_file_info):
        """Test loading persistent memory when the file doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock file not found
        mock_get_file_info.return_value = MagicMock(success=True, exists=False)

        # Act
        result = memory._load_persistent_memory("testuser")

        # Assert
        assert result is None
        mock_get_file_info.assert_called_once_with(mock_path)
        mock_logger.debug.assert_called_once()

    @patch("quackcore.teaching.npc.memory.fs.get_file_info")
    @patch("quackcore.teaching.npc.memory.fs.read_json")
    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    @patch("quackcore.teaching.npc.memory.logger")
    def test_load_persistent_memory_read_error(self, mock_logger, mock_get_path,
                                               mock_read_json, mock_get_file_info):
        """Test loading persistent memory when there's an error reading the file."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock file exists but read fails
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)
        mock_read_json.return_value = MagicMock(success=False, error="Read error")

        # Act
        result = memory._load_persistent_memory("testuser")

        # Assert
        assert result is None
        mock_read_json.assert_called_once_with(mock_path)
        mock_logger.warning.assert_called_once()

    @patch("quackcore.teaching.npc.memory.fs.get_file_info")
    @patch("quackcore.teaching.npc.memory.fs.read_json")
    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    def test_load_persistent_memory_wrong_user(self, mock_get_path, mock_read_json,
                                               mock_get_file_info):
        """Test loading persistent memory for a different user."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock file exists and read succeeds, but for a different user
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)
        mock_read_json.return_value = MagicMock(
            success=True,
            data={"github_username": "otheruser",
                  "last_interaction": datetime.now().isoformat()},
        )

        # Act
        result = memory._load_persistent_memory("testuser")

        # Assert
        assert result is None

    @patch("quackcore.teaching.npc.memory.fs.get_file_info")
    @patch("quackcore.teaching.npc.memory.fs.read_json")
    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    @patch("quackcore.teaching.npc.memory.logger")
    def test_load_persistent_memory_expired(self, mock_logger, mock_get_path,
                                            mock_read_json, mock_get_file_info):
        """Test loading persistent memory that has expired."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock file exists and read succeeds, but memory is expired
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)

        # Create a date older than MEMORY_EXPIRES_DAYS
        old_date = datetime.now() - timedelta(days=memory.MEMORY_EXPIRES_DAYS + 1)

        mock_read_json.return_value = MagicMock(
            success=True,
            data={"github_username": "testuser",
                  "last_interaction": old_date.isoformat()},
        )

        # Act
        result = memory._load_persistent_memory("testuser")

        # Assert
        assert result is None
        mock_logger.debug.assert_called_with(
            "Memory has expired, creating fresh memory")

    @patch("quackcore.teaching.npc.memory.fs.get_file_info")
    @patch("quackcore.teaching.npc.memory.fs.read_json")
    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    def test_load_persistent_memory_success(self, mock_get_path, mock_read_json,
                                            mock_get_file_info):
        """Test successfully loading persistent memory."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock file exists and read succeeds
        mock_get_file_info.return_value = MagicMock(success=True, exists=True)

        # Create valid memory data
        memory_data = {
            "github_username": "testuser",
            "last_interaction": datetime.now().isoformat(),
            "xp": 100,
            "level": 2,
            "completed_quests": ["quest1", "quest2"],
            "badges": ["badge1"],
            "conversation_count": 5,
            "interests": ["python", "github"],
            "custom_data": {"key": "value"},
        }

        mock_read_json.return_value = MagicMock(success=True, data=memory_data)

        # Act
        result = memory._load_persistent_memory("testuser")

        # Assert
        assert result == memory_data
        mock_read_json.assert_called_once_with(mock_path)

    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    @patch("quackcore.teaching.npc.memory.fs.write_json")
    @patch("quackcore.teaching.npc.memory.logger")
    def test_save_persistent_memory_success(self, mock_logger, mock_write_json,
                                            mock_get_path):
        """Test successfully saving persistent memory."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock successful write
        mock_write_json.return_value = MagicMock(success=True)

        # Create user memory
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            last_interaction=datetime.now().isoformat(),
        )

        # Act
        result = memory._save_persistent_memory(user_memory)

        # Assert
        assert result is True
        mock_write_json.assert_called_once_with(mock_path, user_memory.model_dump())
        mock_logger.debug.assert_called_once()

    @patch("quackcore.teaching.npc.memory._get_memory_file_path")
    @patch("quackcore.teaching.npc.memory.fs.write_json")
    @patch("quackcore.teaching.npc.memory.logger")
    def test_save_persistent_memory_error(self, mock_logger, mock_write_json,
                                          mock_get_path):
        """Test error when saving persistent memory."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_get_path.return_value = mock_path

        # Mock write error
        mock_write_json.return_value = MagicMock(success=False, error="Write error")

        # Create user memory
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            last_interaction=datetime.now().isoformat(),
        )

        # Act
        result = memory._save_persistent_memory(user_memory)

        # Assert
        assert result is False
        mock_write_json.assert_called_once_with(mock_path, user_memory.model_dump())
        mock_logger.warning.assert_called_once()

    @patch("quackcore.teaching.npc.memory._save_persistent_memory")
    def test_update_user_memory(self, mock_save):
        """Test updating user memory with new information."""
        # Setup
        mock_save.return_value = True

        # Create initial user memory
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            conversation_count=5,
            completed_quests=["quest1"],
            badges=["badge1"],
            interests=["python"],
            custom_data={},
        )

        # User input that includes interests and learning style indicators
        user_input = (
            "I really like working with javascript and docker. "
            "I prefer to see diagrams and visual examples when learning."
        )

        # Act
        updated_memory = memory.update_user_memory(user_memory, user_input)

        # Assert
        assert updated_memory.conversation_count == 6  # Incremented
        assert "javascript" in updated_memory.interests
        assert "docker" in updated_memory.interests
        assert "python" in updated_memory.interests  # Kept old interest
        assert "learning_style" in updated_memory.custom_data
        assert updated_memory.custom_data["learning_style"] == "visual"

        # Verify memory was saved
        mock_save.assert_called_once()

    @patch("quackcore.teaching.npc.memory._save_persistent_memory")
    def test_update_user_memory_with_stuck_points(self, mock_save):
        """Test updating user memory with stuck points."""
        # Setup
        mock_save.return_value = True

        # Create initial user memory
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            conversation_count=5,
            custom_data={},
        )

        # User input indicating being stuck
        user_input = "I am stuck with understanding GitHub integration. Having trouble with pull requests too."

        # Act
        updated_memory = memory.update_user_memory(user_memory, user_input)

        # Assert
        assert "stuck_points" in updated_memory.custom_data
        assert len(updated_memory.custom_data["stuck_points"]) == 2
        assert "GitHub integration" in updated_memory.custom_data["stuck_points"]
        assert "pull requests" in updated_memory.custom_data["stuck_points"]

    @patch("quackcore.teaching.npc.memory._load_persistent_memory")
    @patch("quackcore.teaching.npc.memory.utils.load_progress")
    @patch("quackcore.teaching.npc.memory.quests")
    @patch("quackcore.teaching.npc.memory.badges")
    def test_get_user_memory_new(self, mock_badges, mock_quests, mock_load_progress,
                                 mock_load_persistent):
        """Test getting user memory for a new user (no persistent memory)."""
        # Setup
        # Mock user progress
        mock_user = MagicMock(spec=UserProgress)
        mock_user.github_username = "testuser"
        mock_user.xp = 100
        mock_user.get_level.return_value = 2
        mock_user.completed_quest_ids = ["quest1", "quest2"]
        mock_user.earned_badge_ids = ["badge1"]
        mock_user.get_xp_to_next_level.return_value = 50

        mock_load_progress.return_value = mock_user

        # Mock no persistent memory
        mock_load_persistent.return_value = None

        # Mock quest and badge data
        mock_quest = MagicMock()
        mock_quest.name = "Test Quest"
        mock_quests.get_user_quests.return_value = {
            "completed": [mock_quest],
            "available": [],
        }

        mock_badge = MagicMock()
        mock_badge.name = "Test Badge"
        mock_badges.get_user_badges.return_value = [mock_badge]

        mock_suggested_quest = MagicMock()
        mock_suggested_quest.id = "quest3"
        mock_suggested_quest.name = "Suggested Quest"
        mock_suggested_quest.description = "A suggested quest"
        mock_suggested_quest.reward_xp = 20
        mock_quests.get_suggested_quests.return_value = [mock_suggested_quest]

        # Act
        result = memory.get_user_memory()

        # Assert
        assert isinstance(result, UserMemory)
        assert result.github_username == "testuser"
        assert result.xp == 100
        assert result.level == 2
        assert set(result.completed_quests) == {"quest1", "quest2"}
        assert set(result.badges) == {"badge1"}
        assert result.conversation_count == 0  # New user
        assert "last_interaction" in result.dict()
        assert "badge_names" in result.custom_data
        assert "completed_quest_names" in result.custom_data
        assert "xp_to_next_level" in result.custom_data