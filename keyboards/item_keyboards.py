"""
@package keyboards
@brief Module for inline keyboards associated with viewing and managing single/multiple items.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.pagination import get_page_items, pagination_arrows_row, pagination_row
from utils.constants import (
    ITEM_TYPE_NOTE,
    ITEM_TYPE_REMINDER,
    STATUS_COMPLETED,
)
from utils.text_utils import ITEM_BUTTON_TEXT_LENGTH, cut_text


def items_keyboard(items: list[dict], list_id: int, page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard listing items belonging to a specific list.

    @param items Item dictionary collection.
    @param list_id Target list identifier.
    @param page Current page index.
    @return Inline keyboard containing items and pagination controls.
    """
    page_items, page, total_pages = get_page_items(items, page)

    keyboard = []

    for item in page_items:
        icon = "📝" if item["item_type"] == ITEM_TYPE_NOTE else "⏰"
        short_text = cut_text(item["text"], ITEM_BUTTON_TEXT_LENGTH)
        status = "✅" if item["status"] == STATUS_COMPLETED else ""

        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {status} {short_text}",
                callback_data=f"item_open:{item['id']}"
            )
        ])

    keyboard.append(
        pagination_row(
            page=page,
            total_pages=total_pages,
            back_callback="lists_view",
            prev_callback=f"items_page:{list_id}:{page - 1}",
            next_callback=f"items_page:{list_id}:{page + 1}"
        )
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def item_actions_keyboard(
    item_id: int,
    item_type: str,
    status: str,
    list_id: int | None = None,
    page: int = 0,
    back_callback: str | None = None
) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard containing contextual actions for a specific item.

    @param item_id Unique identifier of the item.
    @param item_type Type of the item ('note' or 'reminder').
    @param status Current status of the item.
    @param list_id Associated list ID.
    @param page Page index to return to.
    @param back_callback Custom back navigation payload.
    @return Keyboard with edit, delete, and navigation options.
    """
    keyboard = []

    can_edit = not (item_type == ITEM_TYPE_REMINDER and status == STATUS_COMPLETED)

    if can_edit:
        keyboard.append([
            InlineKeyboardButton(text="✏️ Edit text", callback_data=f"item_edit:{item_id}")
        ])

        keyboard.append([
            InlineKeyboardButton(text="⭐ Change priority", callback_data=f"item_edit_priority:{item_id}")
        ])

    if item_type == ITEM_TYPE_REMINDER and status != STATUS_COMPLETED:
        keyboard.append([
            InlineKeyboardButton(text="🕒 Change time", callback_data=f"item_edit_time:{item_id}")
        ])

        keyboard.append([
            InlineKeyboardButton(text="✅ Mark as completed", callback_data=f"item_done:{item_id}")
        ])

    keyboard.append([
        InlineKeyboardButton(text="🗑 Delete", callback_data=f"item_delete:{item_id}")
    ])

    if back_callback is None:
        if list_id is not None:
            back_callback = f"items_page:{list_id}:{page}"
        else:
            back_callback = "lists_view"

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Back to items",
            callback_data=back_callback
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_delete_item_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """
    @brief Creates a confirmation keyboard for deleting an item.

    @param item_id Item ID to confirm deletion for.
    @return Keyboard with confirm/cancel buttons.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Yes, delete",
                callback_data=f"item_delete_confirm:{item_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=f"item_delete_cancel:{item_id}"
            )
        ]
    ])


def back_to_item_keyboard(item_id: int, new_message: bool = False) -> InlineKeyboardMarkup:
    """
    @brief Creates a navigation keyboard returning to the item detail view.

    @param item_id Target item identifier.
    @param new_message Whether action requires sending a new message.
    @return Keyboard containing back button.
    """
    callback_data = f"item_open_new:{item_id}" if new_message else f"item_open:{item_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=callback_data
            )
        ]
    ])


def notes_keyboard(items: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a paginated keyboard list of notes.

    @param items Collection of note items.
    @param page Current page index.
    @return Paginated notes list keyboard.
    """
    page_items, page, total_pages = get_page_items(items, page)

    keyboard = []

    for item in page_items:
        short_text = cut_text(item["text"], ITEM_BUTTON_TEXT_LENGTH)

        keyboard.append([
            InlineKeyboardButton(
                text=f"📝 {short_text}",
                callback_data=f"item_open:{item['id']}"
            )
        ])

    navigation = pagination_arrows_row(
        page=page,
        total_pages=total_pages,
        prev_callback=f"notes_page:{page - 1}",
        next_callback=f"notes_page:{page + 1}"
    )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def reminders_keyboard(items: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a paginated keyboard list of reminders.

    @param items Collection of reminder items.
    @param page Current page index.
    @return Paginated reminders list keyboard.
    """
    page_items, page, total_pages = get_page_items(items, page)

    keyboard = []

    for item in page_items:
        short_text = cut_text(item["text"], ITEM_BUTTON_TEXT_LENGTH)
        remind_at = item["remind_at"] if item["remind_at"] else "—"
        status_icon = "✅" if item["status"] == STATUS_COMPLETED else "⏰"

        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {short_text} | {remind_at}",
                callback_data=f"item_open:{item['id']}"
            )
        ])

    navigation = pagination_arrows_row(
        page=page,
        total_pages=total_pages,
        prev_callback=f"reminders_page:{page - 1}",
        next_callback=f"reminders_page:{page + 1}"
    )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def edit_priority_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard for selecting a new priority for an existing item.

    @param item_id Target item identifier.
    @return Inline keyboard with priority options.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" ⭐ ⭐ ⭐", callback_data=f"item_priority:{item_id}:high")],
        [InlineKeyboardButton(text=" ⭐ ⭐", callback_data=f"item_priority:{item_id}:medium")],
        [InlineKeyboardButton(text=" ⭐", callback_data=f"item_priority:{item_id}:low")],
        [InlineKeyboardButton(text="No priority", callback_data=f"item_priority:{item_id}:none")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data=f"item_open:{item_id}")]
    ])


def back_after_delete_keyboard(source: str, list_id: int | None = None, page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard to navigate back after an item deletion.

    @param source Origin view source ('notes', 'reminders', 'lists').
    @param list_id Target list ID if originating from list view.
    @param page Previous active page number.
    @return Back navigation inline keyboard.
    """
    if source == "notes":
        callback_data = f"notes_page_new:{page}"
    elif source == "reminders":
        callback_data = f"reminders_page_new:{page}"
    elif source == "lists" and list_id is not None:
        callback_data = f"items_page_new:{list_id}:{page}"
    else:
        callback_data = "lists_view"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Back to items",
                callback_data=callback_data
            )
        ]
    ])