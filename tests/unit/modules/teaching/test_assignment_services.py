"""Tests for AssignmentService."""

import uuid
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.teaching.ai_client import AICheckResult, GeneratedAssignment
from src.modules.teaching.enums import AssignmentStatus, AssignmentType
from src.modules.teaching.services import AssignmentService
from src.modules.users.dto import UserCreateDTO
from src.modules.users.repositories import UserRepository

# Expected test values
EXPECTED_COUNT_3 = 3
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
def mock_ai_client() -> MagicMock:
    client = MagicMock()
    client.generate_assignment = AsyncMock()
    client.check_text_assignment = AsyncMock()
    client.check_voice_assignment = AsyncMock()
    client.check_multiple_choice = MagicMock()
    return client


@pytest.fixture
def assignment_service(
    session: AsyncSession,
    mock_ai_client: MagicMock,
) -> AssignmentService:
    return AssignmentService(session, ai_client=mock_ai_client)


class TestCreateAssignment:
    async def test_create_manual_assignment(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        result = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test Assignment",
            assignment_type=AssignmentType.TEXT,
            content={"questions": [{"id": "q1", "text": "What is 2+2?"}]},
            description="A simple test",
        )

        assert result.id is not None
        assert result.title == "Test Assignment"
        assert result.assignment_type == AssignmentType.TEXT
        assert result.ai_generated is False

    async def test_create_assignment_with_due_date(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        from datetime import datetime

        due = datetime.now(UTC)
        result = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
            due_date=due,
        )

        assert result.due_date is not None


