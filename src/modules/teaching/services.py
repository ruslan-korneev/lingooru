import secrets
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.bot_info import get_bot_username
from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.teaching.ai_client import (
    TeachingAIClient,
    get_teaching_ai_client,
)
from src.modules.teaching.dto import (
    AssignmentCreateDTO,
    AssignmentReadDTO,
    AssignmentSubmissionCreateDTO,
    AssignmentSubmissionReadDTO,
    AssignmentSummaryDTO,
    InviteCodeDTO,
    TeacherDashboardStatsDTO,
    TeacherStudentCreateDTO,
    TeacherStudentReadDTO,
    TeacherStudentWithUserDTO,
)
from src.modules.teaching.enums import (
    AssignmentStatus,
    AssignmentType,
    TeacherStudentStatus,
)
from src.modules.teaching.models import Assignment
from src.modules.teaching.repositories import (
    AssignmentRepository,
    AssignmentSubmissionRepository,
    TeacherStudentRepository,
)


def generate_invite_code() -> str:
    """Generate a 12-character invite code (uppercase alphanumeric)."""
    return secrets.token_hex(6).upper()


def create_deep_link(invite_code: str) -> str:
    """Create a deep link for the invite code."""
    return f"https://t.me/{get_bot_username()}?start=join_{invite_code}"


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

        assignment_repo = AssignmentRepository(self._session)
        active_assignments = await assignment_repo.count_active_by_teacher(teacher_id)

        return TeacherDashboardStatsDTO(
            students_count=students_count,
            active_assignments_count=active_assignments,
        )


class AssignmentService:
    """Service for assignment functionality."""

    def __init__(
        self,
        session: AsyncSession,
        ai_client: TeachingAIClient | None = None,
    ) -> None:
        self._session = session
        self._assignment_repo = AssignmentRepository(session)
        self._submission_repo = AssignmentSubmissionRepository(session)
        self._ai_client = ai_client or get_teaching_ai_client()

    # ---- Creation ----

    async def create_assignment(
        self,
        teacher_id: UUID,
        student_id: UUID,
        title: str,
        assignment_type: AssignmentType,
        content: dict[str, Any],
        description: str | None = None,
        due_date: datetime | None = None,
        *,
        ai_generated: bool = False,
    ) -> AssignmentReadDTO:
        """Create assignment manually."""
        dto = AssignmentCreateDTO(
            teacher_id=teacher_id,
            student_id=student_id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            content=content,
            due_date=due_date,
            ai_generated=ai_generated,
        )
        return await self._assignment_repo.save(dto)

    async def generate_ai_assignment(
        self,
        teacher_id: UUID,
        student_id: UUID,
        topic: str,
        assignment_type: AssignmentType,
        language_pair: str = "en_ru",
        difficulty: str = "medium",
        question_count: int = 5,
    ) -> AssignmentReadDTO:
        """Generate assignment using AI."""
        generated = await self._ai_client.generate_assignment(
            topic=topic,
            assignment_type=assignment_type,
            language_pair=language_pair,
            difficulty=difficulty,
            question_count=question_count,
        )

        return await self.create_assignment(
            teacher_id=teacher_id,
            student_id=student_id,
            title=generated.title,
            assignment_type=assignment_type,
            content=generated.content,
            description=generated.description,
            ai_generated=True,
        )

    # ---- Retrieval ----

    async def get_assignment(self, assignment_id: UUID) -> AssignmentReadDTO | None:
        """Get assignment by ID."""
        return await self._assignment_repo.get_by_id(assignment_id)

    async def get_teacher_assignments(
        self,
        teacher_id: UUID,
        status: AssignmentStatus | None = None,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get all assignments created by teacher."""
        return await self._assignment_repo.get_by_teacher(teacher_id, status)

    async def get_student_assignments(
        self,
        student_id: UUID,
        status: AssignmentStatus | None = None,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get all assignments for a student."""
        return await self._assignment_repo.get_by_student(student_id, status)

    async def get_student_pending_assignments(
        self,
        student_id: UUID,
    ) -> Sequence[AssignmentSummaryDTO]:
        """Get assignments awaiting student action."""
        return await self._assignment_repo.get_pending_for_student(student_id)

    async def get_active_count_for_teacher(self, teacher_id: UUID) -> int:
        """Get count of active assignments for dashboard stats."""
        return await self._assignment_repo.count_active_by_teacher(teacher_id)

    # ---- Submission ----

    async def submit_assignment(
        self,
        assignment_id: UUID,
        student_id: UUID,
        content: dict[str, Any],
        language_pair: str = "en_ru",
    ) -> AssignmentSubmissionReadDTO:
        """Submit student answers and trigger AI check."""
        assignment = await self._assignment_repo.get_model_by_id(assignment_id)
        if assignment is None:
            raise NotFoundError

        if assignment.student_id != student_id:
            raise ValidationError

        # Create submission
        dto = AssignmentSubmissionCreateDTO(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
        )
        submission = await self._submission_repo.save(dto)

        # Update assignment status
        await self._assignment_repo.update_status(
            assignment_id,
            AssignmentStatus.SUBMITTED,
        )

        # Trigger AI check based on type
        await self._check_with_ai(submission, assignment, language_pair)

        # Return updated submission
        result = await self._submission_repo.get_by_id(submission.id)
        assert result is not None
        return result

    async def _check_with_ai(
        self,
        submission: AssignmentSubmissionReadDTO,
        assignment: Assignment,
        language_pair: str,
    ) -> None:
        """Run AI check on submission based on assignment type."""
        if assignment.assignment_type == AssignmentType.MULTIPLE_CHOICE:
            result = self._ai_client.check_multiple_choice(
                questions=assignment.content.get("questions", []),
                answers=submission.content.get("answers", []),
            )
        elif assignment.assignment_type == AssignmentType.VOICE:
            result = await self._ai_client.check_voice_assignment(
                words=assignment.content.get("words", []),
                recordings=submission.content.get("recordings", []),
            )
        else:  # TEXT
            result = await self._ai_client.check_text_assignment(
                questions=assignment.content.get("questions", []),
                answers=submission.content.get("answers", []),
                language_pair=language_pair,
            )

        await self._submission_repo.update_ai_feedback(
            submission.id,
            ai_feedback=result.feedback,
            ai_score=result.score,
        )

    async def get_submission(
        self,
        assignment_id: UUID,
    ) -> AssignmentSubmissionReadDTO | None:
        """Get submission for an assignment."""
        return await self._submission_repo.get_by_assignment(assignment_id)

    # ---- Grading ----

    async def grade_assignment(
        self,
        submission_id: UUID,
        teacher_id: UUID,
        grade: int,
        feedback: str | None = None,
    ) -> AssignmentSubmissionReadDTO:
        """Teacher grades a submission."""
        submission = await self._submission_repo.get_by_id(submission_id)
        if submission is None:
            raise NotFoundError

        # Verify teacher owns the assignment
        assignment = await self._assignment_repo.get_by_id(submission.assignment_id)
        if assignment is None or assignment.teacher_id != teacher_id:
            raise ValidationError

        await self._submission_repo.update_teacher_feedback(
            submission_id,
            teacher_feedback=feedback or "",
            grade=grade,
        )

        # Update assignment status
        await self._assignment_repo.update_status(
            submission.assignment_id,
            AssignmentStatus.GRADED,
        )

        result = await self._submission_repo.get_by_id(submission_id)
        assert result is not None
        return result
