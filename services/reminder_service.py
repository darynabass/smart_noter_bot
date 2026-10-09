"""
@package services
@brief Background task worker for dispatching scheduled reminder notifications.

Runs an infinite loop checking for due reminders at configured intervals and sends
Telegram messages to recipient users.
"""

import asyncio
import logging

from aiogram import Bot

from database.queries import get_due_reminders, mark_item_status
from keyboards.time_keyboards import reminder_notification_keyboard
from utils.constants import REMINDER_CHECK_INTERVAL, STATUS_NOTIFIED
from utils.priority_utils import format_priority

logger = logging.getLogger(__name__)


async def reminder_worker(bot: Bot) -> None:
    """
    @brief Background worker that regularly scans for and sends pending reminders.

    @param bot Active aiogram Bot instance used for sending messages.
    """
    while True:
        try:
            reminders = await get_due_reminders()

            for reminder in reminders:
                try:
                    await bot.send_message(
                        chat_id=reminder["telegram_id"],
                        text=(
                            "🔔 Reminder\n\n"
                            f"{reminder['text']}\n\n"
                            f"Priority: {format_priority(reminder['priority'])}\n"
                            f"List: {reminder['list_name']}\n\n"
                            "Snooze for:"
                        ),
                        reply_markup=reminder_notification_keyboard(reminder["id"])
                    )

                    await mark_item_status(reminder["id"], STATUS_NOTIFIED)

                except Exception:
                    logger.exception(
                        "Failed to send reminder with id=%s",
                        reminder["id"]
                    )

        except Exception:
            logger.exception("Error occurred in background reminder service")

        await asyncio.sleep(REMINDER_CHECK_INTERVAL)