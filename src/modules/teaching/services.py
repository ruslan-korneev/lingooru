import secrets
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.teaching.dto import (
    InviteCodeDTO,
    TeacherDashboardStatsDTO,
    TeacherStudentCreateDTO,
    TeacherStudentReadDTO,
    TeacherStudentWithUserDTO,
)
from src.modules.teaching.enums import TeacherStudentStatus
from src.modules.teaching.repositories import TeacherStudentRepository


def generate_invite_code() -> str:
    """Generate a 12-character invite code (uppercase alphanumeric)."""
    return secrets.token_hex(6).upper()


def create_deep_link(invite_code: str) -> str:
    """Create a deep link for the invite code."""
    bot_username = settings.telegram.bot_username
    return f"https://t.me/{bot_username}?start=join_{invite_code}"


class TeachingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ts_repo = TeacherStudentRepository(session)

    async def become_teacher(self, user_id: UUID) -> InviteCodeDTO:
        """Become a teacher and get an invite code.

        If user already has a pending invite, return it.
        Otherwise create a new one.
        """
        existing = await self._ts_repo.get_pending_invite_for_teacher(user_id)
        if existing:
            return InviteCodeDTO(
                code=existing.invite_code,
                deep_link=create_deep_link(existing.invite_code),
            )

        code = generate_invite_code()
        dto = TeacherStudentCreateDTO(
            teacher_id=user_id,
            student_id=None,
            invite_code=code,
            status=TeacherStudentStatus.PENDING,
        )
        await self._ts_repo.save(dto)

        return InviteCodeDTO(
            code=code,
            deep_link=create_deep_link(code),
        )

    async def regenerate_invite_code(self, user_id: UUID) -> InviteCodeDTO:
        """Regenerate invite code for a teacher."""
        existing = await self._ts_repo.get_pending_invite_for_teacher(user_id)
        if existing:
            await self._ts_repo.delete(existing.id)

        return await self.become_teacher(user_id)

    async def validate_invite_code(self, code: str) -> TeacherStudentReadDTO | None:
        """Validate an invite code and return the relationship if valid."""
        return await self._ts_repo.get_by_invite_code(code)

    async def join_teacher(
        self,
        student_id: UUID,
        invite_code: str,
    ) -> TeacherStudentReadDTO:
        """Join a teacher using an invite code.

        Raises:
            NotFoundError: If invite code is invalid
            ValidationError: If trying to join self
            ConflictError: If already has this teacher
        """
        ts = await self._ts_repo.get_model_by_invite_code(invite_code)
        if ts is None:
            raise NotFoundError

        if ts.teacher_id == student_id:
            raise ValidationError

        existing = await self._ts_repo.get_by_teacher_and_student(
            ts.teacher_id,
            student_id,
        )
        if existing:
            raise ConflictError

        ts.student_id = student_id
        ts.status = TeacherStudentStatus.ACTIVE

        await self._ts_repo.update_status(
            ts.id,
            TeacherStudentStatus.ACTIVE,
            student_id=student_id,
        )

        return TeacherStudentReadDTO.model_validate(ts)

    async def remove_student(self, teacher_id: UUID, student_id: UUID) -> None:
        """Remove a student from teacher's list."""
        ts = await self._ts_repo.get_by_teacher_and_student(teacher_id, student_id)
        if ts is None:
            raise NotFoundError

        await self._ts_repo.update_status(ts.id, TeacherStudentStatus.ARCHIVED)

    async def leave_teacher(self, student_id: UUID, teacher_id: UUID) -> None:
        """Leave a teacher as a student."""
        ts = await self._ts_repo.get_by_teacher_and_student(teacher_id, student_id)
        if ts is None:
            raise NotFoundError

        await self._ts_repo.update_status(ts.id, TeacherStudentStatus.ARCHIVED)

    async def get_students(
        self,
        teacher_id: UUID,
        status: TeacherStudentStatus | None = TeacherStudentStatus.ACTIVE,
    ) -> Sequence[TeacherStudentWithUserDTO]:
        """Get all students for a teacher."""
        return await self._ts_repo.get_students_for_teacher(teacher_id, status)

    async def get_teacher(
        self,
        student_id: UUID,
    ) -> TeacherStudentWithUserDTO | None:
        """Get teacher for a student."""
        return await self._ts_repo.get_teacher_for_student(
            student_id,
            TeacherStudentStatus.ACTIVE,
        )

    async def is_teacher(self, user_id: UUID) -> bool:
        """Check if user is a teacher."""
        return await self._ts_repo.is_teacher(user_id)

    async def is_student(self, user_id: UUID) -> bool:
        """Check if user has a teacher."""
        return await self._ts_repo.is_student(user_id)

    async def get_teacher_dashboard_stats(
        self,
        teacher_id: UUID,
    ) -> TeacherDashboardStatsDTO:
        """Get dashboard statistics for a teacher."""
        students_count = await self._ts_repo.count_students(
            teacher_id,
            TeacherStudentStatus.ACTIVE,
        )

        return TeacherDashboardStatsDTO(
            students_count=students_count,
            active_assignments_count=0,  # Will be implemented in phase 6.2
        )