class TestGenerateAIAssignment:
    async def test_generate_ai_assignment(
        self,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        mock_ai_client.generate_assignment.return_value = GeneratedAssignment(
            title="AI Generated Title",
            description="AI Generated Description",
            content={"questions": [{"id": "q1", "text": "Question"}]},
        )

        result = await assignment_service.generate_ai_assignment(
            teacher_id=teacher,
            student_id=student,
            topic="fruits",
            assignment_type=AssignmentType.TEXT,
            language_pair="en_ru",
            difficulty="easy",
            question_count=3,
        )

        assert result.title == "AI Generated Title"
        assert result.description == "AI Generated Description"
        assert result.ai_generated is True
        mock_ai_client.generate_assignment.assert_called_once()


class TestGetAssignment:
    async def test_get_existing_assignment(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        created = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        result = await assignment_service.get_assignment(created.id)

        assert result is not None
        assert result.id == created.id

    async def test_get_nonexistent_assignment(
        self,
        assignment_service: AssignmentService,
    ) -> None:
        result = await assignment_service.get_assignment(uuid.uuid4())
        assert result is None


class TestGetTeacherAssignments:
    async def test_get_teacher_assignments(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        for i in range(3):
            await assignment_service.create_assignment(
                teacher_id=teacher,
                student_id=student,
                title=f"Assignment {i}",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )

        result = await assignment_service.get_teacher_assignments(teacher)

        assert len(result) == EXPECTED_COUNT_3

    async def test_get_teacher_assignments_by_status(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Published",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        # Default status is PUBLISHED
        result = await assignment_service.get_teacher_assignments(teacher, status=AssignmentStatus.PUBLISHED)
        assert len(result) == 1

        result = await assignment_service.get_teacher_assignments(teacher, status=AssignmentStatus.GRADED)
        assert len(result) == 0


class TestGetStudentAssignments:
    async def test_get_student_assignments(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        result = await assignment_service.get_student_assignments(student)

        assert len(result) == 1

    async def test_get_student_pending_assignments(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Pending",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        result = await assignment_service.get_student_pending_assignments(student)

        assert len(result) == 1


class TestSubmitAssignment:
    async def test_submit_text_assignment(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": [{"id": "q1", "text": "What is 2+2?"}]},
        )

        mock_ai_client.check_text_assignment.return_value = AICheckResult(
            score=85,
            feedback="Good job!",
            detailed_results=[],
        )

        result = await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": [{"question_id": "q1", "answer": "4"}]},
            language_pair="en_ru",
        )
        await session.flush()

        assert result.id is not None
        assert result.assignment_id == assignment.id
        mock_ai_client.check_text_assignment.assert_called_once()

    async def test_submit_mc_assignment(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Quiz",
            assignment_type=AssignmentType.MULTIPLE_CHOICE,
            content={
                "questions": [
                    {
                        "id": "q1",
                        "text": "What?",
                        "options": ["A", "B"],
                        "correct_index": 0,
                    }
                ]
            },
        )

        mock_ai_client.check_multiple_choice.return_value = AICheckResult(
            score=100,
            feedback="Perfect!",
            detailed_results=[],
        )

        result = await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": [{"question_id": "q1", "selected_index": 0}]},
        )
        await session.flush()

        assert result is not None
        mock_ai_client.check_multiple_choice.assert_called_once()

    async def test_submit_voice_assignment(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Pronunciation",
            assignment_type=AssignmentType.VOICE,
            content={"words": [{"id": "w1", "text": "hello"}]},
        )

        mock_ai_client.check_voice_assignment.return_value = AICheckResult(
            score=80,
            feedback="Good!",
            detailed_results=[],
        )

        result = await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"recordings": [{"word_id": "w1", "rating": 4}]},
        )
        await session.flush()

        assert result is not None
        mock_ai_client.check_voice_assignment.assert_called_once()

    async def test_submit_nonexistent_assignment(
        self,
        assignment_service: AssignmentService,
        student: uuid.UUID,
    ) -> None:
        with pytest.raises(NotFoundError):
            await assignment_service.submit_assignment(
                assignment_id=uuid.uuid4(),
                student_id=student,
                content={"answers": []},
            )

    async def test_submit_wrong_student(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        wrong_student = uuid.uuid4()
        with pytest.raises(ValidationError):
            await assignment_service.submit_assignment(
                assignment_id=assignment.id,
                student_id=wrong_student,
                content={"answers": []},
            )


class TestGetSubmission:
    async def test_get_submission(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        mock_ai_client.check_text_assignment.return_value = AICheckResult(
            score=50,
            feedback="OK",
            detailed_results=[],
        )

        await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": []},
        )
        await session.flush()

        result = await assignment_service.get_submission(assignment.id)

        assert result is not None
        assert result.assignment_id == assignment.id

    async def test_get_submission_not_found(
        self,
        assignment_service: AssignmentService,
    ) -> None:
        result = await assignment_service.get_submission(uuid.uuid4())
        assert result is None


class TestGradeAssignment:
    async def test_grade_assignment(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        mock_ai_client.check_text_assignment.return_value = AICheckResult(
            score=80,
            feedback="Good",
            detailed_results=[],
        )

        submission = await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": []},
        )
        await session.flush()

        result = await assignment_service.grade_assignment(
            submission_id=submission.id,
            teacher_id=teacher,
            grade=EXPECTED_GRADE_5,
            feedback="Excellent work!",
        )
        await session.flush()

        assert result.grade == EXPECTED_GRADE_5
        assert result.teacher_feedback == "Excellent work!"
        assert result.graded_at is not None

    async def test_grade_nonexistent_submission(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
    ) -> None:
        with pytest.raises(NotFoundError):
            await assignment_service.grade_assignment(
                submission_id=uuid.uuid4(),
                teacher_id=teacher,
                grade=5,
            )

    async def test_grade_wrong_teacher(
        self,
        session: AsyncSession,
        assignment_service: AssignmentService,
        mock_ai_client: MagicMock,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        assignment = await assignment_service.create_assignment(
            teacher_id=teacher,
            student_id=student,
            title="Test",
            assignment_type=AssignmentType.TEXT,
            content={"questions": []},
        )

        mock_ai_client.check_text_assignment.return_value = AICheckResult(
            score=70,
            feedback="OK",
            detailed_results=[],
        )

        submission = await assignment_service.submit_assignment(
            assignment_id=assignment.id,
            student_id=student,
            content={"answers": []},
        )
        await session.flush()

        wrong_teacher = uuid.uuid4()
        with pytest.raises(ValidationError):
            await assignment_service.grade_assignment(
                submission_id=submission.id,
                teacher_id=wrong_teacher,
                grade=5,
            )


class TestGetActiveCount:
    async def test_get_active_count_for_teacher(
        self,
        assignment_service: AssignmentService,
        teacher: uuid.UUID,
        student: uuid.UUID,
    ) -> None:
        for i in range(3):
            await assignment_service.create_assignment(
                teacher_id=teacher,
                student_id=student,
                title=f"Assignment {i}",
                assignment_type=AssignmentType.TEXT,
                content={"questions": []},
            )

        count = await assignment_service.get_active_count_for_teacher(teacher)

        # All are PUBLISHED, which counts as active
        assert count == EXPECTED_COUNT_3
