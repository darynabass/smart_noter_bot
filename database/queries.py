"""
@package database
@brief Database queries module containing all asynchronous CRUD operations for SQLite.

Provides helper functions for managing users, lists, notes, reminders, status updates,
and generating user activity statistics.
"""

from datetime import datetime
import aiosqlite

from database.db import DB_NAME
from utils.constants import (
    DEFAULT_GENERAL_LIST,
    DEFAULT_NOTES_LIST,
    ITEM_TYPE_NOTE,
    ITEM_TYPE_REMINDER,
    STATUS_ACTIVE,
    STATUS_COMPLETED,
    STATUS_NOTIFIED,
)


async def _ensure_default_lists(db: aiosqlite.Connection, user_id: int) -> None:
    """
    @brief Ensures that mandatory default lists exist for a user.

    Creates 'Notes' and 'General' lists if they do not already exist for the given user.

    @param db Open aiosqlite connection instance.
    @param user_id The internal user ID in the database.
    """
    for name in (DEFAULT_NOTES_LIST, DEFAULT_GENERAL_LIST):
        cursor = await db.execute(
            "SELECT id FROM lists WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        exists = await cursor.fetchone()

        if not exists:
            await db.execute(
                "INSERT INTO lists (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )


async def get_or_create_user(telegram_id: int, username: str | None) -> int:
    """
    @brief Finds an existing user by Telegram ID or creates a new database record.

    Also ensures that default lists are populated for new or returning users.

    @param telegram_id Unique Telegram ID of the user.
    @param username Telegram username string or None.
    @return Internal primary key ID of the user in the database.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        user = await cursor.fetchone()

        if user:
            user_id = user[0]
            await _ensure_default_lists(db, user_id)
            await db.commit()
            return user_id

        cursor = await db.execute(
            "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )

        user_id = cursor.lastrowid

        await _ensure_default_lists(db, user_id)
        await db.commit()

        return user_id


async def get_list_by_name(user_id: int, name: str) -> int | None:
    """
    @brief Finds a user's list ID by its exact name.

    @param user_id Internal database ID of the user.
    @param name Exact name of the list to search for.
    @return List ID if found, otherwise None.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM lists WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_list_by_id(user_id: int, list_id: int) -> dict | None:
    """
    @brief Retrieves list details by list ID and user ID.

    @param user_id Internal database ID of the user.
    @param list_id Database ID of the list.
    @return Dictionary containing list fields ('id', 'name') if found, otherwise None.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT id, name
            FROM lists
            WHERE id = ? AND user_id = ?
        """, (list_id, user_id))

        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_list(user_id: int, name: str) -> tuple[int, bool]:
    """
    @brief Creates a new list for a user after verifying name uniqueness.

    @param user_id Internal database ID of the user.
    @param name Target list name.
    @return Tuple of (list_id, is_created), where is_created indicates if a new list was inserted.
    """
    name = name.strip()

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM lists WHERE user_id = ? AND lower(name) = lower(?)",
            (user_id, name)
        )
        existing = await cursor.fetchone()

        if existing:
            return existing[0], False

        cursor = await db.execute(
            "INSERT INTO lists (user_id, name) VALUES (?, ?)",
            (user_id, name)
        )
        await db.commit()

        return cursor.lastrowid, True


async def get_lists(user_id: int, include_notes: bool = True) -> list[dict]:
    """
    @brief Fetches all lists owned by a user along with their total item count.

    @param user_id Internal database ID of the user.
    @param include_notes Whether to include the default system 'Notes' list.
    @return List of dictionaries containing list details and item counts.
    """
    query = """
        SELECT l.id, l.name, COUNT(i.id) AS item_count
        FROM lists l
        LEFT JOIN items i ON i.list_id = l.id
        WHERE l.user_id = ?
    """

    params = [user_id]

    if not include_notes:
        query += " AND l.name != ?"
        params.append(DEFAULT_NOTES_LIST)

    query += " GROUP BY l.id, l.name ORDER BY l.name"

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_reminder_lists(user_id: int) -> list[dict]:
    """
    @brief Retrieves user lists available for assigning reminders.

    Ensures that at least a 'General' list exists if no other lists are found.

    @param user_id Internal database ID of the user.
    @return List of custom reminder list dictionaries.
    """
    lists = await get_lists(user_id, include_notes=False)

    if lists:
        return lists

    await create_list(user_id, DEFAULT_GENERAL_LIST)
    return await get_lists(user_id, include_notes=False)


