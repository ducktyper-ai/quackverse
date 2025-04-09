# QuackCore Teaching Module Documentation

## Overview

The `quackcore.teaching` module provides comprehensive functionality for teaching and educational workflows within the QuackVerse ecosystem. It's designed to simplify the management of courses, assignments, students, and grading workflows, with a particular focus on GitHub integration for code-based assignments.

This documentation will guide you through the core concepts, components, and usage patterns of the `quackcore.teaching` module to help you incorporate educational workflows in your QuackCore applications.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Components](#core-components)
3. [Teaching Context](#teaching-context)
4. [Assignment Management](#assignment-management)
5. [Student Management](#student-management)
6. [Course Structure](#course-structure)
7. [Feedback and Grading](#feedback-and-grading)
8. [GitHub Integration](#github-integration)
9. [Plugin System](#plugin-system)
10. [Common Workflows](#common-workflows)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [API Reference](#api-reference)

## Getting Started

### Installation

The `quackcore.teaching` module is included with the QuackCore package. If you've installed QuackCore, you already have access to the teaching module.

```bash
pip install quackcore
```

### Basic Usage

The quickest way to start using the teaching module is through the global service instance:

```python
from quackcore.teaching import service

# Initialize the teaching service
result = service.initialize()
if result.success:
    print("Teaching service initialized successfully!")
else:
    print(f"Error: {result.error}")

# Create a new teaching context
result = service.create_context(
    course_name="Introduction to Programming",
    github_org="my-teaching-org"
)
if result.success:
    print("Teaching context created successfully!")
```

### Configuration

You can configure the teaching module through a YAML file:

```yaml
# teaching_config.yaml
course_name: "Introduction to Programming"
course_id: "cs101"
github:
  organization: "my-teaching-org"
  template_repo_prefix: "template-"
  assignment_branch_prefix: "assignment-"
  auto_create_repos: true
assignments_dir: "assignments"
feedback_dir: "feedback"
students_file: "students.yaml"
```

Then load this configuration when initializing the service:

```python
from quackcore.teaching import service

result = service.initialize("path/to/teaching_config.yaml")
if result.success:
    print("Teaching service initialized with configuration!")
```

## Core Components

The teaching module consists of several core components that work together to provide educational functionality:

### Service

The `TeachingService` is the main entry point for the teaching module, providing high-level operations for teaching workflows.

```python
from quackcore.teaching import service

# Create an assignment from a template
result = service.create_assignment_from_template(
    assignment_name="Project 1",
    template_repo="template-project1",
    students=["student1", "student2", "student3"]
)
```

### Context

The `TeachingContext` manages the teaching environment, including configuration, directories, and dependencies.

```python
from quackcore.teaching import TeachingContext

# Create a context manually
context = TeachingContext.create_default(
    course_name="Python Programming",
    github_org="python-class",
    base_dir="./course-data"
)

# Ensure directories exist
context.ensure_directories()
```

### Models

The module includes Pydantic models for various educational entities:

- `Assignment`: Represents an educational assignment
- `Student`: Represents a student with their information and submissions
- `Course`: Represents a course with modules and content
- `Feedback`: Represents structured feedback for a submission
- `GradingCriteria`: Defines criteria for evaluating student work

```python
from quackcore.teaching import Assignment, AssignmentType

# Create an assignment
assignment = Assignment.create(
    name="Midterm Project",
    description="Build a web application using Flask",
    assignment_type=AssignmentType.PROJECT,
    due_date="2025-05-15"
)
```

### Results

All operations return standardized result objects that follow the consistent pattern used throughout QuackCore:

```python
result = service.find_student_submissions("Project 1", student="student1")
if result.success:
    submission = result.content
    print(f"Found submission: {submission}")
else:
    print(f"Error: {result.error}")
```

## Teaching Context

The `TeachingContext` is responsible for managing the teaching environment, including configuration, directories, and dependencies.

### Creating a Context

You can create a teaching context in several ways:

```python
from quackcore.teaching import TeachingContext, TeachingConfig, GitHubConfig

# From a configuration file
context = TeachingContext.from_config("teaching_config.yaml")

# With default settings
context = TeachingContext.create_default(
    course_name="Data Structures",
    github_org="ds-class"
)

# With custom configuration
config = TeachingConfig(
    course_name="Algorithms",
    course_id="cs202",
    github=GitHubConfig(
        organization="algo-class",
        auto_create_repos=True
    )
)
context = TeachingContext(config)
```

### Directory Structure

The teaching context manages a standard directory structure for teaching resources:

```
base_dir/
├── assignments/        # Assignment data
├── feedback/           # Feedback for submissions
├── grading/            # Grading criteria and results
├── submissions/        # Student submissions
├── students.yaml       # Student roster
└── course.yaml         # Course configuration
```

You can access these directories through the context:

```python
# Get directory paths
assignments_dir = context.assignments_dir
feedback_dir = context.feedback_dir
grading_dir = context.grading_dir
submissions_dir = context.submissions_dir

# Ensure directories exist
context.ensure_directories()
```

### GitHub Integration

The teaching context provides access to the GitHub integration:

```python
# Get the GitHub integration
github = context.github

# Check if a repository exists
repo_result = github.get_repo("my-org/repo-name")
```

## Assignment Management

The teaching module provides comprehensive functionality for managing assignments, including:

- Creating assignments
- Publishing assignments to GitHub
- Tracking assignment status
- Finding student submissions

### Creating Assignments

```python
from quackcore.teaching import Assignment, AssignmentType, AssignmentStatus

# Create a new assignment
assignment = Assignment.create(
    name="Final Project",
    description="Implement a full-stack web application",
    assignment_type=AssignmentType.PROJECT,
    due_date="2025-06-15",
    points=100.0
)

# Publish the assignment
assignment.publish()

# Check if the assignment is past due
if assignment.is_past_due():
    print("Assignment is past due")
else:
    print("Assignment is still active")
```

### Managing Multiple Assignments

The `AssignmentManager` class helps you manage multiple assignments:

```python
from quackcore.teaching import AssignmentManager

# Create a manager
manager = AssignmentManager()

# Add assignments
manager.add_assignment(assignment1)
manager.add_assignment(assignment2)

# Get assignments
active_assignments = manager.get_active_assignments()
past_due = manager.get_past_due_assignments()

# Save to file
manager.save_to_file("assignments.yaml")

# Load from file
manager = AssignmentManager.load_from_file("assignments.yaml")
```

### Creating Assignment Repositories

Using the teaching service, you can create GitHub repositories for assignments:

```python
from quackcore.teaching import service

# Create repositories from a template
result = service.create_assignment_from_template(
    assignment_name="Project 2",
    template_repo="template-project2",
    description="Build a React application",
    due_date="2025-05-30",
    students=["student1", "student2", "student3"]
)

if result.success:
    repositories = result.repositories
    print(f"Created {len(repositories)} repositories")
else:
    print(f"Error: {result.error}")
```

### Finding Submissions

```python
# Find submissions for a specific student
result = service.find_student_submissions(
    assignment_name="Project 1",
    student="student1"
)

if result.success:
    submission = result.content
    print(f"Found submission repository: {submission.full_name}")
```

## Student Management

The teaching module provides functionality for managing students and their submissions.

### Creating Students

```python
from quackcore.teaching import Student

# Create a student
student = Student.create(
    github_username="student1",
    name="Jane Doe",
    email="jane@example.com",
    group="Section A"
)
```

### Managing Submissions

```python
from quackcore.teaching import StudentSubmission, SubmissionStatus

# Create a submission
submission = StudentSubmission.create(
    student_id=student.id,
    assignment_id=assignment.id
)

# Mark as submitted
submission.mark_submitted(
    pr_url="https://github.com/org/repo/pull/1",
    repo_url="https://github.com/org/repo"
)

# Mark as graded
submission.mark_graded(
    score=85.0,
    feedback_id="feedback-123"
)

# Add submission to student
student.add_submission(submission)

# Get a student's submission for an assignment
student_submission = student.get_submission(assignment.id)
```

### Student Roster

The `StudentRoster` class helps you manage multiple students:

```python
from quackcore.teaching import StudentRoster

# Create a roster
roster = StudentRoster()

# Add students
roster.add_student(student1)
roster.add_student(student2)

# Get students
student = roster.get_student_by_github("student1")
active_students = roster.get_active_students()
section_a = roster.get_students_by_group("Section A")

# Save to file
roster.save_to_file("students.yaml")

# Load from file
roster = StudentRoster.load_from_file("students.yaml")
```

## Course Structure

The teaching module allows you to create and manage course structure, including modules and content items.

### Creating Courses

```python
from quackcore.teaching import Course

# Create a course
course = Course.create(
    name="Advanced Python Programming",
    code="CS301",
    description="An in-depth exploration of Python programming concepts",
    start_date="2025-01-15",
    end_date="2025-05-30",
    instructors=["John Doe", "Jane Smith"]
)
```

### Creating Modules

```python
from quackcore.teaching import CourseModule

# Create a module
module = CourseModule.create(
    title="Module 1: Introduction to Advanced Concepts",
    description="This module covers advanced Python concepts",
    position=0,
    published=True
)

# Add to course
course.add_module(module)
```

### Adding Content Items

```python
from quackcore.teaching import ModuleItem, ItemType

# Create a lecture item
lecture = ModuleItem.create(
    title="Variables and Memory Management",
    type=ItemType.LECTURE,
    description="Understanding how Python manages memory",
    url="https://example.com/lectures/memory-management"
)

# Create an assignment item
assignment_item = ModuleItem.create(
    title="Memory Profiling Project",
    type=ItemType.ASSIGNMENT,
    description="Analyze and optimize memory usage in a Python application",
    assignment_id=assignment.id,
    due_date="2025-02-15",
    points=50.0
)

# Add to module
module.add_item(lecture)
module.add_item(assignment_item)
```

### Managing Courses

The `CourseManager` class helps you manage multiple courses:

```python
from quackcore.teaching import CourseManager

# Create a manager
manager = CourseManager()

# Add courses
manager.add_course(course1)
manager.add_course(course2)

# Get courses
course = manager.get_course(course_id)
active_courses = manager.get_active_courses()

# Save to file
manager.save_to_file("courses.yaml")

# Load from file
manager = CourseManager.load_from_file("courses.yaml")
```

## Feedback and Grading

The teaching module provides tools for giving structured feedback and grading student submissions.

### Creating Feedback

```python
from quackcore.teaching import Feedback, FeedbackItem, FeedbackItemType

# Create feedback
feedback = Feedback.create(
    submission_id=submission.id,
    student_id=student.id,
    assignment_id=assignment.id,
    reviewer="instructor1"
)

# Add feedback items
item = FeedbackItem.create(
    text="Your solution is well-structured and follows good practices.",
    type=FeedbackItemType.CODE_QUALITY,
    score=20.0
)
feedback.add_item(item)

# Calculate overall score
total_score = feedback.calculate_score()
```

### Code Annotations

```python
from quackcore.teaching import Annotation, AnnotationType

# Create an annotation
annotation = Annotation.create(
    file_path="app.py",
    line_start=25,
    text="This loop could be optimized using a list comprehension",
    type=AnnotationType.SUGGESTION,
    suggestion="return [process(item) for item in items]"
)

# Add to a feedback item
item.add_annotation(annotation)
```

### Grading Criteria

```python
from quackcore.teaching import GradingCriteria, GradingCriterion, FileCheckCriterion, PatternCheckCriterion

# Create criteria
criterion1 = GradingCriterion.create(
    name="Code Style",
    points=20.0,
    description="Follows PEP 8 style guidelines",
    category="style"
)

# Create a file check criterion
file_criterion = FileCheckCriterion.create(
    name="Required Files",
    points=10.0,
    files=["app.py", "tests.py", "README.md"],
    required=True
)

# Create a pattern check criterion
pattern_criterion = PatternCheckCriterion.create(
    name="No Print Debugging",
    points=5.0,
    patterns=[
        {
            "pattern": r"print\(['\"]DEBUG",
            "description": "Remove debug print statements"
        }
    ],
    file_patterns=["*.py"]
)

# Create grading criteria
criteria = GradingCriteria.create(
    name="Project 1 Grading",
    assignment_id=assignment.id,
    criteria=[criterion1, file_criterion, pattern_criterion],
    passing_threshold=0.7
)
```

### Grading Submissions

```python
from quackcore.teaching import Grader

# Create a grader
grader = Grader(criteria)

# Grade a submission
grade_result = grader.grade_submission(
    submission_id=submission.id,
    student_id=student.id,
    submission_dir="./submissions/student1/project1",
    grader="instructor1"
)

if grade_result.passed:
    print(f"Submission passed with score: {grade_result.score}/{grade_result.max_points}")
else:
    print(f"Submission failed with score: {grade_result.score}/{grade_result.max_points}")

# Format for feedback
feedback_text = grade_result.format_for_feedback()
```

### Managing Feedback and Grades

```python
from quackcore.teaching import FeedbackManager, GradeManager

# Feedback manager
feedback_mgr = FeedbackManager()
feedback_mgr.add_feedback(feedback)
feedback_mgr.save_to_file("feedback.yaml")

# Grade manager
grade_mgr = GradeManager()
grade_mgr.add_grade(grade_result)
grade_mgr.save_to_file("grades.yaml")

# Get a student's grades
student_grades = grade_mgr.get_student_grades(student.id)

# Get grades for an assignment
assignment_grades = grade_mgr.get_assignment_grades(assignment.id)
```

## GitHub Integration

The teaching module integrates with GitHub for managing assignments, submissions, and feedback.

### Prerequisites

Before using GitHub integration, you need to:

1. Create a GitHub organization for your course
2. Generate a GitHub Personal Access Token with appropriate permissions
3. Configure the GitHub integration in your teaching context

```yaml
# teaching_config.yaml
github:
  organization: "my-teaching-org"
  template_repo_prefix: "template-"
  assignment_branch_prefix: "assignment-"
  default_base_branch: "main"
  pr_title_template: "[SUBMISSION] {title}"
  auto_create_repos: true
  auto_star_repos: true
```

### Creating Assignment Repositories

```python
# Create repositories from a template repository
result = service.create_assignment_from_template(
    assignment_name="Project 1",
    template_repo="template-project1",
    students=["student1", "student2"]
)
```

### Finding Student Submissions

```python
# Find a student's submission
result = service.find_student_submissions(
    assignment_name="Project 1",
    student="student1"
)
```

### Ensuring Repository Exists

```python
# Ensure a repository exists
result = service.ensure_repo_exists(
    repo_name="project1-student1",
    private=True,
    description="Project 1 for Student 1"
)
```

## Plugin System

The teaching module provides a plugin interface for integration with the QuackCore plugin system.

### Using the Plugin

```python
from quackcore.plugins import PluginManager
from quackcore.teaching.plugin import create_plugin

# Create and register the plugin
plugin_manager = PluginManager()
teaching_plugin = create_plugin()
plugin_manager.register(teaching_plugin)

# Initialize the plugin
result = teaching_plugin.initialize({
    "config_path": "teaching_config.yaml"
})

# Use the plugin
result = teaching_plugin.create_assignment(
    assignment_name="Project 1",
    template_repo="template-project1",
    students=["student1", "student2"]
)
```

### Plugin Methods

The teaching plugin provides the following methods:

- `initialize(options)`: Initialize the plugin
- `create_context(course_name, github_org, base_dir)`: Create a teaching context
- `create_assignment(assignment_name, template_repo, ...)`: Create an assignment
- `find_student_submissions(assignment_name, student)`: Find submissions
- `get_context()`: Get the current teaching context
- `call(method, **kwargs)`: Call a plugin method dynamically

## Common Workflows

### Setting Up a New Course

```python
from quackcore.teaching import service, Course, CourseModule, ModuleItem, ItemType

# Initialize the teaching service
service.initialize("teaching_config.yaml")

# Create a new course
course = Course.create(
    name="Python for Data Science",
    code="DS101",
    description="Introduction to Python for data analysis and visualization",
    start_date="2025-02-01",
    end_date="2025-06-15"
)

# Create modules
module1 = CourseModule.create(
    title="Module 1: Python Basics",
    description="Introduction to Python syntax and data structures",
    position=0
)

module2 = CourseModule.create(
    title="Module 2: Data Analysis with Pandas",
    description="Using Pandas for data manipulation and analysis",
    position=1
)

# Add modules to course
course.add_module(module1)
course.add_module(module2)

# Create and add content items
module1.add_item(ModuleItem.create(
    title="Introduction to Python",
    type=ItemType.LECTURE,
    url="https://example.com/lectures/intro"
))

module1.add_item(ModuleItem.create(
    title="Python Basics Assignment",
    type=ItemType.ASSIGNMENT,
    assignment_id="python-basics"
))

# Save the course
manager = CourseManager()
manager.add_course(course)
manager.save_to_file("course.yaml")
```

### Creating and Distributing an Assignment

```python
from quackcore.teaching import service, Assignment, AssignmentType, StudentRoster

# Initialize the teaching service
service.initialize("teaching_config.yaml")

# Create an assignment
assignment = Assignment.create(
    name="Data Visualization Project",
    description="Create data visualizations using Matplotlib and Seaborn",
    assignment_type=AssignmentType.PROJECT,
    due_date="2025-04-15",
    points=100.0
)

# Save the assignment
manager = AssignmentManager()
manager.add_assignment(assignment)
manager.save_to_file("assignments.yaml")

# Load the student roster
roster = StudentRoster.load_from_file("students.yaml")
students = [student.github_username for student in roster.get_active_students()]

# Create repositories from a template
result = service.create_assignment_from_template(
    assignment_name=assignment.name,
    template_repo="template-data-viz",
    description=assignment.description,
    due_date="2025-04-15",
    students=students
)

if result.success:
    # Update assignment with repository information
    for repo in result.repositories:
        assignment.add_repository(repo.full_name)
    
    # Save updated assignment
    manager.save_to_file("assignments.yaml")
```

### Grading Submissions

```python
from quackcore.teaching import service, Grader, GradingCriteria, GradingCriterion, FileCheckCriterion

# Create grading criteria
criteria = GradingCriteria.create(
    name="Data Viz Project Grading",
    assignment_id=assignment.id,
    passing_threshold=0.7
)

# Add criteria
criteria.add_criterion(GradingCriterion.create(
    name="Visualization Quality",
    points=40.0,
    description="Quality and clarity of visualizations"
))

criteria.add_criterion(GradingCriterion.create(
    name="Code Quality",
    points=30.0,
    description="Code structure, readability, and documentation"
))

criteria.add_criterion(FileCheckCriterion.create(
    name="Required Files",
    points=10.0,
    files=["visualization.py", "data_processing.py", "README.md"],
    required=True
))

# Create a grader
grader = Grader(criteria)

# Grade a submission
grade_result = grader.grade_submission(
    submission_id="submission-123",
    student_id="student-456",
    submission_dir="./submissions/student1/data-viz-project"
)

# Save the grade
grade_mgr = GradeManager()
grade_mgr.add_grade(grade_result)
grade_mgr.save_to_file("grades.yaml")

# Create feedback based on the grade
feedback = Feedback.create(
    submission_id="submission-123",
    student_id="student-456",
    assignment_id=assignment.id,
    score=grade_result.score,
    summary="Your visualizations are excellent, but there's room for improvement in code structure."
)

# Save the feedback
feedback_mgr = FeedbackManager()
feedback_mgr.add_feedback(feedback)
feedback_mgr.save_to_file("feedback.yaml")
```

## Best Practices

### Directory Structure

Maintain a consistent directory structure for your teaching resources:

```
course/
├── teaching_config.yaml   # Teaching configuration
├── assignments/           # Assignment data
│   ├── assignment1.yaml   # Assignment 1 details
│   └── assignment2.yaml   # Assignment 2 details
├── feedback/              # Feedback data
│   ├── student1/          # Feedback for student1
│   └── student2/          # Feedback for student2
├── grading/               # Grading criteria and results
│   ├── criteria/          # Grading criteria
│   └── results/           # Grading results
├── submissions/           # Student submissions
│   ├── student1/          # Submissions from student1
│   └── student2/          # Submissions from student2
└── students.yaml          # Student roster
```

### Error Handling

Always check the success status of result objects:

```python
# Good - checks for success before using the content
result = service.find_student_submissions("Project 1", "student1")
if result.success:
    submission = result.content
    # Process submission
else:
    print(f"Error: {result.error}")
    # Handle the error
```

### Configuration Management

Store sensitive information like GitHub tokens in environment variables:

```python
# In your environment
export GITHUB_TOKEN="your_github_token_here"

# In your code
import os
os.environ["GITHUB_TOKEN"] = "your_github_token_here"  # Only if not set in environment
```

### Modular Design

Break down your teaching workflows into reusable components:

```python
def setup_assignment(name, template, students):
    """Set up an assignment for students."""
    # Create the assignment
    assignment = Assignment.create(name=name, ...)
    
    # Create repositories
    result = service.create_assignment_from_template(
        assignment_name=name,
        template_repo=template,
        students=students
    )
    
    return assignment, result

def process_submissions(assignment_name, grading_criteria):
    """Process submissions for an assignment."""
    # Find submissions
    # Grade submissions
    # Generate feedback
```

### Regular Backups

Regularly back up your teaching data:

```python
def backup_teaching_data(backup_dir):
    """Back up teaching data to a directory."""
    import shutil
    from datetime import datetime
    
    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/backup_{timestamp}"
    os.makedirs(backup_path, exist_ok=True)
    
    # Back up files
    shutil.copy("teaching_config.yaml", f"{backup_path}/teaching_config.yaml")
    shutil.copy("students.yaml", f"{backup_path}/students.yaml")
    shutil.copytree("assignments", f"{backup_path}/assignments")
    # ...
```

## Troubleshooting

### Common Issues and Solutions

#### GitHub Integration Not Working

**Issue**: GitHub operations fail with authentication errors.

**Solutions**:
1. Check if your GitHub token is set correctly
2. Verify that the token has the required permissions
3. Check if the GitHub organization exists and you have access

```python
# Check if GitHub integration is available
import os
print(f"GitHub token set: {'GITHUB_TOKEN' in os.environ}")

# Try a simple GitHub operation
result = service.context.github.get_repo(f"{org_name}/any-repo")
if not result.success:
    print(f"GitHub error: {result.error}")
```

#### Assignment Creation Fails

**Issue**: Creating assignment repositories fails.

**Solutions**:
1. Check if the template repository exists
2. Verify that you have permission to create repositories in the organization
3. Check if repositories for the students already exist

```python
# Check if template repository exists
template_result = service.context.github.get_repo(f"{org_name}/{template_repo}")
if not template_result.success:
    print(f"Template repository error: {template_result.error}")
```

#### Service Initialization Fails

**Issue**: Service initialization fails with configuration errors.

**Solutions**:
1. Check if the configuration file exists and has the correct format
2. Verify that the required directories exist and are accessible
3. Check for any missing dependencies

```python
# Check if configuration file exists
from pathlib import Path
config_path = Path("teaching_config.yaml")
print(f"Config file exists: {config_path.exists()}")

# Try loading the config manually
import yaml
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print("Config loaded successfully")
except Exception as e:
    print(f"Config error: {str(e)}")
```

#### File Operations Fail

**Issue**: Reading or writing files fails.

**Solutions**:
1. Check if the directories exist and have the correct permissions
2. Verify that the file paths are correct
3. Check for any file system issues

```python
# Check if directories exist
from pathlib import Path
dirs = ["assignments", "feedback", "grading", "submissions"]
for dir_name in dirs:
    path = Path(dir_name)
    print(f"{dir_name} exists: {path.exists()}, is directory: {path.is_dir() if path.exists() else False}")
```

## API Reference

### TeachingService

The main service for teaching operations.

```python
from quackcore.teaching import service
```

**Methods**:

- `initialize(config_path=None, base_dir=None) -> TeachingResult`: Initialize the teaching service
- `create_context(course_name, github_org, base_dir=None) -> TeachingResult`: Create a new teaching context
- `create_assignment_from_template(assignment_name, template_repo, description=None, due_date=None, students=None) -> AssignmentResult`: Create an assignment from a template
- `find_student_submissions(assignment_name, student=None) -> TeachingResult`: Find submissions for an assignment
- `ensure_repo_exists(repo_name, private=True, description=None) -> TeachingResult`: Ensure a repository exists
- `save_config(config_path=None) -> TeachingResult`: Save the current configuration

### TeachingContext

Manages the teaching environment and configuration.

```python
from quackcore.teaching import TeachingContext
```

**Methods**:

- `from_config(config_path=None, base_dir=None) -> TeachingContext`: Create a context from a configuration file
- `create_default(course_name, github_org, base_dir=None) -> TeachingContext`: Create a context with default settings
- `ensure_directories() -> None`: Ensure all required directories exist

**Properties**:

- `github`: Get the GitHub integration
- `config`: Get the teaching configuration
- `base_dir`: Get the base directory
- `assignments_dir`: Get the assignments directory
- `feedback_dir`: Get the feedback directory
- `grading_dir`: Get the grading directory
- `submissions_dir`: Get the submissions directory
- `students_file`: Get the students roster file
- `course_config_file`: Get the course configuration file

### Assignment

Represents an educational assignment.

```python
from quackcore.teaching import Assignment, AssignmentStatus, AssignmentType
```

**Methods**:

- `create(name, description=None, assignment_type=AssignmentType.INDIVIDUAL, due_date=None, points=100.0) -> Assignment`: Create a new assignment
- `publish() -> Assignment`: Mark the assignment as published
- `close() -> Assignment`: Mark the assignment as closed
- `is_past_due() -> bool`: Check if the assignment is past due
- `update_status() -> Assignment`: Update the assignment status based on current date
- `add_repository(repo_name) -> None`: Add a GitHub repository to the assignment
- `get_student_repo_name(student_github) -> str`: Get the expected repository name for a student

### AssignmentManager

Manages a collection of assignments.

```python
from quackcore.teaching import AssignmentManager
```

**Methods**:

- `add_assignment(assignment) -> None`: Add an assignment to the manager
- `get_assignment(assignment_id) -> Assignment | None`: Get an assignment by ID
- `get_assignment_by_name(name) -> Assignment | None`: Get an assignment by name
- `add_assignments(assignments) -> None`: Add multiple assignments
- `remove_assignment(assignment_id) -> bool`: Remove an assignment
- `update_statuses() -> None`: Update the status of all assignments
- `get_active_assignments() -> list[Assignment]`: Get all active assignments
- `get_past_due_assignments() -> list[Assignment]`: Get all past due assignments
- `load_from_file(file_path) -> AssignmentManager`: Load assignments from a file
- `save_to_file(file_path) -> bool`: Save assignments to a file

### Student

Represents a student in a course.

```python
from quackcore.teaching import Student
```

**Methods**:

- `create(github_username, name, email=None, group=None) -> Student`: Create a new student
- `add_submission(submission) -> None`: Add a submission for this student
- `get_submission(