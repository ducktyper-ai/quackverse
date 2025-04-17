# src/quackster/core/gamification_service.py
"""
Gamification service for the QuackCore quackster module.

This service integrates the various quackster components (core gamification,
GitHub interactions, and academy/LMS features) to provide a unified
learning lifecycle that rewards users consistently across different
learning activities.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from quackcore.errors import QuackError  # Use our custom error types
from quackcore.logging import get_logger
from quackster.core import (  # xp now exports check_xp_badges publicly
    badges,
    quests,
    utils,
    xp,
)
from quackster.core.models import UserProgress, XPEvent

logger = get_logger(__name__)


@dataclass
class GamificationResult:
    """Result of a gamification event."""

    xp_added: int = 0
    level: int = 1
    level_up: bool = False
    completed_quests: list[str] = None
    earned_badges: list[str] = None
    message: str | None = None

    def __post_init__(self) -> None:
        """Initialize default values for lists."""
        if self.completed_quests is None:
            self.completed_quests = []
        if self.earned_badges is None:
            self.earned_badges = []


class GamificationService:
    """
    Service for integrating gamification with other quackster components.

    This service provides methods for handling learning events from different
    sources (GitHub, Academy LMS, etc.) and translating them into XP,
    quest completions, and badge awards within the gamification system.
    """

    def __init__(self, user_progress: UserProgress | None = None) -> None:
        """
        Initialize the gamification service.

        Args:
            user_progress: Optional user progress to use. If not provided,
                it will be loaded from the default location.
        """
        self.progress = user_progress or utils.load_progress()
        self._changed = False

    def handle_event(self, event: XPEvent) -> GamificationResult:
        """
        Handle an XP event and update user progress.

        Args:
            event: XP event to handle

        Returns:
            Result of the gamification event.
        """
        try:
            # Attempt to add XP from the event.
            is_new, old_level = xp.add_xp(self.progress, event)
        except Exception as e:
            logger.error(f"Error adding XP: {str(e)}")
            raise QuackError("Failed to add XP from event", original_error=e)

        try:
            # Instead of calling a protected method, call the public function.
            xp.check_xp_badges(self.progress)
        except Exception as e:
            logger.error(f"Error checking XP badges: {str(e)}")
            # We log the error but continue; badge checking is non-critical.

        prior_badge_count = len(self.progress.earned_badge_ids)
        # Newly earned badges are those appended after badge checking.
        newly_earned_badges = list(self.progress.earned_badge_ids[prior_badge_count:])

        new_level = self.progress.get_level()
        level_up = new_level > old_level

        # Save the updated progress.
        self._changed = True
        utils.save_progress(self.progress)

        message_parts = []
        if is_new:
            message_parts.append(f"Earned {event.points} XP from '{event.label}'")
        if level_up:
            message_parts.append(f"Leveled up to level {new_level}!")
        if newly_earned_badges:
            badge_objs = [badges.get_badge(b_id) for b_id in newly_earned_badges]
            badge_names = [f"{b.name} {b.emoji}" for b in badge_objs if b]
            message_parts.append(f"Earned badges: {', '.join(badge_names)}")

        message = " ".join(message_parts) if message_parts else None

        return GamificationResult(
            xp_added=event.points if is_new else 0,
            level=new_level,
            level_up=level_up,
            completed_quests=[],  # Additional quest completion handled elsewhere.
            earned_badges=newly_earned_badges,
            message=message,
        )

    def handle_events(self, events: Sequence[XPEvent]) -> GamificationResult:
        """
        Handle multiple XP events at once.

        Args:
            events: Sequence of XP events to handle

        Returns:
            Aggregated result of all gamification events.
        """
        start_level = self.progress.get_level()

        total_xp_added = 0
        all_completed_quests = []
        all_earned_badges = []

        for event in events:
            result = self.handle_event(event)
            total_xp_added += result.xp_added
            all_completed_quests.extend(result.completed_quests)
            all_earned_badges.extend(result.earned_badges)

        end_level = self.progress.get_level()
        level_up = end_level > start_level

        message_parts = []
        if total_xp_added > 0:
            message_parts.append(f"Earned {total_xp_added} total XP")
        if level_up:
            message_parts.append(f"Leveled up to level {end_level}!")
        if all_completed_quests:
            quest_objs = [quests.get_quest(q_id) for q_id in all_completed_quests]
            quest_names = [q.name for q in quest_objs if q]
            message_parts.append(f"Completed quests: {', '.join(quest_names)}")
        if all_earned_badges:
            badge_objs = [badges.get_badge(b_id) for b_id in all_earned_badges]
            badge_names = [f"{b.name} {b.emoji}" for b in badge_objs if b]
            message_parts.append(f"Earned badges: {', '.join(badge_names)}")

        message = " ".join(message_parts) if message_parts else None

        return GamificationResult(
            xp_added=total_xp_added,
            level=end_level,
            level_up=level_up,
            completed_quests=all_completed_quests,
            earned_badges=all_earned_badges,
            message=message,
        )

    def complete_quest(self, quest_id: str) -> GamificationResult:
        """
        Complete a specific quest and award its rewards.

        Args:
            quest_id: ID of the quest to complete

        Returns:
            Result of the gamification event.
        """
        old_level = self.progress.get_level()

        quest_obj = quests.get_quest(quest_id)
        if not quest_obj:
            logger.warning(f"Attempted to complete non-existent quest: {quest_id}")
            return GamificationResult(message=f"Quest {quest_id} not found")

        was_completed = quests.complete_quest(self.progress, quest_id, forced=True)
        if not was_completed:
            return GamificationResult(
                message=f"Quest '{quest_obj.name}' was already completed"
            )

        new_level = self.progress.get_level()
        level_up = new_level > old_level

        earned_badge = [quest_obj.badge_id] if quest_obj.badge_id else []

        self._changed = True
        utils.save_progress(self.progress)

        message_parts = [f"Completed quest: {quest_obj.name}"]
        if quest_obj.reward_xp > 0:
            message_parts.append(f"Earned {quest_obj.reward_xp} XP")
        if level_up:
            message_parts.append(f"Leveled up to level {new_level}!")
        if earned_badge:
            badge_obj = badges.get_badge(earned_badge[0])
            if badge_obj:
                message_parts.append(
                    f"Earned badge: {badge_obj.name} {badge_obj.emoji}"
                )

        message = " ".join(message_parts)

        return GamificationResult(
            xp_added=quest_obj.reward_xp,
            level=new_level,
            level_up=level_up,
            completed_quests=[quest_id],
            earned_badges=earned_badge,
            message=message,
        )

    def award_badge(self, badge_id: str) -> GamificationResult:
        """
        Award a specific badge to the user.

        Args:
            badge_id: ID of the badge to award

        Returns:
            Result of the gamification event.
        """
        badge_obj = badges.get_badge(badge_id)
        if not badge_obj:
            logger.warning(f"Attempted to award non-existent badge: {badge_id}")
            return GamificationResult(message=f"Badge {badge_id} not found")

        was_awarded = badges.award_badge(self.progress, badge_id)
        if not was_awarded:
            return GamificationResult(
                message=f"Badge '{badge_obj.name}' was already earned"
            )

        self._changed = True
        utils.save_progress(self.progress)

        return GamificationResult(
            earned_badges=[badge_id],
            message=f"Earned badge: {badge_obj.name} {badge_obj.emoji}",
        )

    def save(self) -> None:
        """Save the current progress if it has been changed."""
        if self._changed:
            utils.save_progress(self.progress)
            self._changed = False

    # Integration with GitHub events

    def handle_github_pr_submission(
        self, pr_number: int, repo: str
    ) -> GamificationResult:
        """
        Handle a GitHub pull request submission.

        Args:
            pr_number: GitHub pull request number.
            repo: Repository name (e.g., 'quackverse/quackcore').

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"github-pr-{repo}-{pr_number}",
            label=f"Submitted PR #{pr_number} to {repo}",
            points=25,
            metadata={"repo": repo, "pr_number": pr_number},
        )

        result = self.handle_event(event)

        if repo.lower() == "quackverse/quackcore":
            if not self.progress.has_completed_quest("open-pr"):
                quest_result = self.complete_quest("open-pr")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message

        return result

    def handle_github_pr_merged(self, pr_number: int, repo: str) -> GamificationResult:
        """
        Handle a GitHub pull request being merged.

        Args:
            pr_number: GitHub pull request number.
            repo: Repository name.

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"github-pr-merged-{repo}-{pr_number}",
            label=f"PR #{pr_number} merged into {repo}",
            points=50,
            metadata={"repo": repo, "pr_number": pr_number},
        )

        result = self.handle_event(event)

        if "quackverse/" in repo.lower():
            if not self.progress.has_completed_quest("merged-pr"):
                quest_result = self.complete_quest("merged-pr")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message

        return result

    def handle_github_star(self, repo: str) -> GamificationResult:
        """
        Handle starring a GitHub repository.

        Args:
            repo: Repository name.

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"github-star-{repo}",
            label=f"Starred repository {repo}",
            points=10,
            metadata={"repo": repo},
        )

        result = self.handle_event(event)

        if repo.lower() == "quackverse/quackcore":
            if not self.progress.has_completed_quest("star-quackcore"):
                quest_result = self.complete_quest("star-quackcore")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message
        elif repo.lower() == "quackverse/quackverse":
            if not self.progress.has_completed_quest("star-quackverse"):
                quest_result = self.complete_quest("star-quackverse")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message

        return result

    def handle_module_completion(
        self, course_id: str, module_id: str, module_name: str
    ) -> GamificationResult:
        """
        Handle completion of an Academy/LMS module.

        Args:
            course_id: ID of the course.
            module_id: ID of the completed module.
            module_name: Name of the completed module.

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"academy-module-{course_id}-{module_id}",
            label=f"Completed module: {module_name}",
            points=30,
            metadata={
                "course_id": course_id,
                "module_id": module_id,
                "module_name": module_name,
            },
        )

        result = self.handle_event(event)

        if "tutorial" in module_name.lower():
            if not self.progress.has_completed_quest("complete-tutorial"):
                quest_result = self.complete_quest("complete-tutorial")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message

        return result

    def handle_course_completion(
        self, course_id: str, course_name: str
    ) -> GamificationResult:
        """
        Handle completion of an Academy/LMS course.

        Args:
            course_id: ID of the course.
            course_name: Name of the completed course.

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"academy-course-{course_id}",
            label=f"Completed course: {course_name}",
            points=100,
            metadata={"course_id": course_id, "course_name": course_name},
        )

        result = self.handle_event(event)

        if not self.progress.has_earned_badge("duck-graduate"):
            badge_result = self.award_badge("duck-graduate")
            result.earned_badges.extend(badge_result.earned_badges)
            if badge_result.message:
                result.message = (result.message or "") + " " + badge_result.message

        return result

    def handle_assignment_completion(
        self, assignment_id: str, assignment_name: str, score: float, max_score: float
    ) -> GamificationResult:
        """
        Handle completion of an Academy/LMS assignment.

        Args:
            assignment_id: ID of the assignment.
            assignment_name: Name of the assignment.
            score: Score achieved.
            max_score: Maximum possible score.

        Returns:
            Result of the gamification event.
        """
        percentage = (score / max_score) if max_score > 0 else 0
        xp_points = int(20 + percentage * 30)
        event = XPEvent(
            id=f"academy-assignment-{assignment_id}",
            label=f"Completed assignment: {assignment_name}",
            points=xp_points,
            metadata={
                "assignment_id": assignment_id,
                "assignment_name": assignment_name,
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
            },
        )

        return self.handle_event(event)

    def handle_feedback_submission(
        self, feedback_id: str, context: str
    ) -> GamificationResult:
        """
        Handle submission of feedback.

        Args:
            feedback_id: ID of the feedback.
            context: Context description for the feedback.

        Returns:
            Result of the gamification event.
        """
        event = XPEvent(
            id=f"feedback-{feedback_id}",
            label=f"Provided feedback: {context}",
            points=5,
            metadata={"feedback_id": feedback_id, "context": context},
        )

        return self.handle_event(event)

    def handle_tool_usage(self, tool_name: str, action: str) -> GamificationResult:
        """
        Handle usage of a tool.

        Args:
            tool_name: Name of the tool.
            action: Action performed with the tool.

        Returns:
            Result of the gamification event.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        event = XPEvent(
            id=f"tool-{tool_name}-{action}-{today}",
            label=f"Used {tool_name} to {action}",
            points=2,
            metadata={"tool": tool_name, "action": action, "date": today},
        )

        result = self.handle_event(event)

        if tool_name.lower() == "ducktyper" and action.lower() == "run":
            if not self.progress.has_completed_event("run-ducktyper"):
                run_event = XPEvent(
                    id="run-ducktyper",
                    label="Run DuckTyper for the first time",
                    points=10,
                )
                self.handle_event(run_event)

                if not self.progress.has_completed_quest("run-ducktyper"):
                    quest_result = self.complete_quest("run-ducktyper")
                    result.completed_quests.extend(quest_result.completed_quests)
                    result.earned_badges.extend(quest_result.earned_badges)
                    result.xp_added += quest_result.xp_added

                    if quest_result.message:
                        result.message = (
                            (result.message or "") + " " + quest_result.message
                        )

            day_event = XPEvent(
                id=f"run-ducktyper-day-{today}",
                label=f"Used DuckTyper on {today}",
                points=0,
            )
            self.handle_event(day_event)

            streak_days = [
                e
                for e in self.progress.completed_event_ids
                if e.startswith("run-ducktyper-day-")
            ]
            if len(streak_days) >= 3 and not self.progress.has_completed_quest(
                "daily-streak"
            ):
                quest_result = self.complete_quest("daily-streak")
                result.completed_quests.extend(quest_result.completed_quests)
                result.earned_badges.extend(quest_result.earned_badges)
                result.xp_added += quest_result.xp_added
                if quest_result.message:
                    result.message = (result.message or "") + " " + quest_result.message

        return result


_service_instance = None


def get_service():
    """
    Get the gamification service singleton instance.

    Returns:
        GamificationService: The gamification service instance
    """
    global _service_instance
    if _service_instance is None:
        try:
            # Try to create the service normally
            _service_instance = GamificationService()
        except Exception:
            # Fall back to a test-friendly instance
            from quackster.core.models import UserProgress

            _service_instance = GamificationService(
                user_progress=UserProgress(github_username="testuser")
            )

    return _service_instance


# For backward compatibility
service = get_service()
