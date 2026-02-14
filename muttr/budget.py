"""Daily word budget tracking with 7-day rollover."""

import os
import sqlite3
from datetime import date, timedelta

from muttr.config import APP_SUPPORT_DIR
from muttr import license

DB_PATH = os.path.join(APP_SUPPORT_DIR, "budget.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS word_usage (
    date TEXT PRIMARY KEY,
    words_used INTEGER NOT NULL DEFAULT 0
)
"""

ROLLOVER_DAYS = 7


def _connect():
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def record_usage(word_count: int) -> None:
    """Record words used in a transcription."""
    today = date.today().isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO word_usage (date, words_used) VALUES (?, ?)"
            " ON CONFLICT(date) DO UPDATE SET words_used = words_used + ?",
            (today, word_count, word_count),
        )
        conn.commit()
    finally:
        conn.close()


def _get_usage(day: str) -> int:
    """Get word usage for a specific day."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT words_used FROM word_usage WHERE date = ?", (day,)
        ).fetchone()
        return row["words_used"] if row else 0
    finally:
        conn.close()


def _has_record(day: str) -> bool:
    """Return True if there is a usage record for this day."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM word_usage WHERE date = ?", (day,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _get_rollover_budget() -> int:
    """Calculate rollover words from unused budget in the past 7 days.

    Only counts days that have a usage record — days before the app was
    installed don't contribute rollover.
    """
    daily_limit = license.get_daily_word_limit()
    if daily_limit is None:
        return 0  # unlimited tier, no rollover needed

    today = date.today()
    rollover = 0
    for i in range(1, ROLLOVER_DAYS + 1):
        day = (today - timedelta(days=i)).isoformat()
        if not _has_record(day):
            continue  # no record = app wasn't used that day
        used = _get_usage(day)
        unused = max(0, daily_limit - used)
        rollover += unused

    return rollover


def words_remaining_today() -> int | None:
    """Return words remaining today, or None for unlimited tiers."""
    daily_limit = license.get_daily_word_limit()
    if daily_limit is None:
        return None  # unlimited

    today_used = _get_usage(date.today().isoformat())
    rollover = _get_rollover_budget()
    total_budget = daily_limit + rollover
    remaining = total_budget - today_used
    return max(0, remaining)


def is_over_budget() -> bool:
    """Return True if the user has exceeded their daily word budget."""
    remaining = words_remaining_today()
    if remaining is None:
        return False  # unlimited
    return remaining <= 0


def get_today_usage() -> int:
    """Return words used today."""
    return _get_usage(date.today().isoformat())
