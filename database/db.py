"""
@package database
@brief Database initialization and schema management module.

Handles SQLite connection setup, enables foreign key constraints,
and creates required tables (users, lists, items).
"""

import aiosqlite

## Name of the SQLite database file.
DB_NAME: str = "activity_bot.db"


async def init_db() -> None:
    """
    @brief Asynchronously initializes the database tables and constraints.

    Creates the following tables if they do not already exist:
    - `users`: Stores user profile details from Telegram.
    - `lists`: Stores custom task/note lists owned by users.
    - `items`: Stores notes and reminders linked to users and lists.

    Also enables SQLite foreign key enforcement (`PRAGMA foreign_keys = ON`).

    @exception aiosqlite.Error If a database operation fails.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Enable foreign key check in SQLite
        await db.execute("PRAGMA foreign_keys = ON")

        # Create users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create lists table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create items table (notes and reminders)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                item_type TEXT NOT NULL,
                remind_at TEXT,
                priority TEXT DEFAULT 'none',
                status TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (list_id) REFERENCES lists(id),
                
                CHECK (item_type IN ('reminder', 'note')),
                CHECK (
                    (item_type = 'reminder' AND status IN ('active', 'notified', 'completed')) OR
                    (item_type = 'note' AND status IS NULL)
                )
            )
        """)

        # Commit changes after table creation
        await db.commit()