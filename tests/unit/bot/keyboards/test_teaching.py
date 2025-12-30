"""Tests for teaching keyboards."""

from unittest.mock import MagicMock
from uuid import uuid4

from aiogram_i18n import I18nContext

from src.bot.keyboards.teaching import (
    get_confirm_leave_keyboard,
    get_confirm_remove_keyboard,
    get_invite_keyboard,
    get_join_cancel_keyboard,
    get_role_selection_keyboard,
    get_student_detail_keyboard,
    get_student_list_keyboard,
    get_student_panel_keyboard,
    get_teacher_dashboard_keyboard,
)
from src.modules.teaching.dto import TeacherStudentWithUserDTO
from src.modules.teaching.enums import TeacherStudentStatus

# Expected keyboard row counts
ROWS_ROLE_NOT_TEACHER_NO_TEACHER = 3  # become + join + back
ROWS_ROLE_IS_TEACHER_NO_TEACHER = 3  # dashboard + join + back
ROWS_ROLE_NOT_TEACHER_HAS_TEACHER = 3  # become + panel + back
ROWS_ROLE_IS_TEACHER_HAS_TEACHER = 3  # dashboard + panel + back

ROWS_DASHBOARD = 3  # students+assignments, invite, back
ROWS_STUDENT_DETAIL = 3  # assignment, remove, back
ROWS_PANEL_WITH_TEACHER = 3  # assignments, leave, back
ROWS_PANEL_NO_TEACHER = 1  # back only
ROWS_INVITE = 2  # regenerate, back
ROWS_CONFIRM = 1  # confirm + cancel in one row
ROWS_CANCEL = 1  # cancel only

# Pagination constants
PAGE_SIZE = 5

# Dynamic row counts
ROWS_SINGLE_STUDENT_LIST = 2  # student + back
ROWS_THREE_STUDENTS_LIST = 4  # 3 students + back
ROWS_MANY_STUDENTS_PAGE = 7  # 5 students + pagination + back
ROWS_SECOND_PAGE = 4  # 2 students + pagination + back
BUTTONS_IN_CONFIRM_ROW = 2  # confirm + cancel


def create_mock_i18n() -> MagicMock:
    """Create a mock I18nContext."""
    i18n = MagicMock(spec=I18nContext)
    i18n.get = MagicMock(side_effect=lambda key, **_: f"[{key}]")
    return i18n


def create_mock_students(count: int) -> list[TeacherStudentWithUserDTO]:
    """Create mock students list."""
    return [
        TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username=f"student{i}",
            first_name=f"Student {i}",
            status=TeacherStudentStatus.ACTIVE,
        )
        for i in range(count)
    ]


class TestGetRoleSelectionKeyboard:
    """Tests for get_role_selection_keyboard function."""

    def test_not_teacher_no_teacher(self) -> None:
        """Shows become teacher and join buttons."""
        i18n = create_mock_i18n()

        keyboard = get_role_selection_keyboard(i18n, is_teacher=False, has_teacher=False)

        assert len(keyboard.inline_keyboard) == ROWS_ROLE_NOT_TEACHER_NO_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:become"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:join"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"

    def test_is_teacher_no_teacher(self) -> None:
        """Shows dashboard and join buttons when teacher."""
        i18n = create_mock_i18n()

        keyboard = get_role_selection_keyboard(i18n, is_teacher=True, has_teacher=False)

        assert len(keyboard.inline_keyboard) == ROWS_ROLE_IS_TEACHER_NO_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:dashboard"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:join"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"

    def test_not_teacher_has_teacher(self) -> None:
        """Shows become teacher and panel buttons when student."""
        i18n = create_mock_i18n()

        keyboard = get_role_selection_keyboard(i18n, is_teacher=False, has_teacher=True)

        assert len(keyboard.inline_keyboard) == ROWS_ROLE_NOT_TEACHER_HAS_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:become"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:panel"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"

    def test_is_teacher_has_teacher(self) -> None:
        """Shows dashboard and panel buttons when both."""
        i18n = create_mock_i18n()

        keyboard = get_role_selection_keyboard(i18n, is_teacher=True, has_teacher=True)

        assert len(keyboard.inline_keyboard) == ROWS_ROLE_IS_TEACHER_HAS_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:dashboard"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:panel"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:main"


class TestGetTeacherDashboardKeyboard:
    """Tests for get_teacher_dashboard_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with correct structure."""
        i18n = create_mock_i18n()

        keyboard = get_teacher_dashboard_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_DASHBOARD
        # First row: students and assignments
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:students"
        assert keyboard.inline_keyboard[0][1].callback_data == "assign:list"
        # Second row: invite
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:invite"
        # Third row: back
        assert keyboard.inline_keyboard[2][0].callback_data == "teaching:role"


