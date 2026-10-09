"""
@package keyboards
@brief Module defining the primary main menu reply keyboard layout.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Add"),
            KeyboardButton(text="📋 Lists"),
            KeyboardButton(text="📊 Statistics")
        ],
        [
            KeyboardButton(text="⏰ Reminders"),
            KeyboardButton(text="📝 Notes"),
            KeyboardButton(text="ℹ️ Help")
        ]
    ],
    resize_keyboard=True
)