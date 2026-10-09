"""
@package handlers
@brief Telegram bot router handling individual item lifecycle, details, editing, and deletion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database.queries import (
    delete_item,
    get_item_by_id,
    get_items_by_list,
    get_list_by_id,
    get_or_create_user,
    mark_item_completed,
    update_item_priority,
    update_item_remind_at,
    update_item_text,
)
from keyboards.item_keyboards import (
    back_after_delete_keyboard,
    back_to_item_keyboard,
    confirm_delete_item_keyboard,
    edit_priority_keyboard,
    item_actions_keyboard,
    items_keyboard,
)
from keyboards.list_keyboards import back_to_lists_view_keyboard
from keyboards.time_keyboards import quick_time_keyboard
from utils.constants import (
    ITEM_TYPE_REMINDER,
    SOURCE_LISTS,
    SOURCE_NOTES,
    SOURCE_REMINDERS,
    STATUS_COMPLETED,
)
from utils.datetime_utils import get_quick_datetime, parse_user_datetime
from utils.formatters import format_item
from utils.message_utils import (
    remove_old_inline_keyboard,
    save_active_inline_message,
)
from utils.text_utils import MAX_ITEM_TEXT_LENGTH, is_valid_item_text

router = Router()


class ItemStates(StatesGroup):
    """
    @brief FSM states for managing item editing workflows.
    """
    waiting_new_item_text = State()
    waiting_new_remind_at = State()


def get_back_callback(source: str, list_id: Optional[int], page: int) -> str:
    """
    @brief Generates a target callback string for navigation based on source context.

    @param source Originating context string (e.g., SOURCE_NOTES, SOURCE_REMINDERS, SOURCE_LISTS).
    @param list_id Identifier of the parent list, if applicable.
    @param page Current pagination page number.

    @return Callback query data string for back navigation.
    """
    if source == SOURCE_NOTES:
        return f"notes_page:{page}"
    if source == SOURCE_REMINDERS:
        return f"reminders_page:{page}"
    if list_id is not None:
        return f"items_page:{list_id}:{page}"
    return "lists_view"


async def show_items_page(callback: CallbackQuery, state: FSMContext, list_id: int, page: int = 0) -> None:
    """
    @brief Renders a page listing items contained within a specified list.

    @param callback Incoming callback query trigger.
    @param state Current FSM context instance.
    @param list_id Target list identifier.
    @param page Page index to render.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)

    await state.update_data(
        current_list_id=list_id,
        current_items_page=page,
        current_items_source=SOURCE_LISTS,
    )

    items: List[Dict[str, Any]] = await get_items_by_list(user_id, list_id)
    list_data: Optional[Dict[str, Any]] = await get_list_by_id(user_id, list_id)

    list_name: str = list_data["name"] if list_data else "this list"

    if not items:
        sent_message: Message = await callback.message.edit_text(
            f"The list \"{list_name}\" is currently empty.",
            reply_markup=back_to_lists_view_keyboard(),
        )
    else:
        sent_message: Message = await callback.message.edit_text(
            "Select an item:",
            reply_markup=items_keyboard(items, list_id, page),
        )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("open_list:"))
