# tests/test_teaching/test_npc/test_tools/test_init.py
"""
Tests for the module initialization and registry in quackcore.teaching.npc.tools.

This module tests the TOOL_REGISTRY and imports in __init__.py.
"""

from quackcore.teaching.npc.tools import (
    TOOL_REGISTRY,
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
    get_badge_details,
    get_certificate_info,
    get_quest_details,
    get_tutorial,
    list_badges,
    list_quests,
    list_xp_and_level,
    standardize_tool_output,
    suggest_next_quest,
    verify_quest_completion,
)


class TestToolsInit:
    """Tests for the tools module initialization."""

    def test_tool_registry_contains_all_tools(self):
        """Test that the tool registry contains all expected tools."""
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

    def test_tool_registry_values_are_functions(self):
        """Test that the tool registry values are callable functions."""
        for tool_name, tool_func in TOOL_REGISTRY.items():
            assert callable(tool_func), f"Tool '{tool_name}' is not callable"

    def test_public_exports(self):
        """Test that all expected names are exported."""
        # Tool functions should be directly importable
        assert callable(list_xp_and_level)
        assert callable(list_badges)
        assert callable(get_badge_details)
        assert callable(list_quests)
        assert callable(get_quest_details)
        assert callable(suggest_next_quest)
        assert callable(verify_quest_completion)
        assert callable(get_tutorial)
        assert callable(get_certificate_info)
        assert callable(standardize_tool_output)

        # Output types should be importable
        assert issubclass(ToolOutput, object)
        assert issubclass(QuestListOutput, ToolOutput)
        assert issubclass(QuestDetailOutput, ToolOutput)
        assert issubclass(QuestCompletionOutput, ToolOutput)
        assert issubclass(BadgeListOutput, ToolOutput)
        assert issubclass(BadgeDetailOutput, ToolOutput)
        assert issubclass(ProgressOutput, ToolOutput)
        assert issubclass(CertificateListOutput, ToolOutput)
        assert issubclass(TutorialOutput, ToolOutput)

        # ToolType enum should be importable
        assert isinstance(ToolType.QUEST, ToolType)
        assert isinstance(ToolType.BADGE, ToolType)
        assert isinstance(ToolType.PROGRESS, ToolType)
        assert isinstance(ToolType.CERTIFICATE, ToolType)
        assert isinstance(ToolType.TUTORIAL, ToolType)
        assert isinstance(ToolType.META, ToolType)

    def test_tool_registry_matches_functions(self):
        """Test that the registry functions match the exported functions."""
        # For each function in the registry, test that it matches the exported function
        assert TOOL_REGISTRY["list_xp_and_level"] is list_xp_and_level
        assert TOOL_REGISTRY["list_badges"] is list_badges
        assert TOOL_REGISTRY["get_badge_details"] is get_badge_details
        assert TOOL_REGISTRY["list_quests"] is list_quests
        assert TOOL_REGISTRY["get_quest_details"] is get_quest_details
        assert TOOL_REGISTRY["suggest_next_quest"] is suggest_next_quest
        assert TOOL_REGISTRY["verify_quest_completion"] is verify_quest_completion
        assert TOOL_REGISTRY["get_tutorial"] is get_tutorial
        assert TOOL_REGISTRY["get_certificate_info"] is get_certificate_info
