from datetime import datetime
from uuid import UUID

from src.core.types.dto import BaseDTO
from src.modules.teaching.enums import TeacherStudentStatus


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
    active_assignments_count: int = 0  # Will be used in phase 6.2
