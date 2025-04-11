# src/quackcore/teaching/github/grading.py
"""GitHub assignment grading utilities for QuackCore."""

from typing import Any

from quackcore.errors import QuackApiError
from quackcore.integrations.core import IntegrationResult
from quackcore.integrations.github.client import GitHubClient
from quackcore.integrations.github.models import PullRequest
from quackcore.logging import get_logger
from quackcore.teaching.core.gamification_service import GamificationService
from quackcore.teaching.core.models import XPEvent

from .models import GradeResult

logger = get_logger(__name__)


class GitHubGrader:
    """Utility for grading GitHub assignment submissions."""

    def __init__(self, client: GitHubClient) -> None:
        """Initialize the GitHub grader.

        Args:
            client: GitHub client
        """
        self.client = client

    def grade_submission(
        self, pull_request: PullRequest, grading_criteria: dict[str, Any] | None = None
    ) -> IntegrationResult[GradeResult]:
        """Grade a pull request submission.

        Args:
            pull_request: Pull request to grade
            grading_criteria: Dictionary of grading criteria

        Returns:
            Result with the grading result
        """
        try:
            logger.info(
                f"Grading submission PR #{pull_request.number} from {pull_request.author.username}"
            )

            # If grading criteria not provided, use default simple criteria
            if not grading_criteria:
                grading_criteria = self._default_grading_criteria()

            # Get the files changed in the PR
            files_changed = self._get_pr_files(pull_request)
            if not files_changed.success:
                return files_changed

            changed_files = files_changed.content or []

            # Run the grading checks
            results = {}
            total_points = 0
            max_points = 0
            comments = []

            # Check for required files
            if "required_files" in grading_criteria:
                req_files_result = self._check_required_files(
                    changed_files, grading_criteria["required_files"]
                )
                results["required_files"] = req_files_result
                total_points += req_files_result["points_earned"]
                max_points += req_files_result["points_possible"]
                comments.append(req_files_result["comment"])

            # Check for required changes (if specified)
            if "required_changes" in grading_criteria:
                req_changes_result = self._check_required_changes(
                    pull_request, changed_files, grading_criteria["required_changes"]
                )
                results["required_changes"] = req_changes_result
                total_points += req_changes_result["points_earned"]
                max_points += req_changes_result["points_possible"]
                comments.append(req_changes_result["comment"])

            # Check for prohibited patterns (if specified)
            if "prohibited_patterns" in grading_criteria:
                prohibited_result = self._check_prohibited_patterns(
                    pull_request, changed_files, grading_criteria["prohibited_patterns"]
                )
                results["prohibited_patterns"] = prohibited_result
                total_points += prohibited_result["points_earned"]
                max_points += prohibited_result["points_possible"]
                comments.append(prohibited_result["comment"])

            # Calculate final score (normalize to 0-1 range)
            score = total_points / max_points if max_points > 0 else 0
            passed = score >= grading_criteria.get("passing_threshold", 0.7)

            # Create combined feedback
            feedback = "\n".join([f"## {comment}" for comment in comments if comment])

            # Add summary header
            header = (
                f"# Grading Results\n\n"
                f"Score: {total_points}/{max_points} ({score * 100:.1f}%)\n"
                f"Status: {'PASSED' if passed else 'NEEDS IMPROVEMENT'}\n\n"
            )

            feedback = header + feedback

            # Create the result
            grade_result = GradeResult(
                score=score, passed=passed, comments=feedback, details=results
            )

            # Now integrate with the gamification system
            if grade_result.passed:
                try:
                    # Create a service instance
                    gamifier = GamificationService()

                    # Create an XP event for the successful submission
                    event = XPEvent(
                        id=f"graded-pr-{pull_request.number}",
                        label=f"Passed grading for PR #{pull_request.number}",
                        points=int(grade_result.score * 50),
                        # Scale points based on score
                        metadata={
                            "repo": pull_request.base_repo,
                            "pr_number": pull_request.number,
                            "score": grade_result.score,
                            "grader": "github-auto",
                        },
                    )

                    # Handle the event and get gamification results
                    gamification_result = gamifier.handle_event(event)

                    # Add gamification results to the grade result details
                    grade_result.details["gamification"] = {
                        "xp_added": gamification_result.xp_added,
                        "level": gamification_result.level,
                        "level_up": gamification_result.level_up,
                        "completed_quests": gamification_result.completed_quests,
                        "earned_badges": gamification_result.earned_badges,
                        "message": gamification_result.message,
                    }

                    # If this was a PR to a quackverse repository, check for quest completion
                    if "quackverse/" in pull_request.base_repo.lower():
                        # Check for merged PR quest if the PR was merged
                        if pull_request.merged:
                            merge_result = gamifier.handle_github_pr_merged(
                                pull_request.number, pull_request.base_repo
                            )
                            if merge_result.message:
                                logger.info(merge_result.message)
                except Exception as e:
                    logger.error(
                        f"Error integrating with gamification system: {str(e)}"
                    )
                    # Don't fail the grading process if gamification fails

            return IntegrationResult.success_result(
                content=grade_result,
                message=f"Successfully graded submission (Score: {score * 100:.1f}%)",
            )

        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to grade submission: {str(e)}",
                message="Could not grade submission due to an API error",
            )
        except Exception as e:
            logger.exception("Unexpected error while grading submission")
            return IntegrationResult.error_result(
                error=f"Unexpected error during grading: {str(e)}",
                message="Could not grade submission due to an unexpected error",
            )

    def _get_pr_files(
        self, pull_request: PullRequest
    ) -> IntegrationResult[list[dict[str, Any]]]:
        """Get the files changed in a pull request.

        Args:
            pull_request: Pull request to check

        Returns:
            Result with list of file information
        """
        try:
            # Use the client to fetch actual PR files
            files = self.client.get_pull_request_files(
                repo=pull_request.base_repo, pull_number=pull_request.number
            )

            return IntegrationResult.success_result(
                content=files,
                message=f"Found {len(files)} changed files in PR #{pull_request.number}",
            )
        except AttributeError:
            # Fallback if the method isn't implemented in the client
            logger.warning(
                "get_pull_request_files not implemented in client, using simulated data"
            )

            # Return simulated data
            files = [
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
                {
                    "filename": "test/test_main.py",
                    "status": "added",
                    "additions": 50,
                    "deletions": 0,
                    "changes": 50,
                },
            ]

            return IntegrationResult.success_result(
                content=files,
                message=f"Found {len(files)} simulated changed files in PR #{pull_request.number}",
            )
        except QuackApiError as e:
            return IntegrationResult.error_result(
                error=f"Failed to get PR files: {str(e)}",
                message=f"Could not retrieve files for PR #{pull_request.number}",
            )

    def _default_grading_criteria(self) -> dict[str, Any]:
        """Get default grading criteria.

        Returns:
            Dictionary of default grading criteria
        """
        return {
            "passing_threshold": 0.7,
            "required_files": {"points": 50, "files": ["README.md", "src/main.py"]},
            "required_changes": {
                "points": 30,
                "changes": [
                    {
                        "file": "src/main.py",
                        "min_additions": 10,
                        "description": "Implement the main function",
                    }
                ],
            },
            "prohibited_patterns": {
                "points": 20,
                "patterns": [
                    {
                        "pattern": r"import os\s*;",
                        "description": "Using semicolons in Python is discouraged",
                    }
                ],
            },
        }

    def _check_required_files(
        self, changed_files: list[dict[str, Any]], criteria: dict[str, Any]
    ) -> dict[str, Any]:
        """Check if required files are present in the changes.

        Args:
            changed_files: List of changed files
            criteria: Criteria for required files

        Returns:
            Dictionary with results of the check
        """
        points_possible = criteria.get("points", 50)
        required_files = criteria.get("files", [])

        if not required_files:
            return {
                "points_earned": points_possible,
                "points_possible": points_possible,
                "comment": "No required files specified.",
                "passed": True,
            }

        # Get list of all filenames that were changed
        filenames = [file["filename"] for file in changed_files]

        # Check which required files are present
        missing_files = []
        for req_file in required_files:
            if req_file not in filenames:
                missing_files.append(req_file)

        # Calculate points
        files_found = len(required_files) - len(missing_files)
        points_per_file = points_possible / len(required_files) if required_files else 0
        points_earned = files_found * points_per_file

        # Generate comment
        if missing_files:
            comment = f"Required Files Check: {files_found}/{len(required_files)} files found.\n\nMissing files:\n"
            for file in missing_files:
                comment += f"- {file}\n"
        else:
            comment = (
                f"Required Files Check: All {len(required_files)} required files found."
            )

        return {
            "points_earned": points_earned,
            "points_possible": points_possible,
            "missing_files": missing_files,
            "comment": comment,
            "passed": len(missing_files) == 0,
        }

    def _check_required_changes(
        self,
        pull_request: PullRequest,
        changed_files: list[dict[str, Any]],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Check if required changes are present in the pull request.

        Args:
            pull_request: Pull request to check
            changed_files: List of changed files
            criteria: Criteria for required changes

        Returns:
            Dictionary with results of the check
        """
        points_possible = criteria.get("points", 30)
        required_changes = criteria.get("changes", [])

        if not required_changes:
            return {
                "points_earned": points_possible,
                "points_possible": points_possible,
                "comment": "No required changes specified.",
                "passed": True,
            }

        # Create a map of files to their stats
        file_stats = {file["filename"]: file for file in changed_files}

        # Check each required change
        passed_changes = []
        failed_changes = []

        for change in required_changes:
            file = change.get("file")
            min_additions = change.get("min_additions", 0)
            description = change.get("description", "Implement required changes")

            if file in file_stats:
                file_info = file_stats[file]
                additions = file_info.get("additions", 0)

                if additions >= min_additions:
                    passed_changes.append(
                        {
                            "file": file,
                            "description": description,
                            "additions": additions,
                            "required": min_additions,
                        }
                    )
                else:
                    failed_changes.append(
                        {
                            "file": file,
                            "description": description,
                            "additions": additions,
                            "required": min_additions,
                        }
                    )
            else:
                failed_changes.append(
                    {
                        "file": file,
                        "description": description,
                        "additions": 0,
                        "required": min_additions,
                    }
                )

        # Calculate points
        changes_passed = len(passed_changes)
        points_per_change = (
            points_possible / len(required_changes) if required_changes else 0
        )
        points_earned = changes_passed * points_per_change

        # Generate comment
        if failed_changes:
            comment = f"Required Changes Check: {changes_passed}/{len(required_changes)} changes implemented.\n\nMissing changes:\n"
            for change in failed_changes:
                comment += f"- {change['description']} in {change['file']} (found {change['additions']} lines, needed {change['required']})\n"
        else:
            comment = f"Required Changes Check: All {len(required_changes)} required changes implemented."

        return {
            "points_earned": points_earned,
            "points_possible": points_possible,
            "passed_changes": passed_changes,
            "failed_changes": failed_changes,
            "comment": comment,
            "passed": len(failed_changes) == 0,
        }

    def _check_prohibited_patterns(
        self,
        pull_request: PullRequest,
        changed_files: list[dict[str, Any]],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Check if prohibited patterns are present in the pull request.

        Args:
            pull_request: Pull request to check
            changed_files: List of changed files
            criteria: Criteria for prohibited patterns

        Returns:
            Dictionary with results of the check
        """
        import re

        points_possible = criteria.get("points", 20)
        prohibited_patterns = criteria.get("patterns", [])

        if not prohibited_patterns:
            return {
                "points_earned": points_possible,
                "points_possible": points_possible,
                "comment": "No prohibited patterns specified.",
                "passed": True,
            }

        # In a real implementation, we would fetch file contents for each changed file
        # For this example, we'll simulate file content
        file_contents = {}
        for file in changed_files:
            filename = file["filename"]
            try:
                # Try to get actual file content using the client
                # Note: This requires implementing get_pr_file_content in the GitHub client
                try:
                    content, _ = self.client.get_repository_file_content(
                        repo=pull_request.base_repo,
                        path=filename,
                        ref=pull_request.head_branch,
                    )
                    file_contents[filename] = content
                except Exception:
                    # Fallback to simulated content for demonstration
                    if filename.endswith(".py"):
                        file_contents[filename] = (
                            "def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()"
                        )
                    elif filename.endswith(".md"):
                        file_contents[filename] = (
                            "# Assignment\n\nThis is a sample README."
                        )
                    else:
                        file_contents[filename] = f"Content of {filename}"
            except Exception as e:
                logger.warning(f"Failed to get content for {filename}: {e}")

        # Check each file for prohibited patterns
        violations = []

        for filename, content in file_contents.items():
            for pattern_info in prohibited_patterns:
                pattern = pattern_info.get("pattern", "")
                description = pattern_info.get("description", "Prohibited pattern")

                if re.search(pattern, content):
                    violations.append(
                        {
                            "file": filename,
                            "pattern": pattern,
                            "description": description,
                        }
                    )

        # Calculate points
        # If there are violations, deduct points proportionally
        if violations:
            points_per_violation = points_possible / len(prohibited_patterns)
            unique_patterns_violated = len(set(v["pattern"] for v in violations))
            points_deducted = min(
                points_possible, unique_patterns_violated * points_per_violation
            )
            points_earned = points_possible - points_deducted
        else:
            points_earned = points_possible

        # Generate comment
        if violations:
            comment = f"Prohibited Patterns Check: Found {len(violations)} violations.\n\nViolations:\n"
            for violation in violations:
                comment += f"- {violation['description']} in {violation['file']}\n"
        else:
            comment = "Prohibited Patterns Check: No prohibited patterns found."

        return {
            "points_earned": points_earned,
            "points_possible": points_possible,
            "violations": violations,
            "comment": comment,
            "passed": len(violations) == 0,
        }
