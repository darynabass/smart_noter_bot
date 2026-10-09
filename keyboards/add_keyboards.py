"""
@package keyboards
@brief Module for inline keyboards used during item creation workflows.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.pagination import get_page_items, pagination_arrows_row
from utils.text_utils import LIST_BUTTON_TEXT_LENGTH, cut_text


def time_choice_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard for choosing entry type (Reminder or Note).

    @return Keyboard with entry type choices.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, it's a reminder", callback_data="add_time_yes"),
            InlineKeyboardButton(text="No, it's a note", callback_data="add_time_no")
        ]
    ])


def priority_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard for selecting entry priority level.

    @return Keyboard containing priority options.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" ⭐ ⭐ ⭐", callback_data="add_priority:high")],
        [InlineKeyboardButton(text=" ⭐ ⭐", callback_data="add_priority:medium")],
        [InlineKeyboardButton(text=" ⭐", callback_data="add_priority:low")],
        [InlineKeyboardButton(text="No priority", callback_data="add_priority:none")]
    ])


def select_list_keyboard(lists: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a paginated keyboard for picking a target list.

    @param lists List of dictionaries representing list records.
    @param page Current active page index.
    @return Paginated inline keyboard with available lists.
    """
    page_lists, page, total_pages = get_page_items(lists, page)

    keyboard = []

    for item in page_lists:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{cut_text(item['name'], LIST_BUTTON_TEXT_LENGTH)} ({item['item_count']})",
                callback_data=f"select_list:{item['id']}"
            )
        ])

    pagination_buttons = pagination_arrows_row(
        page=page,
        total_pages=total_pages,
        prev_callback=f"select_list_page:{page - 1}",
        next_callback=f"select_list_page:{page + 1}"
    )

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)