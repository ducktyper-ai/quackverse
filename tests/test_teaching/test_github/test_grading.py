# tests/test_teaching/test_github/test_grading.py
"""
Tests for the GitHub grading functionality.

This module tests the GitHub grading functionality in quackcore.teaching.github.grading.
"""
from unittest.mock import MagicMock, patch

from quackcore.errors import QuackApiError
from quackcore.integrations.core import IntegrationResult
from quackcore.teaching.github.grading import GitHubGrader
from quackcore.teaching.github.models import GradeResult


class TestGitHubGrader:
    """Tests for the GitHub grader."""

    def test_init(self):
        """Test initialization of the GitHub grader."""
        # Setup
        mock_client = MagicMock()

        # Act
        grader = GitHubGrader(mock_client)

        # Assert
        assert grader.client is mock_client

    @patch("quackcore.teaching.github.grading.GamificationService")
    def test_grade_submission_success(self, mock_gamification_service_class):
        """Test successful submission grading."""
        # Setup
        mock_client = MagicMock()

        # Mock get_pull_request_files
        mock_files = [
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "changes": 12,
            },
            {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 25,
                "deletions": 5,
                "changes": 30,
            },
        ]
        mock_client.get_pull_request_files.return_value = mock_files

        # Mock gamification service
        mock_gamification_service = MagicMock()
        mock_gamification_service_class.return_value = mock_gamification_service

        mock_result = MagicMock()
        mock_result.xp_added = 25
        mock_result.level = 2
        mock_result.level_up = False
        mock_result.completed_quests = []
        mock_result.earned_badges = []
        mock_result.message = "XP awarded"
        mock_gamification_service.handle_event.return_value = mock_result

        # Create grader and pull request
        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"
        mock_pr.author = MagicMock(username="testuser")
        mock_pr.merged = False

        # Act
        result = grader.grade_submission(mock_pr)

        # Assert
        assert result.success is True
        assert "Successfully graded submission" in result.message

        # Verify the result content
        grade_result = result.content
        assert isinstance(grade_result, GradeResult)
        assert 0.0 <= grade_result.score <= 1.0
        assert grade_result.comments is not None
        assert "# Grading Results" in grade_result.comments

        # Verify client calls
        mock_client.get_pull_request_files.assert_called_once_with(
            repo="test/repo", pull_number=42
        )

        # Verify gamification calls
        mock_gamification_service.handle_event.assert_called_once()
        event_arg = mock_gamification_service.handle_event.call_args[0][0]
        assert f"graded-pr-{mock_pr.number}" in event_arg.id
        assert "Passed grading" in event_arg.label

    @patch("quackcore.teaching.github.grading.GamificationService")
    def test_grade_submission_merged_pr(self, mock_gamification_service_class):
        """Test grading a merged pull request."""
        # Setup
        mock_client = MagicMock()

        # Mock get_pull_request_files
        mock_files = [
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "changes": 12,
            },
        ]
        mock_client.get_pull_request_files.return_value = mock_files

        # Mock gamification service
        mock_gamification_service = MagicMock()
        mock_gamification_service_class.return_value = mock_gamification_service

        # Mock handle_event result
        mock_event_result = MagicMock()
        mock_event_result.xp_added = 25
        mock_event_result.level = 2
        mock_event_result.level_up = False
        mock_event_result.completed_quests = []
        mock_event_result.earned_badges = []
        mock_event_result.message = "XP awarded"

        # Mock handle_github_pr_merged result
        mock_pr_merged_result = MagicMock()
        mock_pr_merged_result.message = "PR merge recorded"

        mock_gamification_service.handle_event.return_value = mock_event_result
        mock_gamification_service.handle_github_pr_merged.return_value = mock_pr_merged_result

        # Create grader and pull request
        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "quackverse/test-repo"
        mock_pr.author = MagicMock(username="testuser")
        mock_pr.merged = True

        # Act
        result = grader.grade_submission(mock_pr)

        # Assert
        assert result.success is True

        # Verify the gamification calls
        mock_gamification_service.handle_event.assert_called_once()
        mock_gamification_service.handle_github_pr_merged.assert_called_once_with(
            42, "quackverse/test-repo"
        )

        # Verify the gamification result is included in the grade result
        grade_result = result.content
        assert "gamification" in grade_result.details

    def test_grade_submission_api_error(self):
        """Test grading when a GitHub API error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_pull_request_files.side_effect = QuackApiError("API error")

        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"

        # Act
        result = grader.grade_submission(mock_pr)

        # Assert
        assert result.success is False
        assert "Failed to grade submission" in result.error
        assert "API error" in result.error

    def test_grade_submission_general_error(self):
        """Test grading when a general error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_pull_request_files.side_effect = Exception("Unexpected error")

        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"

        # Act
        result = grader.grade_submission(mock_pr)

        # Assert
        assert result.success is False
        assert "Unexpected error during grading" in result.error

    def test_get_pr_files_client_method_available(self):
        """Test _get_pr_files when the client method is available."""
        # Setup
        mock_client = MagicMock()
        mock_files = [{"filename": "README.md"}]
        mock_client.get_pull_request_files.return_value = mock_files

        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"

        # Act
        result = grader._get_pr_files(mock_pr)

        # Assert
        assert result.success is True
        assert result.content == mock_files
        assert "Found 1 changed files" in result.message

        mock_client.get_pull_request_files.assert_called_once_with(
            repo="test/repo", pull_number=42
        )

    def test_get_pr_files_attribute_error(self):
        """Test _get_pr_files when the client method is not available (AttributeError)."""
        # Setup
        mock_client = MagicMock()

        # Remove the get_pull_request_files attribute to simulate AttributeError
        del mock_client.get_pull_request_files

        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"

        # Act
        result = grader._get_pr_files(mock_pr)

        # Assert
        assert result.success is True
        assert len(result.content) > 0  # Should return simulated data
        assert "simulated" in result.message.lower()

    def test_get_pr_files_api_error(self):
        """Test _get_pr_files when a GitHub API error occurs."""
        # Setup
        mock_client = MagicMock()
        mock_client.get_pull_request_files.side_effect = QuackApiError("API error")

        grader = GitHubGrader(mock_client)
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"

        # Act
        result = grader._get_pr_files(mock_pr)

        # Assert
        assert result.success is False
        assert "Failed to get PR files" in result.error
        assert "API error" in result.error

    def test_default_grading_criteria(self):
        """Test the default grading criteria."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Act
        criteria = grader._default_grading_criteria()

        # Assert
        assert isinstance(criteria, dict)
        assert "passing_threshold" in criteria
        assert "required_files" in criteria
        assert "required_changes" in criteria
        assert "prohibited_patterns" in criteria

        # Check required files structure
        required_files = criteria["required_files"]
        assert "points" in required_files
        assert "files" in required_files
        assert isinstance(required_files["files"], list)

        # Check required changes structure
        required_changes = criteria["required_changes"]
        assert "points" in required_changes
        assert "changes" in required_changes
        assert isinstance(required_changes["changes"], list)

        # Check prohibited patterns structure
        prohibited_patterns = criteria["prohibited_patterns"]
        assert "points" in prohibited_patterns
        assert "patterns" in prohibited_patterns
        assert isinstance(prohibited_patterns["patterns"], list)

    def test_check_required_files_all_present(self):
        """Test checking for required files when all are present."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        changed_files = [
            {"filename": "README.md"},
            {"filename": "src/main.py"},
            {"filename": "test/test_main.py"},
        ]

        criteria = {
            "points": 50,
            "files": ["README.md", "src/main.py"],
        }

        # Act
        result = grader._check_required_files(changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 50  # All files present, full points
        assert result["points_possible"] == 50
        assert result["missing_files"] == []
        assert "All 2 required files found" in result["comment"]
        assert result["passed"] is True

    def test_check_required_files_some_missing(self):
        """Test checking for required files when some are missing."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        changed_files = [
            {"filename": "README.md"},
            # src/main.py is missing
        ]

        criteria = {
            "points": 50,
            "files": ["README.md", "src/main.py"],
        }

        # Act
        result = grader._check_required_files(changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 25  # Half the files, half the points
        assert result["points_possible"] == 50
        assert "src/main.py" in result["missing_files"]
        assert "1/2 files found" in result["comment"]
        assert result["passed"] is False

    def test_check_required_files_no_criteria(self):
        """Test checking for required files when criteria is empty."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        changed_files = [{"filename": "README.md"}]
        criteria = {"points": 50, "files": []}

        # Act
        result = grader._check_required_files(changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 50  # Full points, no requirements
        assert result["points_possible"] == 50
        assert "No required files specified" in result["comment"]
        assert result["passed"] is True

    def test_check_required_changes_all_satisfied(self):
        """Test checking for required changes when all are satisfied."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        mock_pr = MagicMock()
        changed_files = [
            {
                "filename": "src/main.py",
                "additions": 15,
                "deletions": 2,
                "changes": 17,
            },
            {
                "filename": "README.md",
                "additions": 5,
                "deletions": 0,
                "changes": 5,
            },
        ]

        criteria = {
            "points": 30,
            "changes": [
                {
                    "file": "src/main.py",
                    "min_additions": 10,
                    "description": "Implement the main function",
                },
                {
                    "file": "README.md",
                    "min_additions": 5,
                    "description": "Update documentation",
                },
            ],
        }

        # Act
        result = grader._check_required_changes(mock_pr, changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 30  # All changes satisfied, full points
        assert result["points_possible"] == 30
        assert len(result["passed_changes"]) == 2
        assert len(result["failed_changes"]) == 0
        assert "All 2 required changes implemented" in result["comment"]
        assert result["passed"] is True

    def test_check_required_changes_partially_satisfied(self):
        """Test checking for required changes when some are not satisfied."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        mock_pr = MagicMock()
        changed_files = [
            {
                "filename": "src/main.py",
                "additions": 5,  # Less than required
                "deletions": 2,
                "changes": 7,
            },
            {
                "filename": "README.md",
                "additions": 5,
                "deletions": 0,
                "changes": 5,
            },
        ]

        criteria = {
            "points": 30,
            "changes": [
                {
                    "file": "src/main.py",
                    "min_additions": 10,
                    "description": "Implement the main function",
                },
                {
                    "file": "README.md",
                    "min_additions": 5,
                    "description": "Update documentation",
                },
            ],
        }

        # Act
        result = grader._check_required_changes(mock_pr, changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 15  # Half the changes, half the points
        assert result["points_possible"] == 30
        assert len(result["passed_changes"]) == 1
        assert len(result["failed_changes"]) == 1
        assert "1/2 changes implemented" in result["comment"]
        assert result["passed"] is False

    def test_check_required_changes_missing_file(self):
        """Test checking for required changes when a file is missing."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        mock_pr = MagicMock()
        changed_files = [
            {
                "filename": "README.md",
                "additions": 5,
                "deletions": 0,
                "changes": 5,
            },
            # src/main.py is missing
        ]

        criteria = {
            "points": 30,
            "changes": [
                {
                    "file": "src/main.py",
                    "min_additions": 10,
                    "description": "Implement the main function",
                },
                {
                    "file": "README.md",
                    "min_additions": 5,
                    "description": "Update documentation",
                },
            ],
        }

        # Act
        result = grader._check_required_changes(mock_pr, changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 15  # Half the changes, half the points
        assert result["points_possible"] == 30
        assert len(result["passed_changes"]) == 1
        assert len(result["failed_changes"]) == 1
        assert "1/2 changes implemented" in result["comment"]
        assert result["passed"] is False

    def test_check_required_changes_no_criteria(self):
        """Test checking for required changes when criteria is empty."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Create test data
        mock_pr = MagicMock()
        changed_files = [{"filename": "README.md"}]
        criteria = {"points": 30, "changes": []}

        # Act
        result = grader._check_required_changes(mock_pr, changed_files, criteria)

        # Assert
        assert isinstance(result, dict)
        assert result["points_earned"] == 30  # Full points, no requirements
        assert result["points_possible"] == 30
        assert "No required changes specified" in result["comment"]
        assert result["passed"] is True

    @patch.object(GitHubGrader, '_check_prohibited_patterns')
    @patch.object(GitHubGrader, '_check_required_changes')
    @patch.object(GitHubGrader, '_check_required_files')
    @patch.object(GitHubGrader, '_get_pr_files')
    def test_grade_submission_custom_criteria(self, mock_get_pr_files, mock_check_files,
                                              mock_check_changes, mock_check_patterns):
        """Test grading using custom criteria."""
        # Setup
        mock_client = MagicMock()
        grader = GitHubGrader(mock_client)

        # Mock PR and files
        mock_pr = MagicMock()
        mock_pr.number = 42
        mock_pr.base_repo = "test/repo"
        mock_pr.author = MagicMock(username="testuser")
        mock_pr.merged = False

        mock_files = [{"filename": "README.md"}]
        mock_get_pr_files.return_value = IntegrationResult(
            success=True, content=mock_files, message="Found files"
        )

        # Mock check results
        mock_check_files.return_value = {
            "points_earned": 45,
            "points_possible": 50,
            "passed": True,
            "comment": "Files check passed",
        }
        mock_check_changes.return_value = {
            "points_earned": 25,
            "points_possible": 30,
            "passed": True,
            "comment": "Changes check passed",
        }
        mock_check_patterns.return_value = {
            "points_earned": 15,
            "points_possible": 20,
            "passed": True,
            "comment": "Patterns check passed",
        }

        # Custom criteria
        criteria = {
            "passing_threshold": 0.8,
            "required_files": {"points": 50, "files": ["README.md"]},
            "required_changes": {"points": 30, "changes": [{"file": "README.md"}]},
            "prohibited_patterns": {"points": 20, "patterns": [{"pattern": "bad"}]},
        }

        # Act
        with patch("quackcore.teaching.github.grading.GamificationService"):
            result = grader.grade_submission(mock_pr, criteria)

        # Assert
        assert result.success is True

        # Verify correct criteria was passed to each check
        mock_check_files.assert_called_once_with(mock_files, criteria["required_files"])
        mock_check_changes.assert_called_once_with(mock_pr, mock_files,
                                                   criteria["required_changes"])
        mock_check_patterns.assert_called_once_with(mock_pr, mock_files,
                                                    criteria["prohibited_patterns"])

        # Verify score calculation
        grade_result = result.content
        assert grade_result.score == 0.85  # (45+25+15)/(50+30+20)
        assert grade_result.passed is True  # 0.85 > 0.8 threshold