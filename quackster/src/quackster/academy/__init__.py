# quackster/src/quackster/academy/__init__.py
"""
QuackCore Teaching LMS Module.

This module provides traditional LMS functionality for quackster and educational
workflows in the QuackVerse ecosystem. It integrates with GitHub for assignment
management, student collaboration, and grading workflows.

Note: This is the traditional LMS-style implementation, while the main quackster
module now offers a gamified, CLI-first approach.
"""

from quackster.academy.assignment import Assignment, AssignmentStatus
from quackster.academy.context import TeachingContext
from quackster.academy.course import Course, CourseModule, ModuleItem
from quackster.academy.feedback import Annotation, Feedback, FeedbackItem
from quackster.academy.grading import GradeResult, GradingCriteria
from quackster.academy.results import (
    AssignmentResult,
    FeedbackResult,
    TeachingResult,
)

# Export the service instance
from quackster.academy.service import service
from quackster.academy.student import (
    Student,
    StudentSubmission,
    SubmissionStatus,
)

__all__ = [
    # Core classes
    "Assignment",
    "AssignmentStatus",
    "TeachingContext",
    "Student",
    "StudentSubmission",
    "SubmissionStatus",
    "Course",
    "CourseModule",
    "ModuleItem",
    "Feedback",
    "FeedbackItem",
    "Annotation",
    "GradingCriteria",
    "GradeResult",
    # Result classes
    "TeachingResult",
    "AssignmentResult",
    "FeedbackResult",
    # Service
    "service",
]
