"""Keyboards for assignment functionality."""

from collections.abc import Sequence
from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext

from src.modules.teaching.dto import AssignmentReadDTO, AssignmentSummaryDTO
from src.modules.teaching.enums import AssignmentStatus, AssignmentType

PAGE_SIZE = 5
TITLE_MAX_LENGTH = 20


def get_assignment_type_keyboard(
    i18n: I18nContext,
    student_id: UUID,
) -> InlineKeyboardMarkup:
    """Keyboard for selecting assignment type."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-type-text"),
            callback_data=f"assign:type:text:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-type-mc"),
            callback_data=f"assign:type:mc:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-type-voice"),
            callback_data=f"assign:type:voice:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=f"teaching:student:{student_id}",
        ),
    )
    return builder.as_markup()


def get_assignment_method_keyboard(
    i18n: I18nContext,
    student_id: UUID,
    assignment_type: str,
) -> InlineKeyboardMarkup:
    """Keyboard for choosing AI or manual creation."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-method-ai"),
            callback_data=f"assign:ai:{assignment_type}:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-method-manual"),
            callback_data=f"assign:manual:{assignment_type}:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=f"assign:new:{student_id}",
        ),
    )
    return builder.as_markup()


def get_difficulty_keyboard(
    i18n: I18nContext,
    student_id: UUID,
    assignment_type: str,
) -> InlineKeyboardMarkup:
    """Keyboard for selecting difficulty level."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-easy"),
            callback_data=f"assign:diff:easy:{assignment_type}:{student_id}",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-medium"),
            callback_data=f"assign:diff:medium:{assignment_type}:{student_id}",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn-hard"),
            callback_data=f"assign:diff:hard:{assignment_type}:{student_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=f"assign:type:{assignment_type}:{student_id}",
        ),
    )
    return builder.as_markup()


def get_assignment_list_keyboard(
    i18n: I18nContext,
    assignments: Sequence[AssignmentSummaryDTO],
    page: int = 0,
    *,
    is_teacher: bool,
) -> InlineKeyboardMarkup:
    """Keyboard for listing assignments with pagination."""
    builder = InlineKeyboardBuilder()

    total = len(assignments)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_assignments = list(assignments)[start:end]

    for assignment in page_assignments:
        status_icon = _get_status_icon(assignment.status)
        type_icon = _get_type_icon(assignment.assignment_type)
        title = (
            assignment.title[:TITLE_MAX_LENGTH] + "..."
            if len(assignment.title) > TITLE_MAX_LENGTH
            else assignment.title
        )
        builder.row(
            InlineKeyboardButton(
                text=f"{status_icon}{type_icon} {title}",
                callback_data=f"assign:view:{assignment.id}",
            ),
        )

    # Pagination
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="<",
                    callback_data=f"assign:page:{page - 1}",
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
                    text=">",
                    callback_data=f"assign:page:{page + 1}",
                ),
            )
        builder.row(*nav_buttons)

    back_callback = "teaching:dashboard" if is_teacher else "teaching:panel"
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=back_callback,
        ),
    )
    return builder.as_markup()


def get_assignment_detail_keyboard(
    i18n: I18nContext,
    assignment: AssignmentReadDTO,
    *,
    is_teacher: bool,
    has_submission: bool = False,
) -> InlineKeyboardMarkup:
    """Keyboard for assignment detail view."""
    builder = InlineKeyboardBuilder()

    if is_teacher:
        if has_submission:
            builder.row(
                InlineKeyboardButton(
                    text=i18n.get("btn-view-submission"),
                    callback_data=f"assign:submission:{assignment.id}",
                ),
            )
        back_callback = "assign:list"
    else:
        if assignment.status == AssignmentStatus.PUBLISHED:
            builder.row(
                InlineKeyboardButton(
                    text=i18n.get("btn-start-assignment"),
                    callback_data=f"assign:start:{assignment.id}",
                ),
            )
        elif has_submission:
            builder.row(
                InlineKeyboardButton(
                    text=i18n.get("btn-view-result"),
                    callback_data=f"assign:result:{assignment.id}",
                ),
            )
        back_callback = "assign:pending"

    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=back_callback,
        ),
    )
    return builder.as_markup()


def get_submission_review_keyboard(
    i18n: I18nContext,
    submission_id: UUID,
) -> InlineKeyboardMarkup:
    """Keyboard for reviewing submission."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-grade"),
            callback_data=f"assign:grade:{submission_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data="assign:list",
        ),
    )
    return builder.as_markup()


def get_grade_keyboard(
    i18n: I18nContext,
    submission_id: UUID,
) -> InlineKeyboardMarkup:
    """Keyboard for grading (1-5 buttons)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1", callback_data=f"assign:rate:1:{submission_id}"),
        InlineKeyboardButton(text="2", callback_data=f"assign:rate:2:{submission_id}"),
        InlineKeyboardButton(text="3", callback_data=f"assign:rate:3:{submission_id}"),
        InlineKeyboardButton(text="4", callback_data=f"assign:rate:4:{submission_id}"),
        InlineKeyboardButton(text="5", callback_data=f"assign:rate:5:{submission_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-back"),
            callback_data=f"assign:submission:{submission_id}",
        ),
    )
    return builder.as_markup()


def get_answer_cancel_keyboard(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Keyboard for cancelling answer flow."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-cancel"),
            callback_data="assign:pending",
        ),
    )
    return builder.as_markup()


def get_topic_cancel_keyboard(
    i18n: I18nContext,
    student_id: UUID,
    assignment_type: str,
) -> InlineKeyboardMarkup:
    """Keyboard for cancelling topic input."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("btn-cancel"),
            callback_data=f"assign:type:{assignment_type}:{student_id}",
        ),
    )
    return builder.as_markup()


def _get_status_icon(status: AssignmentStatus) -> str:
    """Get icon for assignment status."""
    icons = {
        AssignmentStatus.PUBLISHED: "",
        AssignmentStatus.SUBMITTED: "!",
        AssignmentStatus.GRADED: "+",
    }
    return icons.get(status, "")


def _get_type_icon(assignment_type: AssignmentType) -> str:
    """Get icon for assignment type."""
    icons = {
        AssignmentType.TEXT: "T",
        AssignmentType.MULTIPLE_CHOICE: "?",
        AssignmentType.VOICE: "V",
    }
    return icons.get(assignment_type, "")
