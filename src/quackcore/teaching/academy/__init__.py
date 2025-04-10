# src/quackcore/teaching/academy/__init__.py
"""
QuackCore Teaching LMS Module.

This module provides traditional LMS functionality for teaching and educational
workflows in the QuackVerse ecosystem. It integrates with GitHub for assignment
management, student collaboration, and grading workflows.

Note: This is the traditional LMS-style implementation, while the main teaching
module now offers a gamified, CLI-first approach.
"""

from quackcore.teaching.academy.assignment import Assignment, AssignmentStatus
from quackcore.teaching.academy.context import TeachingContext
from quackcore.teaching.academy.course import Course, CourseModule, ModuleItem
from quackcore.teaching.academy.feedback import Annotation, Feedback, FeedbackItem
from quackcore.teaching.academy.grading import GradeResult, GradingCriteria
from quackcore.teaching.academy.results import (
    AssignmentResult,
    FeedbackResult,
    TeachingResult,
)

# Export the service instance
from quackcore.teaching.academy.service import service
from quackcore.teaching.academy.student import (
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
