"""
@package handlers
@brief Module for handling user onboarding, start commands, and help documentation.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.queries import get_or_create_user
from keyboards.main_menu import main_menu
from utils.message_utils import remove_old_inline_keyboard

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    """
    @brief Handles the /start command to register user and show welcome message.

    @param message Telegram message object.
    @param state Finite State Machine context.
    """
    await state.clear()

    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    await message.answer(
        "Welcome! I am a bot for organizing notes and reminders.\n\n"
        "Press ➕ to add an entry.",
        reply_markup=main_menu
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Help")
async def help_message(message: Message, state: FSMContext) -> None:
    """
    @brief Displays system instructions and help information.

    @param message Telegram message object.
    @param state Finite State Machine context.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    await message.answer(
        "ℹ️ Help\n\n"
        "➕ Add (/add) — create a note or reminder.\n"
        "📋 Lists (/lists) — view lists, create or delete a list.\n"
        "📊 Statistics (/stats) — view count of notes, reminders, and completed tasks.\n"
        "⏰ Reminders (/reminders) — view, edit, or mark a reminder as completed.\n"
        "📝 Notes (/notes) — view or edit notes.\n\n"
        "Notes are automatically saved to the «Notes» list.\n"
        "For reminders, you can choose a separate list.\n"
        "Time can be selected using quick buttons or specified as 'in X minutes/hours/days' and 'today/tomorrow/day after tomorrow at HH/HH:MM'.\n",
        reply_markup=main_menu
    )