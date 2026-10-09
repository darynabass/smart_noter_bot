"""
@package utils
@brief Module for formatting database items into user-friendly text messages.
"""

from utils.constants import (
    ITEM_TYPE_NOTE,
    STATUS_ACTIVE,
    STATUS_COMPLETED,
    STATUS_NOTIFIED,
)
from utils.priority_utils import format_priority


def format_item(item: dict) -> str:
    """
    @brief Formats an item entity dictionary into a structured readable string.

    @param item Dictionary representing item attributes.
    @return Multi-line formatted display string.
    """
    item_type = "Note" if item["item_type"] == ITEM_TYPE_NOTE else "Reminder"

    base_text = (
        f"{item_type}\n\n"
        f"Text: {item['text']}\n"
        f"Priority: {format_priority(item.get('priority'))}"
    )

    if item["item_type"] == ITEM_TYPE_NOTE:
        return base_text

    remind_at = item["remind_at"] if item["remind_at"] else "—"

    statuses = {
        STATUS_ACTIVE: "active",
        STATUS_NOTIFIED: "sent, pending completion",
        STATUS_COMPLETED: "completed"
    }

    status = statuses.get(item["status"], "—") if item["status"] else "—"

    result = (
        f"{base_text}\n"
        f"List: {item['list_name']}\n"
        f"Reminder time: {remind_at}\n"
        f"Status: {status}"
    )

    if item["status"] == STATUS_COMPLETED:
        completed_at = item["completed_at"] if item.get("completed_at") else "—"
        result += f"\nCompleted at: {completed_at}"

    return result