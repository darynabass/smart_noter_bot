"""
@package keyboards
@brief Module for inline keyboards handling list management, creation, and deletion.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.pagination import get_page_items, pagination_row
from utils.constants import DEFAULT_NOTES_LIST
from utils.text_utils import LIST_BUTTON_TEXT_LENGTH, cut_text


def list_menu_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates the main options menu keyboard for list management.

    @return Keyboard with View, Create, and Delete list options.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 View lists", callback_data="lists_view")],
        [InlineKeyboardButton(text="➕ Create list", callback_data="lists_create")],
        [InlineKeyboardButton(text="🗑 Delete list", callback_data="lists_delete")]
    ])


def open_lists_keyboard(lists: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a paginated keyboard displaying user lists.

    @param lists Collection of list records.
    @param page Current page index.
    @return Paginated inline keyboard of user lists.
    """
    page_lists, page, total_pages = get_page_items(lists, page)

    keyboard = []

    for item in page_lists:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{cut_text(item['name'], LIST_BUTTON_TEXT_LENGTH)} ({item['item_count']})",
                callback_data=f"open_list:{item['id']}"
            )
        ])

    keyboard.append(
        pagination_row(
            page=page,
            total_pages=total_pages,
            back_callback="lists_menu",
            prev_callback=f"lists_view_page:{page - 1}",
            next_callback=f"lists_view_page:{page + 1}"
        )
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_lists_menu_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates a back navigation keyboard targeting the lists menu.

    @return Keyboard containing back button.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="lists_menu")]
    ])


def back_to_lists_view_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates a back navigation keyboard targeting the main lists view.

    @return Keyboard containing back button.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="lists_view")]
    ])


def back_to_lists_menu_new_keyboard() -> InlineKeyboardMarkup:
    """
    @brief Creates a back keyboard targeting list menu via sending a new message.

    @return Keyboard containing back button with new message target.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="lists_menu_new")]
    ])


def delete_lists_keyboard(lists: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard displaying custom lists eligible for deletion.

    Filters out default system lists (e.g. Notes).

    @param lists Collection of list records.
    @param page Active page index.
    @return Deletable lists selection keyboard.
    """
    page_lists, page, total_pages = get_page_items(lists, page)

    keyboard = []

    for item in page_lists:
        if item["name"] != DEFAULT_NOTES_LIST:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑 {cut_text(item['name'], LIST_BUTTON_TEXT_LENGTH)} ({item['item_count']})",
                    callback_data=f"delete_list:{item['id']}:{page}"
                )
            ])

    keyboard.append(
        pagination_row(
            page=page,
            total_pages=total_pages,
            back_callback="lists_menu",
            prev_callback=f"lists_delete_page:{page - 1}",
            next_callback=f"lists_delete_page:{page + 1}"
        )
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_delete_list_keyboard(list_id: int, page: int) -> InlineKeyboardMarkup:
    """
    @brief Creates a confirmation keyboard for deleting a list.

    @param list_id ID of list to delete.
    @param page Previous page index for returning upon cancellation.
    @return Confirmation inline keyboard.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Yes, delete",
                callback_data=f"delete_list_confirm:{list_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=f"lists_delete_page:{page}"
            )
        ]
    ])