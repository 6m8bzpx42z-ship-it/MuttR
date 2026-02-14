"""Tests for muttr.history -- SQLite transcription history."""

import os
import tempfile
import shutil
from unittest.mock import patch

import pytest

from muttr import history


class TestHistoryCRUD:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "history.db")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_db = patch("muttr.history.DB_PATH", self._db_path)
        self._patch_dir.start()
        self._patch_db.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_db.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_add_entry_returns_id(self):
        row_id = history.add_entry("raw text", "cleaned text")
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_add_entry_increments_count(self):
        assert history.count() == 0
        history.add_entry("raw", "cleaned")
        assert history.count() == 1
        history.add_entry("raw2", "cleaned2")
        assert history.count() == 2

    def test_get_recent_returns_entries(self):
        history.add_entry("first raw", "first cleaned")
        history.add_entry("second raw", "second cleaned")
        entries = history.get_recent(limit=10)
        assert len(entries) == 2
        # Newest first
        assert entries[0]["raw_text"] == "second raw"
        assert entries[1]["raw_text"] == "first raw"

    def test_get_recent_respects_limit(self):
        for i in range(10):
            history.add_entry(f"raw {i}", f"cleaned {i}")
        entries = history.get_recent(limit=3)
        assert len(entries) == 3

    def test_get_recent_respects_offset(self):
        for i in range(5):
            history.add_entry(f"raw {i}", f"cleaned {i}")
        entries = history.get_recent(limit=2, offset=2)
        assert len(entries) == 2
        # With 5 entries newest-first: raw 4, raw 3, raw 2, raw 1, raw 0
        # offset=2 skips first 2 -> raw 2, raw 1
        assert entries[0]["raw_text"] == "raw 2"
        assert entries[1]["raw_text"] == "raw 1"

    def test_delete_entry(self):
        row_id = history.add_entry("to delete", "to delete")
        assert history.count() == 1
        history.delete_entry(row_id)
        assert history.count() == 0

    def test_delete_nonexistent_entry(self):
        # Should not raise
        history.delete_entry(9999)

    def test_clear_all(self):
        for i in range(5):
            history.add_entry(f"raw {i}", f"cleaned {i}")
        assert history.count() == 5
        history.clear_all()
        assert history.count() == 0

    def test_entry_has_expected_fields(self):
        history.add_entry("raw", "cleaned", engine="whisper", duration_s=2.5)
        entries = history.get_recent(limit=1)
        entry = entries[0]
        assert "id" in entry
        assert "timestamp" in entry
        assert entry["raw_text"] == "raw"
        assert entry["cleaned_text"] == "cleaned"
        assert entry["engine"] == "whisper"
        assert entry["duration_s"] == 2.5

    def test_default_engine_is_whisper(self):
        history.add_entry("raw", "cleaned")
        entries = history.get_recent(limit=1)
        assert entries[0]["engine"] == "whisper"

    def test_default_duration_is_zero(self):
        history.add_entry("raw", "cleaned")
        entries = history.get_recent(limit=1)
        assert entries[0]["duration_s"] == 0.0


class TestHistorySearch:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "history.db")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_db = patch("muttr.history.DB_PATH", self._db_path)
        self._patch_dir.start()
        self._patch_db.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_db.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_search_in_raw_text(self):
        history.add_entry("meeting with Sarah", "Meeting with Sarah.")
        history.add_entry("grocery list", "Grocery list.")
        results = history.search("Sarah")
        assert len(results) == 1
        assert "Sarah" in results[0]["raw_text"]

    def test_search_in_cleaned_text(self):
        history.add_entry("raw version", "Cleaned unique keyword version.")
        results = history.search("unique keyword")
        assert len(results) == 1

    def test_search_case_insensitive(self):
        history.add_entry("Hello World", "Hello World.")
        results = history.search("hello")
        assert len(results) == 1

    def test_search_no_results(self):
        history.add_entry("some text", "some text")
        results = history.search("nonexistent")
        assert len(results) == 0

    def test_search_respects_limit(self):
        for i in range(10):
            history.add_entry(f"meeting {i}", f"meeting {i}")
        results = history.search("meeting", limit=3)
        assert len(results) == 3

    def test_search_empty_query(self):
        history.add_entry("some text", "some text")
        # Empty string matches everything via LIKE %%
        results = history.search("")
        assert len(results) == 1

    def test_search_special_characters(self):
        history.add_entry("check https://example.com", "check https://example.com")
        results = history.search("https://example.com")
        assert len(results) == 1


class TestHistoryEdgeCases:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "history.db")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_db = patch("muttr.history.DB_PATH", self._db_path)
        self._patch_dir.start()
        self._patch_db.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_db.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_unicode_text(self):
        history.add_entry("cafe\u0301 na\u00efve", "Caf\u00e9 na\u00efve.")
        entries = history.get_recent(limit=1)
        assert "caf" in entries[0]["raw_text"].lower()

    def test_empty_text(self):
        row_id = history.add_entry("", "")
        assert row_id >= 1
        entries = history.get_recent(limit=1)
        assert entries[0]["raw_text"] == ""

    def test_very_long_text(self):
        long_text = "word " * 5000
        history.add_entry(long_text, long_text)
        entries = history.get_recent(limit=1)
        assert len(entries[0]["raw_text"]) == len(long_text)

    def test_multiple_adds_and_deletes(self):
        ids = []
        for i in range(5):
            ids.append(history.add_entry(f"entry {i}", f"entry {i}"))
        # Delete even entries
        for i in range(0, 5, 2):
            history.delete_entry(ids[i])
        assert history.count() == 2

    def test_get_recent_empty_db(self):
        entries = history.get_recent()
        assert entries == []

    def test_count_empty_db(self):
        assert history.count() == 0

    def test_timestamp_is_set(self):
        import time
        before = time.time()
        history.add_entry("timed", "timed")
        after = time.time()
        entries = history.get_recent(limit=1)
        ts = entries[0]["timestamp"]
        assert before <= ts <= after
