# tests/test_teaching/test_npc/test_dialogue.py
"""
Tests for the Quackster NPC dialogue registry.

This module tests the dialogue registry functionality in quackcore.teaching.npc.dialogue.registry.
"""

from unittest.mock import MagicMock, patch

from quackcore.teaching.npc.dialogue.registry import DialogueRegistry
from quackcore.teaching.npc.schema import UserMemory


class TestDialogueRegistry:
    """Tests for NPC dialogue registry functionality."""

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_greeting_first_time(self, mock_load_yaml):
        """Test getting a greeting for a first-time user."""
        # Setup
        mock_load_yaml.return_value = {
            "first_time": ["Hello, new user!"],
            "returning": {
                "general": ["Welcome back!"],
            },
        }

        user_memory = UserMemory(
            github_username="testuser",
            conversation_count=0,  # First time
        )

        # Act
        result = DialogueRegistry.get_greeting(user_memory)

        # Assert
        assert result == "Hello, new user!"
        mock_load_yaml.assert_called_once_with("greetings")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_greeting_returning_general(self, mock_load_yaml):
        """Test getting a general greeting for a returning user."""
        # Setup
        mock_load_yaml.return_value = {
            "first_time": ["Hello, new user!"],
            "returning": {
                "general": ["Welcome back!"],
            },
        }

        user_memory = UserMemory(
            github_username="testuser",
            conversation_count=5,  # Returning user
        )

        # Act
        result = DialogueRegistry.get_greeting(user_memory)

        # Assert
        assert result == "Welcome back!"
        mock_load_yaml.assert_called_once_with("greetings")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    @patch("quackcore.teaching.npc.dialogue.registry.random.choice")
    def test_get_greeting_with_level(self, mock_choice, mock_load_yaml):
        """Test getting a level-specific greeting."""
        # Setup
        mock_load_yaml.return_value = {
            "returning": {
                "general": ["Welcome back!"],
                "level": ["Welcome back, level {{ level }} coder!"],
            },
        }

        # Mock random.choice to always return the level greeting
        mock_choice.return_value = "Welcome back, level {{ level }} coder!"

        user_memory = UserMemory(
            github_username="testuser",
            conversation_count=5,
            level=3,
        )

        # Act
        result = DialogueRegistry.get_greeting(user_memory)

        # Assert
        assert "level 3" in result
        mock_load_yaml.assert_called_once_with("greetings")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    @patch("quackcore.teaching.npc.dialogue.registry.random.choice")
    def test_get_greeting_with_badges(self, mock_choice, mock_load_yaml):
        """Test getting a badge-specific greeting."""
        # Setup
        mock_load_yaml.return_value = {
            "returning": {
                "general": ["Welcome back!"],
                "badges": ["Welcome badge collector with {{ badge_count }} badges!"],
            },
        }

        # Mock random.choice to always return the badge greeting
        mock_choice.return_value = (
            "Welcome badge collector with {{ badge_count }} badges!"
        )

        user_memory = UserMemory(
            github_username="testuser",
            conversation_count=5,
            badges=["badge1", "badge2"],
        )

        # Act
        result = DialogueRegistry.get_greeting(user_memory)

        # Assert
        assert "2 badges" in result
        mock_load_yaml.assert_called_once_with("greetings")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_farewell_general(self, mock_load_yaml):
        """Test getting a general farewell."""
        # Setup
        mock_load_yaml.return_value = {
            "general": ["Goodbye!"],
            "beginner": ["Goodbye, beginner!"],
            "intermediate": ["Goodbye, intermediate!"],
            "advanced": ["Goodbye, advanced!"],
        }

        user_memory = UserMemory(
            github_username="testuser",
            xp=50,  # Beginner level
        )

        # Act
        result = DialogueRegistry.get_farewell(user_memory)

        # Assert
        assert result in ["Goodbye!", "Goodbye, beginner!"]
        mock_load_yaml.assert_called_once_with("farewells")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    @patch("quackcore.teaching.npc.dialogue.registry.random.choice")
    def test_get_farewell_intermediate(self, mock_choice, mock_load_yaml):
        """Test getting an intermediate farewell."""
        # Setup
        mock_load_yaml.return_value = {
            "general": ["Goodbye!"],
            "beginner": ["Goodbye, beginner!"],
            "intermediate": ["Goodbye, level {{ level }} coder!"],
            "advanced": ["Goodbye, advanced!"],
        }

        # Mock random.choice to always return the intermediate greeting
        mock_choice.return_value = "Goodbye, level {{ level }} coder!"

        user_memory = UserMemory(
            github_username="testuser",
            xp=200,  # Intermediate level
            level=3,
        )

        # Act
        result = DialogueRegistry.get_farewell(user_memory)

        # Assert
        assert "level 3" in result
        mock_load_yaml.assert_called_once_with("farewells")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_catchphrase(self, mock_load_yaml):
        """Test getting a catchphrase."""
        # Setup
        mock_load_yaml.return_value = {
            "catchphrases": ["Quacktastic!"],
        }

        # Act
        result = DialogueRegistry.get_catchphrase()

        # Assert
        assert result == "Quacktastic!"
        mock_load_yaml.assert_called_once_with("catchphrases")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_badge_dialogue(self, mock_load_yaml):
        """Test getting badge dialogue."""
        # Setup
        mock_load_yaml.return_value = {
            "test-badge": {
                "description": "Test badge description",
                "guidance": "How to earn the test badge",
                "fun_fact": "Fun fact about test badge",
            },
        }

        # Act
        description = DialogueRegistry.get_badge_dialogue("test-badge", "description")
        guidance = DialogueRegistry.get_badge_dialogue("test-badge", "guidance")
        fun_fact = DialogueRegistry.get_badge_dialogue("test-badge", "fun_fact")
        nonexistent = DialogueRegistry.get_badge_dialogue("test-badge", "nonexistent")

        # Assert
        assert description == "Test badge description"
        assert guidance == "How to earn the test badge"
        assert fun_fact == "Fun fact about test badge"
        assert nonexistent is None
        mock_load_yaml.assert_called_once_with("badges")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    def test_get_quest_dialogue(self, mock_load_yaml):
        """Test getting quest dialogue."""
        # Setup
        mock_load_yaml.return_value = {
            "test-quest": {
                "guidance": "How to complete the test quest",
                "hint": "A hint for the test quest",
                "completion": "Congratulations on completing the test quest",
            },
        }

        # Act
        guidance = DialogueRegistry.get_quest_dialogue("test-quest", "guidance")
        hint = DialogueRegistry.get_quest_dialogue("test-quest", "hint")
        completion = DialogueRegistry.get_quest_dialogue("test-quest", "completion")
        nonexistent = DialogueRegistry.get_quest_dialogue("test-quest", "nonexistent")

        # Assert
        assert guidance == "How to complete the test quest"
        assert hint == "A hint for the test quest"
        assert completion == "Congratulations on completing the test quest"
        assert nonexistent is None
        mock_load_yaml.assert_called_once_with("quests")

    @patch("quackcore.teaching.npc.dialogue.registry.env")
    def test_render_template(self, mock_env):
        """Test rendering a template."""
        # Setup
        mock_template = MagicMock()
        mock_template.render.return_value = "Rendered template with value: test"

        mock_env.get_template.return_value = mock_template

        context = {"value": "test"}

        # Act
        result = DialogueRegistry.render_template("template.md.j2", context)

        # Assert
        assert result == "Rendered template with value: test"
        mock_env.get_template.assert_called_once_with("template.md.j2")
        mock_template.render.assert_called_once_with(**context)

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    @patch("quackcore.teaching.npc.dialogue.registry.random")
    def test_flavor_text_generic(self, mock_random, mock_load_yaml):
        """Test adding flavor text."""
        # Setup
        # Mock random to predictably add flavor
        mock_random.random.return_value = 0.1  # Add flavor
        mock_random.choice.return_value = "Learning time! "  # The flavor text

        # Don't add a quack catchphrase
        mock_load_yaml.return_value = {"catchphrases": ["Quacktastic!"]}
        mock_random.random.side_effect = [
            0.1,
            0.5,
        ]  # First random for flavor category, second for catchphrase

        # Act
        result = DialogueRegistry.flavor_text("tutorial", "Learn Python basics")

        # Assert
        assert result == "Learning time! Learn Python basics 📚 🦆"
        mock_load_yaml.assert_called_once_with("catchphrases")

    @patch("quackcore.teaching.npc.dialogue.registry.load_yaml")
    @patch("quackcore.teaching.npc.dialogue.registry.random")
    def test_flavor_text_with_catchphrase(self, mock_random, mock_load_yaml):
        """Test adding flavor text with a catchphrase."""
        # Setup
        # Mock random to predictably add flavor and catchphrase
        mock_random.random.side_effect = [
            0.5,
            0.1,
        ]  # Skip category flavor, add catchphrase
        mock_random.choice.return_value = "Quacktastic!"  # The catchphrase

        mock_load_yaml.return_value = {"catchphrases": ["Quacktastic!"]}

        # Act
        result = DialogueRegistry.flavor_text("badge", "You earned a badge")

        # Assert
        assert result == "Quacktastic! You earned a badge 🏆 🦆"
        mock_load_yaml.assert_called_once_with("catchphrases")

    @patch("quackcore.teaching.npc.dialogue.registry.random")
    def test_flavor_text_no_duck_emoji(self, mock_random):
        """Test adding flavor text when duck emoji is already present."""
        # Setup
        # Mock random to predictably add flavor
        mock_random.random.return_value = 0.1  # Try to add flavor
        mock_random.choice.return_value = "Nice job! "  # The flavor text

        # Input text already has duck emoji
        input_text = "Progress update 🦆"

        # Act
        result = DialogueRegistry.flavor_text("xp", input_text)

        # Assert
        assert result == "Nice job! Progress update 🦆"
        # No additional duck emoji should be added
