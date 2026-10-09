"""
@package handlers
@brief Router for catching unhandled or unexpected user inputs.

Provides fallback responses when a user inputs text or media that does not match
the current state flow or expected commands.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.main_menu import main_menu

router = Router()


@router.message(F.text)
async def unknown_text_message(message: Message, state: FSMContext) -> None:
    """
    @brief Handles unknown or out-of-context text messages.

    @param message Incoming Telegram Message instance.
    @param state FSM context.
    """
    current_state = await state.get_state()

    if current_state:
        await message.answer(
            "I am waiting for input in the active scenario. "
            "Please enter the requested data or use the provided inline buttons."
        )
        return

    await message.answer(
        "Sorry, I did not understand that message.\n\n"
        "Use the menu buttons to add a note or reminder, view lists, or check your statistics.",
        reply_markup=main_menu
    )


@router.message()
async def unknown_content_message(message: Message, state: FSMContext) -> None:
    """
    @brief Handles unsupported content types (e.g., photos, voice notes, stickers).

    @param message Incoming Telegram Message instance.
    @param state FSM context.
    """
    current_state = await state.get_state()

    if current_state:
        await message.answer(
            "At this step, please send a text message or press a button."
        )
        return

    await message.answer(
        "Sorry, currently I can only process text messages and menu buttons.",
        reply_markup=main_menu
    )