async def open_list(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Handles callback to open a specific list from start index.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    list_id: int = int(callback.data.split(":")[1])
    await show_items_page(callback, state, list_id, page=0)


@router.callback_query(F.data.startswith("items_page:"))
async def items_page(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Navigates between pagination pages of items inside a list.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    data: List[str] = callback.data.split(":")

    if len(data) != 3 or data[1] == "None":
        await callback.answer("Failed to return to the item list.", show_alert=True)
        return

    list_id: int = int(data[1])
    page: int = int(data[2])

    await show_items_page(callback, state, list_id, page)


@router.callback_query(F.data.startswith("item_open:"))
async def item_open(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Displays item details and action options by updating the existing message.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    await state.set_state(None)
    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.message.edit_text("Item not found.", reply_markup=None)
        await state.clear()
        await callback.answer()
        return

    data: Dict[str, Any] = await state.get_data()
    source: str = data.get("current_items_source", SOURCE_LISTS)
    list_id: Optional[int] = data.get("current_list_id")
    page: int = data.get("current_items_page", 0)

    back_callback: str = get_back_callback(source, list_id, page)

    sent_message: Message = await callback.message.edit_text(
        format_item(item),
        reply_markup=item_actions_keyboard(
            item["id"],
            item["item_type"],
            item["status"],
            list_id,
            page,
            back_callback,
        ),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_open_new:"))
async def item_open_new(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Displays item details by sending a fresh Telegram message.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    await state.set_state(None)
    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    data: Dict[str, Any] = await state.get_data()
    source: str = data.get("current_items_source", SOURCE_LISTS)
    list_id: Optional[int] = data.get("current_list_id")
    page: int = data.get("current_items_page", 0)

    back_callback: str = get_back_callback(source, list_id, page)

    sent_message: Message = await callback.message.answer(
        format_item(item),
        reply_markup=item_actions_keyboard(
            item["id"],
            item["item_type"],
            item["status"],
            list_id,
            page,
            back_callback,
        ),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_edit:"))
async def item_edit_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Initiates text editing flow for a target item.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    if item["item_type"] == ITEM_TYPE_REMINDER and item["status"] == STATUS_COMPLETED:
        await callback.answer("Completed reminders cannot be edited.", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ItemStates.waiting_new_item_text)

    sent_message: Message = await callback.message.edit_text(
        "Enter new text for this item:",
        reply_markup=back_to_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.message(ItemStates.waiting_new_item_text)
async def item_edit_finish(message: Message, state: FSMContext) -> None:
    """
    @brief Validates input and persists updated item text to database.

    @param message Incoming text message with new item content.
    @param state Current FSM context instance.
    """
    new_text: str = message.text.strip() if message.text else ""

    if not new_text:
        await message.answer("Text cannot be empty. Please enter valid text:")
        return

    if not is_valid_item_text(new_text):
        await message.answer(
            f"Item text is too long. Maximum allowed length is {MAX_ITEM_TEXT_LENGTH} characters."
        )
        return

    data: Dict[str, Any] = await state.get_data()
    item_id: Optional[int] = data.get("item_id")

    if not item_id:
        await message.answer("State error occurred. Please navigate back and try again.")
        await state.clear()
        return

    user_id: int = await get_or_create_user(message.from_user.id, message.from_user.username)
    await update_item_text(user_id, item_id, new_text)

    await remove_old_inline_keyboard(message, state)
    await state.set_state(None)

    sent_message: Message = await message.answer(
        "Item text updated successfully.",
        reply_markup=back_to_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(F.data.startswith("item_edit_priority:"))
async def item_edit_priority_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Displays priority selection options for an item.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    if item["item_type"] == ITEM_TYPE_REMINDER and item["status"] == STATUS_COMPLETED:
        await callback.answer("Completed reminders cannot be edited.", show_alert=True)
        return

    sent_message: Message = await callback.message.edit_text(
        "Select a new priority:",
        reply_markup=edit_priority_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_priority:"))
async def item_edit_priority_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Applies selected priority level to target item.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    data: List[str] = callback.data.split(":", 2)

    item_id: int = int(data[1])
    new_priority: str = data[2]

    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    if item["item_type"] == ITEM_TYPE_REMINDER and item["status"] == STATUS_COMPLETED:
        await callback.answer("Completed reminders cannot be edited.", show_alert=True)
        return

    await update_item_priority(user_id, item_id, new_priority)

    sent_message: Message = await callback.message.edit_text(
        "Item priority updated successfully.",
        reply_markup=back_to_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_edit_time:"))
async def item_edit_time_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Prompts user to select or enter new schedule time for a reminder.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    if item["item_type"] != ITEM_TYPE_REMINDER:
        await callback.answer("Time can only be set for reminders.", show_alert=True)
        return

    if item["status"] == STATUS_COMPLETED:
        await callback.answer("Completed reminders cannot be edited.", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ItemStates.waiting_new_remind_at)

    sent_message: Message = await callback.message.edit_text(
        "Enter date and time in format DD.MM.YYYY HH:MM.\n"
        "Example: 25.05.2026 14:30\n\n"
        "Or choose a quick preset option:",
        reply_markup=quick_time_keyboard("edit_time_preset"),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(ItemStates.waiting_new_remind_at, F.data.startswith("edit_time_preset:"))
async def item_edit_time_preset(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Updates reminder schedule time using preset callback selection.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    preset: str = callback.data.split(":")[1]
    reminder_datetime: Optional[datetime] = get_quick_datetime(preset)

    if not reminder_datetime:
        await callback.answer("Failed to parse quick time preset.", show_alert=True)
        return

    data: Dict[str, Any] = await state.get_data()
    item_id: Optional[int] = data.get("item_id")

    if not item_id:
        await callback.answer("State error occurred.", show_alert=True)
        await state.clear()
        return

    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        await state.clear()
        return

    if item["item_type"] != ITEM_TYPE_REMINDER or item["status"] == STATUS_COMPLETED:
        await callback.answer("This reminder cannot be modified.", show_alert=True)
        await state.clear()
        return

    new_remind_at: str = reminder_datetime.strftime("%Y-%m-%d %H:%M")
    await update_item_remind_at(user_id, item_id, new_remind_at)

    await state.set_state(None)

    sent_message: Message = await callback.message.edit_text(
        f"Reminder time updated.\nNew time: {new_remind_at}",
        reply_markup=back_to_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.message(ItemStates.waiting_new_remind_at)
async def item_edit_time_finish(message: Message, state: FSMContext) -> None:
    """
    @brief Parses manual text input and updates reminder schedule time.

    @param message Incoming message with custom datetime string.
    @param state Current FSM context instance.
    """
    reminder_datetime: Optional[datetime] = parse_user_datetime(message.text or "")

    if not reminder_datetime:
        await message.answer(
            "Invalid date format. Please try again.\nExample: 25.05.2026 14:30"
        )
        return

    if reminder_datetime <= datetime.now():
        await message.answer("Reminder time must be in the future. Please enter a valid date:")
        return

    data: Dict[str, Any] = await state.get_data()
    item_id: Optional[int] = data.get("item_id")

    if not item_id:
        await message.answer("State error occurred. Please try again.")
        await state.clear()
        return

    user_id: int = await get_or_create_user(message.from_user.id, message.from_user.username)
    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await message.answer("Item not found.")
        await state.clear()
        return

    if item["item_type"] != ITEM_TYPE_REMINDER or item["status"] == STATUS_COMPLETED:
        await message.answer("This reminder cannot be modified.")
        await state.clear()
        return

    new_remind_at: str = reminder_datetime.strftime("%Y-%m-%d %H:%M")
    await update_item_remind_at(user_id, item_id, new_remind_at)

    await remove_old_inline_keyboard(message, state)
    await state.set_state(None)

    sent_message: Message = await message.answer(
        f"Reminder time updated.\nNew time: {new_remind_at}",
        reply_markup=back_to_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)


@router.callback_query(F.data.startswith("item_delete:"))
async def item_delete_confirm_start(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Prompts user for confirmation before deleting an item.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    item_id: int = int(callback.data.split(":")[1])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await state.update_data(
        item_info_chat_id=callback.message.chat.id,
        item_info_message_id=callback.message.message_id,
    )

    sent_message: Message = await callback.message.answer(
        "Are you sure you want to delete this item?",
        reply_markup=confirm_delete_item_keyboard(item_id),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_delete_confirm:"))
async def item_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Permanently deletes an item from the database upon confirmation.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    data: Dict[str, Any] = await state.get_data()
    source: str = data.get("current_items_source", SOURCE_LISTS)
    list_id: Optional[int] = data.get("current_list_id")
    page: int = data.get("current_items_page", 0)

    await delete_item(user_id, item_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await state.clear()

    sent_message: Message = await callback.message.edit_text(
        "Item deleted successfully.",
        reply_markup=back_after_delete_keyboard(
            source=source,
            list_id=list_id,
            page=page,
        ),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("items_page_new:"))
async def items_page_new(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Renders items page in a new message after destructive actions.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    data: List[str] = callback.data.split(":")

    if len(data) != 3 or data[1] == "None":
        await callback.answer("Failed to return to the item list.", show_alert=True)
        return

    list_id: int = int(data[1])
    page: int = int(data[2])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)

    await state.update_data(
        current_list_id=list_id,
        current_items_page=page,
        current_items_source=SOURCE_LISTS,
    )

    items: List[Dict[str, Any]] = await get_items_by_list(user_id, list_id)
    list_data: Optional[Dict[str, Any]] = await get_list_by_id(user_id, list_id)
    list_name: str = list_data["name"] if list_data else "this list"

    if not items:
        sent_message: Message = await callback.message.answer(
            f"The list \"{list_name}\" is currently empty.",
            reply_markup=back_to_lists_view_keyboard(),
        )
    else:
        sent_message: Message = await callback.message.answer(
            "Select an item:",
            reply_markup=items_keyboard(items, list_id, page),
        )

    await save_active_inline_message(sent_message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("item_delete_cancel:"))
async def item_delete_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Cancels item deletion flow and restores original keyboard view.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    item: Optional[Dict[str, Any]] = await get_item_by_id(user_id, item_id)

    if not item:
        await callback.answer("Item not found.", show_alert=True)
        return

    data: Dict[str, Any] = await state.get_data()
    item_info_chat_id: Optional[int] = data.get("item_info_chat_id")
    item_info_message_id: Optional[int] = data.get("item_info_message_id")

    source: str = data.get("current_items_source", SOURCE_LISTS)
    list_id: Optional[int] = data.get("current_list_id")
    page: int = data.get("current_items_page", 0)

    back_callback: str = get_back_callback(source, list_id, page)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

    if item_info_chat_id and item_info_message_id:
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=item_info_chat_id,
                message_id=item_info_message_id,
                reply_markup=item_actions_keyboard(
                    item["id"],
                    item["item_type"],
                    item["status"],
                    list_id,
                    page,
                    back_callback,
                ),
            )
        except TelegramBadRequest:
            sent_message: Message = await callback.message.answer(
                format_item(item),
                reply_markup=item_actions_keyboard(
                    item["id"],
                    item["item_type"],
                    item["status"],
                    list_id,
                    page,
                    back_callback,
                ),
            )
            await save_active_inline_message(sent_message, state)

    await callback.answer()


@router.callback_query(F.data.startswith("item_done:"))
async def item_done(callback: CallbackQuery, state: FSMContext) -> None:
    """
    @brief Marks an item as completed and updates state view.

    @param callback Incoming callback query.
    @param state Current FSM context instance.
    """
    user_id: int = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    item_id: int = int(callback.data.split(":")[1])

    await mark_item_completed(user_id, item_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await state.set_state(None)

    sent_message: Message = await callback.message.answer(
        "Item marked as completed.",
        reply_markup=back_to_item_keyboard(item_id, new_message=True),
    )

    await save_active_inline_message(sent_message, state)
    await callback.answer()