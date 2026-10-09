"""
@package handlers
@brief Module for managing user reminders, including pagination, completion, and snoozing.
"""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.queries import (
    get_items_by_type,
    get_or_create_user,
    mark_item_completed,
    snooze_reminder,
)
from keyboards.item_keyboards import reminders_keyboard
from keyboards.main_menu import main_menu
from utils.constants import ITEM_TYPE_REMINDER, SOURCE_REMINDERS
from utils.message_utils import (
    remove_old_inline_keyboard,
    save_active_inline_message,
)

router = Router()


@router.message(Command("reminders"))
@router.message(F.text == "⏰ Reminders")
async def reminders_start(message: Message, state: FSMContext) -> None:
    """
    @brief Starts the reminders view from the main menu or via command.

    @param message Telegram message object from user.
    @param state Finite State Machine context.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    user_id = await get_or_create_user(
        message.from_user.id,
        message.from_user.username
    )

    items = await get_items_by_type(user_id, ITEM_TYPE_REMINDER)

    if not items:
        await message.answer("You don't have any reminders yet.", reply_markup=main_menu)
        return

    sent_message = await message.answer(
        "Select a reminder:",
        reply_markup=reminders_keyboard(items, page=0)
    )

    await state.update_data(
        current_list_id=None,
        current_items_page=0,
        current_items_source=SOURCE_REMINDERS
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(F.data.startswith("reminders_page:"))
async def reminders_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles pagination within the reminders list by editing the current message.

    @param callback Telegram callback query object.
    @param state Finite State Machine context.
    """
    page = int(callback.data.split(":")[1])

    user_id = await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username
    )

    items = await get_items_by_type(user_id, ITEM_TYPE_REMINDER)

    if not items:
        sent_message = await callback.message.edit_text(
            "You don't have any reminders yet.",
            reply_markup=main_menu
        )

        await save_active_inline_message(sent_message, state)
        await callback.answer()
        return

    sent_message = await callback.message.edit_text(
        "Select a reminder:",
        reply_markup=reminders_keyboard(items, page=page)
    )

    await state.update_data(
        current_list_id=None,
        current_items_page=page,
        current_items_source=SOURCE_REMINDERS
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("reminders_page_new:"))
async def reminders_page_new(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles returning to the reminders list by sending a new message.

    @param callback Telegram callback query object.
    @param state Finite State Machine context.
    """
    page = int(callback.data.split(":")[1])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    user_id = await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username
    )

    items = await get_items_by_type(user_id, ITEM_TYPE_REMINDER)

    await state.update_data(
        current_list_id=None,
        current_items_page=page,
        current_items_source=SOURCE_REMINDERS
    )

    if not items:
        await callback.message.answer("You don't have any reminders yet.", reply_markup=main_menu)
        await callback.answer()
        return

    sent_message = await callback.message.answer(
        "Select a reminder:",
        reply_markup=reminders_keyboard(items, page=page)
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_done:"))
async def reminder_done(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Marks a reminder as completed from a notification callback.

    @param callback Telegram callback query object.
    @param state Finite State Machine context.
    """
    user_id = await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username
    )

    item_id = int(callback.data.split(":")[1])

    await mark_item_completed(user_id, item_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        "Reminder marked as completed.",
        reply_markup=main_menu
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("reminder_snooze:"))
async def reminder_snooze(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Snoozes a reminder for a designated duration in minutes.

    @param callback Telegram callback query object.
    @param state Finite State Machine context.
    """
    data = callback.data.split(":")

    if len(data) != 3:
        await callback.answer("Invalid button data.", show_alert=True)
        return

    item_id = int(data[1])
    minutes = int(data[2])

    if minutes not in (5, 15, 30, 60):
        await callback.answer("Invalid snooze duration.", show_alert=True)
        return

    new_remind_at = datetime.now() + timedelta(minutes=minutes)
    new_remind_at_text = new_remind_at.strftime("%Y-%m-%d %H:%M")

    user_id = await get_or_create_user(
        callback.from_user.id,
        callback.from_user.username
    )

    updated = await snooze_reminder(
        user_id=user_id,
        item_id=item_id,
        new_remind_at=new_remind_at_text
    )

    if not updated:
        await callback.answer(
            "Reminder not found or already completed.",
            show_alert=True
        )
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        f"Reminder snoozed for {minutes} min.\n"
        f"New time: {new_remind_at_text}",
        reply_markup=main_menu
    )

    await state.clear()
    await callback.answer()