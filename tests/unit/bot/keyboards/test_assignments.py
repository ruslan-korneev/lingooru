"""Tests for assignment keyboards."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from aiogram_i18n import I18nContext

from src.bot.keyboards.assignments import (
    TITLE_MAX_LENGTH,
    _get_status_icon,
    _get_type_icon,
    get_answer_cancel_keyboard,
    get_assignment_detail_keyboard,
    get_assignment_list_keyboard,
    get_assignment_method_keyboard,
    get_assignment_type_keyboard,
    get_difficulty_keyboard,
    get_grade_keyboard,
    get_submission_review_keyboard,
    get_topic_cancel_keyboard,
)
from src.modules.teaching.dto import AssignmentReadDTO, AssignmentSummaryDTO
from src.modules.teaching.enums import AssignmentStatus, AssignmentType

# Expected keyboard row counts
ROWS_TYPE_KEYBOARD = 4  # text, mc, voice, back
ROWS_METHOD_KEYBOARD = 3  # ai, manual, back
ROWS_DIFFICULTY_KEYBOARD = 2  # 3 buttons in row, back
ROWS_DETAIL_TEACHER_WITH_SUB = 2  # view, back
ROWS_DETAIL_TEACHER_NO_SUB = 1  # back only
ROWS_DETAIL_STUDENT_PUBLISHED = 2  # start, back
ROWS_DETAIL_STUDENT_SUBMITTED = 1  # back only
ROWS_DETAIL_STUDENT_GRADED = 2  # result, back
ROWS_SUBMISSION_REVIEW = 2  # grade, back
ROWS_GRADE = 2  # 5 buttons, back
ROWS_CANCEL = 1

BUTTONS_IN_DIFFICULTY_ROW = 3
BUTTONS_IN_GRADE_ROW = 5

# List keyboard row counts
ROWS_SINGLE_ASSIGNMENT = 2  # assignment + back
ROWS_THREE_ASSIGNMENTS = 4  # 3 assignments + back
ROWS_MANY_WITH_PAGINATION = 7  # 5 assignments + pagination + back


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


def create_mock_assignment(
    status: AssignmentStatus = AssignmentStatus.PUBLISHED,
    assignment_type: AssignmentType = AssignmentType.TEXT,
    title: str = "Test Assignment",
) -> AssignmentReadDTO:
    """Create a mock assignment."""
    return AssignmentReadDTO(
        id=uuid4(),
        teacher_id=uuid4(),
        student_id=uuid4(),
        title=title,
        description="Test",
        assignment_type=assignment_type,
        content={"questions": []},
        status=status,
        ai_generated=False,
        due_date=None,
        created_at=datetime.now(UTC),
    )


def create_mock_assignment_summary(
    status: AssignmentStatus = AssignmentStatus.PUBLISHED,
    assignment_type: AssignmentType = AssignmentType.TEXT,
    title: str = "Test Assignment",
) -> AssignmentSummaryDTO:
    """Create a mock assignment summary."""
    return AssignmentSummaryDTO(
        id=uuid4(),
        title=title,
        assignment_type=assignment_type,
        status=status,
        due_date=None,
        created_at=datetime.now(UTC),
    )


class TestGetAssignmentTypeKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        student_id = uuid4()

        keyboard = get_assignment_type_keyboard(i18n, student_id)

        assert len(keyboard.inline_keyboard) == ROWS_TYPE_KEYBOARD
        assert keyboard.inline_keyboard[0][0].callback_data == f"assign:type:text:{student_id}"
        assert keyboard.inline_keyboard[1][0].callback_data == f"assign:type:mc:{student_id}"
        assert keyboard.inline_keyboard[2][0].callback_data == f"assign:type:voice:{student_id}"
        assert keyboard.inline_keyboard[3][0].callback_data == f"teaching:student:{student_id}"


class TestGetAssignmentMethodKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        student_id = uuid4()
        assignment_type = "text"

        keyboard = get_assignment_method_keyboard(i18n, student_id, assignment_type)

        assert len(keyboard.inline_keyboard) == ROWS_METHOD_KEYBOARD
        assert keyboard.inline_keyboard[0][0].callback_data == f"assign:ai:{assignment_type}:{student_id}"
        assert keyboard.inline_keyboard[1][0].callback_data == f"assign:manual:{assignment_type}:{student_id}"
        assert keyboard.inline_keyboard[2][0].callback_data == f"assign:new:{student_id}"


class TestGetDifficultyKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        student_id = uuid4()
        assignment_type = "text"

        keyboard = get_difficulty_keyboard(i18n, student_id, assignment_type)

        assert len(keyboard.inline_keyboard) == ROWS_DIFFICULTY_KEYBOARD
        assert len(keyboard.inline_keyboard[0]) == BUTTONS_IN_DIFFICULTY_ROW

        # First row: easy, medium, hard
        assert keyboard.inline_keyboard[0][0].callback_data == f"assign:diff:easy:{assignment_type}:{student_id}"
        assert keyboard.inline_keyboard[0][1].callback_data == f"assign:diff:medium:{assignment_type}:{student_id}"
        assert keyboard.inline_keyboard[0][2].callback_data == f"assign:diff:hard:{assignment_type}:{student_id}"
        # Back row
        assert keyboard.inline_keyboard[1][0].callback_data == f"assign:type:{assignment_type}:{student_id}"


class TestGetAssignmentListKeyboard:
    def test_empty_list(self) -> None:
        i18n = create_mock_i18n()
        assignments: list[AssignmentSummaryDTO] = []

        keyboard = get_assignment_list_keyboard(i18n, assignments, is_teacher=True)

        # Only back button
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:dashboard"

    def test_single_assignment(self) -> None:
        i18n = create_mock_i18n()
        assignments = [create_mock_assignment_summary()]

        keyboard = get_assignment_list_keyboard(i18n, assignments, is_teacher=True)

        # Assignment + back
        assert len(keyboard.inline_keyboard) == ROWS_SINGLE_ASSIGNMENT
        callback_data = keyboard.inline_keyboard[0][0].callback_data
        assert callback_data is not None
        assert "assign:view:" in callback_data

    def test_pagination_not_shown_for_few(self) -> None:
        i18n = create_mock_i18n()
        assignments = [create_mock_assignment_summary() for _ in range(3)]

        keyboard = get_assignment_list_keyboard(i18n, assignments, is_teacher=True)

        # 3 assignments + back
        assert len(keyboard.inline_keyboard) == ROWS_THREE_ASSIGNMENTS
        # No noop (page indicator)
        for row in keyboard.inline_keyboard:
            for button in row:
                assert button.callback_data != "noop"

    def test_pagination_shown_for_many(self) -> None:
        i18n = create_mock_i18n()
        assignments = [create_mock_assignment_summary() for _ in range(7)]

        keyboard = get_assignment_list_keyboard(i18n, assignments, page=0, is_teacher=True)

        # 5 assignments + pagination + back
        assert len(keyboard.inline_keyboard) == ROWS_MANY_WITH_PAGINATION
        pagination_row = keyboard.inline_keyboard[5]
        has_noop = any(btn.callback_data == "noop" for btn in pagination_row)
        assert has_noop

    def test_back_button_for_student(self) -> None:
        i18n = create_mock_i18n()
        assignments = [create_mock_assignment_summary()]

        keyboard = get_assignment_list_keyboard(i18n, assignments, is_teacher=False)

        # Back should go to panel for students
        back_button = keyboard.inline_keyboard[-1][0]
        assert back_button.callback_data == "teaching:panel"

    def test_truncates_long_title(self) -> None:
        i18n = create_mock_i18n()
        long_title = "A" * (TITLE_MAX_LENGTH + 10)
        assignments = [create_mock_assignment_summary(title=long_title)]

        keyboard = get_assignment_list_keyboard(i18n, assignments, is_teacher=True)

        button_text = keyboard.inline_keyboard[0][0].text
        assert "..." in button_text


class TestGetAssignmentDetailKeyboard:
    def test_teacher_with_submission(self) -> None:
        i18n = create_mock_i18n()
        assignment = create_mock_assignment()

        keyboard = get_assignment_detail_keyboard(i18n, assignment, is_teacher=True, has_submission=True)

        assert len(keyboard.inline_keyboard) == ROWS_DETAIL_TEACHER_WITH_SUB
        callback_data = keyboard.inline_keyboard[0][0].callback_data
        assert callback_data is not None
        assert f"assign:submission:{assignment.id}" in callback_data

    def test_teacher_no_submission(self) -> None:
        i18n = create_mock_i18n()
        assignment = create_mock_assignment()

        keyboard = get_assignment_detail_keyboard(i18n, assignment, is_teacher=True, has_submission=False)

        assert len(keyboard.inline_keyboard) == ROWS_DETAIL_TEACHER_NO_SUB
        assert keyboard.inline_keyboard[0][0].callback_data == "assign:list"

    def test_student_published(self) -> None:
        i18n = create_mock_i18n()
        assignment = create_mock_assignment(status=AssignmentStatus.PUBLISHED)

        keyboard = get_assignment_detail_keyboard(i18n, assignment, is_teacher=False, has_submission=False)

        assert len(keyboard.inline_keyboard) == ROWS_DETAIL_STUDENT_PUBLISHED
        callback_data = keyboard.inline_keyboard[0][0].callback_data
        assert callback_data is not None
        assert f"assign:start:{assignment.id}" in callback_data

    def test_student_submitted_no_result(self) -> None:
        i18n = create_mock_i18n()
        assignment = create_mock_assignment(status=AssignmentStatus.SUBMITTED)

        keyboard = get_assignment_detail_keyboard(i18n, assignment, is_teacher=False, has_submission=False)

        # Only back button when submitted but no submission to view
        assert len(keyboard.inline_keyboard) == ROWS_DETAIL_STUDENT_SUBMITTED
        assert keyboard.inline_keyboard[0][0].callback_data == "assign:pending"

    def test_student_graded_with_submission(self) -> None:
        i18n = create_mock_i18n()
        assignment = create_mock_assignment(status=AssignmentStatus.GRADED)

        keyboard = get_assignment_detail_keyboard(i18n, assignment, is_teacher=False, has_submission=True)

        assert len(keyboard.inline_keyboard) == ROWS_DETAIL_STUDENT_GRADED
        callback_data = keyboard.inline_keyboard[0][0].callback_data
        assert callback_data is not None
        assert f"assign:result:{assignment.id}" in callback_data


class TestGetSubmissionReviewKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        submission_id = uuid4()

        keyboard = get_submission_review_keyboard(i18n, submission_id)

        assert len(keyboard.inline_keyboard) == ROWS_SUBMISSION_REVIEW
        callback_data = keyboard.inline_keyboard[0][0].callback_data
        assert callback_data is not None
        assert f"assign:grade:{submission_id}" in callback_data
        assert keyboard.inline_keyboard[1][0].callback_data == "assign:list"


class TestGetGradeKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        submission_id = uuid4()

        keyboard = get_grade_keyboard(i18n, submission_id)

        assert len(keyboard.inline_keyboard) == ROWS_GRADE
        assert len(keyboard.inline_keyboard[0]) == BUTTONS_IN_GRADE_ROW

        # Check grade buttons
        for i in range(1, 6):
            assert keyboard.inline_keyboard[0][i - 1].text == str(i)
            assert keyboard.inline_keyboard[0][i - 1].callback_data == f"assign:rate:{i}:{submission_id}"


class TestGetAnswerCancelKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()

        keyboard = get_answer_cancel_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_CANCEL
        assert keyboard.inline_keyboard[0][0].callback_data == "assign:pending"


class TestGetTopicCancelKeyboard:
    def test_keyboard_structure(self) -> None:
        i18n = create_mock_i18n()
        student_id = uuid4()
        assignment_type = "text"

        keyboard = get_topic_cancel_keyboard(i18n, student_id, assignment_type)

        assert len(keyboard.inline_keyboard) == ROWS_CANCEL
        assert keyboard.inline_keyboard[0][0].callback_data == f"assign:type:{assignment_type}:{student_id}"


class TestStatusIcon:
    def test_published(self) -> None:
        assert _get_status_icon(AssignmentStatus.PUBLISHED) == ""

    def test_submitted(self) -> None:
        assert _get_status_icon(AssignmentStatus.SUBMITTED) == "!"

    def test_graded(self) -> None:
        assert _get_status_icon(AssignmentStatus.GRADED) == "+"


class TestTypeIcon:
    def test_text(self) -> None:
        assert _get_type_icon(AssignmentType.TEXT) == "T"

    def test_multiple_choice(self) -> None:
        assert _get_type_icon(AssignmentType.MULTIPLE_CHOICE) == "?"

    def test_voice(self) -> None:
        assert _get_type_icon(AssignmentType.VOICE) == "V"
