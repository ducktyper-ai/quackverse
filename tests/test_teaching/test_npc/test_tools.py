# tests/test_teaching/test_npc/test_tools.py
"""
Tests for the Quackster NPC tools functionality.

This module tests the tools functionality in quackcore.teaching.npc.tools.
"""
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.npc.schema import UserMemory
from quackcore.teaching.npc.tools import (
    ToolType,
    badge_tools,
    certificate_tools,
    common,
    progress_tools,
    quest_tools,
    schema,
    tutorial_tools,
    utils,
)


class TestNPCTools:
    """Tests for NPC tools functionality."""

    def test_tool_registry(self):
        """Test that the tool registry contains all necessary tools."""
        from quackcore.teaching.npc.tools import TOOL_REGISTRY

        # Check that essential tools are registered
        assert "list_xp_and_level" in TOOL_REGISTRY
        assert "list_badges" in TOOL_REGISTRY
        assert "get_badge_details" in TOOL_REGISTRY
        assert "list_quests" in TOOL_REGISTRY
        assert "get_quest_details" in TOOL_REGISTRY
        assert "suggest_next_quest" in TOOL_REGISTRY
        assert "verify_quest_completion" in TOOL_REGISTRY
        assert "get_tutorial" in TOOL_REGISTRY
        assert "get_certificate_info" in TOOL_REGISTRY

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_basic(self, mock_registry):
        """Test basic functionality of standardize_tool_output."""
        # Setup
        mock_registry.flavor_text.return_value = "Quacktastic! Result text 🦆"

        tool_name = "test_tool"
        result = {
            "key1": "value1",
            "key2": "value2",
            "formatted_text": "Result text",
        }

        # Act
        output = common.standardize_tool_output(tool_name, result)

        # Assert
        assert output.name == tool_name
        assert output.type == ToolType.META
        assert output.formatted_text == "Quacktastic! Result text 🦆"
        assert output.result == result
        assert output.badge_awarded is False
        assert output.xp_gained == 0
        assert output.quests_completed is False
        assert output.level_up is False

        mock_registry.flavor_text.assert_called_once()

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_flavor_disabled(self, mock_registry):
        """Test standardize_tool_output with flavor disabled."""
        # Setup
        tool_name = "test_tool"
        result = {
            "formatted_text": "Result text",
        }

        # Act
        output = common.standardize_tool_output(tool_name, result, flavor=False)

        # Assert
        assert output.formatted_text == "Result text"
        mock_registry.flavor_text.assert_not_called()

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_metadata(self, mock_registry):
        """Test standardize_tool_output with metadata."""
        # Setup
        mock_registry.flavor_text.return_value = "Result text 🦆"

        tool_name = "test_tool"
        result = {
            "formatted_text": "Result text",
            "badge_awarded": True,
            "xp_gained": 50,
            "quests_completed": True,
            "level_up": True,
        }

        # Act
        output = common.standardize_tool_output(tool_name, result)

        # Assert
        assert output.badge_awarded is True
        assert output.xp_gained == 50
        assert output.quests_completed is True
        assert output.level_up is True

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_quest_list(self, mock_registry):
        """Test standardize_tool_output with quest list output."""
        # Setup
        mock_registry.flavor_text.return_value = "Quest list 🦆"

        tool_name = "list_quests"
        result = {
            "formatted_text": "Quest list",
            "completed": [],
            "completed_count": 0,
            "completed_formatted": ["No quests completed"],
            "available": [],
            "available_count": 0,
            "available_formatted": ["No quests available"],
            "suggested": [],
            "suggested_formatted": ["No suggested quests"],
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.QuestListOutput
        )

        # Assert
        assert isinstance(output, schema.QuestListOutput)
        assert output.type == ToolType.QUEST
        assert output.name == "list_quests"
        assert output.formatted_text == "Quest list 🦆"
        assert output.result.completed_count == 0
        assert output.result.available_count == 0
        assert "No quests completed" in output.result.completed_formatted

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_quest_detail(self, mock_registry):
        """Test standardize_tool_output with quest detail output."""
        # Setup
        mock_registry.flavor_text.return_value = "Quest detail 🦆"

        tool_name = "get_quest_details"
        result = {
            "formatted_text": "Quest detail",
            "id": "quest1",
            "name": "Test Quest",
            "description": "A test quest",
            "reward_xp": 50,
            "badge_id": "badge1",
            "is_completed": False,
            "guidance": "Complete the quest",
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.QuestDetailOutput
        )

        # Assert
        assert isinstance(output, schema.QuestDetailOutput)
        assert output.type == ToolType.QUEST
        assert output.name == "get_quest_details"
        assert output.formatted_text == "Quest detail 🦆"
        assert output.result.id == "quest1"
        assert output.result.name == "Test Quest"
        assert output.result.description == "A test quest"
        assert output.result.reward_xp == 50
        assert output.result.badge_id == "badge1"
        assert output.result.is_completed is False
        assert output.result.guidance == "Complete the quest"

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_quest_completion(self, mock_registry):
        """Test standardize_tool_output with quest completion output."""
        # Setup
        mock_registry.flavor_text.return_value = "Quest completion 🦆"

        tool_name = "verify_quest_completion"
        result = {
            "formatted_text": "Quest completion",
            "quests_completed": True,
            "completed_quests": [],
            "completed_details": [],
            "total_completed_count": 1,
            "old_level": 1,
            "new_level": 2,
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.QuestCompletionOutput
        )

        # Assert
        assert isinstance(output, schema.QuestCompletionOutput)
        assert output.type == ToolType.QUEST
        assert output.name == "verify_quest_completion"
        assert output.formatted_text == "Quest completion 🦆"
        assert output.result.quests_completed is True
        assert output.result.total_completed_count == 1
        assert output.result.old_level == 1
        assert output.result.new_level == 2

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_badge_list(self, mock_registry):
        """Test standardize_tool_output with badge list output."""
        # Setup
        mock_registry.flavor_text.return_value = "Badge list 🦆"

        tool_name = "list_badges"
        result = {
            "formatted_text": "Badge list",
            "earned_badges": [],
            "earned_count": 0,
            "earned_formatted": ["No badges earned"],
            "next_badges": [],
            "next_badges_formatted": ["No badges to earn"],
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.BadgeListOutput
        )

        # Assert
        assert isinstance(output, schema.BadgeListOutput)
        assert output.type == ToolType.BADGE
        assert output.name == "list_badges"
        assert output.formatted_text == "Badge list 🦆"
        assert output.result.earned_count == 0
        assert "No badges earned" in output.result.earned_formatted

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_badge_detail(self, mock_registry):
        """Test standardize_tool_output with badge detail output."""
        # Setup
        mock_registry.flavor_text.return_value = "Badge detail 🦆"

        tool_name = "get_badge_details"
        result = {
            "formatted_text": "Badge detail",
            "id": "badge1",
            "name": "Test Badge",
            "emoji": "🏆",
            "description": "A test badge",
            "required_xp": 100,
            "is_earned": False,
            "progress": 50.0,
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.BadgeDetailOutput
        )

        # Assert
        assert isinstance(output, schema.BadgeDetailOutput)
        assert output.type == ToolType.BADGE
        assert output.name == "get_badge_details"
        assert output.formatted_text == "Badge detail 🦆"
        assert output.result.id == "badge1"
        assert output.result.name == "Test Badge"
        assert output.result.emoji == "🏆"
        assert output.result.description == "A test badge"
        assert output.result.required_xp == 100
        assert output.result.is_earned is False
        assert output.result.progress == 50.0

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_progress(self, mock_registry):
        """Test standardize_tool_output with progress output."""
        # Setup
        mock_registry.flavor_text.return_value = "Progress 🦆"

        tool_name = "list_xp_and_level"
        result = {
            "formatted_text": "Progress",
            "level": 2,
            "xp": 150,
            "next_level": 3,
            "xp_needed": 50,
            "progress_pct": 75,
            "progress_bar": "█████████░",
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.ProgressOutput
        )

        # Assert
        assert isinstance(output, schema.ProgressOutput)
        assert output.type == ToolType.PROGRESS
        assert output.name == "list_xp_and_level"
        assert output.formatted_text == "Progress 🦆"
        assert output.result.level == 2
        assert output.result.xp == 150
        assert output.result.next_level == 3
        assert output.result.xp_needed == 50
        assert output.result.progress_pct == 75
        assert output.result.progress_bar == "█████████░"

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_certificate(self, mock_registry):
        """Test standardize_tool_output with certificate output."""
        # Setup
        mock_registry.flavor_text.return_value = "Certificate info 🦆"

        tool_name = "get_certificate_info"
        result = {
            "formatted_text": "Certificate info",
            "certificates": [],
            "earned_any": False,
            "certificate_count": 0,
            "earned_count": 0,
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.CertificateListOutput
        )

        # Assert
        assert isinstance(output, schema.CertificateListOutput)
        assert output.type == ToolType.CERTIFICATE
        assert output.name == "get_certificate_info"
        assert output.formatted_text == "Certificate info 🦆"
        assert output.result.earned_any is False
        assert output.result.certificate_count == 0
        assert output.result.earned_count == 0

    @patch("quackcore.teaching.npc.tools.common.DialogueRegistry")
    def test_standardize_tool_output_tutorial(self, mock_registry):
        """Test standardize_tool_output with tutorial output."""
        # Setup
        mock_registry.flavor_text.return_value = "Tutorial 🦆"

        tool_name = "get_tutorial"
        result = {
            "formatted_text": "Tutorial",
            "topic": "python",
            "title": "Python Tutorial",
            "description": "Learn Python basics",
            "content": "Python content",
        }

        # Act
        output = common.standardize_tool_output(
            tool_name, result, return_type=schema.TutorialOutput
        )

        # Assert
        assert isinstance(output, schema.TutorialOutput)
        assert output.type == ToolType.TUTORIAL
        assert output.name == "get_tutorial"
        assert output.formatted_text == "Tutorial 🦆"
        assert output.result.topic == "python"
        assert output.result.title == "Python Tutorial"
        assert output.result.description == "Learn Python basics"
        assert output.result.content == "Python content"

    def test_detect_tool_triggers(self):
        """Test detecting which tools to trigger based on user input."""
        # Setup
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
        )

        # Test cases with expected tools
        test_cases = [
            ("What's my current XP?",
             [("list_xp_and_level", {"user_memory": user_memory})]),
            ("Show me my badges", [("list_badges", {"user_memory": user_memory})]),
            ("Tell me about the github-collaborator badge",
             [("get_badge_details", {"badge_id": "github-collaborator"})]),
            ("What quests are available?",
             [("list_quests", {"user_memory": user_memory})]),
            ("How do I complete the star-quackcore quest?",
             [("get_quest_details", {"quest_id": "star-quackcore"})]),
            ("What should I do next?",
             [("suggest_next_quest", {"user_memory": user_memory})]),
            ("I just completed the tutorial",
             [("verify_quest_completion", {"user_memory": user_memory})]),
            ("Can you show me certificates?",
             [("get_certificate_info", {"user_memory": user_memory})]),
            ("Tutorial on GitHub integration", [("get_tutorial", {"topic": "github"})]),
            # Multiple tools
            (
                "What's my XP and tell me about badges?",
                [
                    ("list_xp_and_level", {"user_memory": user_memory}),
                    ("list_badges", {"user_memory": user_memory}),
                ],
            ),
        ]

        for user_input, expected in test_cases:
            # Act
            triggers = utils.detect_tool_triggers(user_input, user_memory)

            # Assert
            assert len(triggers) == len(expected)
            for (tool_name, tool_args), (exp_name, exp_args) in zip(triggers, expected):
                assert tool_name == exp_name
                # For user_memory, just check that it's present
                if "user_memory" in tool_args and "user_memory" in exp_args:
                    assert tool_args["user_memory"] is user_memory
                # For other args, check exact values
                for key, value in exp_args.items():
                    if key != "user_memory":
                        assert key in tool_args
                        assert tool_args[key] == value

    @patch("quackcore.teaching.npc.tools.utils.TOOL_REGISTRY")
    def test_run_tools(self, mock_registry):
        """Test running tools with triggers."""
        # Setup
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
        )

        # Mock tool functions
        mock_xp_tool = MagicMock()
        mock_xp_tool.return_value = "XP output"

        mock_quest_tool = MagicMock()
        mock_quest_tool.return_value = "Quest output"

        # Set up mock registry
        mock_registry.get.side_effect = lambda name: {
            "list_xp_and_level": mock_xp_tool,
            "list_quests": mock_quest_tool,
        }.get(name)

        triggers = [
            ("list_xp_and_level", {"user_memory": user_memory}),
            ("list_quests", {"user_memory": user_memory}),
        ]

        # Act
        outputs = utils.run_tools(triggers)

        # Assert
        assert len(outputs) == 2
        mock_xp_tool.assert_called_once_with(user_memory=user_memory)
        mock_quest_tool.assert_called_once_with(user_memory=user_memory)

    @patch("quackcore.teaching.npc.tools.utils.TOOL_REGISTRY")
    @patch("quackcore.teaching.npc.tools.utils.logger")
    def test_run_tools_error(self, mock_logger, mock_registry):
        """Test error handling when running tools."""
        # Setup
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
        )

        # Mock tool function that raises an exception
        mock_error_tool = MagicMock()
        mock_error_tool.side_effect = Exception("Tool error")

        # Set up mock registry
        mock_registry.get.return_value = mock_error_tool

        triggers = [
            ("error_tool", {"user_memory": user_memory}),
        ]

        # Act
        outputs = utils.run_tools(triggers)

        # Assert
        assert len(outputs) == 0  # No outputs from failed tool
        mock_error_tool.assert_called_once_with(user_memory=user_memory)
        mock_logger.error.assert_called_once()

    @patch("quackcore.teaching.npc.tools.badge_tools.badges")
    @patch("quackcore.teaching.npc.tools.badge_tools.utils")
    def test_list_badges(self, mock_utils, mock_badges):
        """Test the list_badges tool."""
        # Setup
        user = MagicMock()
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            badges=["badge1", "badge2"],
        )

        mock_utils.load_progress.return_value = user

        # Mock badge objects
        mock_badge1 = MagicMock()
        mock_badge1.id = "badge1"
        mock_badge1.name = "Badge 1"
        mock_badge1.emoji = "🏆"
        mock_badge1.description = "First badge"
        mock_badge1.required_xp = 50

        mock_badge2 = MagicMock()
        mock_badge2.id = "badge2"
        mock_badge2.name = "Badge 2"
        mock_badge2.emoji = "🎖️"
        mock_badge2.description = "Second badge"
        mock_badge2.required_xp = 100

        mock_next_badge = MagicMock()
        mock_next_badge.id = "badge3"
        mock_next_badge.name = "Badge 3"
        mock_next_badge.emoji = "🥇"
        mock_next_badge.description = "Next badge"
        mock_next_badge.required_xp = 200

        mock_badges.get_user_badges.return_value = [mock_badge1, mock_badge2]
        mock_badges.get_next_badges.return_value = [mock_next_badge]

        # Act
        with patch(
                "quackcore.teaching.npc.tools.badge_tools.standardize_tool_output") as mock_standardize:
            badge_tools.list_badges(user_memory)

            # Assert
            mock_utils.load_progress.assert_called_once()
            mock_badges.get_user_badges.assert_called_once_with(user)
            mock_badges.get_next_badges.assert_called_once()
            mock_standardize.assert_called_once()

            # Check that the standardized output contains the correct data
            args = mock_standardize.call_args[0]
            assert args[0] == "list_badges"
            assert len(args[1]["earned_badges"]) == 2
            assert args[1]["earned_count"] == 2
            assert len(args[1]["next_badges"]) == 1

    @patch("quackcore.teaching.npc.tools.badge_tools.badges")
    @patch("quackcore.teaching.npc.tools.badge_tools.utils")
    @patch("quackcore.teaching.npc.tools.badge_tools.DialogueRegistry")
    def test_get_badge_details(self, mock_registry, mock_utils, mock_badges):
        """Test the get_badge_details tool."""
        # Setup
        user = MagicMock()
        mock_utils.load_progress.return_value = user

        # Mock badge
        mock_badge = MagicMock()
        mock_badge.id = "test-badge"
        mock_badge.name = "Test Badge"
        mock_badge.emoji = "🏆"
        mock_badge.description = "A test badge"
        mock_badge.required_xp = 100

        mock_badges.get_badge.return_value = mock_badge
        mock_badges.get_badge_progress.return_value = 0.5  # 50% progress

        # Mock user having the badge
        user.has_earned_badge.return_value = False

        # Mock dialogue registry
        mock_registry.get_badge_dialogue.return_value = "Badge description"
        mock_registry.render_badge_status.return_value = "Rendered badge status"

        # Act
        with patch(
                "quackcore.teaching.npc.tools.badge_tools.standardize_tool_output") as mock_standardize:
            badge_tools.get_badge_details("test-badge")

            # Assert
            mock_utils.load_progress.assert_called_once()
            mock_badges.get_badge.assert_called_once_with("test-badge")
            user.has_earned_badge.assert_called_once_with("test-badge")
            mock_badges.get_badge_progress.assert_called_once()
            mock_registry.render_badge_status.assert_called_once()
            mock_standardize.assert_called_once()

            # Check that the standardized output contains the correct data
            args = mock_standardize.call_args[0]
            assert args[0] == "get_badge_details"
            assert args[1]["id"] == "test-badge"
            assert args[1]["name"] == "Test Badge"
            assert args[1]["emoji"] == "🏆"
            assert args[1]["progress"] == 50.0
            assert args[1]["is_earned"] is False

    @patch("quackcore.teaching.npc.tools.certificate_tools.certificates")
    @patch("quackcore.teaching.npc.tools.certificate_tools.utils")
    def test_get_certificate_info(self, mock_utils, mock_certificates):
        """Test the get_certificate_info tool."""
        # Setup
        user = MagicMock()
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            completed_quests=["star-quackcore", "run-ducktyper"],
        )

        mock_utils.load_progress.return_value = user

        # Mock certificate status
        mock_certificates.has_earned_certificate.side_effect = lambda u,
                                                                      c: c == "quackverse-basics"

        # Act
        with patch(
                "quackcore.teaching.npc.tools.certificate_tools.standardize_tool_output") as mock_standardize:
            certificate_tools.get_certificate_info(user_memory)

            # Assert
            mock_utils.load_progress.assert_called_once()
            assert mock_certificates.has_earned_certificate.call_count > 0
            mock_standardize.assert_called_once()

            # Check that the standardized output contains the correct data
            args = mock_standardize.call_args[0]
            assert args[0] == "get_certificate_info"
            assert "certificates" in args[1]
            assert "earned_any" in args[1]
            assert "certificate_count" in args[1]
            assert "earned_count" in args[1]
            assert "formatted_text" in args[1]

    @patch("quackcore.teaching.npc.tools.progress_tools.standardize_tool_output")
    def test_list_xp_and_level(self, mock_standardize):
        """Test the list_xp_and_level tool."""
        # Setup
        user_memory = UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            custom_data={"xp_to_next_level": 50},
        )

        # Act
        progress_tools.list_xp_and_level(user_memory)

        # Assert
        mock_standardize.assert_called_once()

        # Check that the standardized output contains the correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "list_xp_and_level"
        assert args[1]["level"] == 2
        assert args[1]["xp"] == 150
        assert args[1]["next_level"] == 3
        assert args[1]["xp_needed"] == 50
        assert "progress_pct" in args[1]
        assert "progress_bar" in args[1]
        assert "formatted_text" in args[1]

    @patch("quackcore.teaching.npc.tools.quest_tools.quests")
    @patch("quackcore.teaching.npc.tools.quest_tools.utils")
    def test_list_quests(self, mock_utils, mock_quests):
        """Test the list_quests tool."""
        # Setup
        user = MagicMock()
        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            completed_quests=["quest1", "quest2"],
        )

        mock_utils.load_progress.return_value = user

        # Mock quest objects
        mock_quest1 = MagicMock()
        mock_quest1.id = "quest1"
        mock_quest1.name = "Quest 1"
        mock_quest1.description = "First quest"
        mock_quest1.reward_xp = 10

        mock_quest2 = MagicMock()
        mock_quest2.id = "quest2"
        mock_quest2.name = "Quest 2"
        mock_quest2.description = "Second quest"
        mock_quest2.reward_xp = 20

        mock_quest3 = MagicMock()
        mock_quest3.id = "quest3"
        mock_quest3.name = "Quest 3"
        mock_quest3.description = "Third quest"
        mock_quest3.reward_xp = 30

        mock_quests.get_user_quests.return_value = {
            "completed": [mock_quest1, mock_quest2],
            "available": [mock_quest3],
        }

        mock_quests.get_suggested_quests.return_value = [mock_quest3]

        # Act
        with patch(
                "quackcore.teaching.npc.tools.quest_tools.standardize_tool_output") as mock_standardize:
            quest_tools.list_quests(user_memory)

            # Assert
            mock_utils.load_progress.assert_called_once()
            mock_quests.get_user_quests.assert_called_once_with(user)
            mock_quests.get_suggested_quests.assert_called_once()
            mock_standardize.assert_called_once()

            # Check that the standardized output contains the correct data
            args = mock_standardize.call_args[0]
            assert args[0] == "list_quests"
            assert args[1]["completed_count"] == 2
            assert args[1]["available_count"] == 1
            assert len(args[1]["completed"]) == 2
            assert len(args[1]["available"]) == 1
            assert len(args[1]["suggested"]) == 1