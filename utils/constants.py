"""
@package utils
@brief Module defining application-wide domain constants and configuration defaults.
"""

## Default name for general system notes list.
DEFAULT_NOTES_LIST: str = "Notes"

## Default fallback name for generic lists.
DEFAULT_GENERAL_LIST: str = "General"

## Item classification identifier for notes.
ITEM_TYPE_NOTE: str = "note"

## Item classification identifier for reminders.
ITEM_TYPE_REMINDER: str = "reminder"

## Status for scheduled active reminders.
STATUS_ACTIVE: str = "active"

## Status for dispatched/notified reminders waiting for user completion.
STATUS_NOTIFIED: str = "notified"

## Status for finished/fulfilled tasks.
STATUS_COMPLETED: str = "completed"

## High priority tag.
PRIORITY_HIGH: str = "high"

## Medium priority tag.
PRIORITY_MEDIUM: str = "medium"

## Low priority tag.
PRIORITY_LOW: str = "low"

## Default unassigned priority tag.
PRIORITY_NONE: str = "none"

## Source identifier corresponding to custom list context.
SOURCE_LISTS: str = "lists"

## Source identifier corresponding to notes context.
SOURCE_NOTES: str = "notes"

## Source identifier corresponding to reminders context.
SOURCE_REMINDERS: str = "reminders"

## Scheduled task execution interval in seconds.
REMINDER_CHECK_INTERVAL: int = 30