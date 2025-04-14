# tests/quackster/test_npc/test_tools/test_quest_tools.py
"""
Tests for the quest tools in quackster.npc.tools.quest_tools.

This module tests the functions for retrieving quest information,
listing available quests, suggesting next quests, and verifying quest completion.
"""

from unittest.mock import MagicMock

import pytest

from quackster.npc.schema import UserMemory
from quackster.npc.tools import (
    QuestCompletionOutput,
    QuestDetailOutput,
    QuestListOutput,
    quest_tools,
)


class TestQuestTools:
    """Tests for quest tools functionality."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object for testing."""
        user = MagicMock()
        user.has_completed_quest.return_value = False
        return user

    @pytest.fixture
    def user_memory_basic(self):
        """Create a basic UserMemory object for testing."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            completed_quests=["quest1", "quest2"],
            custom_data={},
        )

    @pytest.fixture
    def user_memory_with_suggested_quests(self):
        """Create a UserMemory with suggested quests."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            completed_quests=["quest1", "quest2"],
            custom_data={
                "suggested_quests": [
                    {"id": "quest3", "name": "Quest 3", "description": "Third quest"},
                ],
                "recent_quests_discussed": ["quest3"],
            },
        )

    @pytest.fixture
    def user_memory_with_learning_style(self):
        """Create a UserMemory with learning style."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            completed_quests=["quest1", "quest2"],
            custom_data={"learning_style": "challenge"},
        )

    @pytest.fixture
    def mock_quests(self):
        """Create mock quest objects."""
        quest1 = MagicMock()
        quest1.id = "quest1"
        quest1.name = "Quest 1"
        quest1.description = "First quest"
        quest1.reward_xp = 10
        quest1.badge_id = None

        quest2 = MagicMock()
        quest2.id = "quest2"
        quest2.name = "Quest 2"
        quest2.description = "Second quest"
        quest2.reward_xp = 20
        quest2.badge_id = "badge1"

        quest3 = MagicMock()
        quest3.id = "quest3"
        quest3.name = "Quest 3"
        quest3.description = "Third quest"
        quest3.reward_xp = 30
        quest3.badge_id = "badge2"

        return [quest1, quest2, quest3]

    def test_list_quests_basic(self, mocker, mock_user, mock_quests, user_memory_basic):
        """Test the list_quests function with basic UserMemory."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_user_quests.return_value = {
            "completed": mock_quests[:2],  # First two quests completed
            "available": [mock_quests[2]],  # Third quest available
        }
        mock_quests_module.get_suggested_quests.return_value = [mock_quests[2]]

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestListOutput(
            name="list_quests",
            result=MagicMock(),
            formatted_text="Quest list output",
        )

        # Call the function
        result = quest_tools.list_quests(user_memory_basic)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_user_quests.assert_called_once_with(mock_user)
        mock_quests_module.get_suggested_quests.assert_called_once_with(
            mock_user, limit=3
        )
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "list_quests"
        assert args[1]["completed_count"] == 2
        assert args[1]["available_count"] == 1
        assert len(args[1]["completed"]) == 2
        assert len(args[1]["available"]) == 1
        assert len(args[1]["suggested"]) == 1
        assert "formatted_text" in args[1]

        # Verify result
        assert isinstance(result, QuestListOutput)

    def test_list_quests_with_suggested_quests(
        self, mocker, mock_user, mock_quests, user_memory_with_suggested_quests
    ):
        """Test list_quests with suggested quests in user_memory."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_user_quests.return_value = {
            "completed": mock_quests[:2],  # First two quests completed
            "available": [mock_quests[2]],  # Third quest available
        }
        mock_quests_module.get_quest.return_value = mock_quests[2]

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestListOutput(
            name="list_quests",
            result=MagicMock(),
            formatted_text="Quest list with suggested quests",
        )

        # Call the function
        result = quest_tools.list_quests(user_memory_with_suggested_quests)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_user_quests.assert_called_once_with(mock_user)
        mock_quests_module.get_quest.assert_called_once_with("quest3")
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "list_quests"
        assert args[1]["completed_count"] == 2
        assert args[1]["available_count"] == 1
        assert len(args[1]["suggested"]) == 1
        assert args[1]["suggested"][0].id == "quest3"
        assert (
            "recent_quests_discussed" in user_memory_with_suggested_quests.custom_data
        )
        assert "formatted_text" in args[1]
        assert "asking about 'quest3'" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestListOutput)

    def test_list_quests_with_learning_style(
        self, mocker, mock_user, mock_quests, user_memory_with_learning_style
    ):
        """Test list_quests with learning style in user_memory."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_user_quests.return_value = {
            "completed": mock_quests[:2],  # First two quests completed
            "available": [mock_quests[2]],  # Third quest available
        }
        mock_quests_module.get_suggested_quests.return_value = [mock_quests[2]]

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestListOutput(
            name="list_quests",
            result=MagicMock(),
            formatted_text="Quest list with learning style",
        )

        # Call the function
        result = quest_tools.list_quests(user_memory_with_learning_style)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_user_quests.assert_called_once_with(mock_user)
        mock_quests_module.get_suggested_quests.assert_called_once_with(
            mock_user, limit=3
        )
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert "learning_style" in user_memory_with_learning_style.custom_data
        assert "formatted_text" in args[1]
        # The response should be adapted for challenge learning style
        assert (
            "challenge" in user_memory_with_learning_style.custom_data["learning_style"]
        )

        # Verify result
        assert isinstance(result, QuestListOutput)

    def test_get_quest_details(self, mocker, mock_user, mock_quests):
        """Test the get_quest_details function."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_quest.return_value = mock_quests[0]

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.side_effect = lambda quest_id, dialogue_type: {
            "guidance": "Quest guidance",
            "hint": "Quest hint",
        }.get(dialogue_type)
        mock_registry.render_quest_intro.return_value = "Rendered quest intro"

        mock_rag = mocker.patch("quackster.npc.tools.quest_tools.rag")
        mock_rag.get_quest_info.return_value = {
            "guidance": "RAG quest guidance",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="get_quest_details",
            result=MagicMock(),
            formatted_text="Quest details output",
        )

        # Call the function
        result = quest_tools.get_quest_details("quest1")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_quest.assert_called_once_with("quest1")
        mock_user.has_completed_quest.assert_called_once_with("quest1")
        mock_registry.render_quest_intro.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "get_quest_details"
        assert args[1]["id"] == "quest1"
        assert args[1]["name"] == "Quest 1"
        assert args[1]["description"] == "First quest"
        assert args[1]["is_completed"] is False
        assert args[1]["guidance"] == "Quest guidance"
        assert args[1]["hint"] == "Quest hint"
        assert args[1]["formatted_text"] == "Rendered quest intro"

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_get_quest_details_nonexistent_quest(self, mocker, mock_user):
        """Test get_quest_details with a nonexistent quest."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_quest.return_value = None  # Quest not found

        mock_rag = mocker.patch("quackster.npc.tools.quest_tools.rag")
        mock_rag.get_quest_info.return_value = {
            "name": "Unknown Quest",
            "description": "Quest information not found",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="get_quest_details",
            result=MagicMock(),
            formatted_text="Quest not found",
        )

        # Call the function
        result = quest_tools.get_quest_details("nonexistent-quest")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_quest.assert_called_once_with("nonexistent-quest")
        mock_standardize.assert_called_once()

        # Check that the standardized output contains placeholder data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_quest_details"
        assert args[1]["id"] == "nonexistent-quest"
        assert "not found" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_get_quest_details_completed_quest(self, mocker, mock_user, mock_quests):
        """Test get_quest_details with a completed quest."""
        # Configure mock user to have completed the quest
        mock_user.has_completed_quest.return_value = True

        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_quest.return_value = mock_quests[0]

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.return_value = "Quest guidance"
        mock_registry.render_quest_intro.return_value = "Rendered completed quest intro"

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="get_quest_details",
            result=MagicMock(),
            formatted_text="Completed quest details",
        )

        # Call the function
        result = quest_tools.get_quest_details("quest1")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_quest.assert_called_once_with("quest1")
        mock_user.has_completed_quest.assert_called_once_with("quest1")
        mock_registry.render_quest_intro.assert_called_once()
        mock_standardize.assert_called_once()

        # Check that the standardized output shows the quest as completed
        args = mock_standardize.call_args[0]
        assert args[0] == "get_quest_details"
        assert args[1]["is_completed"] is True

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_get_quest_details_render_failure(self, mocker, mock_user, mock_quests):
        """Test get_quest_details when template rendering fails."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_quest.return_value = mock_quests[0]

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.return_value = "Quest guidance"
        # Simulate a rendering error
        mock_registry.render_quest_intro.side_effect = Exception("Rendering error")

        # Mock logger
        mock_logger = mocker.patch("quackster.npc.tools.quest_tools.logger")

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="get_quest_details",
            result=MagicMock(),
            formatted_text="Quest details fallback",
        )

        # Call the function
        result = quest_tools.get_quest_details("quest1")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_quest.assert_called_once_with("quest1")
        mock_registry.render_quest_intro.assert_called_once()
        mock_logger.error.assert_called_once()
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_suggest_next_quest_from_memory(
        self, mocker, mock_user, mock_quests, user_memory_with_suggested_quests
    ):
        """Test suggest_next_quest using quests from user_memory."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_quest.return_value = mock_quests[2]

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.side_effect = lambda quest_id, dialogue_type: {
            "guidance": "Quest guidance",
            "hint": "Quest hint",
        }.get(dialogue_type)
        mock_registry.render_quest_intro.return_value = "Rendered suggested quest intro"

        mock_rag = mocker.patch("quackster.npc.tools.quest_tools.rag")
        mock_rag.get_quest_info.return_value = {
            "guidance": "RAG quest guidance",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="suggest_next_quest",
            result=MagicMock(),
            formatted_text="Suggested quest output",
        )

        # Call the function
        result = quest_tools.suggest_next_quest(user_memory_with_suggested_quests)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_quest.assert_called_once_with("quest3")
        mock_registry.render_quest_intro.assert_called_once()
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "suggest_next_quest"
        assert args[1]["id"] == "quest3"
        assert args[1]["name"] == "Quest 3"
        assert args[1]["has_suggestion"] is True
        assert "guidance" in args[1]
        assert "hint" in args[1]
        assert "formatted_text" in args[1]

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_suggest_next_quest_from_quests_module(
        self, mocker, mock_user, mock_quests, user_memory_basic
    ):
        """Test suggest_next_quest using quests from quests module."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_suggested_quests.return_value = [mock_quests[2]]
        mock_quests_module.get_quest.return_value = mock_quests[2]

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.side_effect = lambda quest_id, dialogue_type: {
            "guidance": "Quest guidance",
            "hint": "Quest hint",
        }.get(dialogue_type)
        mock_registry.render_quest_intro.return_value = "Rendered suggested quest intro"

        mock_rag = mocker.patch("quackster.npc.tools.quest_tools.rag")
        mock_rag.get_quest_info.return_value = {
            "guidance": "RAG quest guidance",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="suggest_next_quest",
            result=MagicMock(),
            formatted_text="Suggested quest output",
        )

        # Call the function
        result = quest_tools.suggest_next_quest(user_memory_basic)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_suggested_quests.assert_called_once_with(
            mock_user, limit=1
        )
        mock_registry.render_quest_intro.assert_called_once()
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_suggest_next_quest_no_suggestions(
        self, mocker, mock_user, user_memory_basic
    ):
        """Test suggest_next_quest with no available suggestions."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.get_suggested_quests.return_value = []  # No suggested quests

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestDetailOutput(
            name="suggest_next_quest",
            result=MagicMock(),
            formatted_text="No quest suggestions available",
        )

        # Call the function
        result = quest_tools.suggest_next_quest(user_memory_basic)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.get_suggested_quests.assert_called_once_with(
            mock_user, limit=1
        )
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "suggest_next_quest"
        assert args[1]["has_suggestion"] is False
        assert "No quest suggestions" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestDetailOutput)

    def test_verify_quest_completion_no_new_quests(
        self, mocker, mock_user, user_memory_basic
    ):
        """Test verify_quest_completion with no newly completed quests."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.check_quest_completion.return_value = []  # No newly completed quests

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestCompletionOutput(
            name="verify_quest_completion",
            result=MagicMock(),
            formatted_text="No newly completed quests",
        )

        # Call the function
        result = quest_tools.verify_quest_completion(user_memory_basic)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.check_quest_completion.assert_called_once_with(mock_user)
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "verify_quest_completion"
        assert args[1]["quests_completed"] is False
        assert args[1]["completed_quests"] == []
        assert args[1]["total_completed_count"] == 0
        assert "No newly completed quests" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestCompletionOutput)

    def test_verify_quest_completion_with_new_quests(
        self, mocker, mock_user, mock_quests, user_memory_basic
    ):
        """Test verify_quest_completion with newly completed quests."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.check_quest_completion.return_value = [
            mock_quests[2]
        ]  # Newly completed quest
        mock_quests_module.complete_quest = MagicMock()

        mock_badges_module = mocker.patch("quackster.npc.tools.quest_tools.badges")
        badge = MagicMock()
        badge.id = "badge2"
        badge.name = "Badge 2"
        badge.emoji = "🎖️"
        mock_badges_module.get_badge.return_value = badge

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.return_value = "Completion message"

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestCompletionOutput(
            name="verify_quest_completion",
            result=MagicMock(),
            formatted_text="Quest completion output",
            badge_awarded=True,
            xp_gained=30,
        )

        # Call the function
        result = quest_tools.verify_quest_completion(user_memory_basic)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.check_quest_completion.assert_called_once_with(mock_user)
        mock_quests_module.complete_quest.assert_called_once_with(mock_user, "quest3")
        mock_utils.save_progress.assert_called_once_with(mock_user)
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "verify_quest_completion"
        assert args[1]["quests_completed"] is True
        assert len(args[1]["completed_quests"]) == 1
        assert args[1]["completed_quests"][0].id == "quest3"
        assert args[1]["badge_awarded"] is True
        assert args[1]["xp_gained"] == 30
        assert "QUEST COMPLETED" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestCompletionOutput)
        assert result.badge_awarded is True
        assert result.xp_gained == 30

    def test_verify_quest_completion_with_level_up(
        self, mocker, mock_user, mock_quests, user_memory_basic
    ):
        """Test verify_quest_completion with level up."""
        # Set up user_memory with XP close to level up
        user_memory = UserMemory(
            github_username="testuser",
            xp=195,  # Level 2, close to level 3
            level=2,
            completed_quests=["quest1", "quest2"],
            custom_data={},
        )

        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.quest_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_quests_module = mocker.patch("quackster.npc.tools.quest_tools.quests")
        mock_quests_module.check_quest_completion.return_value = [
            mock_quests[2]
        ]  # Newly completed quest (30 XP)
        mock_quests_module.complete_quest = MagicMock()

        mock_registry = mocker.patch("quackster.npc.tools.quest_tools.DialogueRegistry")
        mock_registry.get_quest_dialogue.return_value = "Completion message"

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.quest_tools.standardize_tool_output"
        )
        mock_standardize.return_value = QuestCompletionOutput(
            name="verify_quest_completion",
            result=MagicMock(),
            formatted_text="Quest completion with level up",
            xp_gained=30,
            level_up=True,
        )

        # Call the function
        result = quest_tools.verify_quest_completion(user_memory)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_quests_module.check_quest_completion.assert_called_once_with(mock_user)
        mock_quests_module.complete_quest.assert_called_once_with(mock_user, "quest3")
        mock_utils.save_progress.assert_called_once_with(mock_user)
        mock_standardize.assert_called_once()

        # Check the data passed to standardize_tool_output
        args = mock_standardize.call_args[0]
        assert args[0] == "verify_quest_completion"
        assert args[1]["quests_completed"] is True
        assert args[1]["xp_gained"] == 30
        assert args[1]["level_up"] is True
        assert args[1]["old_level"] == 2
        assert args[1]["new_level"] == 3
        assert "LEVEL UP" in args[1]["formatted_text"]

        # Verify result
        assert isinstance(result, QuestCompletionOutput)
        assert result.level_up is True
