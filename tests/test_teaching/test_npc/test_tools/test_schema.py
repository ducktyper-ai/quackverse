# tests/test_teaching/test_npc/test_tools/test_schema.py
"""
Tests for the schema models in quackcore.teaching.npc.tools.schema.

This module tests the Pydantic model definitions and their behaviors.
"""

import pytest
from pydantic import ValidationError

from quackcore.teaching.npc.tools.schema import (
    BadgeInfo,
    BadgeListOutput,
    BadgeListResult,
    CertificateInfo,
    CertificateListOutput,
    CertificateListResult,
    ProgressOutput,
    ProgressResult,
    QuestCompletionDetail,
    QuestCompletionOutput,
    QuestCompletionResult,
    QuestDetailOutput,
    QuestInfo,
    QuestListOutput,
    QuestListResult,
    ToolOutput,
    ToolType,
    TutorialOutput,
    TutorialResult,
)


class TestToolSchema:
    """Tests for the tool schema models."""

    def test_tool_type_enum(self):
        """Test the ToolType enum values and behavior."""
        # Check all expected enum values
        assert ToolType.PROGRESS == "progress"
        assert ToolType.QUEST == "quest"
        assert ToolType.BADGE == "badge"
        assert ToolType.CERTIFICATE == "certificate"
        assert ToolType.TUTORIAL == "tutorial"
        assert ToolType.META == "meta"

        # Test string conversion
        assert str(ToolType.PROGRESS) == "progress"

        # Test creation from string
        assert ToolType("quest") == ToolType.QUEST

        # Test invalid value
        with pytest.raises(ValueError):
            ToolType("invalid_type")

    def test_tool_output_basic(self):
        """Test the basic ToolOutput model."""
        # Create a simple ToolOutput
        output = ToolOutput(
            name="test_tool",
            result={"key": "value"},
            formatted_text="Test output",
        )

        # Check default values
        assert output.type == ToolType.META
        assert output.badge_awarded is False
        assert output.xp_gained == 0
        assert output.quests_completed is False
        assert output.level_up is False

        # Check provided values
        assert output.name == "test_tool"
        assert output.result == {"key": "value"}
        assert output.formatted_text == "Test output"

        # Test JSON serialization
        json_data = output.model_dump_json()
        assert "test_tool" in json_data
        assert "Test output" in json_data

    def test_tool_output_with_custom_values(self):
        """Test ToolOutput with custom values for all fields."""
        # Create a ToolOutput with non-default values
        output = ToolOutput(
            name="test_tool",
            result={"key": "value"},
            formatted_text="Test output",
            type=ToolType.BADGE,
            badge_awarded=True,
            xp_gained=100,
            quests_completed=True,
            level_up=True,
        )

        # Check values
        assert output.type == ToolType.BADGE
        assert output.badge_awarded is True
        assert output.xp_gained == 100
        assert output.quests_completed is True
        assert output.level_up is True

    def test_tool_output_validation(self):
        """Test validation of the ToolOutput model."""
        # Missing required fields
        with pytest.raises(ValidationError):
            ToolOutput()

        with pytest.raises(ValidationError):
            ToolOutput(name="test_tool")

        with pytest.raises(ValidationError):
            ToolOutput(name="test_tool", result={"key": "value"})

        # Invalid values
        with pytest.raises(ValidationError):
            ToolOutput(
                name="test_tool",
                result={"key": "value"},
                formatted_text="Test output",
                type="invalid_type",
            )

        with pytest.raises(ValidationError):
            ToolOutput(
                name="test_tool",
                result={"key": "value"},
                formatted_text="Test output",
                xp_gained="invalid_xp",
            )

    def test_badge_info_model(self):
        """Test the BadgeInfo model."""
        # Create with minimum required fields
        badge = BadgeInfo(
            id="test_badge",
            name="Test Badge",
            description="A test badge",
        )

        # Check default values
        assert badge.emoji == "🏆"
        assert badge.is_earned is False
        assert badge.progress == 0.0
        assert badge.required_xp == 0

        # Create with all fields
        badge = BadgeInfo(
            id="test_badge",
            name="Test Badge",
            emoji="🎯",
            description="A test badge",
            is_earned=True,
            progress=75.5,
            required_xp=100,
        )

        # Check provided values
        assert badge.id == "test_badge"
        assert badge.name == "Test Badge"
        assert badge.emoji == "🎯"
        assert badge.description == "A test badge"
        assert badge.is_earned is True
        assert badge.progress == 75.5
        assert badge.required_xp == 100

    def test_badge_list_result_model(self):
        """Test the BadgeListResult model."""
        # Create with default values
        result = BadgeListResult()

        # Check default values
        assert result.earned_badges == []
        assert result.earned_count == 0
        assert result.earned_formatted == []
        assert result.next_badges == []
        assert result.next_badges_formatted == []

        # Create with populated values
        badge1 = BadgeInfo(
            id="badge1",
            name="Badge 1",
            description="First badge",
            is_earned=True,
        )
        badge2 = BadgeInfo(
            id="badge2",
            name="Badge 2",
            description="Second badge",
            is_earned=False,
            progress=50.0,
        )

        result = BadgeListResult(
            earned_badges=[badge1],
            earned_count=1,
            earned_formatted=["Badge 1 earned"],
            next_badges=[badge2],
            next_badges_formatted=["Badge 2 (50% complete)"],
        )

        # Check values
        assert len(result.earned_badges) == 1
        assert result.earned_badges[0].id == "badge1"
        assert result.earned_count == 1
        assert result.earned_formatted == ["Badge 1 earned"]
        assert len(result.next_badges) == 1
        assert result.next_badges[0].id == "badge2"
        assert result.next_badges_formatted == ["Badge 2 (50% complete)"]

    def test_badge_list_output_model(self):
        """Test the BadgeListOutput model."""
        # Create badge list result
        result = BadgeListResult(
            earned_badges=[],
            earned_count=0,
            earned_formatted=["No badges earned"],
            next_badges=[],
            next_badges_formatted=["No next badges"],
        )

        # Create badge list output
        output = BadgeListOutput(
            name="list_badges",
            result=result,
            formatted_text="Badge List Output",
        )

        # Check values
        assert output.name == "list_badges"
        assert output.type == ToolType.BADGE
        assert output.formatted_text == "Badge List Output"
        assert output.result.earned_count == 0
        assert output.result.earned_formatted == ["No badges earned"]

    def test_quest_info_model(self):
        """Test the QuestInfo model."""
        # Create with minimum required fields
        quest = QuestInfo(
            id="test_quest",
            name="Test Quest",
            description="A test quest",
        )

        # Check default values
        assert quest.reward_xp == 0
        assert quest.badge_id is None
        assert quest.is_completed is False
        assert quest.guidance is None
        assert quest.hint is None

        # Create with all fields
        quest = QuestInfo(
            id="test_quest",
            name="Test Quest",
            description="A test quest",
            reward_xp=50,
            badge_id="test_badge",
            is_completed=True,
            guidance="Complete the quest",
            hint="Look for clues",
        )

        # Check values
        assert quest.id == "test_quest"
        assert quest.name == "Test Quest"
        assert quest.description == "A test quest"
        assert quest.reward_xp == 50
        assert quest.badge_id == "test_badge"
        assert quest.is_completed is True
        assert quest.guidance == "Complete the quest"
        assert quest.hint == "Look for clues"

    def test_quest_list_result_model(self):
        """Test the QuestListResult model."""
        # Create with default values
        result = QuestListResult()

        # Check default values
        assert result.completed == []
        assert result.completed_count == 0
        assert result.completed_formatted == []
        assert result.available == []
        assert result.available_count == 0
        assert result.available_formatted == []
        assert result.suggested == []
        assert result.suggested_formatted == []

        # Create with populated values
        quest1 = QuestInfo(
            id="quest1",
            name="Quest 1",
            description="First quest",
            is_completed=True,
        )
        quest2 = QuestInfo(
            id="quest2",
            name="Quest 2",
            description="Second quest",
            is_completed=False,
            reward_xp=100,
        )
        quest3 = QuestInfo(
            id="quest3",
            name="Quest 3",
            description="Third quest",
            is_completed=False,
            reward_xp=200,
        )

        result = QuestListResult(
            completed=[quest1],
            completed_count=1,
            completed_formatted=["Quest 1 completed"],
            available=[quest2],
            available_count=1,
            available_formatted=["Quest 2 available"],
            suggested=[quest3],
            suggested_formatted=["Quest 3 suggested"],
        )

        # Check values
        assert len(result.completed) == 1
        assert result.completed[0].id == "quest1"
        assert result.completed_count == 1
        assert result.completed_formatted == ["Quest 1 completed"]
        assert len(result.available) == 1
        assert result.available[0].id == "quest2"
        assert result.available_count == 1
        assert result.available_formatted == ["Quest 2 available"]
        assert len(result.suggested) == 1
        assert result.suggested[0].id == "quest3"
        assert result.suggested_formatted == ["Quest 3 suggested"]

    def test_quest_completion_detail_model(self):
        """Test the QuestCompletionDetail model."""
        # Create with minimum required fields
        detail = QuestCompletionDetail(
            id="test_quest",
            name="Test Quest",
            reward_xp=50,
            completion_message="You completed the quest!",
            formatted="Quest completed",
        )

        # Check values and defaults
        assert detail.id == "test_quest"
        assert detail.name == "Test Quest"
        assert detail.reward_xp == 50
        assert detail.badge is None
        assert detail.completion_message == "You completed the quest!"
        assert detail.formatted == "Quest completed"

        # Create with all fields
        detail = QuestCompletionDetail(
            id="test_quest",
            name="Test Quest",
            reward_xp=50,
            badge="🏆 Test Badge",
            completion_message="You completed the quest!",
            formatted="Quest completed + Badge earned",
        )

        # Check values
        assert detail.badge == "🏆 Test Badge"
        assert detail.formatted == "Quest completed + Badge earned"

    def test_quest_completion_result_model(self):
        """Test the QuestCompletionResult model."""
        # Create with default values
        result = QuestCompletionResult()

        # Check default values
        assert result.quests_completed is False
        assert result.completed_quests == []
        assert result.completed_details == []
        assert result.total_completed_count == 0
        assert result.old_level is None
        assert result.new_level is None

        # Create with populated values
        quest = QuestInfo(
            id="quest1",
            name="Quest 1",
            description="First quest",
            is_completed=True,
        )
        detail = QuestCompletionDetail(
            id="quest1",
            name="Quest 1",
            reward_xp=50,
            completion_message="You completed Quest 1!",
            formatted="Quest 1 completed",
        )

        result = QuestCompletionResult(
            quests_completed=True,
            completed_quests=[quest],
            completed_details=[detail],
            total_completed_count=5,
            old_level=2,
            new_level=3,
        )

        # Check values
        assert result.quests_completed is True
        assert len(result.completed_quests) == 1
        assert result.completed_quests[0].id == "quest1"
        assert len(result.completed_details) == 1
        assert result.completed_details[0].id == "quest1"
        assert result.total_completed_count == 5
        assert result.old_level == 2
        assert result.new_level == 3

    def test_progress_result_model(self):
        """Test the ProgressResult model."""
        # Create with required fields
        result = ProgressResult(
            level=3,
            xp=250,
            next_level=4,
            xp_needed=50,
            progress_pct=83.3,
            progress_bar="████████░░",
        )

        # Check values
        assert result.level == 3
        assert result.xp == 250
        assert result.next_level == 4
        assert result.xp_needed == 50
        assert result.progress_pct == 83.3
        assert result.progress_bar == "████████░░"

    def test_certificate_info_model(self):
        """Test the CertificateInfo model."""
        # Create with minimum required fields
        cert = CertificateInfo(
            id="test_cert",
            name="Test Certificate",
            description="A test certificate",
            formatted="Test Certificate - A test certificate",
        )

        # Check default values
        assert cert.earned is False
        assert cert.requirements == []
        assert cert.progress == 0.0
        assert cert.progress_bar == ""

        # Create with all fields
        cert = CertificateInfo(
            id="test_cert",
            name="Test Certificate",
            description="A test certificate",
            earned=True,
            requirements=["Req 1", "Req 2"],
            progress=75.0,
            progress_bar="███████░░░",
            formatted="Test Certificate - Earned!",
        )

        # Check values
        assert cert.id == "test_cert"
        assert cert.name == "Test Certificate"
        assert cert.description == "A test certificate"
        assert cert.earned is True
        assert cert.requirements == ["Req 1", "Req 2"]
        assert cert.progress == 75.0
        assert cert.progress_bar == "███████░░░"
        assert cert.formatted == "Test Certificate - Earned!"

    def test_certificate_list_result_model(self):
        """Test the CertificateListResult model."""
        # Create with default values
        result = CertificateListResult()

        # Check default values
        assert result.certificates == []
        assert result.earned_any is False
        assert result.certificate_count == 0
        assert result.earned_count == 0

        # Create with populated values
        cert1 = CertificateInfo(
            id="cert1",
            name="Certificate 1",
            description="First certificate",
            earned=True,
            formatted="Certificate 1 - Earned",
        )
        cert2 = CertificateInfo(
            id="cert2",
            name="Certificate 2",
            description="Second certificate",
            earned=False,
            progress=50.0,
            formatted="Certificate 2 - In progress",
        )

        result = CertificateListResult(
            certificates=[cert1, cert2],
            earned_any=True,
            certificate_count=2,
            earned_count=1,
        )

        # Check values
        assert len(result.certificates) == 2
        assert result.certificates[0].id == "cert1"
        assert result.certificates[1].id == "cert2"
        assert result.earned_any is True
        assert result.certificate_count == 2
        assert result.earned_count == 1

    def test_tutorial_result_model(self):
        """Test the TutorialResult model."""
        # Create with minimum required fields
        result = TutorialResult(
            topic="python",
            title="Python Tutorial",
        )

        # Check default values
        assert result.description == ""
        assert result.content == ""

        # Create with all fields
        result = TutorialResult(
            topic="python",
            title="Python Tutorial",
            description="Learn Python basics",
            content="Python is a versatile programming language...",
        )

        # Check values
        assert result.topic == "python"
        assert result.title == "Python Tutorial"
        assert result.description == "Learn Python basics"
        assert result.content == "Python is a versatile programming language..."

    def test_specialized_output_models(self):
        """Test that specialized output models have correct type values."""
        # Test BadgeListOutput
        result = BadgeListResult()
        output = BadgeListOutput(
            name="list_badges",
            result=result,
            formatted_text="Badge list",
        )
        assert output.type == ToolType.BADGE

        # Test QuestListOutput
        result = QuestListResult()
        output = QuestListOutput(
            name="list_quests",
            result=result,
            formatted_text="Quest list",
        )
        assert output.type == ToolType.QUEST

        # Test QuestDetailOutput
        quest = QuestInfo(
            id="quest1",
            name="Quest 1",
            description="First quest",
        )
        output = QuestDetailOutput(
            name="get_quest_details",
            result=quest,
            formatted_text="Quest details",
        )
        assert output.type == ToolType.QUEST

        # Test QuestCompletionOutput
        result = QuestCompletionResult()
        output = QuestCompletionOutput(
            name="verify_quest_completion",
            result=result,
            formatted_text="Quest completion",
        )
        assert output.type == ToolType.QUEST

        # Test ProgressOutput
        result = ProgressResult(
            level=1,
            xp=50,
            next_level=2,
            xp_needed=50,
            progress_pct=50.0,
            progress_bar="█████░░░░░",
        )
        output = ProgressOutput(
            name="list_xp_and_level",
            result=result,
            formatted_text="Progress info",
        )
        assert output.type == ToolType.PROGRESS

        # Test CertificateListOutput
        result = CertificateListResult()
        output = CertificateListOutput(
            name="get_certificate_info",
            result=result,
            formatted_text="Certificate list",
        )
        assert output.type == ToolType.CERTIFICATE

        # Test TutorialOutput
        result = TutorialResult(
            topic="python",
            title="Python Tutorial",
        )
        output = TutorialOutput(
            name="get_tutorial",
            result=result,
            formatted_text="Tutorial content",
        )
        assert output.type == ToolType.TUTORIAL
