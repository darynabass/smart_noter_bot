"""
@package utils
@brief Module for text validation, trimming, and formatting limits.
"""

## Maximum allowed character length for an item (note/reminder) text.
MAX_ITEM_TEXT_LENGTH: int = 4000

## Maximum allowed character length for a list name.
MAX_LIST_NAME_LENGTH: int = 30

## Truncation length limit for items displayed in inline keyboard buttons.
ITEM_BUTTON_TEXT_LENGTH: int = 35

## Truncation length limit for list names displayed in inline keyboard buttons.
LIST_BUTTON_TEXT_LENGTH: int = 25


def is_valid_item_text(text: str) -> bool:
    """
    @brief Validates whether an item text length falls within allowed boundaries.

    @param text Raw input string to check.
    @return True if text length is between 1 and MAX_ITEM_TEXT_LENGTH, False otherwise.
    """
    return 1 <= len(text.strip()) <= MAX_ITEM_TEXT_LENGTH


def is_valid_list_name(name: str) -> bool:
    """
    @brief Validates whether a list name length falls within allowed boundaries.

    @param name Raw input list name to check.
    @return True if name length is between 2 and MAX_LIST_NAME_LENGTH, False otherwise.
    """
    return 2 <= len(name.strip()) <= MAX_LIST_NAME_LENGTH


def cut_text(text: str, max_length: int) -> str:
    """
    @brief Truncates a string to a specified length and appends an ellipsis if exceeded.

    @param text Target text to be truncated.
    @param max_length Maximum allowed character length before truncation.
    @return Truncated text with '...' appended if length exceeds limit, or original text.
    """
    text = text.strip()

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "..."