from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.types.repositories import BaseRepository
from src.modules.teaching.dto import (
    AssignmentCreateDTO,
    AssignmentReadDTO,
    AssignmentSubmissionCreateDTO,
    AssignmentSubmissionReadDTO,
    AssignmentSummaryDTO,
    TeacherStudentCreateDTO,
    TeacherStudentReadDTO,
    TeacherStudentWithUserDTO,
)
from src.modules.teaching.enums import AssignmentStatus, TeacherStudentStatus
from src.modules.teaching.models import Assignment, AssignmentSubmission, TeacherStudent
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


class AssignmentRepository(BaseRepository[Assignment, AssignmentCreateDTO, AssignmentReadDTO]):
    _model = Assignment
    _create_dto = AssignmentCreateDTO
    _read_dto = AssignmentReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, assignment_id: UUID) -> AssignmentReadDTO | None:
        query = select(self._model).where(self._model.id == assignment_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_model_by_id(self, assignment_id: UUID) -> Assignment | None:
        query = select(self._model).where(self._model.id == assignment_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_teacher(
        self,
        teacher_id: UUID,
        status: AssignmentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get assignments created by teacher."""
        query = select(self._model).where(self._model.teacher_id == teacher_id)
        if status is not None:
            query = query.where(self._model.status == status)
        query = query.order_by(self._model.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        instances = result.scalars().all()
        return [AssignmentSummaryDTO.model_validate(i) for i in instances]

    async def get_by_student(
        self,
        student_id: UUID,
        status: AssignmentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get assignments for a student."""
        query = select(self._model).where(self._model.student_id == student_id)
        if status is not None:
            query = query.where(self._model.status == status)
        query = query.order_by(self._model.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        instances = result.scalars().all()
        return [AssignmentSummaryDTO.model_validate(i) for i in instances]

    async def get_pending_for_student(
        self,
        student_id: UUID,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get assignments awaiting student action (PUBLISHED status)."""
        query = (
            select(self._model)
            .where(
                self._model.student_id == student_id,
                self._model.status == AssignmentStatus.PUBLISHED,
            )
            .order_by(self._model.due_date.asc().nullslast(), self._model.created_at.desc())
        )

        result = await self._session.execute(query)
        instances = result.scalars().all()
        return [AssignmentSummaryDTO.model_validate(i) for i in instances]

    async def count_by_teacher(
        self,
        teacher_id: UUID,
        status: AssignmentStatus | None = None,
    ) -> int:
        """Count assignments by teacher."""
        query = select(func.count()).select_from(self._model).where(self._model.teacher_id == teacher_id)
        if status is not None:
            query = query.where(self._model.status == status)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_active_by_teacher(self, teacher_id: UUID) -> int:
        """Count assignments with status PUBLISHED or SUBMITTED."""
        query = (
            select(func.count())
            .select_from(self._model)
            .where(
                self._model.teacher_id == teacher_id,
                self._model.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.SUBMITTED]),
            )
        )

        result = await self._session.execute(query)
        return result.scalar_one()

    async def update_status(self, assignment_id: UUID, status: AssignmentStatus) -> None:
        """Update assignment status."""
        instance = await self.get_model_by_id(assignment_id)
        if instance is None:
            return
        instance.status = status
        await self._session.flush()


class AssignmentSubmissionRepository(
    BaseRepository[AssignmentSubmission, AssignmentSubmissionCreateDTO, AssignmentSubmissionReadDTO]
):
    _model = AssignmentSubmission
    _create_dto = AssignmentSubmissionCreateDTO
    _read_dto = AssignmentSubmissionReadDTO

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, submission_id: UUID) -> AssignmentSubmissionReadDTO | None:
        query = select(self._model).where(self._model.id == submission_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_model_by_id(self, submission_id: UUID) -> AssignmentSubmission | None:
        query = select(self._model).where(self._model.id == submission_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_assignment(self, assignment_id: UUID) -> AssignmentSubmissionReadDTO | None:
        """Get submission for an assignment (one per assignment)."""
        query = select(self._model).where(self._model.assignment_id == assignment_id)
        result = await self._session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._read_dto.model_validate(instance)

    async def get_pending_for_teacher(
        self,
        teacher_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[AssignmentSubmissionReadDTO]:
        """Get submissions pending teacher review."""
        query = (
            select(self._model)
            .join(Assignment, Assignment.id == self._model.assignment_id)
            .where(
                Assignment.teacher_id == teacher_id,
                Assignment.status == AssignmentStatus.SUBMITTED,
            )
            .order_by(self._model.submitted_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(query)
        instances = result.scalars().all()
        return [self._read_dto.model_validate(i) for i in instances]

    async def update_ai_feedback(
        self,
        submission_id: UUID,
        ai_feedback: str,
        ai_score: int,
    ) -> None:
        """Update submission with AI feedback."""
        instance = await self.get_model_by_id(submission_id)
        if instance is None:
            return
        instance.ai_feedback = ai_feedback
        instance.ai_score = ai_score
        await self._session.flush()

    async def update_teacher_feedback(
        self,
        submission_id: UUID,
        teacher_feedback: str,
        grade: int,
    ) -> None:
        """Update submission with teacher feedback and grade."""
        instance = await self.get_model_by_id(submission_id)
        if instance is None:
            return
        instance.teacher_feedback = teacher_feedback
        instance.grade = grade
        instance.graded_at = datetime.now(UTC)
        await self._session.flush()
