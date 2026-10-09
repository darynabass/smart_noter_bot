"""
@package handlers
@brief Telegram bot router handling viewing and navigation for system notes.
"""

from typing import Any, Dict, List, Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.queries import (
    get_items_by_list,
    get_list_by_name,
    get_or_create_user,
)
from keyboards.item_keyboards import notes_keyboard
from keyboards.main_menu import main_menu
from utils.constants import DEFAULT_NOTES_LIST, SOURCE_NOTES
from utils.message_utils import (
    remove_old_inline_keyboard,
    save_active_inline_message,
)

router = Router()


@router.message(Command("notes"))
@router.message(F.text == "📝 Notes")
async def notes_start(message: Message, state: FSMContext) -> None:
    """
    @brief Entry point for displaying notes list via command or keyboard button.

    @param message Incoming text message or command.
    @param state Current FSM context instance.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    user_id: int = await get_or_create_user(message.from_user.id, message.from_user.username)
    notes_list_id: Optional[int] = await get_list_by_name(user_id, DEFAULT_NOTES_LIST)

    items: List[Dict[str, Any]] = await get_items_by_list(user_id, notes_list_id) if notes_list_id else []

    await state.update_data(
        current_list_id=notes_list_id,
        current_items_page=0,
        current_items_source=SOURCE_NOTES,
    )

    if not items:
        await message.answer(
            "The \"Notes\" list is currently empty.",
            reply_markup=main_menu,
        )
        return

    sent_message: Message = await message.answer(
        "Select a note:",
        reply_markup=notes_keyboard(items, page=0),
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(F.data.startswith("notes_page:"))
async def notes_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles pagination for viewing notes list in current inline message.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    page: int = int(callback.data.split(":")[1])

    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    notes_list_id: Optional[int] = await get_list_by_name(user_id, DEFAULT_NOTES_LIST)

    items: List[Dict[str, Any]] = await get_items_by_list(user_id, notes_list_id) if notes_list_id else []

    await state.update_data(
        current_list_id=notes_list_id,
        current_items_page=page,
        current_items_source=SOURCE_NOTES,
    )

    sent_message: Message = await callback.message.edit_text(
        "Select a note:",
        reply_markup=notes_keyboard(items, page=page),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("notes_page_new:"))
async def notes_page_new(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Renders paginated notes list in a new message after previous views are cleared.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    page: int = int(callback.data.split(":")[1])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    notes_list_id: Optional[int] = await get_list_by_name(user_id, DEFAULT_NOTES_LIST)

    items: List[Dict[str, Any]] = await get_items_by_list(user_id, notes_list_id) if notes_list_id else []

    await state.update_data(
        current_list_id=notes_list_id,
        current_items_page=page,
        current_items_source=SOURCE_NOTES,
    )

    if not items:
        await callback.message.answer(
            "The \"Notes\" list is currently empty.",
            reply_markup=main_menu,
        )
        await callback.answer()
        return

    sent_message: Message = await callback.message.answer(
        "Select a note:",
        reply_markup=notes_keyboard(items, page=page),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()