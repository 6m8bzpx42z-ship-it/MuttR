"""Tests for muttr.account -- local account model with sign in/out."""

import json
import os
import tempfile
import shutil
from unittest.mock import patch

import pytest

from muttr import account, events
from muttr.account import (
    load_account,
    save_account,
    sign_in,
    sign_out,
    update_preferences,
    ACCOUNT_DEFAULTS,
)


class TestAccountLoad:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._account_path = os.path.join(self._tmpdir, "account.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.account.ACCOUNT_PATH", self._account_path)
        self._patch_dir.start()
        self._patch_path.start()
        events.clear()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        events.clear()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_returns_defaults_when_no_file(self):
        acct = load_account()
        assert acct["email"] == ""
        assert acct["display_name"] == ""
        assert acct["signed_in"] is False
        assert acct["preferences"]["auto_copy"] is True
        assert acct["preferences"]["sound_feedback"] is False
        assert acct["preferences"]["show_overlay"] is True

    def test_load_merges_stored_values(self):
        with open(self._account_path, "w") as f:
            json.dump({"email": "test@example.com", "signed_in": True}, f)
        acct = load_account()
        assert acct["email"] == "test@example.com"
        assert acct["signed_in"] is True
        # Defaults for preferences still present
        assert acct["preferences"]["auto_copy"] is True

    def test_load_merges_partial_preferences(self):
        with open(self._account_path, "w") as f:
            json.dump({
                "preferences": {"auto_copy": False}
            }, f)
        acct = load_account()
        assert acct["preferences"]["auto_copy"] is False
        # Other defaults preserved
        assert acct["preferences"]["sound_feedback"] is False
        assert acct["preferences"]["show_overlay"] is True

    def test_load_handles_corrupt_json(self):
        with open(self._account_path, "w") as f:
            f.write("not valid json {{{")
        acct = load_account()
        assert acct["signed_in"] is False

    def test_load_does_not_mutate_defaults(self):
        acct = load_account()
        acct["email"] = "changed@example.com"
        acct["preferences"]["auto_copy"] = False
        # Re-load should return fresh defaults
        acct2 = load_account()
        assert acct2["email"] == ""
        assert acct2["preferences"]["auto_copy"] is True


class TestAccountSignInOut:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._account_path = os.path.join(self._tmpdir, "account.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.account.ACCOUNT_PATH", self._account_path)
        self._patch_dir.start()
        self._patch_path.start()
        events.clear()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        events.clear()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_sign_in_sets_email_and_state(self):
        acct = sign_in("user@example.com", "Test User")
        assert acct["email"] == "user@example.com"
        assert acct["display_name"] == "Test User"
        assert acct["signed_in"] is True

    def test_sign_in_derives_name_from_email(self):
        acct = sign_in("paul@test.com")
        assert acct["display_name"] == "paul"

    def test_sign_in_persists_to_disk(self):
        sign_in("user@example.com", "User")
        acct = load_account()
        assert acct["signed_in"] is True
        assert acct["email"] == "user@example.com"

    def test_sign_out_clears_state(self):
        sign_in("user@example.com", "User")
        acct = sign_out()
        assert acct["signed_in"] is False
        # Email is preserved, only signed_in cleared
        assert acct["email"] == "user@example.com"

    def test_sign_out_persists(self):
        sign_in("user@example.com", "User")
        sign_out()
        acct = load_account()
        assert acct["signed_in"] is False

    def test_sign_in_emits_event(self):
        received = []
        events.on("account_changed", lambda **kw: received.append(kw))
        sign_in("user@example.com")
        assert len(received) == 1
        assert received[0]["account"]["signed_in"] is True

    def test_sign_out_emits_event(self):
        sign_in("user@example.com")
        received = []
        events.on("account_changed", lambda **kw: received.append(kw))
        sign_out()
        assert len(received) == 1
        assert received[0]["account"]["signed_in"] is False


class TestAccountPreferences:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._account_path = os.path.join(self._tmpdir, "account.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.account.ACCOUNT_PATH", self._account_path)
        self._patch_dir.start()
        self._patch_path.start()
        events.clear()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        events.clear()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_update_preferences(self):
        acct = update_preferences({"auto_copy": False, "sound_feedback": True})
        assert acct["preferences"]["auto_copy"] is False
        assert acct["preferences"]["sound_feedback"] is True
        assert acct["preferences"]["show_overlay"] is True  # unchanged

    def test_update_preferences_persists(self):
        update_preferences({"sound_feedback": True})
        acct = load_account()
        assert acct["preferences"]["sound_feedback"] is True

    def test_update_preferences_emits_event(self):
        received = []
        events.on("account_changed", lambda **kw: received.append(kw))
        update_preferences({"auto_copy": False})
        assert len(received) == 1

    def test_preferences_survive_sign_in_out(self):
        sign_in("user@example.com")
        update_preferences({"sound_feedback": True})
        sign_out()
        acct = load_account()
        assert acct["preferences"]["sound_feedback"] is True

    def test_add_custom_preference(self):
        acct = update_preferences({"custom_pref": "value"})
        assert acct["preferences"]["custom_pref"] == "value"
