"""Tests for assignment repositories."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.teaching.dto import AssignmentCreateDTO, AssignmentSubmissionCreateDTO
from src.modules.teaching.enums import AssignmentStatus, AssignmentType
from src.modules.teaching.repositories import (
    AssignmentRepository,
    AssignmentSubmissionRepository,
)
from src.modules.users.dto import UserCreateDTO
from src.modules.users.repositories import UserRepository

# Expected test values
EXPECTED_COUNT_3 = 3
EXPECTED_ACTIVE_COUNT_2 = 2
EXPECTED_AI_SCORE_85 = 85
EXPECTED_GRADE_5 = 5


@pytest.fixture
async def teacher(session: AsyncSession) -> uuid.UUID:
    repo = UserRepository(session)
    user = await repo.save(UserCreateDTO(telegram_id=111111, username="teacher1", first_name="Teacher"))
    return user.id


@pytest.fixture
async def student(session: AsyncSession) -> uuid.UUID:
    repo = UserRepository(session)
    user = await repo.save(UserCreateDTO(telegram_id=222222, username="student1", first_name="Student"))
    return user.id


@pytest.fixture
async def assignment_repo(session: AsyncSession) -> AssignmentRepository:
    return AssignmentRepository(session)


@pytest.fixture
async def submission_repo(session: AsyncSession) -> AssignmentSubmissionRepository:
    return AssignmentSubmissionRepository(session)


class TestAssignmentRepository:
    async def test_save_creates_assignment(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        dto = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Test Assignment",
            assignment_type=AssignmentType.TEXT,
            content={"questions": [{"id": "q1", "text": "What is 2+2?"}]},
        )
        result = await assignment_repo.save(dto)

        assert result.id is not None
        assert result.title == "Test Assignment"
        assert result.assignment_type == AssignmentType.TEXT
        assert result.status == AssignmentStatus.PUBLISHED

    async def test_get_by_id_returns_assignment(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        dto = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )
        created = await assignment_repo.save(dto)

        result = await assignment_repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_by_id_returns_none_for_unknown(
        self,
        assignment_repo: AssignmentRepository,
    ) -> None:
        result = await assignment_repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_get_model_by_id_returns_model(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        dto = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )
        created = await assignment_repo.save(dto)

        model = await assignment_repo.get_model_by_id(created.id)

        assert model is not None
        assert model.id == created.id

    async def test_get_by_teacher_returns_list(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        for i in range(3):
            await assignment_repo.save(
                AssignmentCreateDTO(
                    teacher_id=teacher,
                    student_id=student,
                    title=f"Assignment {i}",
                    assignment_type=AssignmentType.TEXT,
                    content={"questions": []},
                )
            )

        result = await assignment_repo.get_by_teacher(teacher)

        assert len(result) == EXPECTED_COUNT_3

    async def test_get_by_teacher_filters_by_status(
        self,
        session: AsyncSession,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        # Create assignment and manually set status
        dto = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )
        created = await assignment_repo.save(dto)
        await assignment_repo.update_status(created.id, AssignmentStatus.GRADED)
        await session.flush()

        result = await assignment_repo.get_by_teacher(teacher, status=AssignmentStatus.GRADED)

        assert len(result) == 1

    async def test_get_by_student_returns_list(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )

        result = await assignment_repo.get_by_student(student)

        assert len(result) == 1

    async def test_get_pending_for_student_returns_published_only(
        self,
        session: AsyncSession,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        # Create two assignments
        dto1 = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Pending",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )
        dto2 = AssignmentCreateDTO(
            teacher_id=teacher,
            student_id=student,
            title="Graded",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )
        await assignment_repo.save(dto1)
        graded = await assignment_repo.save(dto2)
        await assignment_repo.update_status(graded.id, AssignmentStatus.GRADED)
        await session.flush()

        result = await assignment_repo.get_pending_for_student(student)

        assert len(result) == 1
        assert result[0].title == "Pending"

    async def test_count_by_teacher(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        for i in range(3):
            await assignment_repo.save(
                AssignmentCreateDTO(
                    teacher_id=teacher,
                    student_id=student,
                    title=f"Assignment {i}",
                    assignment_type=AssignmentType.TEXT,
                    content={"questions": []},
                )
            )

        count = await assignment_repo.count_by_teacher(teacher)

        assert count == EXPECTED_COUNT_3

    async def test_count_active_by_teacher(
        self,
        session: AsyncSession,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        # Create assignments with different statuses
        await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Published",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        sub = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Submitted",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        graded = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Graded",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        await assignment_repo.update_status(sub.id, AssignmentStatus.SUBMITTED)
        await assignment_repo.update_status(graded.id, AssignmentStatus.GRADED)
        await session.flush()

        count = await assignment_repo.count_active_by_teacher(teacher)

        assert count == EXPECTED_ACTIVE_COUNT_2  # Published + Submitted

    async def test_update_status(
        self,
        assignment_repo: AssignmentRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        created = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )

        await assignment_repo.update_status(created.id, AssignmentStatus.GRADED)

        result = await assignment_repo.get_by_id(created.id)
        assert result is not None
        assert result.status == AssignmentStatus.GRADED

    async def test_update_status_nonexistent(
        self,
        assignment_repo: AssignmentRepository,
    ) -> None:
        # Should not raise
        await assignment_repo.update_status(uuid.uuid4(), AssignmentStatus.GRADED)


class TestAssignmentSubmissionRepository:
    async def test_save_creates_submission(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )

        dto = AssignmentSubmissionCreateDTO(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": [{"question_id": "q1", "answer": "test"}]},
        )
        result = await submission_repo.save(dto)

        assert result.id is not None
        assert result.assignment_id == assignment.id

    async def test_get_by_id_returns_submission(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        created = await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )

        result = await submission_repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_by_id_returns_none_for_unknown(
        self,
        submission_repo: AssignmentSubmissionRepository,
    ) -> None:
        result = await submission_repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_get_model_by_id(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        created = await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )

        model = await submission_repo.get_model_by_id(created.id)

        assert model is not None

    async def test_get_by_assignment_returns_submission(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )

        result = await submission_repo.get_by_assignment(assignment.id)

        assert result is not None

    async def test_get_by_assignment_returns_none(
        self,
        submission_repo: AssignmentSubmissionRepository,
    ) -> None:
        result = await submission_repo.get_by_assignment(uuid.uuid4())
        assert result is None

    async def test_get_pending_for_teacher(
        self,
        session: AsyncSession,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )
        await assignment_repo.update_status(assignment.id, AssignmentStatus.SUBMITTED)
        await session.flush()

        result = await submission_repo.get_pending_for_teacher(teacher)

        assert len(result) == 1

    async def test_update_ai_feedback(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        created = await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )

        await submission_repo.update_ai_feedback(created.id, "Good job!", EXPECTED_AI_SCORE_85)

        result = await submission_repo.get_by_id(created.id)
        assert result is not None
        assert result.ai_feedback == "Good job!"
        assert result.ai_score == EXPECTED_AI_SCORE_85

    async def test_update_ai_feedback_nonexistent(
        self,
        submission_repo: AssignmentSubmissionRepository,
    ) -> None:
        # Should not raise
        await submission_repo.update_ai_feedback(uuid.uuid4(), "test", 50)

    async def test_update_teacher_feedback(
        self,
        assignment_repo: AssignmentRepository,
        submission_repo: AssignmentSubmissionRepository,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_repo.save(
            AssignmentCreateDTO(
                teacher_id=teacher,
                student_id=student,
                title="Test",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )
        )
        created = await submission_repo.save(
            AssignmentSubmissionCreateDTO(
                assignment_id=assignment.id,
                student_id=student,
                content={"answers": []},
            )
        )

        await submission_repo.update_teacher_feedback(created.id, "Excellent!", EXPECTED_GRADE_5)

        result = await submission_repo.get_by_id(created.id)
        assert result is not None
        assert result.teacher_feedback == "Excellent!"
        assert result.grade == EXPECTED_GRADE_5
        assert result.graded_at is not None

    async def test_update_teacher_feedback_nonexistent(
        self,
        submission_repo: AssignmentSubmissionRepository,
    ) -> None:
        # Should not raise
        await submission_repo.update_teacher_feedback(uuid.uuid4(), "test", 5)