async def delete_list_if_empty(user_id: int, list_id: int) -> tuple[bool, str]:
    """
    @brief Deletes a list if it contains no items and is not a protected system list.

    @param user_id Internal database ID of the user.
    @param list_id Database ID of the list to delete.
    @return Tuple of (success_status, descriptive_message).
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name FROM lists WHERE id = ? AND user_id = ?",
            (list_id, user_id)
        )
        row = await cursor.fetchone()

        if not row:
            return False, "List not found."

        name = row[0]

        if name == DEFAULT_NOTES_LIST:
            return False, f"System list '{DEFAULT_NOTES_LIST}' cannot be deleted."

        cursor = await db.execute(
            "SELECT COUNT(*) FROM items WHERE list_id = ?",
            (list_id,)
        )
        count = (await cursor.fetchone())[0]

        if count > 0:
            return False, "Cannot delete a list that contains items."

        await db.execute(
            "DELETE FROM lists WHERE id = ? AND user_id = ?",
            (list_id, user_id)
        )
        await db.commit()

        return True, f"List '{name}' successfully deleted."


async def create_item(
    user_id: int,
    list_id: int,
    text: str,
    item_type: str,
    priority: str,
    remind_at: str | None = None
) -> int:
    """
    @brief Inserts a new note or reminder item into the database.

    @param user_id Internal database ID of the user.
    @param list_id Database ID of the parent list.
    @param text Description/text content of the item.
    @param item_type Type of item ('reminder' or 'note').
    @param priority Priority level string ('none', 'low', 'medium', 'high').
    @param remind_at ISO formatted datetime string for reminders, or None for notes.
    @return ID of the created item.
    @exception ValueError If an invalid item_type is provided.
    """
    if item_type == ITEM_TYPE_REMINDER:
        status = STATUS_ACTIVE
    elif item_type == ITEM_TYPE_NOTE:
        status = None
    else:
        raise ValueError(f"item_type must be '{ITEM_TYPE_REMINDER}' or '{ITEM_TYPE_NOTE}'")

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO items (user_id, list_id, text, item_type, remind_at, priority, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, list_id, text, item_type, remind_at, priority, status, None))

        await db.commit()
        return cursor.lastrowid


async def get_items_by_type(user_id: int, item_type: str) -> list[dict]:
    """
    @brief Retrieves items filtered by type ('reminder' or 'note').

    @param user_id Internal database ID of the user.
    @param item_type Type string ('reminder' or 'note').
    @return List of matching item dictionaries.
    """
    order_by = "remind_at DESC" if item_type == ITEM_TYPE_REMINDER else "created_at DESC"

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"""
            SELECT id, text, item_type, remind_at, priority, status, created_at
            FROM items
            WHERE user_id = ? AND item_type = ?
            ORDER BY {order_by}
        """, (user_id, item_type))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_items_by_list(user_id: int, list_id: int) -> list[dict]:
    """
    @brief Retrieves all items associated with a specific list.

    @param user_id Internal database ID of the user.
    @param list_id ID of the target list.
    @return List of item dictionaries ordered by creation date.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, text, item_type, remind_at, priority, status, created_at
            FROM items
            WHERE user_id = ? AND list_id = ?
            ORDER BY created_at DESC
        """, (user_id, list_id))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_item_by_id(user_id: int, item_id: int) -> dict | None:
    """
    @brief Retrieves item details along with its list name by item ID.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the item.
    @return Item dictionary if found, otherwise None.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT i.*, l.name AS list_name
            FROM items i
            LEFT JOIN lists l ON l.id = i.list_id
            WHERE i.id = ? AND i.user_id = ?
        """, (item_id, user_id))

        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_item_text(user_id: int, item_id: int, new_text: str) -> None:
    """
    @brief Updates the text content of an existing item.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the item to update.
    @param new_text New text value.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE items SET text = ? WHERE id = ? AND user_id = ?",
            (new_text, item_id, user_id)
        )
        await db.commit()


async def update_item_priority(user_id: int, item_id: int, new_priority: str) -> None:
    """
    @brief Updates the priority level of an uncompleted item.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the item.
    @param new_priority New priority string value.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE items
            SET priority = ?
            WHERE id = ?
              AND user_id = ?
              AND NOT (item_type = ? AND status = ?)
        """, (
            new_priority,
            item_id,
            user_id,
            ITEM_TYPE_REMINDER,
            STATUS_COMPLETED
        ))

        await db.commit()


async def update_item_remind_at(user_id: int, item_id: int, new_remind_at: str) -> None:
    """
    @brief Updates the scheduled reminder time and resets status to active.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the item.
    @param new_remind_at New reminder datetime formatted string.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE items
            SET remind_at = ?,
                status = ?,
                completed_at = NULL
            WHERE id = ?
              AND user_id = ?
              AND item_type = ?
              AND status != ?
        """, (
            new_remind_at,
            STATUS_ACTIVE,
            item_id,
            user_id,
            ITEM_TYPE_REMINDER,
            STATUS_COMPLETED
        ))

        await db.commit()


