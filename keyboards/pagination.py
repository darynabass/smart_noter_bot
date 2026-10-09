"""
@package keyboards
@brief Module containing helper functions and layout generators for pagination.
"""

from aiogram.types import InlineKeyboardButton

## Number of records rendered per page.
PAGE_SIZE: int = 5


def get_page_items(items: list, page: int) -> tuple[list, int, int]:
    """
    @brief Calculates pagination limits and extracts slice for current page.

    @param items Complete collection of elements.
    @param page Target page index.
    @return A tuple containing:
            - Sublist of items for the page.
            - Adjusted valid page index.
            - Total computed pages count.
    """
    total_pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    return items[start:end], page, total_pages


def pagination_row(
    page: int, 
    total_pages: int, 
    back_callback: str, 
    prev_callback: str, 
    next_callback: str
) -> list[InlineKeyboardButton]:
    """
    @brief Generates a standard pagination row with Back, Previous, and Next buttons.

    @param page Current page index.
    @param total_pages Total number of pages.
    @param back_callback Callback string for Back button.
    @param prev_callback Callback string for Previous page button.
    @param next_callback Callback string for Next page button.
    @return List of inline buttons forming the navigation row.
    """
    row = [
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=back_callback
        )
    ]

    if page > 0:
        row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=prev_callback
            )
        )

    if page < total_pages - 1:
        row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=next_callback
            )
        )

    return row


def pagination_arrows_row(
    page: int,
    total_pages: int,
    prev_callback: str,
    next_callback: str
) -> list[InlineKeyboardButton]:
    """
    @brief Generates a simplified pagination row consisting only of arrow buttons.

    @param page Current page index.
    @param total_pages Total page count.
    @param prev_callback Callback string for Previous button.
    @param next_callback Callback string for Next button.
    @return List containing active arrow buttons.
    """
    row = []

    if page > 0:
        row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=prev_callback
            )
        )

    if page < total_pages - 1:
        row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=next_callback
            )
        )

    return row