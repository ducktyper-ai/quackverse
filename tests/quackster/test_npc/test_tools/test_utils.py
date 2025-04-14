# tests/quackster/test_npc/test_tools/test_utils.py
"""
Tests for the utility functions in quackcore.quackster.npc.tools.utils.

This module tests the helper functions for tool operations,
including tool discovery and invocation.
"""

import pytest

from quackster.npc.schema import UserMemory
from quackster.npc.tools import ToolOutput, utils


class TestToolUtils:
    """Tests for tool utility functions."""

    @pytest.fixture
    def user_memory(self):
        """Create a UserMemory object for testing."""
        return UserMemory(
            github_username="testuser",
            xp=150,
            level=2,
            completed_quests=["quest1", "quest2"],
            badges=["badge1"],
            custom_data={},
        )

    def test_detect_tool_triggers_xp_and_level(self, user_memory):
        """Test detecting XP and level tool triggers."""
        # Input messages that should trigger list_xp_and_level
        test_inputs = [
            "What is my current XP?",
            "Show me my level",
            "How much progress have I made?",
            "Tell me about my XP and level",
        ]

        for message in test_inputs:
            triggers = utils.detect_tool_triggers(message, user_memory)

            # Check that list_xp_and_level is triggered
            assert any(trigger[0] == "list_xp_and_level" for trigger in triggers)

            # Check that the user_memory is passed correctly
            for trigger in triggers:
                if trigger[0] == "list_xp_and_level":
                    assert trigger[1]["user_memory"] is user_memory

    def test_detect_tool_triggers_badges(self, user_memory):
        """Test detecting badge tool triggers."""
        # Input for list_badges
        list_triggers = utils.detect_tool_triggers("Show me my badges", user_memory)
        assert any(trigger[0] == "list_badges" for trigger in list_triggers)

        # Input for specific badge details
        detail_triggers = utils.detect_tool_triggers(
            "Tell me about the github-collaborator badge", user_memory
        )
        badge_trigger = next(
            (t for t in detail_triggers if t[0] == "get_badge_details"), None
        )
        assert badge_trigger is not None
        assert badge_trigger[1]["badge_id"] == "github-collaborator"

    def test_detect_tool_triggers_quests(self, user_memory):
        """Test detecting quest tool triggers."""
        # Input for list_quests
        list_triggers = utils.detect_tool_triggers(
            "What quests are available?", user_memory
        )
        assert any(trigger[0] == "list_quests" for trigger in list_triggers)

        # Input for specific quest details
        detail_triggers = utils.detect_tool_triggers(
            "How do I complete the star-quackcore quest?", user_memory
        )
        quest_trigger = next(
            (t for t in detail_triggers if t[0] == "get_quest_details"), None
        )
        assert quest_trigger is not None
        assert quest_trigger[1]["quest_id"] == "star-quackcore"

        # Input for next quest suggestion
        suggest_triggers = utils.detect_tool_triggers(
            "What should I do next?", user_memory
        )
        assert any(trigger[0] == "suggest_next_quest" for trigger in suggest_triggers)

        # Input for quest completion verification
        verify_triggers = utils.detect_tool_triggers(
            "I completed the tutorial", user_memory
        )
        assert any(
            trigger[0] == "verify_quest_completion" for trigger in verify_triggers
        )

    def test_detect_tool_triggers_certificates(self, user_memory):
        """Test detecting certificate tool triggers."""
        # Input for certificate info
        cert_triggers = utils.detect_tool_triggers(
            "Show me my certificates", user_memory
        )
        assert any(trigger[0] == "get_certificate_info" for trigger in cert_triggers)

    def test_detect_tool_triggers_tutorials(self, user_memory):
        """Test detecting tutorial tool triggers."""
        # Input for tutorial on a specific topic
        tutorial_triggers = utils.detect_tool_triggers(
            "Show me a tutorial on GitHub integration", user_memory
        )
        tut_trigger = next(
            (t for t in tutorial_triggers if t[0] == "get_tutorial"), None
        )
        assert tut_trigger is not None
        assert tut_trigger[1]["topic"] == "github"

    def test_detect_tool_triggers_multiple(self, user_memory):
        """Test detecting multiple tool triggers in one message."""
        # Input that should trigger multiple tools
        multi_triggers = utils.detect_tool_triggers(
            "What's my XP and tell me about my badges?", user_memory
        )

        assert len(multi_triggers) == 2
        assert any(trigger[0] == "list_xp_and_level" for trigger in multi_triggers)
        assert any(trigger[0] == "list_badges" for trigger in multi_triggers)

    def test_run_tools_basic(self, mocker):
        """Test running tools with valid triggers."""
        # Create mock tools
        mock_tool1 = mocker.MagicMock()
        mock_tool1.return_value = ToolOutput(
            name="tool1",
            result={"key": "value1"},
            formatted_text="Tool 1 output",
        )

        mock_tool2 = mocker.MagicMock()
        mock_tool2.return_value = ToolOutput(
            name="tool2",
            result={"key": "value2"},
            formatted_text="Tool 2 output",
        )

        # Mock the tool registry
        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.utils.TOOL_REGISTRY"
        )
        mock_registry.get.side_effect = lambda name: {
            "tool1": mock_tool1,
            "tool2": mock_tool2,
        }.get(name)

        # Create triggers
        triggers = [
            ("tool1", {"arg1": "value1"}),
            ("tool2", {"arg2": "value2"}),
        ]

        # Run the tools
        outputs = utils.run_tools(triggers)

        # Verify that both tools were called correctly
        assert len(outputs) == 2
        mock_tool1.assert_called_once_with(arg1="value1")
        mock_tool2.assert_called_once_with(arg2="value2")

        # Verify outputs
        assert outputs[0].name == "tool1"
        assert outputs[0].result == {"key": "value1"}
        assert outputs[1].name == "tool2"
        assert outputs[1].result == {"key": "value2"}

    def test_run_tools_missing_tool(self, mocker):
        """Test running tools with a missing tool."""
        # Create a mock tool
        mock_tool = mocker.MagicMock()
        mock_tool.return_value = ToolOutput(
            name="valid_tool",
            result={"key": "value"},
            formatted_text="Valid tool output",
        )

        # Mock the tool registry and logger
        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.utils.TOOL_REGISTRY"
        )
        mock_registry.get.side_effect = lambda name: {"valid_tool": mock_tool}.get(name)

        mock_logger = mocker.patch("quackcore.quackster.npc.tools.utils.logger")

        # Create triggers with one valid and one missing tool
        triggers = [
            ("valid_tool", {"arg": "value"}),
            ("missing_tool", {"arg": "value"}),
        ]

        # Run the tools
        outputs = utils.run_tools(triggers)

        # Verify that only the valid tool was called
        assert len(outputs) == 1
        mock_tool.assert_called_once_with(arg="value")
        mock_logger.warning.assert_called_once()

        # Verify output
        assert outputs[0].name == "valid_tool"
        assert outputs[0].result == {"key": "value"}

    def test_run_tools_error(self, mocker):
        """Test running tools with a tool that raises an error."""
        # Create a mock tool that raises an exception
        mock_tool = mocker.MagicMock()
        mock_tool.side_effect = Exception("Tool error")

        # Mock the tool registry and logger
        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.utils.TOOL_REGISTRY"
        )
        mock_registry.get.return_value = mock_tool

        mock_logger = mocker.patch("quackcore.quackster.npc.tools.utils.logger")

        # Create a trigger
        triggers = [("error_tool", {"arg": "value"})]

        # Run the tools
        outputs = utils.run_tools(triggers)

        # Verify that the error was logged and no outputs were returned
        assert len(outputs) == 0
        mock_tool.assert_called_once_with(arg="value")
        mock_logger.error.assert_called_once()

    def test_run_tools_non_tool_output(self, mocker):
        """Test running tools with a tool that returns a non-ToolOutput value."""
        # Create a mock tool that returns a non-ToolOutput value
        mock_tool = mocker.MagicMock()
        mock_tool.return_value = "Not a ToolOutput"

        # Mock the tool registry and logger
        mock_registry = mocker.patch(
            "quackcore.quackster.npc.tools.utils.TOOL_REGISTRY"
        )
        mock_registry.get.return_value = mock_tool

        mock_logger = mocker.patch("quackcore.quackster.npc.tools.utils.logger")

        # Create a trigger
        triggers = [("invalid_tool", {"arg": "value"})]

        # Run the tools
        outputs = utils.run_tools(triggers)

        # Verify that the warning was logged and no outputs were returned
        assert len(outputs) == 0
        mock_tool.assert_called_once_with(arg="value")
        mock_logger.warning.assert_called_once()

    def test_detect_tool_triggers_edge_cases(self, user_memory):
        """Test detecting tool triggers with edge case inputs."""
        # Empty message
        empty_triggers = utils.detect_tool_triggers("", user_memory)
        assert empty_triggers == []

        # Unrelated message
        unrelated_triggers = utils.detect_tool_triggers(
            "Hello, how are you?", user_memory
        )
        assert unrelated_triggers == []

        # Exact quoted badge name
        badge_triggers = utils.detect_tool_triggers(
            'Tell me about badge "team-leader"', user_memory
        )
        badge_trigger = next(
            (t for t in badge_triggers if t[0] == "get_badge_details"), None
        )
        assert badge_trigger is not None
        assert badge_trigger[1]["badge_id"] == "team-leader"

        # Exact quoted quest name
        quest_triggers = utils.detect_tool_triggers(
            'How do I complete quest "clone-repo"', user_memory
        )
        quest_trigger = next(
            (t for t in quest_triggers if t[0] == "get_quest_details"), None
        )
        assert quest_trigger is not None
        assert quest_trigger[1]["quest_id"] == "clone-repo"
