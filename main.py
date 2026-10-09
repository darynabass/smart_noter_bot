"""
@package smart_noter_bot
@brief Main entry point for starting and running the Smart Noter Telegram Bot.

Initializes logging, connects handlers, runs the background reminder worker,
and starts long polling.
"""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database.db import init_db
from handlers import add, fallback, items, lists, notes, reminders, start, stats
from services.reminder_service import reminder_worker

## Path to the directory where log files are stored.
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    @brief Asynchronous main function to initialize and start the bot.

    Performs the following initialization steps:
    1. Initializes the SQLite database schema.
    2. Instantiates the Telegram Bot and resets webhooks.
    3. Registers all application routers (handlers) with the Dispatcher.
    4. Launches the background task for reminder monitoring.
    5. Starts long polling to listen for incoming Telegram updates.
    """
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=False)

    # Dispatcher receives all messages and button presses from Telegram
    dp = Dispatcher()

    # Registering routers with the dispatcher
    dp.include_router(start.router)
    dp.include_router(add.router)
    dp.include_router(lists.router)
    dp.include_router(items.router)
    dp.include_router(notes.router)
    dp.include_router(reminders.router)
    dp.include_router(stats.router)
    dp.include_router(fallback.router)

    # Launch background task for monitoring and sending reminders
    asyncio.create_task(reminder_worker(bot))

    print("Bot started")
    # Start bot in long polling mode
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())