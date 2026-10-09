"""
@package handlers
@brief Telegram bot router handling list navigation, creation, viewing, and deletion.
"""

from typing import Any, Dict, List, Tuple

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database.queries import (
    create_list,
    delete_list_if_empty,
    get_lists,
    get_or_create_user,
)
from keyboards.list_keyboards import (
    back_to_lists_menu_keyboard,
    back_to_lists_menu_new_keyboard,
    confirm_delete_list_keyboard,
    delete_lists_keyboard,
    list_menu_keyboard,
    open_lists_keyboard,
)
from utils.message_utils import (
    remove_old_inline_keyboard,
    save_active_inline_message,
)
from utils.text_utils import (
    MAX_LIST_NAME_LENGTH,
    is_valid_list_name,
)

router = Router()


class ListStates(StatesGroup):
    """
    @brief FSM states for managing list creation workflows.
    """
    waiting_list_name = State()


@router.message(Command("lists"))
@router.message(F.text == "📋 Lists")
async def lists_start(message: Message, state: FSMContext) -> None:
    """
    @brief Entry point for the lists menu via command or menu button.

    @param message Incoming text message or command.
    @param state Current FSM context instance.
    """
    await remove_old_inline_keyboard(message, state)
    await state.clear()

    await get_or_create_user(message.from_user.id, message.from_user.username)

    sent_message: Message = await message.answer(
        "Choose an action with lists:",
        reply_markup=list_menu_keyboard(),
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(F.data == "lists_menu")
async def lists_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Renders lists management main menu in the current message.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    await state.clear()

    sent_message: Message = await callback.message.edit_text(
        "Choose an action with lists:",
        reply_markup=list_menu_keyboard(),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data == "lists_menu_new")
async def lists_menu_new(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Displays lists management menu in a new message.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    await state.clear()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    sent_message: Message = await callback.message.answer(
        "Choose an action with lists:",
        reply_markup=list_menu_keyboard(),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data == "lists_create")
async def lists_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Triggers state for creating a new list.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    await state.clear()
    await state.set_state(ListStates.waiting_list_name)

    sent_message: Message = await callback.message.edit_text(
        "Enter name for the new list:",
        reply_markup=back_to_lists_menu_keyboard(),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.message(ListStates.waiting_list_name)
async def lists_create_finish(message: Message, state: FSMContext) -> None:
    """
    @brief Validates input and persists new list creation in database.

    @param message Text message containing new list name.
    @param state Current FSM context instance.
    """
    name: str = message.text.strip() if message.text else ""

    if not is_valid_list_name(name):
        await message.answer(
            f"List name must be between 2 and {MAX_LIST_NAME_LENGTH} characters long. Please try again:"
        )
        return

    user_id: int = await get_or_create_user(message.from_user.id, message.from_user.username)
    _, created = await create_list(user_id, name)

    await remove_old_inline_keyboard(message, state)
    await state.clear()

    if created:
        sent_message: Message = await message.answer(
            f"List \"{name}\" created successfully.",
            reply_markup=back_to_lists_menu_keyboard(),
        )
    else:
        sent_message: Message = await message.answer(
            f"List \"{name}\" already exists.",
            reply_markup=back_to_lists_menu_keyboard(),
        )

    await save_active_inline_message(sent_message, state)


async def show_lists_page(callback: CallbackQuery, state: FSMContext, page: int = 0) -> None:
    """
    @brief Renders lists view with pagination support.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    @param page Page index to render.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    lists: List[Dict[str, Any]] = await get_lists(user_id, include_notes=True)

    sent_message: Message = await callback.message.edit_text(
        "Your lists:",
        reply_markup=open_lists_keyboard(lists, page),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data == "lists_view")
async def lists_view(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Entry point to view all user lists starting from page 0.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    await show_lists_page(callback, state, page=0)


@router.callback_query(F.data.startswith("lists_view_page:"))
async def lists_view_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles pagination navigation across active user lists.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    page: int = int(callback.data.split(":")[1])
    await show_lists_page(callback, state, page)


async def show_delete_lists_page(callback: CallbackQuery, state: FSMContext, page: int = 0) -> None:
    """
    @brief Renders a page listing deletable empty lists.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    @param page Page index to render.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    lists: List[Dict[str, Any]] = await get_lists(user_id, include_notes=False)

    sent_message: Message = await callback.message.edit_text(
        "Select a list to delete. Note: Only empty lists can be deleted:",
        reply_markup=delete_lists_keyboard(lists, page),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data == "lists_delete")
async def lists_delete_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Entry point for list deletion view.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    await show_delete_lists_page(callback, state, page=0)


@router.callback_query(F.data.startswith("lists_delete_page:"))
async def lists_delete_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Pagination for list deletion page view.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    page: int = int(callback.data.split(":")[1])
    await show_delete_lists_page(callback, state, page)


@router.callback_query(F.data.startswith("delete_list:"))
async def lists_delete_confirm_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Requests user confirmation to delete a list.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    data: List[str] = callback.data.split(":")

    list_id: int = int(data[1])
    page: int = int(data[2]) if len(data) > 2 else 0

    sent_message: Message = await callback.message.edit_text(
        "Are you sure you want to delete this list?",
        reply_markup=confirm_delete_list_keyboard(list_id, page),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("delete_list_confirm:"))
async def lists_delete_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Executes list deletion if list is verified as empty.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    list_id: int = int(callback.data.split(":")[1])

    success, message_text = await delete_list_if_empty(user_id, list_id)

    # Переклад відповідей з бази даних на англійську мову
    if success:
        message_text = "List deleted successfully."
    else:
        message_text = "Cannot delete a non-empty list. Remove all items first."

    await state.clear()

    sent_message: Message = await callback.message.edit_text(
        message_text,
        reply_markup=back_to_lists_menu_new_keyboard(),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()