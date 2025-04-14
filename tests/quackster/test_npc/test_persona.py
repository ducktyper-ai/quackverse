# tests/quackster/test_npc/test_persona.py
"""
Tests for the Quackster NPC persona functionality.

This module tests the persona management functionality in quackster.npc.persona.
"""

from unittest.mock import patch

from quackster.npc import persona
from quackster.npc.schema import QuacksterProfile, UserMemory


class TestNPCPersona:
    """Tests for NPC persona functionality."""

    @patch("quackster.npc.persona.DialogueRegistry")
    def test_get_system_prompt_success(self, mock_registry):
        """Test successfully generating a system prompt."""
        # Setup
        mock_registry.render_system_prompt.return_value = "System prompt"

        profile = QuacksterProfile(
            name="Quackster",
            tone="friendly",
            backstory="A helpful duck",
            expertise=["Python", "GitHub"],
        )

        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
        )

        # Act
        result = persona.get_system_prompt(profile, user_memory)

        # Assert
        assert result == "System prompt"
        mock_registry.render_system_prompt.assert_called_once_with(profile, user_memory)

    @patch("quackster.npc.persona.DialogueRegistry")
    @patch("quackster.npc.persona.logger")
    def test_get_system_prompt_error_fallback(self, mock_logger, mock_registry):
        """Test fallback to basic system prompt when template rendering fails."""
        # Setup
        mock_registry.render_system_prompt.side_effect = Exception("Template error")

        profile = QuacksterProfile(
            name="Quackster",
            tone="friendly",
            backstory="A helpful duck",
            expertise=["Python", "GitHub"],
        )

        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
        )

        # Act
        result = persona.get_system_prompt(profile, user_memory)

        # Assert
        assert result  # Should return a non-empty string
        assert isinstance(result, str)
        assert "Quackster" in result  # Should include the NPC name
        assert "friendly" in result  # Should include the tone
        assert "Python" in result  # Should include expertise

        mock_registry.render_system_prompt.assert_called_once()
        mock_logger.error.assert_called_once()

    def test_get_example_conversations(self):
        """Test getting example conversations for few-shot learning."""
        # Act
        result = persona.get_example_conversations()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure of example conversations
        for example in result:
            assert "conversation" in example
            assert isinstance(example["conversation"], list)
            assert len(example["conversation"]) > 0

            # Check that each message has role and content
            for message in example["conversation"]:
                assert "role" in message
                assert message["role"] in ["user", "assistant"]
                assert "content" in message
                assert isinstance(message["content"], str)

    @patch("quackster.npc.persona.DialogueRegistry")
    def test_get_greetings(self, mock_registry):
        """Test getting appropriate greetings based on user memory."""
        # Setup
        mock_registry.get_greeting.return_value = "Quack! Hello!"

        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            conversation_count=5,
        )

        # Act
        result = persona.get_greetings(user_memory)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Quack! Hello!"
        mock_registry.get_greeting.assert_called_once_with(user_memory)

    @patch("quackster.npc.persona.DialogueRegistry")
    def test_get_farewells(self, mock_registry):
        """Test getting appropriate farewells based on user memory."""
        # Setup
        mock_registry.get_farewell.return_value = "Quack for now!"

        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            conversation_count=5,
        )

        # Act
        result = persona.get_farewells(user_memory)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Quack for now!"
        mock_registry.get_farewell.assert_called_once_with(user_memory)

    @patch("quackster.npc.persona.DialogueRegistry")
    def test_get_catchphrases(self, mock_registry):
        """Test getting catchphrases."""
        # Setup
        mock_registry.get_catchphrase.return_value = "Quacktastic!"

        # Act
        result = persona.get_catchphrases()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "Quacktastic!"
        mock_registry.get_catchphrase.assert_called_once()

    def test_get_fallback_system_prompt(self):
        """Test the fallback system prompt function."""
        # Setup
        profile = QuacksterProfile(
            name="Quackster",
            tone="friendly",
            backstory="A helpful duck",
            expertise=["Python", "GitHub"],
            teaching_style="Socratic",
            emoji_style="moderate",
            catchphrases=["Quacktastic!"],
        )

        user_memory = UserMemory(
            github_username="testuser",
            xp=100,
            level=2,
            conversation_count=5,
            completed_quests=["quest1"],
            badges=["badge1"],
        )

        # Act
        result = persona._get_fallback_system_prompt(profile, user_memory)

        # Assert
        assert isinstance(result, str)
        assert "Quackster" in result
        assert "friendly" in result
        assert "A helpful duck" in result
        assert "Python" in result
        assert "GitHub" in result
        assert "Socratic" in result

        # Check user information
        assert "testuser" in result
        assert "Level: 2" in result
        assert "XP: 100" in result

        # Check tools section
        assert "AVAILABLE TOOLS:" in result
        assert "list_xp_and_level" in result
        assert "list_badges" in result
        assert "list_quests" in result
        assert "get_quest_details" in result
        assert "suggest_next_quest" in result
        assert "verify_quest_completion" in result

        # Check response guidelines
        assert "RESPONSE GUIDELINES:" in result
