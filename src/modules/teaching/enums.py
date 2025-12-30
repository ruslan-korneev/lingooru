from enum import StrEnum


class TeacherStudentStatus(StrEnum):
    PENDING = "pending"  # Invite sent, not yet accepted
    ACTIVE = "active"  # Active relationship
    ARCHIVED = "archived"  # Relationship ended


class AssignmentType(StrEnum):
    TEXT = "text"  # Text answer assignment
    MULTIPLE_CHOICE = "multiple_choice"  # Multiple choice test
    VOICE = "voice"  # Voice answer assignment


class AssignmentStatus(StrEnum):
    PUBLISHED = "published"  # Available for student
    SUBMITTED = "submitted"  # Pending review
    GRADED = "graded"  # Completed
