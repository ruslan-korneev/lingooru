from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.types.repositories import BaseRepository
from src.modules.teaching.dto import (
    TeacherStudentCreateDTO,
    TeacherStudentReadDTO,
    TeacherStudentWithUserDTO,
)
from src.modules.teaching.enums import TeacherStudentStatus
from src.modules.teaching.models import TeacherStudent
from src.modules.users.models import User


class TeacherStudentRepository(BaseRepository[TeacherStudent, TeacherStudentCreateDTO, TeacherStudentReadDTO]):
    _model = TeacherStudent
    _create_dto = TeacherStudentCreateDTO
    _read_dto = TeacherStudentReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, ts_id: UUID) -> TeacherStudentReadDTO | None:
        query = select(self._model).where(self._model.id == ts_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_model_by_id(self, ts_id: UUID) -> TeacherStudent | None:
        query = select(self._model).where(self._model.id == ts_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invite_code(self, code: str) -> TeacherStudentReadDTO | None:
        query = select(self._model).where(self._model.invite_code == code)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_model_by_invite_code(self, code: str) -> TeacherStudent | None:
        query = select(self._model).where(self._model.invite_code == code)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_teacher_and_student(
        self,
        teacher_id: UUID,
        student_id: UUID,
    ) -> TeacherStudentReadDTO | None:
        query = select(self._model).where(
            self._model.teacher_id == teacher_id,
            self._model.student_id == student_id,
        )
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_students_for_teacher(
        self,
        teacher_id: UUID,
        status: TeacherStudentStatus | None = None,
    ) -> Sequence[TeacherStudentWithUserDTO]:
        """Get all students for a teacher with user details."""
        query = (
            select(
                self._model.id,
                self._model.student_id,
                self._model.status,
                User.username,
                User.first_name,
            )
            .join(User, User.id == self._model.student_id)
            .where(
                self._model.teacher_id == teacher_id,
                self._model.student_id.isnot(None),
            )
        )
        if status is not None:
            query = query.where(self._model.status == status)

        result = await self._session.execute(query)
        rows = result.all()

        return [
            TeacherStudentWithUserDTO(
                id=row.id,
                user_id=row.student_id,
                username=row.username,
                first_name=row.first_name,
                status=row.status,
            )
            for row in rows
        ]

    async def get_teacher_for_student(
        self,
        student_id: UUID,
        status: TeacherStudentStatus | None = None,
    ) -> TeacherStudentWithUserDTO | None:
        """Get teacher for a student with user details."""
        query = (
            select(
                self._model.id,
                self._model.teacher_id,
                self._model.status,
                User.username,
                User.first_name,
            )
            .join(User, User.id == self._model.teacher_id)
            .where(self._model.student_id == student_id)
        )
        if status is not None:
            query = query.where(self._model.status == status)

        result = await self._session.execute(query)
        row = result.one_or_none()

        if row is None:
            return None

        return TeacherStudentWithUserDTO(
            id=row.id,
            user_id=row.teacher_id,
            username=row.username,
            first_name=row.first_name,
            status=row.status,
        )

    async def count_students(
        self,
        teacher_id: UUID,
        status: TeacherStudentStatus | None = None,
    ) -> int:
        """Count students for a teacher."""
        query = (
            select(func.count())
            .select_from(self._model)
            .where(
                self._model.teacher_id == teacher_id,
                self._model.student_id.isnot(None),
            )
        )
        if status is not None:
            query = query.where(self._model.status == status)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def is_teacher(self, user_id: UUID) -> bool:
        """Check if user has any students (is a teacher)."""
        query = select(func.count()).select_from(self._model).where(self._model.teacher_id == user_id)
        result = await self._session.execute(query)
        count = result.scalar_one()
        return count > 0

    async def is_student(self, user_id: UUID) -> bool:
        """Check if user has a teacher (is a student)."""
        query = (
            select(func.count())
            .select_from(self._model)
            .where(
                self._model.student_id == user_id,
                self._model.status == TeacherStudentStatus.ACTIVE,
            )
        )
        result = await self._session.execute(query)
        count = result.scalar_one()
        return count > 0

    async def get_pending_invite_for_teacher(
        self,
        teacher_id: UUID,
    ) -> TeacherStudentReadDTO | None:
        """Get pending invite code for a teacher (no student assigned yet)."""
        query = select(self._model).where(
            self._model.teacher_id == teacher_id,
            self._model.student_id.is_(None),
            self._model.status == TeacherStudentStatus.PENDING,
        )
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def update_status(
        self,
        ts_id: UUID,
        status: TeacherStudentStatus,
        student_id: UUID | None = None,
    ) -> None:
        """Update teacher-student relationship status."""
        instance = await self.get_model_by_id(ts_id)
        if instance is None:
            return

        instance.status = status
        if student_id is not None:
            instance.student_id = student_id
        if status == TeacherStudentStatus.ACTIVE:
            instance.accepted_at = datetime.now(UTC)

        await self._session.flush()

    async def delete(self, ts_id: UUID) -> None:
        """Delete teacher-student relationship."""
        instance = await self.get_model_by_id(ts_id)
        if instance is not None:
            await self._session.delete(instance)
            await self._session.flush()