async def delete_item(user_id: int, item_id: int) -> None:
    """
    @brief Deletes an item from the database.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the item.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM items WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        )
        await db.commit()


async def mark_item_completed(user_id: int, item_id: int) -> None:
    """
    @brief Marks an active or notified reminder as completed with current timestamp.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the reminder.
    """
    completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE items
            SET status = ?,
                completed_at = ?
            WHERE id = ?
              AND user_id = ?
              AND item_type = ?
              AND status != ?
        """, (
            STATUS_COMPLETED,
            completed_at,
            item_id,
            user_id,
            ITEM_TYPE_REMINDER,
            STATUS_COMPLETED
        ))

        await db.commit()


async def snooze_reminder(user_id: int, item_id: int, new_remind_at: str) -> bool:
    """
    @brief Postpones an existing reminder to a new time and sets status back to active.

    @param user_id Internal database ID of the user.
    @param item_id Database ID of the reminder.
    @param new_remind_at New reminder datetime formatted string.
    @return True if a row was updated, False otherwise.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            UPDATE items
            SET remind_at = ?,
                status = ?,
                completed_at = NULL
            WHERE id = ?
              AND user_id = ?
              AND item_type = ?
              AND status != ?
        """, (
            new_remind_at,
            STATUS_ACTIVE,
            item_id,
            user_id,
            ITEM_TYPE_REMINDER,
            STATUS_COMPLETED
        ))

        await db.commit()

        return cursor.rowcount > 0


async def mark_item_status(item_id: int, status: str) -> None:
    """
    @brief Updates the status of a reminder item directly by item ID.

    @param item_id Database ID of the reminder.
    @param status Target status value (e.g., STATUS_NOTIFIED).
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE items SET status = ? WHERE id = ? AND item_type = ?",
            (status, item_id, ITEM_TYPE_REMINDER)
        )
        await db.commit()


async def get_due_reminders() -> list[dict]:
    """
    @brief Queries active reminders whose scheduled time is past or present.

    @return List of due reminder dictionaries containing telegram_id and item fields.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT i.id, i.text, i.priority, i.remind_at, l.name AS list_name, u.telegram_id
            FROM items i
            JOIN users u ON u.id = i.user_id
            LEFT JOIN lists l ON l.id = i.list_id
            WHERE i.item_type = ?
              AND i.status = ?
              AND i.remind_at <= ?
        """, (ITEM_TYPE_REMINDER, STATUS_ACTIVE, now))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_stats(user_id: int) -> dict[str, int]:
    """
    @brief Aggregates comprehensive user metrics and statistics.

    @param user_id Internal database ID of the user.
    @return Dictionary containing counts for notes, reminders, status splits, and lists.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async def scalar(query: str, params: tuple = ()) -> int:
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return row[0]

        notes = await scalar(
            "SELECT COUNT(*) FROM items WHERE user_id = ? AND item_type = ?",
            (user_id, ITEM_TYPE_NOTE)
        )

        reminders = await scalar(
            "SELECT COUNT(*) FROM items WHERE user_id = ? AND item_type = ?",
            (user_id, ITEM_TYPE_REMINDER)
        )

        active = await scalar(
            """
            SELECT COUNT(*)
            FROM items
            WHERE user_id = ?
              AND item_type = ?
              AND status = ?
            """,
            (user_id, ITEM_TYPE_REMINDER, STATUS_ACTIVE)
        )

        notified = await scalar(
            """
            SELECT COUNT(*)
            FROM items
            WHERE user_id = ?
              AND item_type = ?
              AND status = ?
            """,
            (user_id, ITEM_TYPE_REMINDER, STATUS_NOTIFIED)
        )

        completed = await scalar(
            """
            SELECT COUNT(*)
            FROM items
            WHERE user_id = ?
              AND item_type = ?
              AND status = ?
            """,
            (user_id, ITEM_TYPE_REMINDER, STATUS_COMPLETED)
        )

        completed_on_time = await scalar(
            """
            SELECT COUNT(*)
            FROM items
            WHERE user_id = ?
              AND item_type = ?
              AND status = ?
              AND remind_at IS NOT NULL
              AND completed_at IS NOT NULL
              AND datetime(completed_at) <= datetime(remind_at, '+30 minutes')
            """,
            (user_id, ITEM_TYPE_REMINDER, STATUS_COMPLETED)
        )

        lists = await scalar(
            "SELECT COUNT(*) FROM lists WHERE user_id = ? AND name != ?",
            (user_id, DEFAULT_NOTES_LIST)
        )

        return {
            "notes": notes,
            "reminders": reminders,
            "active": active,
            "notified": notified,
            "completed": completed,
            "completed_on_time": completed_on_time,
            "lists": lists,
        }