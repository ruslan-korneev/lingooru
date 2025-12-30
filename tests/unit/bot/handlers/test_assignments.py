"""Tests for assignment handlers."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.handlers.assignments import (
    AssignmentStates,
    on_ai_method,
    on_answer_input,
    on_assignment_list,
    on_assignment_page,
    on_grade_assignment,
    on_new_assignment,
    on_pending_assignments,
    on_rate_assignment,
    on_select_difficulty,
    on_select_type,
    on_start_assignment,
    on_topic_input,
    on_view_assignment,
    on_view_result,
    on_view_submission,
)
from src.modules.teaching.dto import (
    AssignmentReadDTO,
    AssignmentSubmissionReadDTO,
    AssignmentSummaryDTO,
)
from src.modules.teaching.enums import AssignmentStatus, AssignmentType
from src.modules.users.dto import UserReadDTO
from src.modules.users.enums import LanguagePair, UILanguage


def create_mock_i18n() -> MagicMock:
    i18n = MagicMock()
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


def create_mock_db_user() -> UserReadDTO:
    return UserReadDTO(
        id=uuid4(),
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        ui_language=UILanguage.EN,
        language_pair=LanguagePair.EN_RU,
        timezone="UTC",
        notifications_enabled=True,
        notification_times=["09:00", "21:00"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def create_mock_callback(data: str) -> MagicMock:
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.answer = AsyncMock()
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.message.answer = AsyncMock()
    return callback


def create_mock_message(text: str = "test") -> MagicMock:
    message = MagicMock(spec=Message)
    message.text = text
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


def create_mock_state() -> MagicMock:
    state = MagicMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


def create_mock_assignment(
    teacher_id: UUID | None = None,
    student_id: UUID | None = None,
    status: AssignmentStatus = AssignmentStatus.PUBLISHED,
    assignment_type: AssignmentType = AssignmentType.TEXT,
) -> AssignmentReadDTO:
    return AssignmentReadDTO(
        id=uuid4(),
        teacher_id=teacher_id or uuid4(),
        student_id=student_id or uuid4(),
        title="Test Assignment",
        description="Description",
        assignment_type=assignment_type,
        content={"questions": [{"id": "q1", "text": "What is 2+2?"}]},
        status=status,
        ai_generated=False,
        due_date=None,
        created_at=datetime.now(UTC),
    )


def create_mock_submission() -> AssignmentSubmissionReadDTO:
    return AssignmentSubmissionReadDTO(
        id=uuid4(),
        assignment_id=uuid4(),
        student_id=uuid4(),
        content={"answers": [{"question_id": "q1", "answer": "4"}]},
        ai_feedback="Good job!",
        ai_score=85,
        teacher_feedback=None,
        grade=None,
        submitted_at=datetime.now(UTC),
        graded_at=None,
    )


class TestOnAssignmentList:
    async def test_shows_no_assignments_message(self) -> None:
        callback = create_mock_callback("assign:list")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_teacher_assignments = AsyncMock(return_value=[])

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_assignment_list(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_shows_assignments_list(self) -> None:
        callback = create_mock_callback("assign:list")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        assignment = AssignmentSummaryDTO(
            id=uuid4(),
            title="Test",
            assignment_type=AssignmentType.TEXT,
            status=AssignmentStatus.PUBLISHED,
            due_date=None,
            created_at=datetime.now(UTC),
        )

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_teacher_assignments = AsyncMock(return_value=[assignment])

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_assignment_list(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestOnNewAssignment:
    async def test_shows_type_selection(self) -> None:
        student_id = uuid4()
        callback = create_mock_callback(f"assign:new:{student_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
            await on_new_assignment(callback, i18n, db_user)

            callback.answer.assert_called_once()

    async def test_invalid_student_id(self) -> None:
        callback = create_mock_callback("assign:new:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_new_assignment(callback, i18n, db_user)

        callback.answer.assert_called_once()


class TestOnSelectType:
    async def test_shows_method_selection(self) -> None:
        student_id = uuid4()
        callback = create_mock_callback(f"assign:type:text:{student_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
            await on_select_type(callback, i18n, db_user)

            callback.answer.assert_called_once()


class TestOnAIMethod:
    async def test_shows_difficulty_selection(self) -> None:
        student_id = uuid4()
        callback = create_mock_callback(f"assign:ai:text:{student_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
            await on_ai_method(callback, i18n, db_user)

            callback.answer.assert_called_once()


class TestOnSelectDifficulty:
    async def test_enters_topic_state(self) -> None:
        student_id = uuid4()
        callback = create_mock_callback(f"assign:diff:easy:text:{student_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
            await on_select_difficulty(callback, i18n, db_user, state)

            state.set_state.assert_called_once_with(AssignmentStates.entering_topic)
            state.update_data.assert_called_once()
            callback.answer.assert_called_once()


class TestOnTopicInput:
    async def test_generates_assignment(self) -> None:
        message = create_mock_message("fruits vocabulary")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(
            return_value={
                "student_id": str(uuid4()),
                "assignment_type": "text",
                "difficulty": "easy",
            }
        )

        generating_msg = AsyncMock()
        generating_msg.edit_text = AsyncMock()
        message.answer = AsyncMock(return_value=generating_msg)

        mock_assignment = create_mock_assignment()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.generate_ai_assignment = AsyncMock(return_value=mock_assignment)

                await on_topic_input(message, i18n, db_user, state)

                state.clear.assert_called_once()
                mock_service.generate_ai_assignment.assert_called_once()

    async def test_empty_topic_error(self) -> None:
        message = create_mock_message("")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={})

        await on_topic_input(message, i18n, db_user, state)

        message.answer.assert_called()


class TestOnViewAssignment:
    async def test_shows_assignment_details(self) -> None:
        assignment = create_mock_assignment()
        callback = create_mock_callback(f"assign:view:{assignment.id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)
                mock_service.get_submission = AsyncMock(return_value=None)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_assignment(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_not_found(self) -> None:
        callback = create_mock_callback(f"assign:view:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=None)

                await on_view_assignment(callback, i18n, db_user)

                callback.answer.assert_called()


class TestOnPendingAssignments:
    async def test_shows_pending_list(self) -> None:
        callback = create_mock_callback("assign:pending")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_student_pending_assignments = AsyncMock(return_value=[])

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_pending_assignments(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestOnStartAssignment:
    async def test_starts_text_assignment(self) -> None:
        assignment = create_mock_assignment(assignment_type=AssignmentType.TEXT)
        callback = create_mock_callback(f"assign:start:{assignment.id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_start_assignment(callback, i18n, db_user, state)

                    state.set_state.assert_called_once_with(AssignmentStates.entering_answer)
                    callback.answer.assert_called_once()

    async def test_starts_voice_assignment(self) -> None:
        assignment = create_mock_assignment(assignment_type=AssignmentType.VOICE)
        assignment.content = {"words": [{"id": "w1", "text": "hello"}]}
        callback = create_mock_callback(f"assign:start:{assignment.id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_start_assignment(callback, i18n, db_user, state)

                    state.set_state.assert_called_once()


class TestOnAnswerInput:
    async def test_submits_answer(self) -> None:
        message = create_mock_message("answer1\nanswer2")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={"assignment_id": str(uuid4())})

        submission = create_mock_submission()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.submit_assignment = AsyncMock(return_value=submission)

                await on_answer_input(message, i18n, db_user, state)

                state.clear.assert_called_once()
                mock_service.submit_assignment.assert_called_once()

    async def test_empty_answer_error(self) -> None:
        message = create_mock_message("")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={})

        await on_answer_input(message, i18n, db_user, state)

        message.answer.assert_called()


class TestOnViewSubmission:
    async def test_shows_submission(self) -> None:
        submission = create_mock_submission()
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_submission(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestOnGradeAssignment:
    async def test_shows_grade_keyboard(self) -> None:
        submission_id = uuid4()
        callback = create_mock_callback(f"assign:grade:{submission_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
            await on_grade_assignment(callback, i18n, db_user)

            callback.answer.assert_called_once()


class TestOnRateAssignment:
    async def test_grades_assignment(self) -> None:
        submission_id = uuid4()
        callback = create_mock_callback(f"assign:rate:5:{submission_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.grade_assignment = AsyncMock()

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_rate_assignment(callback, i18n, db_user)

                    mock_service.grade_assignment.assert_called_once()
                    callback.answer.assert_called()

    async def test_invalid_grade(self) -> None:
        submission_id = uuid4()
        callback = create_mock_callback(f"assign:rate:10:{submission_id}")  # Invalid grade
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_rate_assignment(callback, i18n, db_user)

        callback.answer.assert_called()


class TestOnViewResult:
    async def test_shows_result(self) -> None:
        submission = create_mock_submission()
        submission.grade = 5
        callback = create_mock_callback(f"assign:result:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_result(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestOnAssignmentPage:
    async def test_handles_pagination(self) -> None:
        callback = create_mock_callback("assign:page:1")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_teacher_assignments = AsyncMock(return_value=[])
                mock_service.get_student_assignments = AsyncMock(return_value=[])

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_assignment_page(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_pagination_with_teacher_assignments(self) -> None:
        callback = create_mock_callback("assign:page:0")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        assignment = AssignmentSummaryDTO(
            id=uuid4(),
            title="Test",
            assignment_type=AssignmentType.TEXT,
            status=AssignmentStatus.PUBLISHED,
            due_date=None,
            created_at=datetime.now(UTC),
        )

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_teacher_assignments = AsyncMock(return_value=[assignment])

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_assignment_page(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_no_message_returns_early(self) -> None:
        callback = create_mock_callback("assign:page:0")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_assignment_page(callback, i18n, db_user)


class TestNullMessageHandling:
    async def test_assignment_list_no_message(self) -> None:
        callback = create_mock_callback("assign:list")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_assignment_list(callback, i18n, db_user)

    async def test_new_assignment_no_message(self) -> None:
        callback = create_mock_callback(f"assign:new:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_new_assignment(callback, i18n, db_user)

    async def test_select_type_no_message(self) -> None:
        callback = create_mock_callback(f"assign:type:text:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_select_type(callback, i18n, db_user)

    async def test_ai_method_no_message(self) -> None:
        callback = create_mock_callback(f"assign:ai:text:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_ai_method(callback, i18n, db_user)

    async def test_select_difficulty_no_message(self) -> None:
        callback = create_mock_callback(f"assign:diff:easy:text:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        await on_select_difficulty(callback, i18n, db_user, state)

    async def test_view_assignment_no_message(self) -> None:
        callback = create_mock_callback(f"assign:view:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_assignment(callback, i18n, db_user)

    async def test_pending_no_message(self) -> None:
        callback = create_mock_callback("assign:pending")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_pending_assignments(callback, i18n, db_user)

    async def test_start_assignment_no_message(self) -> None:
        callback = create_mock_callback(f"assign:start:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        await on_start_assignment(callback, i18n, db_user, state)

    async def test_view_submission_no_message(self) -> None:
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_submission(callback, i18n, db_user)

    async def test_grade_assignment_no_message(self) -> None:
        callback = create_mock_callback(f"assign:grade:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_grade_assignment(callback, i18n, db_user)

    async def test_rate_assignment_no_message(self) -> None:
        callback = create_mock_callback(f"assign:rate:5:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_rate_assignment(callback, i18n, db_user)

    async def test_view_result_no_message(self) -> None:
        callback = create_mock_callback(f"assign:result:{uuid4()}")
        callback.message = None
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_result(callback, i18n, db_user)


class TestInvalidUUIDHandling:
    async def test_select_type_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:type:text:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_select_type(callback, i18n, db_user)

        callback.answer.assert_called()

    async def test_ai_method_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:ai:text:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_ai_method(callback, i18n, db_user)

        callback.answer.assert_called()

    async def test_select_difficulty_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:diff:easy:text:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        await on_select_difficulty(callback, i18n, db_user, state)

        callback.answer.assert_called()

    async def test_view_assignment_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:view:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_assignment(callback, i18n, db_user)

        callback.answer.assert_called()

    async def test_start_assignment_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:start:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()

        await on_start_assignment(callback, i18n, db_user, state)

        callback.answer.assert_called()

    async def test_view_submission_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:submission:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_submission(callback, i18n, db_user)

        callback.answer.assert_called()

    async def test_grade_assignment_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:grade:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_grade_assignment(callback, i18n, db_user)

        callback.answer.assert_called()

    async def test_view_result_invalid_uuid(self) -> None:
        callback = create_mock_callback("assign:result:invalid")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        await on_view_result(callback, i18n, db_user)

        callback.answer.assert_called()


class TestSubmissionNotFound:
    async def test_view_submission_not_found(self) -> None:
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=None)

                await on_view_submission(callback, i18n, db_user)

                callback.answer.assert_called()

    async def test_view_result_not_found(self) -> None:
        callback = create_mock_callback(f"assign:result:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=None)

                await on_view_result(callback, i18n, db_user)

                callback.answer.assert_called()


class TestAssignmentWithDescription:
    async def test_view_assignment_with_description(self) -> None:
        db_user = create_mock_db_user()
        assignment = create_mock_assignment(teacher_id=db_user.id)
        callback = create_mock_callback(f"assign:view:{assignment.id}")
        i18n = create_mock_i18n()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)
                mock_service.get_submission = AsyncMock(return_value=None)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_assignment(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_view_assignment_without_description(self) -> None:
        """Test assignment without description (line 324 branch)."""
        db_user = create_mock_db_user()
        assignment = create_mock_assignment(teacher_id=db_user.id)
        assignment.description = None  # No description
        callback = create_mock_callback(f"assign:view:{assignment.id}")
        i18n = create_mock_i18n()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)
                mock_service.get_submission = AsyncMock(return_value=None)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_assignment(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestEmptyContent:
    async def test_start_assignment_no_questions(self) -> None:
        db_user = create_mock_db_user()
        assignment = create_mock_assignment(student_id=db_user.id)
        assignment.content = {}  # No questions or words
        callback = create_mock_callback(f"assign:start:{assignment.id}")
        i18n = create_mock_i18n()
        state = create_mock_state()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_assignment = AsyncMock(return_value=assignment)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_start_assignment(callback, i18n, db_user, state)

                    callback.answer.assert_called_once()


class TestRateErrors:
    async def test_rate_not_found(self) -> None:
        from src.core.exceptions import NotFoundError

        submission_id = uuid4()
        callback = create_mock_callback(f"assign:rate:5:{submission_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.grade_assignment = AsyncMock(side_effect=NotFoundError())

                await on_rate_assignment(callback, i18n, db_user)

                callback.answer.assert_called()

    async def test_rate_validation_error(self) -> None:
        from src.core.exceptions import ValidationError

        submission_id = uuid4()
        callback = create_mock_callback(f"assign:rate:5:{submission_id}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.grade_assignment = AsyncMock(side_effect=ValidationError())

                await on_rate_assignment(callback, i18n, db_user)

                callback.answer.assert_called()


class TestTopicErrors:
    async def test_topic_missing_state_data(self) -> None:
        message = create_mock_message("topic")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={})

        await on_topic_input(message, i18n, db_user, state)

        message.answer.assert_called()

    async def test_topic_generation_error(self) -> None:
        from src.core.exceptions import NotFoundError

        message = create_mock_message("topic")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(
            return_value={
                "student_id": str(uuid4()),
                "assignment_type": "text",
                "difficulty": "easy",
            }
        )

        generating_msg = AsyncMock()
        generating_msg.edit_text = AsyncMock()
        message.answer = AsyncMock(return_value=generating_msg)

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.generate_ai_assignment = AsyncMock(side_effect=NotFoundError())

                await on_topic_input(message, i18n, db_user, state)

                generating_msg.edit_text.assert_called()


class TestAnswerErrors:
    async def test_answer_missing_assignment_id(self) -> None:
        message = create_mock_message("answer")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={})

        await on_answer_input(message, i18n, db_user, state)

        message.answer.assert_called()

    async def test_answer_not_found(self) -> None:
        from src.core.exceptions import NotFoundError

        message = create_mock_message("answer")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={"assignment_id": str(uuid4())})

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.submit_assignment = AsyncMock(side_effect=NotFoundError())

                await on_answer_input(message, i18n, db_user, state)

                message.answer.assert_called()

    async def test_answer_validation_error(self) -> None:
        from src.core.exceptions import ValidationError

        message = create_mock_message("answer")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()
        state = create_mock_state()
        state.get_data = AsyncMock(return_value={"assignment_id": str(uuid4())})

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.submit_assignment = AsyncMock(side_effect=ValidationError())

                await on_answer_input(message, i18n, db_user, state)

                message.answer.assert_called()


class TestSubmissionDetails:
    async def test_submission_with_grade(self) -> None:
        submission = create_mock_submission()
        submission.grade = 4
        submission.teacher_feedback = "Well done!"
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_submission(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_submission_with_ai_feedback_no_score(self) -> None:
        """Test submission with AI feedback but no score (line 514 branch)."""
        submission = create_mock_submission()
        submission.ai_feedback = "Good work!"
        submission.ai_score = None  # No AI score
        submission.grade = None
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_submission(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_submission_with_grade_no_feedback(self) -> None:
        """Test submission with grade but no teacher feedback (line 519 branch)."""
        submission = create_mock_submission()
        submission.grade = 4
        submission.teacher_feedback = None  # No teacher feedback
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_submission(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_submission_without_ai_feedback(self) -> None:
        """Test submission without AI feedback (line 512 branch)."""
        submission = create_mock_submission()
        submission.ai_feedback = None
        submission.ai_score = None
        submission.grade = None
        callback = create_mock_callback(f"assign:submission:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_submission(callback, i18n, db_user)

                    callback.answer.assert_called_once()


class TestResultDetails:
    async def test_result_with_teacher_feedback(self) -> None:
        submission = create_mock_submission()
        submission.grade = 5
        submission.teacher_feedback = "Excellent!"
        callback = create_mock_callback(f"assign:result:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_result(callback, i18n, db_user)

                    callback.answer.assert_called_once()

    async def test_result_without_ai_score(self) -> None:
        submission = create_mock_submission()
        submission.ai_score = None
        submission.ai_feedback = None
        callback = create_mock_callback(f"assign:result:{uuid4()}")
        i18n = create_mock_i18n()
        db_user = create_mock_db_user()

        with patch("src.bot.handlers.assignments.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.assignments.AssignmentService") as mock_service_cls:
                mock_service = mock_service_cls.return_value
                mock_service.get_submission = AsyncMock(return_value=submission)

                with patch("src.bot.handlers.assignments.safe_edit_or_send", new_callable=AsyncMock):
                    await on_view_result(callback, i18n, db_user)

                    callback.answer.assert_called_once()
