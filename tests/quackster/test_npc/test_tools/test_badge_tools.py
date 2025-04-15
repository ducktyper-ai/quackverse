# tests/quackster/test_npc/test_tools/test_badge_tools.py
"""
Tests for the badge tools in quackster.npc.tools.badge_tools.

This module tests the functions for retrieving badge information,
listing earned badges, and checking badge progress.
"""

from unittest.mock import MagicMock

import pytest

from quackster.npc.schema import UserMemory
from quackster.npc.tools import BadgeDetailOutput, BadgeListOutput, badge_tools


class TestBadgeTools:
    """Tests for badge tools functionality."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object for testing."""
        user = MagicMock()
        user.has_earned_badge.return_value = False
        return user

    @pytest.fixture
    def mock_badge(self):
        """Create a mock badge object for testing."""
        badge = MagicMock()
        badge.id = "test-badge"
        badge.name = "Test Badge"
        badge.emoji = "🏆"
        badge.description = "A test badge"
        badge.required_xp = 100
        return badge

    @pytest.fixture
    def user_memory(self):
        """Create a UserMemory object for testing."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            badges=["badge1", "badge2"],
            interests=["coding", "badges"],
            custom_data={},
        )

    def test_list_badges(self, mocker, mock_user, user_memory):
        """Test the list_badges function."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")

        # Create mock badge objects
        badge1 = MagicMock()
        badge1.id = "badge1"
        badge1.name = "Badge 1"
        badge1.emoji = "🏆"
        badge1.description = "First badge"
        badge1.required_xp = 50

        badge2 = MagicMock()
        badge2.id = "badge2"
        badge2.name = "Badge 2"
        badge2.emoji = "🎖️"
        badge2.description = "Second badge"
        badge2.required_xp = 100

        next_badge = MagicMock()
        next_badge.id = "next-badge"
        next_badge.name = "Next Badge"
        next_badge.emoji = "🥇"
        next_badge.description = "Next badge to earn"
        next_badge.required_xp = 200

        # Set up mock returns
        mock_badges.get_badge.side_effect = lambda badge_id: {
            "badge1": badge1,
            "badge2": badge2,
            "next-badge": next_badge,
        }.get(badge_id)

        mock_badges.get_next_badges.return_value = [next_badge]
        mock_badges.get_badge_progress.return_value = 0.5  # 50% progress

        # Mock standardize_tool_output to avoid external dependencies
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeListOutput(
            name="list_badges",
            result=MagicMock(),
            formatted_text="Badge list output",
        )

        # Call the function
        result = badge_tools.list_badges(user_memory)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_badge.assert_any_call("badge1")
        mock_badges.get_badge.assert_any_call("badge2")
        mock_badges.get_next_badges.assert_called_once_with(mock_user, limit=3)
        mock_badges.get_badge_progress.assert_called_once_with(mock_user, "next-badge")
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeListOutput)
        assert result.name == "list_badges"

        # Check that the standardized output contains the correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "list_badges"
        assert "earned_badges" in args[1]
        assert "earned_count" in args[1]
        assert "earned_formatted" in args[1]
        assert "next_badges" in args[1]
        assert "next_badges_formatted" in args[1]
        assert "formatted_text" in args[1]

    def test_list_badges_with_no_earned_badges(self, mocker, mock_user):
        """Test list_badges with no earned badges."""
        # Create user memory with no badges
        user_memory = UserMemory(
            github_username="testuser",
            xp=50,
            level=1,
            badges=[],
            interests=[],
            custom_data={},
        )

        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")
        mock_badges.get_next_badges.return_value = []

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeListOutput(
            name="list_badges",
            result=MagicMock(),
            formatted_text="No badges earned yet",
        )

        # Call the function
        result = badge_tools.list_badges(user_memory)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_next_badges.assert_called_once_with(mock_user, limit=3)
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeListOutput)

        # Check that the standardized output contains the correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "list_badges"
        assert args[1]["earned_count"] == 0
        assert len(args[1]["earned_badges"]) == 0

    def test_get_badge_details(self, mocker, mock_user, mock_badge):
        """Test the get_badge_details function."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")
        mock_badges.get_badge.return_value = mock_badge
        mock_badges.get_badge_progress.return_value = 0.5  # 50% progress

        mock_registry = mocker.patch("quackster.npc.tools.badge_tools.DialogueRegistry")
        mock_registry.get_badge_dialogue.return_value = "Badge description"
        mock_registry.render_badge_status.return_value = "Rendered badge status"

        mock_rag = mocker.patch("quackster.npc.tools.badge_tools.rag")
        mock_rag.get_badge_info.return_value = {
            "description": "RAG badge description",
            "guidance": "RAG badge guidance",
            "fun_fact": "RAG badge fun fact",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeDetailOutput(
            name="get_badge_details",
            result=MagicMock(),
            formatted_text="Badge details output",
        )

        # Call the function
        result = badge_tools.get_badge_details("test-badge")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_badge.assert_called_once_with("test-badge")
        mock_user.has_earned_badge.assert_called_once_with("test-badge")
        mock_badges.get_badge_progress.assert_called_once_with(mock_user, "test-badge")
        mock_registry.render_badge_status.assert_called_once()
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeDetailOutput)
        assert result.name == "get_badge_details"

        # Check that the standardized output contains the correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_badge_details"
        assert args[1]["id"] == "test-badge"
        assert args[1]["name"] == "Test Badge"
        assert args[1]["emoji"] == "🏆"
        assert args[1]["description"] == "Badge description"
        assert args[1]["is_earned"] is False
        assert args[1]["progress"] == 50.0

    def test_get_badge_details_nonexistent_badge(self, mocker, mock_user):
        """Test get_badge_details with a nonexistent badge."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")
        mock_badges.get_badge.return_value = None  # Badge not found

        mock_rag = mocker.patch("quackster.npc.tools.badge_tools.rag")
        mock_rag.get_badge_info.return_value = {
            "name": "Unknown Badge",
            "description": "Badge information not found",
        }

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeDetailOutput(
            name="get_badge_details",
            result=MagicMock(),
            formatted_text="Badge not found",
        )

        # Call the function
        result = badge_tools.get_badge_details("nonexistent-badge")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_badge.assert_called_once_with("nonexistent-badge")
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeDetailOutput)

        # Check that the standardized output contains placeholder data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_badge_details"
        assert args[1]["id"] == "nonexistent-badge"
        assert "Badge not found" in args[1]["formatted_text"]

    def test_get_badge_details_earned_badge(self, mocker, mock_user, mock_badge):
        """Test get_badge_details with an earned badge."""
        # Configure mock user to have earned the badge
        mock_user.has_earned_badge.return_value = True

        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")
        mock_badges.get_badge.return_value = mock_badge
        mock_badges.get_badge_progress.return_value = 1.0  # 100% progress

        mock_registry = mocker.patch("quackster.npc.tools.badge_tools.DialogueRegistry")
        mock_registry.get_badge_dialogue.return_value = "Badge description"
        mock_registry.render_badge_status.return_value = (
            "Rendered badge status (earned)"
        )

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeDetailOutput(
            name="get_badge_details",
            result=MagicMock(),
            formatted_text="Badge details output (earned)",
        )

        # Call the function
        result = badge_tools.get_badge_details("test-badge")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_badge.assert_called_once_with("test-badge")
        mock_user.has_earned_badge.assert_called_once_with("test-badge")
        mock_registry.render_badge_status.assert_called_once()
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeDetailOutput)

        # Check that the standardized output shows the badge as earned
        args = mock_standardize.call_args[0]
        assert args[0] == "get_badge_details"
        assert args[1]["is_earned"] is True

    def test_get_badge_details_render_failure(self, mocker, mock_user, mock_badge):
        """Test get_badge_details when template rendering fails."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.badge_tools.api")
        mock_utils.load_progress.return_value = mock_user

        mock_badges = mocker.patch("quackster.npc.tools.badge_tools.badges")
        mock_badges.get_badge.return_value = mock_badge
        mock_badges.get_badge_progress.return_value = 0.5  # 50% progress

        mock_registry = mocker.patch("quackster.npc.tools.badge_tools.DialogueRegistry")
        mock_registry.get_badge_dialogue.return_value = "Badge description"
        # Simulate a rendering error
        mock_registry.render_badge_status.side_effect = Exception("Rendering error")

        # Mock logger
        mock_logger = mocker.patch("quackster.npc.tools.badge_tools.logger")

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.badge_tools.standardize_tool_output"
        )
        mock_standardize.return_value = BadgeDetailOutput(
            name="get_badge_details",
            result=MagicMock(),
            formatted_text="Badge details fallback",
        )

        # Call the function
        result = badge_tools.get_badge_details("test-badge")

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_badges.get_badge.assert_called_once_with("test-badge")
        mock_registry.render_badge_status.assert_called_once()
        mock_logger.error.assert_called_once()
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, BadgeDetailOutput)

        # Check that the standardized output contains fallback formatted text
        args = mock_standardize.call_args[0]
        assert args[0] == "get_badge_details"
        assert "formatted_text" in args[1]
