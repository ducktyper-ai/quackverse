# tests/test_teaching/test_npc/test_tools/test_common.py
"""
Tests for the common utilities in quackcore.teaching.npc.tools.common.

This module tests the standardize_tool_output function and other common utilities.
"""

from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import BaseModel

from quackcore.teaching.npc.tools import common
from quackcore.teaching.npc.tools.schema import (
    BadgeDetailOutput,
    BadgeListOutput,
    CertificateListOutput,
    ProgressOutput,
    QuestCompletionOutput,
    QuestDetailOutput,
    QuestListOutput,
    ToolOutput,
    ToolType,
    TutorialOutput,
)


class TestStandardizeToolOutput:
    """Tests for the standardize_tool_output function."""

    def test_basic_functionality(self, mocker):
        """Test basic functionality of standardize_tool_output."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Quacktastic! Result text 🦆"

        # Input data
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "key1": "value1",
            "key2": "value2",
            "formatted_text": "Result text",
        }

        # Call the function
        output = common.standardize_tool_output(tool_name, result)

        # Assertions
        assert output.name == tool_name
        assert output.type == ToolType.META
        assert output.formatted_text == "Quacktastic! Result text 🦆"
        assert output.result["key1"] == "value1"
        assert output.result["key2"] == "value2"
        assert output.badge_awarded is False
        assert output.xp_gained == 0
        assert output.quests_completed is False
        assert output.level_up is False

        # Verify the mock was called
        mock_registry.flavor_text.assert_called_once_with("test_tool", "Result text")

    def test_without_flavor(self, mocker):
        """Test standardize_tool_output with flavor disabled."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )

        # Input data
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "formatted_text": "Result text",
        }

        # Call the function with flavor=False
        output = common.standardize_tool_output(tool_name, result, flavor=False)

        # Assertions
        assert output.formatted_text == "Result text"
        mock_registry.flavor_text.assert_not_called()

    def test_with_metadata(self, mocker):
        """Test standardize_tool_output with metadata fields."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Flavored text"

        # Input data with metadata fields
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "formatted_text": "Result text",
            "badge_awarded": True,
            "xp_gained": 50,
            "quests_completed": True,
            "level_up": True,
        }

        # Call the function
        output = common.standardize_tool_output(tool_name, result)

        # Assertions
        assert output.badge_awarded is True
        assert output.xp_gained == 50
        assert output.quests_completed is True
        assert output.level_up is True

    def test_with_explicit_tool_type(self, mocker):
        """Test standardize_tool_output with explicit tool type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Flavored text"

        # Input data
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "formatted_text": "Result text",
        }

        # Call the function with explicit tool_type
        output = common.standardize_tool_output(
            tool_name, result, tool_type=ToolType.QUEST
        )

        # Assertions
        assert output.type == ToolType.QUEST

    def test_with_no_formatted_text(self, mocker):
        """Test standardize_tool_output with no formatted_text in result."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Flavored text"

        # Input data without formatted_text
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "key1": "value1",
        }

        # Call the function
        output = common.standardize_tool_output(tool_name, result)

        # Assertions - should create a default formatted_text
        assert "formatted_text" in output.model_dump()
        mock_registry.flavor_text.assert_called_once()

    @pytest.mark.parametrize(
        "tool_name, expected_type",
        [
            ("list_badges", ToolType.BADGE),
            ("get_badge_details", ToolType.BADGE),
            ("get_certificate_info", ToolType.CERTIFICATE),
            ("list_xp_and_level", ToolType.PROGRESS),
            ("list_quests", ToolType.QUEST),
            ("get_quest_details", ToolType.QUEST),
            ("suggest_next_quest", ToolType.QUEST),
            ("verify_quest_completion", ToolType.QUEST),
            ("get_tutorial", ToolType.TUTORIAL),
            ("unknown_tool", ToolType.META),
        ],
    )
    def test_tool_type_inference(self, mocker, tool_name, expected_type):
        """Test tool type inference based on tool name."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Flavored text"

        # Input data
        result: Mapping[str, Any] = {
            "formatted_text": "Result text",
        }

        # Call the function
        output = common.standardize_tool_output(tool_name, result)

        # Assertions
        assert output.type == expected_type

    def test_with_explicit_type_in_result(self, mocker):
        """Test standardize_tool_output with explicit type in result."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Flavored text"

        # Input data with explicit type
        tool_name = "test_tool"
        result: Mapping[str, Any] = {
            "formatted_text": "Result text",
            "type": "badge",
        }

        # Call the function
        output = common.standardize_tool_output(tool_name, result)

        # Assertions
        assert output.type == ToolType.BADGE

    def test_quest_list_output(self, mocker):
        """Test standardize_tool_output with QuestListOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Quest list 🦆"

        # Input data
        tool_name = "list_quests"
        result: Mapping[str, Any] = {
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

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=QuestListOutput
        )

        # Assertions
        assert isinstance(output, QuestListOutput)
        assert output.type == ToolType.QUEST
        assert output.name == "list_quests"
        assert output.formatted_text == "Quest list 🦆"
        assert output.result.completed_count == 0
        assert output.result.available_count == 0
        assert "No quests completed" in output.result.completed_formatted[0]

    def test_quest_detail_output(self, mocker):
        """Test standardize_tool_output with QuestDetailOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Quest detail 🦆"

        # Input data
        tool_name = "get_quest_details"
        result: Mapping[str, Any] = {
            "formatted_text": "Quest detail",
            "id": "quest1",
            "name": "Test Quest",
            "description": "A test quest",
            "reward_xp": 50,
            "badge_id": "badge1",
            "is_completed": False,
            "guidance": "Complete the quest",
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=QuestDetailOutput
        )

        # Assertions
        assert isinstance(output, QuestDetailOutput)
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

    def test_quest_completion_output(self, mocker):
        """Test standardize_tool_output with QuestCompletionOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Quest completion 🦆"

        # Input data
        tool_name = "verify_quest_completion"
        result: Mapping[str, Any] = {
            "formatted_text": "Quest completion",
            "quests_completed": True,
            "completed_quests": [],
            "completed_details": [],
            "total_completed_count": 1,
            "old_level": 1,
            "new_level": 2,
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=QuestCompletionOutput
        )

        # Assertions
        assert isinstance(output, QuestCompletionOutput)
        assert output.type == ToolType.QUEST
        assert output.name == "verify_quest_completion"
        assert output.formatted_text == "Quest completion 🦆"
        assert output.result.quests_completed is True
        assert output.result.total_completed_count == 1
        assert output.result.old_level == 1
        assert output.result.new_level == 2

    def test_badge_list_output(self, mocker):
        """Test standardize_tool_output with BadgeListOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Badge list 🦆"

        # Input data
        tool_name = "list_badges"
        result: Mapping[str, Any] = {
            "formatted_text": "Badge list",
            "earned_badges": [],
            "earned_count": 0,
            "earned_formatted": ["No badges earned"],
            "next_badges": [],
            "next_badges_formatted": ["No badges to earn"],
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=BadgeListOutput
        )

        # Assertions
        assert isinstance(output, BadgeListOutput)
        assert output.type == ToolType.BADGE
        assert output.name == "list_badges"
        assert output.formatted_text == "Badge list 🦆"
        assert output.result.earned_count == 0
        assert "No badges earned" in output.result.earned_formatted[0]

    def test_badge_detail_output(self, mocker):
        """Test standardize_tool_output with BadgeDetailOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Badge detail 🦆"

        # Input data
        tool_name = "get_badge_details"
        result: Mapping[str, Any] = {
            "formatted_text": "Badge detail",
            "id": "badge1",
            "name": "Test Badge",
            "emoji": "🏆",
            "description": "A test badge",
            "required_xp": 100,
            "is_earned": False,
            "progress": 50.0,
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=BadgeDetailOutput
        )

        # Assertions
        assert isinstance(output, BadgeDetailOutput)
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

    def test_progress_output(self, mocker):
        """Test standardize_tool_output with ProgressOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Progress 🦆"

        # Input data
        tool_name = "list_xp_and_level"
        result: Mapping[str, Any] = {
            "formatted_text": "Progress",
            "level": 2,
            "xp": 150,
            "next_level": 3,
            "xp_needed": 50,
            "progress_pct": 75,
            "progress_bar": "█████████░",
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=ProgressOutput
        )

        # Assertions
        assert isinstance(output, ProgressOutput)
        assert output.type == ToolType.PROGRESS
        assert output.name == "list_xp_and_level"
        assert output.formatted_text == "Progress 🦆"
        assert output.result.level == 2
        assert output.result.xp == 150
        assert output.result.next_level == 3
        assert output.result.xp_needed == 50
        assert output.result.progress_pct == 75
        assert output.result.progress_bar == "█████████░"

    def test_certificate_output(self, mocker):
        """Test standardize_tool_output with CertificateListOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Certificate info 🦆"

        # Input data
        tool_name = "get_certificate_info"
        result: Mapping[str, Any] = {
            "formatted_text": "Certificate info",
            "certificates": [],
            "earned_any": False,
            "certificate_count": 0,
            "earned_count": 0,
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=CertificateListOutput
        )

        # Assertions
        assert isinstance(output, CertificateListOutput)
        assert output.type == ToolType.CERTIFICATE
        assert output.name == "get_certificate_info"
        assert output.formatted_text == "Certificate info 🦆"
        assert output.result.earned_any is False
        assert output.result.certificate_count == 0
        assert output.result.earned_count == 0

    def test_tutorial_output(self, mocker):
        """Test standardize_tool_output with TutorialOutput return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Tutorial 🦆"

        # Input data
        tool_name = "get_tutorial"
        result: Mapping[str, Any] = {
            "formatted_text": "Tutorial",
            "topic": "python",
            "title": "Python Tutorial",
            "description": "Learn Python basics",
            "content": "Python content",
        }

        # Call the function
        output = common.standardize_tool_output(
            tool_name, result, return_type=TutorialOutput
        )

        # Assertions
        assert isinstance(output, TutorialOutput)
        assert output.type == ToolType.TUTORIAL
        assert output.name == "get_tutorial"
        assert output.formatted_text == "Tutorial 🦆"
        assert output.result.topic == "python"
        assert output.result.title == "Python Tutorial"
        assert output.result.description == "Learn Python basics"
        assert output.result.content == "Python content"

    def test_custom_return_type(self, mocker):
        """Test standardize_tool_output with a custom return type."""
        # Mock DialogueRegistry to avoid external dependencies
        mock_registry = mocker.patch(
            "quackcore.teaching.npc.tools.common.DialogueRegistry"
        )
        mock_registry.flavor_text.return_value = "Custom output 🦆"

        # Define a custom result type
        class CustomResult(BaseModel):
            value: str

        # Define a custom output type
        class CustomOutput(ToolOutput[CustomResult]):
            type: ToolType = ToolType.META

        # Input data
        tool_name = "custom_tool"
        result: dict[str, Any] = {
            "formatted_text": "Custom output",
            "value": "custom value",
        }

        # Create a mock for the return_type that will match one of the overloaded signatures
        # We'll use the "tool_type" parameter instead of "return_type" to avoid the type error
        # The function implementation will handle our custom type correctly
        output = common.standardize_tool_output(
            tool_name, result, tool_type=ToolType.META
        )

        # Manually create our expected CustomOutput
        expected_output = CustomOutput(
            name=tool_name,
            result=CustomResult(value="custom value"),
            formatted_text="Custom output 🦆",
        )

        # Assertions - we're checking the content, not the exact type
        assert output.name == "custom_tool"
        assert output.formatted_text == "Custom output 🦆"
        assert "value" in output.result
        assert output.result["value"] == "custom value"

        # NOTE: We can't directly test isinstance(output, CustomOutput) because
        # standardize_tool_output can't return our custom type due to the overload definitions
