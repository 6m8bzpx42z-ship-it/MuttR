"""Transcription history stored in SQLite."""

import os
import sqlite3
import time

from muttr.config import APP_SUPPORT_DIR

DB_PATH = os.path.join(APP_SUPPORT_DIR, "history.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    engine TEXT NOT NULL DEFAULT 'whisper',
    duration_s REAL NOT NULL DEFAULT 0.0
)
"""


def _connect():
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def add_entry(raw_text, cleaned_text, engine="whisper", duration_s=0.0):
    """Record a transcription. Returns the new row id."""
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO transcriptions (timestamp, raw_text, cleaned_text, engine, duration_s) "
            "VALUES (?, ?, ?, ?, ?)",
            (time.time(), raw_text, cleaned_text, engine, duration_s),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_recent(limit=50, offset=0):
    """Return recent transcriptions, newest first."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM transcriptions ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search(query, limit=50):
    """Full-text search across raw and cleaned text."""
    conn = _connect()
    try:
        pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM transcriptions "
            "WHERE raw_text LIKE ? OR cleaned_text LIKE ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (pattern, pattern, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_entry(entry_id):
    """Delete a single transcription by id."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM transcriptions WHERE id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()


def clear_all():
    """Delete all transcription history."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM transcriptions")
        conn.commit()
    finally:
        conn.close()


def count():
    """Return total number of transcriptions."""
    conn = _connect()
    try:
        row = conn.execute("SELECT COUNT(*) FROM transcriptions").fetchone()
        return row[0]
    finally:
        conn.close()
