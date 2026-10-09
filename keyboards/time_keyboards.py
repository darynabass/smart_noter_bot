"""
@package keyboards
@brief Module for inline keyboards handling time settings and reminder notification controls.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def quick_time_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """
    @brief Creates a keyboard offering pre-defined relative time slots.

    @param prefix Callback prefix string to differentiate caller routing.
    @return Inline keyboard containing time presets.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="In 15 min",
                callback_data=f"{prefix}:15m"
            ),
            InlineKeyboardButton(
                text="In 30 min",
                callback_data=f"{prefix}:30m"
            )
        ],
        [
            InlineKeyboardButton(
                text="In 1 hr",
                callback_data=f"{prefix}:1h"
            ),
            InlineKeyboardButton(
                text="In 3 hrs",
                callback_data=f"{prefix}:3h"
            )
        ],
        [
            InlineKeyboardButton(
                text="Tomorrow at 09:00",
                callback_data=f"{prefix}:tomorrow_9"
            ),
            InlineKeyboardButton(
                text="Tomorrow at 18:00",
                callback_data=f"{prefix}:tomorrow_18"
            )
        ]
    ])


def reminder_notification_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """
    @brief Creates an action keyboard attached to sent reminder notifications.

    @param item_id Identifier of target reminder item.
    @return Inline keyboard offering Done and Snooze controls.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Done",
                callback_data=f"reminder_done:{item_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏳ 5 min",
                callback_data=f"reminder_snooze:{item_id}:5"
            ),
            InlineKeyboardButton(
                text="⏳ 15 min",
                callback_data=f"reminder_snooze:{item_id}:15"
            ),
            InlineKeyboardButton(
                text="⏳ 30 min",
                callback_data=f"reminder_snooze:{item_id}:30"
            ),
            InlineKeyboardButton(
                text="⏳ 60 min",
                callback_data=f"reminder_snooze:{item_id}:60"
            )
        ]
    ])