"""
@package handlers
@brief Module for computing and presenting user analytical statistics.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.queries import get_or_create_user, get_stats
from keyboards.main_menu import main_menu
from utils.message_utils import remove_old_inline_keyboard

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Statistics")
async def show_stats(message: Message, state: FSMContext) -> None:
    """
    @brief Displays user usage statistics and completion rates.

    @param message Telegram message object.
    @param state Finite State Machine context.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    user_id = await get_or_create_user(message.from_user.id, message.from_user.username)
    stats = await get_stats(user_id)

    reminders = stats["reminders"]
    completed = stats["completed"]
    completed_on_time = stats["completed_on_time"]

    completion_rate = 0 if reminders == 0 else round(completed / reminders * 100, 1)
    on_time_rate = 0 if completed == 0 else round(completed_on_time / completed * 100, 1)

    await message.answer(
        "📊 Statistics\n\n"
        f"Notes: {stats['notes']}\n"
        f"Total Reminders: {stats['reminders']}\n"
        f"Active Reminders: {stats['active']}\n"
        f"Sent but Pending: {stats['notified']}\n"
        f"Completed Reminders: {stats['completed']}\n"
        f"Completed On Time: {stats['completed_on_time']}\n"
        f"Reminder Lists: {stats['lists']}\n"
        f"Completion Rate: {completion_rate}%\n"
        f"On-Time Rate: {on_time_rate}%",
        reply_markup=main_menu
    )