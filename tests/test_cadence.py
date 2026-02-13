"""Tests for muttr.cadence -- dictation cadence fingerprinting."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from muttr.cadence import (
    CadenceProfile,
    CadenceTracker,
    load_profile,
    save_profile,
    reset_profile,
    get_auto_stop_ms,
    _MIN_SAMPLES,
    _FLOOR_MS,
    _CEILING_MS,
    _DEFAULT_AUTO_STOP_MS,
    _RMS_FLOOR,
    PACE_FAST,
    PACE_AVERAGE,
    PACE_DELIBERATE,
)


# -- CadenceProfile tests ---


class TestCadenceProfile:
    def test_default_profile(self):
        p = CadenceProfile()
        assert p.mean_pause_ms == 0.0
        assert p.sample_count == 0
        assert not p.is_trained

    def test_trained_after_min_samples(self):
        p = CadenceProfile(sample_count=_MIN_SAMPLES)
        assert p.is_trained

    def test_not_trained_below_min(self):
        p = CadenceProfile(sample_count=_MIN_SAMPLES - 1)
        assert not p.is_trained

    def test_pace_label_fast(self):
        p = CadenceProfile(mean_pause_ms=200, sample_count=_MIN_SAMPLES)
        assert p.pace_label == PACE_FAST

    def test_pace_label_average(self):
        p = CadenceProfile(mean_pause_ms=450, sample_count=_MIN_SAMPLES)
        assert p.pace_label == PACE_AVERAGE

    def test_pace_label_deliberate(self):
        p = CadenceProfile(mean_pause_ms=700, sample_count=_MIN_SAMPLES)
        assert p.pace_label == PACE_DELIBERATE

    def test_pace_label_untrained_defaults_average(self):
        p = CadenceProfile(mean_pause_ms=100, sample_count=5)
        assert p.pace_label == PACE_AVERAGE

    def test_to_dict_roundtrip(self):
        p = CadenceProfile(
            mean_pause_ms=345.67,
            p75_pause_ms=400.5,
            p90_pause_ms=500.3,
            sample_count=42,
        )
        d = p.to_dict()
        p2 = CadenceProfile.from_dict(d)
        assert abs(p2.mean_pause_ms - 345.7) < 0.1
        assert abs(p2.p75_pause_ms - 400.5) < 0.1
        assert abs(p2.p90_pause_ms - 500.3) < 0.1
        assert p2.sample_count == 42


# -- Persistence tests ---


class TestPersistence:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patch = patch(
            "muttr.cadence._cadence_path",
            return_value=os.path.join(self._tmpdir, "cadence.json"),
        )
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        p = CadenceProfile(
            mean_pause_ms=300,
            p75_pause_ms=400,
            p90_pause_ms=500,
            sample_count=25,
        )
        save_profile(p)
        loaded = load_profile()
        assert loaded.mean_pause_ms == 300.0
        assert loaded.sample_count == 25

    def test_load_missing_returns_default(self):
        p = load_profile()
        assert p.sample_count == 0
        assert not p.is_trained

    def test_reset_profile(self):
        p = CadenceProfile(sample_count=50)
        save_profile(p)
        reset_profile()
        loaded = load_profile()
        assert loaded.sample_count == 0


# -- get_auto_stop_ms tests ---


class TestGetAutoStopMs:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patch = patch(
            "muttr.cadence._cadence_path",
            return_value=os.path.join(self._tmpdir, "cadence.json"),
        )
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch("muttr.config.load")
    def test_default_when_untrained(self, mock_cfg_load):
        mock_cfg_load.return_value = {"adaptive_silence": True}
        assert get_auto_stop_ms() == _DEFAULT_AUTO_STOP_MS

    @patch("muttr.config.load")
    def test_default_when_disabled(self, mock_cfg_load):
        mock_cfg_load.return_value = {"adaptive_silence": False}
        p = CadenceProfile(p90_pause_ms=500, sample_count=50)
        save_profile(p)
        assert get_auto_stop_ms() == _DEFAULT_AUTO_STOP_MS

    @patch("muttr.config.load")
    def test_adaptive_threshold_computed(self, mock_cfg_load):
        mock_cfg_load.return_value = {"adaptive_silence": True}
        p = CadenceProfile(p90_pause_ms=600, sample_count=50)
        save_profile(p)
        result = get_auto_stop_ms()
        # 600 * 2 = 1200, within [800, 3000]
        assert result == 1200

    @patch("muttr.config.load")
    def test_threshold_floor(self, mock_cfg_load):
        mock_cfg_load.return_value = {"adaptive_silence": True}
        p = CadenceProfile(p90_pause_ms=100, sample_count=50)
        save_profile(p)
        result = get_auto_stop_ms()
        # 100 * 2 = 200, but floor is 800
        assert result == _FLOOR_MS

    @patch("muttr.config.load")
    def test_threshold_ceiling(self, mock_cfg_load):
        mock_cfg_load.return_value = {"adaptive_silence": True}
        p = CadenceProfile(p90_pause_ms=2000, sample_count=50)
        save_profile(p)
        result = get_auto_stop_ms()
        # 2000 * 2 = 4000, but ceiling is 3000
        assert result == _CEILING_MS


# -- CadenceTracker tests ---


class TestCadenceTracker:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patch = patch(
            "muttr.cadence._cadence_path",
            return_value=os.path.join(self._tmpdir, "cadence.json"),
        )
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_no_pauses_detected_for_continuous_speech(self):
        tracker = CadenceTracker()
        # Simulate continuous speech (high RMS)
        for _ in range(50):
            tracker.update(0.1)
        assert len(tracker.session_pauses) == 0

    def test_pauses_detected_between_speech(self):
        tracker = CadenceTracker()
        import time

        # Speech phase
        for _ in range(10):
            tracker.update(0.1)
            time.sleep(0.02)

        # Pause phase (silence for > 100ms)
        for _ in range(10):
            tracker.update(0.001)
            time.sleep(0.02)

        # Speech again
        for _ in range(10):
            tracker.update(0.1)
            time.sleep(0.02)

        # Should have detected at least one pause
        assert len(tracker.session_pauses) >= 1

    def test_finish_session_saves_profile(self):
        tracker = CadenceTracker()
        import time

        # Simulate speech -> pause -> speech pattern
        for _ in range(5):
            tracker.update(0.1)
            time.sleep(0.02)
        for _ in range(10):
            tracker.update(0.001)
            time.sleep(0.02)
        for _ in range(5):
            tracker.update(0.1)
            time.sleep(0.02)

        profile = tracker.finish_session()
        assert profile.sample_count >= 0

    def test_finish_session_with_no_pauses(self):
        tracker = CadenceTracker()
        tracker.update(0.1)
        profile = tracker.finish_session()
        # Should return profile without error, sample_count unchanged
        assert profile.sample_count == 0

    def test_ema_smoothing_over_sessions(self):
        # First session with some pauses
        tracker1 = CadenceTracker()
        # Manually inject pauses for deterministic testing
        tracker1._pauses_ms = [300, 400, 350, 500, 450]
        tracker1._had_speech = True
        p1 = tracker1.finish_session()
        assert p1.sample_count == 5

        # Second session
        tracker2 = CadenceTracker()
        tracker2._pauses_ms = [200, 250, 300, 280, 220]
        tracker2._had_speech = True
        p2 = tracker2.finish_session()
        assert p2.sample_count == 10
        # Mean should be between the two session means due to EMA
        assert 200 < p2.mean_pause_ms < 500
