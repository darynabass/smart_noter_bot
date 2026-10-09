"""
@package utils
@brief Module providing utilities for parsing date and time representations from user input.
"""

import re
from datetime import datetime, timedelta


def parse_user_datetime(value: str) -> datetime | None:
    """
    @brief Parses raw text string into a datetime object using regex and strict formats.

    Supports structured representations, relative time, and localized Ukrainian phrases.

    @param value Text containing target date/time input.
    @return Parsed datetime object, or None if parsing failed.
    """
    text = value.strip().lower()

    # 1. Standard datetime formats
    formats = [
        "%d.%m.%Y %H:%M",
        "%d.%m.%y %H:%M",
        "%Y-%m-%d %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue

    now = datetime.now()

    # 2. In N minutes
    match = re.match(r"через\s+(\d+)\s*(хв|хвилин|хвилини|хвилину)", text)
    if match:
        minutes = int(match.group(1))
        return now + timedelta(minutes=minutes)

    # 3. In N hours
    match = re.match(r"через\s+(\d+)\s*(год|годин|години|годину)", text)
    if match:
        hours = int(match.group(1))
        return now + timedelta(hours=hours)

    # 4. In N days
    match = re.match(r"через\s+(\d+)\s*(день|дні|днів)", text)
    if match:
        days = int(match.group(1))
        return now + timedelta(days=days)

    # 5. Today at HH or HH:MM
    match = re.match(r"сьогодні\s+о\s+(\d{1,2})(?::(\d{2}))?", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # 6. Tomorrow at HH or HH:MM
    match = re.match(r"завтра\s+о\s+(\d{1,2})(?::(\d{2}))?", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # 7. Day after tomorrow at HH or HH:MM
    match = re.match(r"післязавтра\s+о\s+(\d{1,2})(?::(\d{2}))?", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            after_tomorrow = now + timedelta(days=2)
            return after_tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None


def get_quick_datetime(value: str) -> datetime | None:
    """
    @brief Converts preset string key identifiers to appropriate datetime instance.

    @param value Code identifier representing predefined time offset.
    @return Computed datetime, or None if key is unknown.
    """
    now = datetime.now()

    if value == "15m":
        return now + timedelta(minutes=15)

    if value == "30m":
        return now + timedelta(minutes=30)

    if value == "1h":
        return now + timedelta(hours=1)

    if value == "3h":
        return now + timedelta(hours=3)

    if value == "tomorrow_9":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

    if value == "tomorrow_18":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)

    return None