"""Tests for cadence coaching features in muttr.cadence.

Tests SpeechMetrics, SpeechProfile, and related persistence functions.
These tests are separate from test_cadence.py which covers the original
CadenceTracker and CadenceProfile pause-tracking features.
"""

import json
import os
import tempfile
import shutil
from unittest.mock import patch

import numpy as np
import pytest

from muttr.cadence import (
    SpeechMetrics,
    SpeechProfile,
    load_speech_profile,
    save_speech_profile,
    reset_speech_profile,
    FEEDBACK_FAST,
    FEEDBACK_QUIET,
    FEEDBACK_CLEAR,
    FEEDBACK_STEADY,
    _SPEECH_PROFILE_MIN_ENTRIES,
    _SPEECH_PROFILE_WINDOW,
)


# -- SpeechMetrics tests ---


class TestSpeechMetrics:
    def test_basic_analysis(self):
        audio = np.array([0.1, 0.2, 0.3, 0.1, 0.2], dtype=np.float32)
        transcript = "hello world how are you"
        metrics = SpeechMetrics.analyze(audio, transcript, duration_s=3.0, confidence=0.9)

        assert metrics["word_count"] == 5
        assert metrics["wpm"] == pytest.approx(100.0, abs=0.1)
        assert metrics["energy_rms"] > 0
        assert metrics["confidence"] == 0.9
        assert metrics["filler_count"] == 0

    def test_wpm_calculation(self):
        audio = np.zeros(100, dtype=np.float32)
        transcript = "one two three four five six"
        metrics = SpeechMetrics.analyze(audio, transcript, duration_s=2.0)
        assert metrics["wpm"] == pytest.approx(180.0, abs=0.1)

    def test_zero_duration(self):
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "hello", duration_s=0.0)
        assert metrics["wpm"] == 0.0

    def test_empty_transcript(self):
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "", duration_s=1.0)
        assert metrics["word_count"] == 0
        assert metrics["wpm"] == 0.0
        assert metrics["filler_count"] == 0

    def test_whitespace_only_transcript(self):
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "   ", duration_s=1.0)
        assert metrics["word_count"] == 0

    def test_filler_word_detection(self):
        audio = np.zeros(100, dtype=np.float32)
        transcript = "um I think uh we should like go"
        metrics = SpeechMetrics.analyze(audio, transcript, duration_s=3.0)
        assert metrics["filler_count"] == 3

    def test_energy_rms_computation(self):
        audio = np.full(100, 0.5, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "test", duration_s=1.0)
        assert metrics["energy_rms"] == pytest.approx(0.5, abs=0.001)

    def test_empty_audio(self):
        audio = np.array([], dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "test", duration_s=1.0)
        assert metrics["energy_rms"] == 0.0

    def test_confidence_passed_through(self):
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "hi", duration_s=1.0, confidence=0.876)
        assert metrics["confidence"] == 0.876

    def test_rounding(self):
        audio = np.full(100, 0.123456789, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "hello world test",
                                        duration_s=1.111, confidence=0.87654)
        assert metrics["wpm"] == round((3 / 1.111) * 60, 1)
        assert len(str(metrics["energy_rms"]).split(".")[-1]) <= 4
        assert metrics["confidence"] == 0.877


# -- SpeechProfile tests ---


