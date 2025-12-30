from enum import StrEnum


class TeacherStudentStatus(StrEnum):
    PENDING = "pending"  # Invite sent, not yet accepted
    ACTIVE = "active"  # Active relationship
    ARCHIVED = "archived"  # Relationship ended
