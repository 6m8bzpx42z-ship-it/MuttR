"""Tests for muttr.config -- load, save, validation, defaults."""

import json
import os
import tempfile
import shutil
from unittest.mock import patch

import pytest

from muttr.config import (
    load,
    save,
    get,
    set_value,
    DEFAULTS,
    VALID_MODELS,
    VALID_ENGINES,
)


class TestConfigLoad:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_path.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_returns_defaults_when_no_file(self):
        cfg = load()
        for key, val in DEFAULTS.items():
            assert cfg[key] == val

    def test_load_merges_stored_values(self):
        with open(self._config_path, "w") as f:
            json.dump({"cleanup_level": 2, "model": "small.en"}, f)
        cfg = load()
        assert cfg["cleanup_level"] == 2
        assert cfg["model"] == "small.en"
        # Other defaults still present
        assert cfg["paste_delay_ms"] == DEFAULTS["paste_delay_ms"]

    def test_load_handles_corrupt_json(self):
        with open(self._config_path, "w") as f:
            f.write("{invalid json!!")
        cfg = load()
        # Should fall back to defaults without crashing
        assert cfg["cleanup_level"] == DEFAULTS["cleanup_level"]

    def test_load_validates_cleanup_level_clamp_low(self):
        with open(self._config_path, "w") as f:
            json.dump({"cleanup_level": -5}, f)
        cfg = load()
        assert cfg["cleanup_level"] == 0

    def test_load_validates_cleanup_level_clamp_high(self):
        with open(self._config_path, "w") as f:
            json.dump({"cleanup_level": 10}, f)
        cfg = load()
        assert cfg["cleanup_level"] == 2

    def test_load_validates_invalid_model(self):
        with open(self._config_path, "w") as f:
            json.dump({"model": "nonexistent.model"}, f)
        cfg = load()
        assert cfg["model"] == DEFAULTS["model"]

    def test_load_validates_invalid_engine(self):
        with open(self._config_path, "w") as f:
            json.dump({"transcription_engine": "fake_engine"}, f)
        cfg = load()
        assert cfg["transcription_engine"] == DEFAULTS["transcription_engine"]

    def test_load_clamps_paste_delay_low(self):
        with open(self._config_path, "w") as f:
            json.dump({"paste_delay_ms": 1}, f)
        cfg = load()
        assert cfg["paste_delay_ms"] == 10

    def test_load_clamps_paste_delay_high(self):
        with open(self._config_path, "w") as f:
            json.dump({"paste_delay_ms": 9999}, f)
        cfg = load()
        assert cfg["paste_delay_ms"] == 500

    def test_load_clamps_timeout_low(self):
        with open(self._config_path, "w") as f:
            json.dump({"transcription_timeout_s": 1}, f)
        cfg = load()
        assert cfg["transcription_timeout_s"] == 5

    def test_load_clamps_timeout_high(self):
        with open(self._config_path, "w") as f:
            json.dump({"transcription_timeout_s": 999}, f)
        cfg = load()
        assert cfg["transcription_timeout_s"] == 120

    def test_load_accepts_valid_engine_whisper(self):
        with open(self._config_path, "w") as f:
            json.dump({"transcription_engine": "whisper"}, f)
        cfg = load()
        assert cfg["transcription_engine"] == "whisper"

    def test_load_rejects_removed_engine_parakeet(self):
        with open(self._config_path, "w") as f:
            json.dump({"transcription_engine": "parakeet"}, f)
        cfg = load()
        assert cfg["transcription_engine"] == "whisper"


class TestConfigSave:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_path.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_creates_file(self):
        save({"cleanup_level": 2, "model": "small.en"})
        assert os.path.exists(self._config_path)

    def test_save_roundtrip(self):
        data = dict(DEFAULTS)
        data["cleanup_level"] = 2
        data["model"] = "small.en"
        save(data)
        cfg = load()
        assert cfg["cleanup_level"] == 2
        assert cfg["model"] == "small.en"

    def test_save_overwrites_existing(self):
        save({"cleanup_level": 0})
        save({"cleanup_level": 2})
        with open(self._config_path, "r") as f:
            stored = json.load(f)
        assert stored["cleanup_level"] == 2


class TestConfigGetAndSet:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_path.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_get_returns_default(self):
        val = get("cleanup_level")
        assert val == DEFAULTS["cleanup_level"]

    def test_get_returns_stored_value(self):
        save({"cleanup_level": 2})
        val = get("cleanup_level")
        assert val == 2

    def test_get_unknown_key_returns_default(self):
        val = get("nonexistent_key", "fallback")
        assert val == "fallback"

    def test_set_value_persists(self):
        set_value("cleanup_level", 2)
        assert get("cleanup_level") == 2

    def test_set_value_does_not_clobber_other_keys(self):
        set_value("cleanup_level", 2)
        set_value("model", "small.en")
        # Both should be persisted
        cfg = load()
        assert cfg["cleanup_level"] == 2
        assert cfg["model"] == "small.en"

    def test_set_value_custom_key(self):
        set_value("custom_setting", True)
        assert get("custom_setting") is True


class TestConfigEdgeCases:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_path.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_with_extra_unknown_keys(self):
        with open(self._config_path, "w") as f:
            json.dump({"unknown_key": "test_value", "cleanup_level": 1}, f)
        cfg = load()
        assert cfg["unknown_key"] == "test_value"
        assert cfg["cleanup_level"] == 1

    def test_load_with_empty_json_object(self):
        with open(self._config_path, "w") as f:
            json.dump({}, f)
        cfg = load()
        for key, val in DEFAULTS.items():
            assert cfg[key] == val

    def test_boolean_config_values(self):
        set_value("context_stitching", False)
        assert get("context_stitching") is False
        set_value("context_stitching", True)
        assert get("context_stitching") is True

    def test_load_creates_directory_if_missing(self):
        nested_dir = os.path.join(self._tmpdir, "sub", "dir")
        nested_path = os.path.join(nested_dir, "config.json")
        with patch("muttr.config.APP_SUPPORT_DIR", nested_dir), \
             patch("muttr.config.CONFIG_PATH", nested_path):
            cfg = load()
            assert os.path.isdir(nested_dir)