class TestSpeechProfile:
    def test_empty_profile(self):
        p = SpeechProfile()
        assert len(p.entries) == 0
        assert p.baseline_wpm == 0.0
        assert p.baseline_energy == 0.0
        assert not p.has_baseline

    def test_update_adds_entry(self):
        p = SpeechProfile()
        metrics = {"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                   "filler_count": 0, "word_count": 10}
        p.update(metrics)
        assert len(p.entries) == 1

    def test_baseline_after_min_entries(self):
        p = SpeechProfile()
        for i in range(_SPEECH_PROFILE_MIN_ENTRIES):
            p.update({"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                       "filler_count": 0, "word_count": 10})
        assert p.has_baseline
        assert p.baseline_wpm == pytest.approx(120.0, abs=0.1)
        assert p.baseline_energy == pytest.approx(0.05, abs=0.001)

    def test_no_baseline_below_min_entries(self):
        p = SpeechProfile()
        for i in range(_SPEECH_PROFILE_MIN_ENTRIES - 1):
            p.update({"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                       "filler_count": 0, "word_count": 10})
        assert not p.has_baseline

    def test_rolling_window_caps_entries(self):
        p = SpeechProfile()
        for i in range(_SPEECH_PROFILE_WINDOW + 20):
            p.update({"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                       "filler_count": 0, "word_count": 10})
        assert len(p.entries) == _SPEECH_PROFILE_WINDOW

    def test_to_dict_roundtrip(self):
        p = SpeechProfile()
        for i in range(10):
            p.update({"wpm": 120.0 + i, "energy_rms": 0.05, "confidence": 0.9,
                       "filler_count": 0, "word_count": 10})
        d = p.to_dict()
        p2 = SpeechProfile.from_dict(d)
        assert len(p2.entries) == 10
        assert p2.baseline_wpm == pytest.approx(p.baseline_wpm, abs=0.1)
        assert p2.baseline_energy == pytest.approx(p.baseline_energy, abs=0.001)


# -- Feedback tests ---


class TestSpeechProfileFeedback:
    def _trained_profile(self, wpm=120.0, energy=0.05):
        """Create a profile with enough data to provide feedback."""
        p = SpeechProfile()
        for i in range(_SPEECH_PROFILE_MIN_ENTRIES + 5):
            p.update({"wpm": wpm, "energy_rms": energy, "confidence": 0.85,
                       "filler_count": 1, "word_count": 10})
        return p

    def test_no_feedback_when_untrained(self):
        p = SpeechProfile()
        p.update({"wpm": 200.0, "energy_rms": 0.001, "confidence": 0.5,
                   "filler_count": 5, "word_count": 10})
        assert p.get_feedback({"wpm": 200.0}) is None

    def test_fast_feedback(self):
        p = self._trained_profile(wpm=120.0)
        feedback = p.get_feedback({"wpm": 160.0, "energy_rms": 0.05,
                                    "confidence": 0.8, "filler_count": 1})
        assert feedback == FEEDBACK_FAST

    def test_quiet_feedback(self):
        p = self._trained_profile(energy=0.05)
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.01,
                                    "confidence": 0.8, "filler_count": 0})
        assert feedback == FEEDBACK_QUIET

    def test_clear_feedback(self):
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.95, "filler_count": 0})
        assert feedback == FEEDBACK_CLEAR

    def test_steady_feedback(self):
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.85, "filler_count": 2})
        assert feedback == FEEDBACK_STEADY

    def test_no_feedback_for_low_confidence(self):
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.5, "filler_count": 2})
        assert feedback is None

    def test_fast_takes_priority_over_clear(self):
        p = self._trained_profile(wpm=100.0)
        feedback = p.get_feedback({"wpm": 200.0, "energy_rms": 0.05,
                                    "confidence": 0.95, "filler_count": 0})
        assert feedback == FEEDBACK_FAST

    def test_quiet_takes_priority_over_clear(self):
        p = self._trained_profile(energy=0.1)
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.01,
                                    "confidence": 0.95, "filler_count": 0})
        assert feedback == FEEDBACK_QUIET


# -- Persistence tests ---


class TestSpeechProfilePersistence:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._patch = patch(
            "muttr.cadence._speech_profile_path",
            return_value=os.path.join(self._tmpdir, "speech_profile.json"),
        )
        self._patch.start()

    def teardown_method(self):
        self._patch.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        p = SpeechProfile()
        for i in range(10):
            p.update({"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                       "filler_count": 0, "word_count": 10})
        save_speech_profile(p)
        loaded = load_speech_profile()
        assert len(loaded.entries) == 10
        assert loaded.baseline_wpm == pytest.approx(120.0, abs=0.1)

    def test_load_missing_returns_empty(self):
        p = load_speech_profile()
        assert len(p.entries) == 0
        assert not p.has_baseline

    def test_reset_speech_profile(self):
        p = SpeechProfile()
        p.update({"wpm": 120.0, "energy_rms": 0.05, "confidence": 0.9,
                   "filler_count": 0, "word_count": 10})
        save_speech_profile(p)
        reset_speech_profile()
        loaded = load_speech_profile()
        assert len(loaded.entries) == 0
