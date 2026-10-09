"""
@package smart_noter_bot
@brief Configuration module for loading environment variables and bot settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

## The Telegram API token used for bot authentication.
BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")

# Validate presence of BOT_TOKEN
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found. Please check your .env file.")