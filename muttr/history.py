"""Transcription history stored in SQLite with encrypted field storage."""

import base64
import logging
import os
import re
import sqlite3
import subprocess
import time

from muttr.config import APP_SUPPORT_DIR

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

log = logging.getLogger(__name__)

DB_PATH = os.path.join(APP_SUPPORT_DIR, "history.db")

_KEYCHAIN_SERVICE = "MuttR"
_KEYCHAIN_ACCOUNT = "encryption-key"
_PBKDF2_SALT = b"MuttR-field-encryption-v1"
_PBKDF2_ITERATIONS = 480_000

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

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

_fernet_instance = None


def _get_hardware_uuid():
    """Return the macOS IOPlatformUUID for this machine."""
    try:
        output = subprocess.check_output(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            text=True,
        )
        match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', output)
        if match:
            return match.group(1)
    except (subprocess.SubprocessError, OSError):
        pass
    raise RuntimeError("Unable to determine hardware UUID")


def _derive_fernet_key(machine_id: str) -> bytes:
    """Derive a Fernet-compatible key from a machine identifier via PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_PBKDF2_SALT,
        iterations=_PBKDF2_ITERATIONS,
    )
    key_bytes = kdf.derive(machine_id.encode("utf-8"))
    return base64.urlsafe_b64encode(key_bytes)


def _keychain_read() -> str | None:
    """Read the encryption key from macOS Keychain.  Returns None if absent."""
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s", _KEYCHAIN_SERVICE,
                "-a", _KEYCHAIN_ACCOUNT,
                "-w",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def _keychain_write(key: str) -> None:
    """Store the encryption key in macOS Keychain."""
    try:
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-s", _KEYCHAIN_SERVICE,
                "-a", _KEYCHAIN_ACCOUNT,
                "-w", key,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        log.warning("Failed to store encryption key in Keychain: %s", exc)


def _get_fernet():
    """Return a cached Fernet instance, creating (and persisting) the key if needed."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    if not _HAS_CRYPTO:
        return None

    # 1. Try to retrieve an existing key from the Keychain.
    stored_key = _keychain_read()
    if stored_key:
        try:
            _fernet_instance = Fernet(stored_key.encode("utf-8"))
            return _fernet_instance
        except Exception:
            log.warning("Stored Keychain key is invalid; regenerating.")

    # 2. Derive a new key from the hardware UUID and persist it.
    try:
        hw_uuid = _get_hardware_uuid()
    except RuntimeError:
        log.warning("Cannot determine hardware UUID; encryption disabled.")
        return None

    key = _derive_fernet_key(hw_uuid)
    _keychain_write(key.decode("utf-8"))
    _fernet_instance = Fernet(key)
    return _fernet_instance


def _encrypt(text: str) -> str:
    """Encrypt *text* and return the Fernet token as a UTF-8 string.

    If encryption is unavailable the original text is returned unchanged.
    """
    fernet = _get_fernet()
    if fernet is None:
        return text
    return fernet.encrypt(text.encode("utf-8")).decode("utf-8")


def _decrypt(data: str) -> str:
    """Decrypt *data* (a Fernet token string) and return plaintext.

    If decryption fails -- for example, because the row was written before
    encryption was enabled -- the original string is returned as-is so that
    the module stays backwards-compatible.
    """
    fernet = _get_fernet()
    if fernet is None:
        return data
    try:
        return fernet.decrypt(data.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Likely a pre-encryption plaintext row; return unchanged.
        return data


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _connect():
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def _decrypt_row(row_dict: dict) -> dict:
    """Return a copy of *row_dict* with text fields decrypted."""
    row_dict["raw_text"] = _decrypt(row_dict["raw_text"])
    row_dict["cleaned_text"] = _decrypt(row_dict["cleaned_text"])
    return row_dict


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_entry(raw_text, cleaned_text, engine="whisper", duration_s=0.0):
    """Record a transcription. Returns the new row id."""
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO transcriptions (timestamp, raw_text, cleaned_text, engine, duration_s) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                time.time(),
                _encrypt(raw_text),
                _encrypt(cleaned_text),
                engine,
                duration_s,
            ),
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
        return [_decrypt_row(dict(r)) for r in rows]
    finally:
        conn.close()


def search(query, limit=50):
    """Full-text search across raw and cleaned text.

    Because the text columns are encrypted, SQL LIKE cannot operate on
    ciphertext.  We therefore fetch all rows, decrypt in Python, and filter
    in-memory.  This is acceptable for a local desktop app with moderate
    data volumes.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM transcriptions ORDER BY timestamp DESC",
        ).fetchall()

        query_lower = query.lower()
        results = []
        for r in rows:
            entry = _decrypt_row(dict(r))
            if (
                query_lower in entry["raw_text"].lower()
                or query_lower in entry["cleaned_text"].lower()
            ):
                results.append(entry)
                if len(results) >= limit:
                    break
        return results
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
