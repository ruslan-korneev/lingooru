from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.types.dto import BaseDTO
from src.modules.teaching.enums import (
    AssignmentStatus,
    AssignmentType,
    TeacherStudentStatus,
)


class TeacherStudentCreateDTO(BaseDTO):
    """DTO for creating a teacher-student relationship."""

    teacher_id: UUID
    student_id: UUID | None = None
    invite_code: str
    status: TeacherStudentStatus = TeacherStudentStatus.PENDING


class TeacherStudentReadDTO(BaseDTO):
    """DTO for reading a teacher-student relationship."""

    id: UUID
    teacher_id: UUID
    student_id: UUID | None
    invite_code: str
    status: TeacherStudentStatus
    created_at: datetime
    accepted_at: datetime | None


class TeacherStudentWithUserDTO(BaseDTO):
    """DTO for displaying student/teacher info in lists."""

    id: UUID
    user_id: UUID
    username: str | None
    first_name: str | None
    status: TeacherStudentStatus
    words_learned: int = 0
    current_streak: int = 0


class InviteCodeDTO(BaseDTO):
    """DTO for invite code with deep link."""

    code: str
    deep_link: str


class TeacherDashboardStatsDTO(BaseDTO):
    """DTO for teacher dashboard statistics."""

    students_count: int
    active_assignments_count: int = 0


# ---- Assignment DTOs ----


class AssignmentCreateDTO(BaseDTO):
    """DTO for creating an assignment."""

    teacher_id: UUID
    student_id: UUID
    title: str
    description: str | None = None
    assignment_type: AssignmentType
    content: dict[str, Any]
    due_date: datetime | None = None
    ai_generated: bool = False


class AssignmentReadDTO(BaseDTO):
    """DTO for reading an assignment."""

    id: UUID
    teacher_id: UUID
    student_id: UUID
    title: str
    description: str | None
    assignment_type: AssignmentType
    content: dict[str, Any]
    status: AssignmentStatus
    ai_generated: bool
    due_date: datetime | None
    created_at: datetime


class AssignmentSummaryDTO(BaseDTO):
    """Lightweight DTO for listing assignments."""

    id: UUID
    title: str
    assignment_type: AssignmentType
    status: AssignmentStatus
    due_date: datetime | None
    created_at: datetime


class AssignmentSubmissionCreateDTO(BaseDTO):
    """DTO for creating a submission."""

    assignment_id: UUID
    student_id: UUID
    content: dict[str, Any]


class AssignmentSubmissionReadDTO(BaseDTO):
    """DTO for reading a submission."""

    id: UUID
    assignment_id: UUID
    student_id: UUID
    content: dict[str, Any]
    ai_feedback: str | None
    ai_score: int | None
    teacher_feedback: str | None
    grade: int | None
    submitted_at: datetime
    graded_at: datetime | None


# ---- AI DTOs ----


class AIGenerateRequestDTO(BaseDTO):
    """Request for AI assignment generation."""

    topic: str
    assignment_type: AssignmentType
    difficulty: str = "medium"
    question_count: int = 5


class AICheckResultDTO(BaseDTO):
    """Result from AI checking."""

    score: int  # 0-100
    feedback: str
    detailed_results: list[dict[str, Any]]
