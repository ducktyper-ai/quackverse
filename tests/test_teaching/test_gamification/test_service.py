# tests/test_teaching/test_gamification/test_service.py
"""
Tests for the gamification service integration features.

This module tests GitHub and LMS integration features in the gamification service.
"""

from unittest.mock import MagicMock, patch

from quackcore.teaching.core.gamification_service import GamificationService
from quackcore.teaching.core.models import UserProgress, XPEvent


class TestGamificationServiceIntegration:
    """Tests for integration features of the gamification service."""

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_pr_submission(self, mock_save):
        """Test handling a GitHub pull request submission."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.completed_quests = []
        mock_result.earned_badges = []
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_github_pr_submission(42, "quackverse/test-repo")

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "PR #42" in event_arg.label
            assert event_arg.points == 25
            assert event_arg.metadata["repo"] == "quackverse/test-repo"
            assert event_arg.metadata["pr_number"] == 42

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_pr_submission_with_open_pr_quest(self, mock_save):
        """Test handling a PR submission that completes the open-pr quest."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_event_result = MagicMock()
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "Handled event"

        # Mock complete_quest to return a specified result
        mock_quest_result = MagicMock()
        mock_quest_result.completed_quests = ["open-pr"]
        mock_quest_result.earned_badges = ["duck-contributor"]
        mock_quest_result.message = "Completed quest"

        with patch.object(
            service, "handle_event", return_value=mock_event_result
        ) as mock_handle_event:
            with patch.object(
                service, "complete_quest", return_value=mock_quest_result
            ) as mock_complete_quest:
                with patch.object(
                    user, "has_completed_quest", return_value=False
                ) as mock_has_completed:
                    # Act
                    result = service.handle_github_pr_submission(
                        42, "quackverse/quackcore"
                    )

                    # Assert
                    mock_handle_event.assert_called_once()
                    mock_has_completed.assert_called_with("open-pr")
                    mock_complete_quest.assert_called_with("open-pr")

                    assert "Handled event" in result.message
                    assert "Completed quest" in result.message
                    assert "open-pr" in result.completed_quests
                    assert "duck-contributor" in result.earned_badges

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_pr_merged(self, mock_save):
        """Test handling a GitHub pull request being merged."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.completed_quests = []
        mock_result.earned_badges = []
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_github_pr_merged(42, "quackverse/test-repo")

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "merged" in event_arg.label.lower()
            assert event_arg.points == 50
            assert event_arg.metadata["repo"] == "quackverse/test-repo"
            assert event_arg.metadata["pr_number"] == 42

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_pr_merged_with_merged_pr_quest(self, mock_save):
        """Test handling a merged PR that completes the merged-pr quest."""
        # Setup
        user = UserProgress(github_username="testuser", xp=100)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_event_result = MagicMock()
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "Handled event"

        # Mock complete_quest to return a specified result
        mock_quest_result = MagicMock()
        mock_quest_result.completed_quests = ["merged-pr"]
        mock_quest_result.earned_badges = ["duck-team-player"]
        mock_quest_result.message = "Completed quest"

        with patch.object(
            service, "handle_event", return_value=mock_event_result
        ) as mock_handle_event:
            with patch.object(
                service, "complete_quest", return_value=mock_quest_result
            ) as mock_complete_quest:
                with patch.object(
                    user, "has_completed_quest", return_value=False
                ) as mock_has_completed:
                    # Act
                    result = service.handle_github_pr_merged(42, "quackverse/test-repo")

                    # Assert
                    mock_handle_event.assert_called_once()
                    mock_has_completed.assert_called_with("merged-pr")
                    mock_complete_quest.assert_called_with("merged-pr")

                    assert "Handled event" in result.message
                    assert "Completed quest" in result.message
                    assert "merged-pr" in result.completed_quests
                    assert "duck-team-player" in result.earned_badges

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_star(self, mock_save):
        """Test handling a GitHub repository star."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.completed_quests = []
        mock_result.earned_badges = []
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_github_star("quackverse/test-repo")

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "Starred" in event_arg.label
            assert event_arg.points == 10
            assert event_arg.metadata["repo"] == "quackverse/test-repo"

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_github_star_quackcore(self, mock_save):
        """Test handling a star on the QuackCore repository."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_event_result = MagicMock()
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "Handled event"

        # Mock complete_quest to return a specified result
        mock_quest_result = MagicMock()
        mock_quest_result.completed_quests = ["star-quackcore"]
        mock_quest_result.earned_badges = ["github-collaborator"]
        mock_quest_result.message = "Completed quest"

        with patch.object(
            service, "handle_event", return_value=mock_event_result
        ) as mock_handle_event:
            with patch.object(
                service, "complete_quest", return_value=mock_quest_result
            ) as mock_complete_quest:
                with patch.object(
                    user, "has_completed_quest", return_value=False
                ) as mock_has_completed:
                    # Act
                    result = service.handle_github_star("quackverse/quackcore")

                    # Assert
                    mock_handle_event.assert_called_once()
                    mock_has_completed.assert_called_with("star-quackcore")
                    mock_complete_quest.assert_called_with("star-quackcore")

                    assert "Handled event" in result.message
                    assert "Completed quest" in result.message
                    assert "star-quackcore" in result.completed_quests
                    assert "github-collaborator" in result.earned_badges

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_module_completion(self, mock_save):
        """Test handling completion of an Academy/LMS module."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.completed_quests = []
        mock_result.earned_badges = []
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_module_completion(
                "test-course", "module-1", "Introduction Module"
            )

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "Completed module" in event_arg.label
            assert "Introduction Module" in event_arg.label
            assert event_arg.points == 30
            assert event_arg.metadata["course_id"] == "test-course"
            assert event_arg.metadata["module_id"] == "module-1"
            assert event_arg.metadata["module_name"] == "Introduction Module"

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_module_completion_tutorial(self, mock_save):
        """Test handling completion of a tutorial module."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_event_result = MagicMock()
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "Handled event"

        # Mock complete_quest to return a specified result
        mock_quest_result = MagicMock()
        mock_quest_result.completed_quests = ["complete-tutorial"]
        mock_quest_result.earned_badges = ["duck-explorer"]
        mock_quest_result.message = "Completed quest"

        with patch.object(
            service, "handle_event", return_value=mock_event_result
        ) as mock_handle_event:
            with patch.object(
                service, "complete_quest", return_value=mock_quest_result
            ) as mock_complete_quest:
                with patch.object(
                    user, "has_completed_quest", return_value=False
                ) as mock_has_completed:
                    # Act
                    result = service.handle_module_completion(
                        "test-course", "tutorial-1", "Basic Tutorial Module"
                    )

                    # Assert
                    mock_handle_event.assert_called_once()
                    mock_has_completed.assert_called_with("complete-tutorial")
                    mock_complete_quest.assert_called_with("complete-tutorial")

                    assert "Handled event" in result.message
                    assert "Completed quest" in result.message
                    assert "complete-tutorial" in result.completed_quests
                    assert "duck-explorer" in result.earned_badges

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_course_completion(self, mock_save):
        """Test handling completion of an Academy/LMS course."""
        # Setup
        user = UserProgress(github_username="testuser", xp=150)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_event_result = MagicMock()
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "Handled event"

        # Mock award_badge to return a specified result
        mock_badge_result = MagicMock()
        mock_badge_result.earned_badges = ["duck-graduate"]
        mock_badge_result.message = "Earned badge"

        with patch.object(
            service, "handle_event", return_value=mock_event_result
        ) as mock_handle_event:
            with patch.object(
                service, "award_badge", return_value=mock_badge_result
            ) as mock_award_badge:
                with patch.object(
                    user, "has_earned_badge", return_value=False
                ) as mock_has_badge:
                    # Act
                    result = service.handle_course_completion(
                        "test-course", "Test Course"
                    )

                    # Assert
                    mock_handle_event.assert_called_once()
                    mock_has_badge.assert_called_with("duck-graduate")
                    mock_award_badge.assert_called_with("duck-graduate")

                    # Check that handle_event was called with the correct event
                    event_arg = mock_handle_event.call_args[0][0]
                    assert isinstance(event_arg, XPEvent)
                    assert "Completed course" in event_arg.label
                    assert "Test Course" in event_arg.label
                    assert event_arg.points == 100
                    assert event_arg.metadata["course_id"] == "test-course"
                    assert event_arg.metadata["course_name"] == "Test Course"

                    assert "Handled event" in result.message
                    assert "Earned badge" in result.message
                    assert "duck-graduate" in result.earned_badges

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_assignment_completion(self, mock_save):
        """Test handling completion of an Academy/LMS assignment."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_assignment_completion(
                "assignment-1", "First Assignment", 85.0, 100.0
            )

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "Completed assignment" in event_arg.label
            assert "First Assignment" in event_arg.label
            assert (
                45 <= event_arg.points <= 50
            )  # Points should be based on percentage (85%)
            assert event_arg.metadata["assignment_id"] == "assignment-1"
            assert event_arg.metadata["assignment_name"] == "First Assignment"
            assert event_arg.metadata["score"] == 85.0
            assert event_arg.metadata["max_score"] == 100.0
            assert event_arg.metadata["percentage"] == 0.85

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_feedback_submission(self, mock_save):
        """Test handling submission of feedback."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_feedback_submission(
                "feedback-1", "Assignment Feedback"
            )

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "Provided feedback" in event_arg.label
            assert "Assignment Feedback" in event_arg.label
            assert event_arg.points == 5
            assert event_arg.metadata["feedback_id"] == "feedback-1"
            assert event_arg.metadata["context"] == "Assignment Feedback"

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    def test_handle_tool_usage(self, mock_save):
        """Test handling tool usage."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock handle_event to return a specified result
        mock_result = MagicMock()
        mock_result.message = "Handled event"

        with patch.object(
            service, "handle_event", return_value=mock_result
        ) as mock_handle_event:
            # Act
            result = service.handle_tool_usage("ducktyper", "analyze")

            # Assert
            assert result is mock_result

            # Check that handle_event was called with the correct event
            event_arg = mock_handle_event.call_args[0][0]
            assert isinstance(event_arg, XPEvent)
            assert "Used ducktyper" in event_arg.label
            assert "analyze" in event_arg.label
            assert event_arg.points == 2
            assert event_arg.metadata["tool"] == "ducktyper"
            assert event_arg.metadata["action"] == "analyze"
            assert "date" in event_arg.metadata  # Should have today's date

    @patch("quackcore.teaching.core.gamification_service.utils.save_progress")
    @patch("quackcore.teaching.core.gamification_service.datetime")
    def test_handle_ducktyper_run_first_time(self, mock_datetime, mock_save):
        """Test handling first run of DuckTyper."""
        # Setup
        user = UserProgress(github_username="testuser", xp=50)
        service = GamificationService(user_progress=user)

        # Mock today's date
        mock_date = MagicMock()
        mock_date.strftime.return_value = "2025-04-11"
        mock_datetime.now.return_value = mock_date

        # Mock handle_event to return specified results
        mock_tool_result = MagicMock()
        mock_tool_result.xp_added = 2
        mock_tool_result.message = "Tool used"

        mock_run_result = MagicMock()
        mock_run_result.xp_added = 10
        mock_run_result.message = "First run"

        mock_quest_result = MagicMock()
        mock_quest_result.completed_quests = ["run-ducktyper"]
        mock_quest_result.xp_added = 10
        mock_quest_result.message = "Quest completed"

        with patch.object(service, "handle_event") as mock_handle_event:
            mock_handle_event.side_effect = [
                mock_tool_result,
                mock_run_result,
                MagicMock(),
            ]

            with patch.object(
                service, "complete_quest", return_value=mock_quest_result
            ) as mock_complete_quest:
                with patch.object(
                    user, "has_completed_event", return_value=False
                ) as mock_has_event:
                    with patch.object(
                        user, "has_completed_quest", return_value=False
                    ) as mock_has_quest:
                        # Act
                        result = service.handle_tool_usage("ducktyper", "run")

                        # Assert
                        assert (
                            mock_handle_event.call_count == 3
                        )  # Tool event, run event, day event
                        mock_has_event.assert_called_with("run-ducktyper")
                        mock_has_quest.assert_called_with("run-ducktyper")
                        mock_complete_quest.assert_called_with("run-ducktyper")

                        assert result.xp_added == 22  # 2 + 10 + 10
                        assert "run-ducktyper" in result.completed_quests
                        assert "Tool used" in result.message
                        assert "First run" in result.message
                        assert "Quest completed" in result.message

                        # Check the day event ID
                        day_event_arg = mock_handle_event.call_args_list[2][0][0]
                        assert day_event_arg.id == "run-ducktyper-day-2025-04-11"
                        assert day_event_arg.points == 0  # Tracking event, no points
