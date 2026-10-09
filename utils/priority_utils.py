"""
@package utils
@brief Module providing helper utilities for handling item priority levels.
"""

from utils.constants import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_NONE,
)


def format_priority(priority: str | None) -> str:
    """
    @brief Formats priority code identifier into human-readable star representation.

    @param priority Code string representing priority level.
    @return Star rating format string.
    """
    priorities = {
        PRIORITY_HIGH: "⭐⭐⭐",
        PRIORITY_MEDIUM: "⭐⭐",
        PRIORITY_LOW: "⭐",
        PRIORITY_NONE: "—",
    }

    return priorities.get(priority, "—")