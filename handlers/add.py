"""
@package handlers
@brief Router for handling the step-by-step creation flow for notes and reminders.

Guides the user through entering item text, specifying time/type, picking target lists,
and selecting priority using finite state machine (FSM).
"""

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database.queries import (
    create_item,
    get_list_by_name,
    get_or_create_user,
    get_reminder_lists,
)
from keyboards.add_keyboards import (
    priority_keyboard,
    select_list_keyboard,
    time_choice_keyboard,
)
from keyboards.main_menu import main_menu
from keyboards.time_keyboards import quick_time_keyboard
from utils.constants import (
    DEFAULT_NOTES_LIST,
    ITEM_TYPE_NOTE,
    ITEM_TYPE_REMINDER,
)
from utils.datetime_utils import get_quick_datetime, parse_user_datetime
from utils.message_utils import (
    remove_old_inline_keyboard,
    save_active_inline_message,
)
from utils.text_utils import (
    MAX_ITEM_TEXT_LENGTH,
    is_valid_item_text,
)

router = Router()


class AddItemStates(StatesGroup):
    """
    @brief FSM state definitions for the item creation process.
    """
    waiting_text = State()
    waiting_time_choice = State()
    waiting_datetime = State()
    waiting_list = State()
    waiting_priority = State()


@router.message(Command("add"))
@router.message(F.text == "➕ Add")
async def add_start(message: Message, state: FSMContext) -> None:
    """
    @brief Starts the item creation flow and prompts the user for text content.

    @param message Incoming Telegram Message instance.
    @param state FSM context.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    user_id = await get_or_create_user(
        message.from_user.id,
        message.from_user.username
    )

    await state.update_data(user_id=user_id)
    await state.set_state(AddItemStates.waiting_text)

    await message.answer("Enter item text:")


@router.message(AddItemStates.waiting_text)
async def add_text(message: Message, state: FSMContext) -> None:
    """
    @brief Validates item text input and asks whether to add a reminder time.

    @param message Incoming Telegram Message instance.
    @param state FSM context.
    """
    text = message.text.strip() if message.text else ""

    if not text:
        await message.answer("Text cannot be empty. Please enter item text:")
        return

    if not is_valid_item_text(text):
        await message.answer(
            f"Item text is too long. Maximum length is {MAX_ITEM_TEXT_LENGTH} characters."
        )
        return

    await state.update_data(text=text)
    await state.set_state(AddItemStates.waiting_time_choice)

    sent_message = await message.answer(
        "Add a reminder time?",
        reply_markup=time_choice_keyboard()
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(AddItemStates.waiting_time_choice, F.data == "add_time_no")
async def add_without_time(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles note option (no time attached) and prompts for priority.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    data = await state.get_data()
    user_id = data["user_id"]

    notes_list_id = await get_list_by_name(user_id, DEFAULT_NOTES_LIST)

    await state.update_data(
        item_type=ITEM_TYPE_NOTE,
        list_id=notes_list_id,
        remind_at=None
    )

    await state.set_state(AddItemStates.waiting_priority)

    sent_message = await callback.message.edit_text(
        "Select priority for the note:",
        reply_markup=priority_keyboard()
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(AddItemStates.waiting_time_choice, F.data == "add_time_yes")
async def add_with_time(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles reminder option and prompts for datetime input or quick presets.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    await state.set_state(AddItemStates.waiting_datetime)

    sent_message = await callback.message.edit_text(
        "Enter reminder date and time.\n"
        "You can write in natural language or format DD.MM.YYYY HH:MM.\n"
        "Example: 25.05.2026 14:30\n"
        "Or pick a quick option:",
        reply_markup=quick_time_keyboard("add_time_preset")
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(AddItemStates.waiting_datetime, F.data.startswith("add_time_preset:"))
async def add_time_preset(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles quick time selection button presses.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    preset = callback.data.split(":")[1]

    reminder_datetime = get_quick_datetime(preset)

    if not reminder_datetime:
        await callback.answer("Failed to parse reminder time.", show_alert=True)
        return

    data = await state.get_data()
    user_id = data["user_id"]

    lists = await get_reminder_lists(user_id)

    await state.update_data(
        item_type=ITEM_TYPE_REMINDER,
        remind_at=reminder_datetime.strftime("%Y-%m-%d %H:%M")
    )

    await state.set_state(AddItemStates.waiting_list)

    sent_message = await callback.message.edit_text(
        "Select a list for the reminder:",
        reply_markup=select_list_keyboard(lists, page=0)
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.message(AddItemStates.waiting_datetime)
async def add_datetime(message: Message, state: FSMContext) -> None:
    """
    @brief Validates manually typed datetime string and moves to list selection.

    @param message Incoming Telegram Message instance.
    @param state FSM context.
    """
    reminder_datetime = parse_user_datetime(message.text or "")

    if not reminder_datetime:
        await message.answer(
            "Invalid date format. Please try again.\n"
            "Example: 25.05.2026 14:30"
        )
        return

    if reminder_datetime <= datetime.now():
        await message.answer("Reminder time must be in the future. Please enter another date:")
        return

    data = await state.get_data()
    user_id = data["user_id"]

    lists = await get_reminder_lists(user_id)

    await state.update_data(
        item_type=ITEM_TYPE_REMINDER,
        remind_at=reminder_datetime.strftime("%Y-%m-%d %H:%M")
    )

    await state.set_state(AddItemStates.waiting_list)

    await remove_old_inline_keyboard(message, state)

    sent_message = await message.answer(
        "Select a list for the reminder:",
        reply_markup=select_list_keyboard(lists, page=0)
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(AddItemStates.waiting_list, F.data.startswith("select_list_page:"))
async def add_select_list_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles pagination for list selection inline keyboard.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    page = int(callback.data.split(":")[1])

    data = await state.get_data()
    user_id = data["user_id"]

    lists = await get_reminder_lists(user_id)

    sent_message = await callback.message.edit_text(
        "Select a list for the reminder:",
        reply_markup=select_list_keyboard(lists, page=page)
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(AddItemStates.waiting_list, F.data.startswith("select_list:"))
async def add_select_list(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Saves selected list ID and prompts for priority level selection.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    list_id = int(callback.data.split(":")[1])

    await state.update_data(list_id=list_id)
    await state.set_state(AddItemStates.waiting_priority)

    sent_message = await callback.message.edit_text(
        "Select priority:",
        reply_markup=priority_keyboard()
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(AddItemStates.waiting_priority, F.data.startswith("add_priority:"))
async def add_priority(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Finalizes priority selection, creates the item in DB, and completes FSM flow.

    @param callback Incoming CallbackQuery instance.
    @param state FSM context.
    """
    priority = callback.data.split(":", 1)[1]
    data = await state.get_data()

    user_id = data["user_id"]

    await create_item(
        user_id=user_id,
        list_id=data["list_id"],
        text=data["text"],
        item_type=data["item_type"],
        remind_at=data.get("remind_at"),
        priority=priority
    )

    await state.clear()

    if data["item_type"] == ITEM_TYPE_NOTE:
        await callback.message.edit_text("Note saved.")
    else:
        await callback.message.edit_text(
            f"Reminder saved.\n"
            f"Time: {data['remind_at']}",
        )

    await callback.message.answer(
        "Choose the next action:",
        reply_markup=main_menu
    )

    await callback.answer()