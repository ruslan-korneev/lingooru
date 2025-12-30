from collections.abc import Sequence
from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from src.modules.teaching.dto import TeacherStudentWithUserDTO


def get_role_selection_keyboard(
    i18n: I18nContext,
    *,
    is_teacher: bool,
    has_teacher: bool,
) -> InlineKeyboardMarkup:
    """Keyboard for selecting role (teacher or student)."""
    builder = InlineKeyboardBuilder()

    if is_teacher:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-dashboard"),
                callback_data="teaching:dashboard",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-become-teacher"),
                callback_data="teaching:become",
            ),
        )

    if has_teacher:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-my-teacher"),
                callback_data="teaching:panel",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-join-teacher"),
                callback_data="teaching:join",
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="menu:main",
        ),
    )
    return builder.as_markup()


def get_teacher_dashboard_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for teacher dashboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-students"),
            callback_data="teaching:students",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-assignments"),
            callback_data="assign:list",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-invite"),
            callback_data="teaching:invite",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="teaching:role",
        ),
    )
    return builder.as_markup()


def get_student_list_keyboard(
    i18n: I18nContext,
    students: Sequence[TeacherStudentWithUserDTO],
    page: int = 0,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """Keyboard for student list with pagination."""
    builder = InlineKeyboardBuilder()

    total = len(students)
    start = page * page_size
    end = min(start + page_size, total)
    page_students = list(students)[start:end]

    for student in page_students:
        name = student.first_name or student.username or i18n.get("unknown-user")
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {name}",
                callback_data=f"teaching:student:{student.user_id}",
            ),
        )

    # Pagination
    total_pages = (total + page_size - 1) // page_size
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"teaching:students:{page - 1}",
                ),
            )
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="noop",
            ),
        )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"teaching:students:{page + 1}",
                ),
            )
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="teaching:dashboard",
        ),
    )
    return builder.as_markup()


def get_student_detail_keyboard(
    i18n: I18nContext,
    student_id: UUID,
) -> InlineKeyboardMarkup:
    """Keyboard for student detail view."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-new-assignment"),
            callback_data=f"assign:new:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-remove-student"),
            callback_data=f"teaching:remove:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="teaching:students",
        ),
    )
    return builder.as_markup()


def get_student_panel_keyboard(
    i18n: I18nContext,
    *,
    has_teacher: bool,
) -> InlineKeyboardMarkup:
    """Keyboard for student panel (my teacher view)."""
    builder = InlineKeyboardBuilder()
    if has_teacher:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-my-assignments"),
                callback_data="assign:pending",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text=i18n.get("btn-leave-teacher"),
                callback_data="teaching:leave",
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="teaching:role",
        ),
    )
    return builder.as_markup()


def get_invite_keyboard(
    i18n: I18nContext,
) -> InlineKeyboardMarkup:
    """Keyboard for invite code view."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-regenerate"),
            callback_data="teaching:regenerate",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="teaching:dashboard",
        ),
    )
    return builder.as_markup()


def get_confirm_remove_keyboard(
    i18n: I18nContext,
    student_id: UUID,
) -> InlineKeyboardMarkup:
    """Keyboard for confirming student removal."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-confirm"),
            callback_data=f"teaching:remove:confirm:{student_id}",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-cancel"),
            callback_data=f"teaching:student:{student_id}",
        ),
    )
    return builder.as_markup()


def get_confirm_leave_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for confirming leaving teacher."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-confirm"),
            callback_data="teaching:leave:confirm",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-cancel"),
            callback_data="teaching:panel",
        ),
    )
    return builder.as_markup()


def get_join_cancel_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for cancelling join flow."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-cancel"),
            callback_data="teaching:role",
        ),
    )
    return builder.as_markup()