class TestGetStudentListKeyboard:
    """Tests for get_student_list_keyboard function."""

    def test_empty_list(self) -> None:
        """Creates keyboard with only back button when empty."""
        i18n = create_mock_i18n()
        students: list[TeacherStudentWithUserDTO] = []

        keyboard = get_student_list_keyboard(i18n, students)

        # Only back button
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:dashboard"

    def test_single_student(self) -> None:
        """Creates keyboard with one student button."""
        i18n = create_mock_i18n()
        students = create_mock_students(1)

        keyboard = get_student_list_keyboard(i18n, students)

        # Student + back
        assert len(keyboard.inline_keyboard) == ROWS_SINGLE_STUDENT_LIST
        assert keyboard.inline_keyboard[0][0].callback_data == f"teaching:student:{students[0].user_id}"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:dashboard"

    def test_pagination_not_shown_for_few_students(self) -> None:
        """No pagination when students fit on one page."""
        i18n = create_mock_i18n()
        students = create_mock_students(3)

        keyboard = get_student_list_keyboard(i18n, students)

        # 3 students + back
        assert len(keyboard.inline_keyboard) == ROWS_THREE_STUDENTS_LIST
        # Check no pagination row (would have page indicator)
        for row in keyboard.inline_keyboard:
            for button in row:
                assert button.callback_data != "noop"

    def test_pagination_shown_for_many_students(self) -> None:
        """Pagination shown when students exceed page size."""
        i18n = create_mock_i18n()
        students = create_mock_students(7)  # More than PAGE_SIZE (5)

        keyboard = get_student_list_keyboard(i18n, students, page=0)

        # 5 students + pagination + back
        assert len(keyboard.inline_keyboard) == ROWS_MANY_STUDENTS_PAGE
        # Check pagination row has noop (page indicator)
        pagination_row = keyboard.inline_keyboard[5]
        has_noop = any(btn.callback_data == "noop" for btn in pagination_row)
        assert has_noop

    def test_second_page(self) -> None:
        """Second page shows remaining students."""
        i18n = create_mock_i18n()
        students = create_mock_students(7)

        keyboard = get_student_list_keyboard(i18n, students, page=1)

        # 2 students on page 2 + pagination + back
        assert len(keyboard.inline_keyboard) == ROWS_SECOND_PAGE
        # Check pagination has prev button
        pagination_row = keyboard.inline_keyboard[2]
        prev_buttons = [btn for btn in pagination_row if btn.callback_data == "teaching:students:0"]
        assert len(prev_buttons) == 1


class TestGetStudentDetailKeyboard:
    """Tests for get_student_detail_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with correct structure."""
        i18n = create_mock_i18n()
        student_id = uuid4()

        keyboard = get_student_detail_keyboard(i18n, student_id)

        assert len(keyboard.inline_keyboard) == ROWS_STUDENT_DETAIL
        # First row: new assignment
        assert keyboard.inline_keyboard[0][0].callback_data == f"assign:new:{student_id}"
        # Second row: remove
        assert keyboard.inline_keyboard[1][0].callback_data == f"teaching:remove:{student_id}"
        # Third row: back
        assert keyboard.inline_keyboard[2][0].callback_data == "teaching:students"


class TestGetStudentPanelKeyboard:
    """Tests for get_student_panel_keyboard function."""

    def test_with_teacher(self) -> None:
        """Creates full keyboard when has teacher."""
        i18n = create_mock_i18n()

        keyboard = get_student_panel_keyboard(i18n, has_teacher=True)

        assert len(keyboard.inline_keyboard) == ROWS_PANEL_WITH_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "assign:pending"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:leave"
        assert keyboard.inline_keyboard[2][0].callback_data == "teaching:role"

    def test_without_teacher(self) -> None:
        """Creates minimal keyboard when no teacher."""
        i18n = create_mock_i18n()

        keyboard = get_student_panel_keyboard(i18n, has_teacher=False)

        assert len(keyboard.inline_keyboard) == ROWS_PANEL_NO_TEACHER
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:role"


class TestGetInviteKeyboard:
    """Tests for get_invite_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with regenerate and back."""
        i18n = create_mock_i18n()

        keyboard = get_invite_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_INVITE
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:regenerate"
        assert keyboard.inline_keyboard[1][0].callback_data == "teaching:dashboard"


class TestGetConfirmRemoveKeyboard:
    """Tests for get_confirm_remove_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with confirm and cancel."""
        i18n = create_mock_i18n()
        student_id = uuid4()

        keyboard = get_confirm_remove_keyboard(i18n, student_id)

        assert len(keyboard.inline_keyboard) == ROWS_CONFIRM
        assert len(keyboard.inline_keyboard[0]) == BUTTONS_IN_CONFIRM_ROW
        assert keyboard.inline_keyboard[0][0].callback_data == f"teaching:remove:confirm:{student_id}"
        assert keyboard.inline_keyboard[0][1].callback_data == f"teaching:student:{student_id}"


class TestGetConfirmLeaveKeyboard:
    """Tests for get_confirm_leave_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with confirm and cancel."""
        i18n = create_mock_i18n()

        keyboard = get_confirm_leave_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_CONFIRM
        assert len(keyboard.inline_keyboard[0]) == BUTTONS_IN_CONFIRM_ROW
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:leave:confirm"
        assert keyboard.inline_keyboard[0][1].callback_data == "teaching:panel"


class TestGetJoinCancelKeyboard:
    """Tests for get_join_cancel_keyboard function."""

    def test_keyboard_structure(self) -> None:
        """Creates keyboard with cancel button."""
        i18n = create_mock_i18n()

        keyboard = get_join_cancel_keyboard(i18n)

        assert len(keyboard.inline_keyboard) == ROWS_CANCEL
        assert keyboard.inline_keyboard[0][0].callback_data == "teaching:role"
