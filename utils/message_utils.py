"""
@package utils
@brief Module containing message editing and UI state persistence tools.
"""

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


async def remove_old_inline_keyboard(message: Message, state: FSMContext) -> None:
    """
    @brief Removes inline markup from the previous active state message to prevent stale interaction.

    @param message Telegram message instance to obtain bot context.
    @param state Finite State Machine context.
    """
    data = await state.get_data()

    chat_id = data.get("active_inline_chat_id")
    message_id = data.get("active_inline_message_id")

    if chat_id and message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None
            )
        except TelegramBadRequest:
            pass

    await state.update_data(
        active_inline_chat_id=None,
        active_inline_message_id=None
    )


async def save_active_inline_message(sent_message: Message, state: FSMContext) -> None:
    """
    @brief Stores the identifiers of an active inline message inside FSM state.

    @param sent_message Newly dispatched Telegram message containing inline markup.
    @param state Finite State Machine context.
    """
    await state.update_data(
        active_inline_chat_id=sent_message.chat.id,
        active_inline_message_id=sent_message.message_id
    )