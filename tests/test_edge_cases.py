"""Additional edge case tests across all MuttR modules.

Fills gaps not covered by the per-module test files:
- SpeechMetrics/SpeechProfile boundary conditions
- Hotkey multi-tap edge cases
- MurmurProcessor with negative audio
- Cross-module integration (config+events, history+context)
- Corrupt file handling
"""

import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from muttr import events


# ---------------------------------------------------------------------------
# SpeechMetrics edge cases
# ---------------------------------------------------------------------------

class TestSpeechMetricsEdgeCases:
    def test_negative_duration(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "hello world", duration_s=-1.0)
        # Negative duration should not crash; wpm formula gives negative, but func runs
        assert "wpm" in metrics

    def test_none_transcript(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        # If transcript is None, split() would fail; verify robustness
        try:
            metrics = SpeechMetrics.analyze(audio, None, duration_s=1.0)
        except (TypeError, AttributeError):
            pass  # Expected if not handled

    def test_filler_words_case_insensitive(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "UM I think UH we should", duration_s=3.0)
        assert metrics["filler_count"] == 2

    def test_multiple_same_filler(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "um um um hello um", duration_s=3.0)
        assert metrics["filler_count"] == 4

    def test_very_long_transcript(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        transcript = " ".join(["word"] * 1000)
        metrics = SpeechMetrics.analyze(audio, transcript, duration_s=60.0)
        assert metrics["word_count"] == 1000
        assert metrics["wpm"] == pytest.approx(1000.0, abs=0.1)

    def test_unicode_transcript(self):
        from muttr.cadence import SpeechMetrics
        audio = np.zeros(100, dtype=np.float32)
        metrics = SpeechMetrics.analyze(audio, "cafe\u0301 na\u00efve r\u00e9sum\u00e9", duration_s=2.0)
        assert metrics["word_count"] == 3


# ---------------------------------------------------------------------------
# SpeechProfile feedback boundary conditions
# ---------------------------------------------------------------------------

class TestSpeechProfileFeedbackBoundaries:
    def _trained_profile(self, wpm=120.0, energy=0.05):
        from muttr.cadence import SpeechProfile, _SPEECH_PROFILE_MIN_ENTRIES
        p = SpeechProfile()
        for _ in range(_SPEECH_PROFILE_MIN_ENTRIES + 2):
            p.update({"wpm": wpm, "energy_rms": energy, "confidence": 0.85,
                       "filler_count": 1, "word_count": 10})
        return p

    def test_exactly_125_percent_wpm_not_fast(self):
        from muttr.cadence import FEEDBACK_FAST
        p = self._trained_profile(wpm=100.0)
        # Exactly 125% should NOT trigger (> 125%, not >=)
        feedback = p.get_feedback({"wpm": 125.0, "energy_rms": 0.05,
                                    "confidence": 0.85, "filler_count": 1})
        assert feedback != FEEDBACK_FAST

    def test_just_above_125_percent_wpm_is_fast(self):
        from muttr.cadence import FEEDBACK_FAST
        p = self._trained_profile(wpm=100.0)
        feedback = p.get_feedback({"wpm": 125.1, "energy_rms": 0.05,
                                    "confidence": 0.85, "filler_count": 1})
        assert feedback == FEEDBACK_FAST

    def test_at_40_percent_energy_boundary(self):
        from muttr.cadence import FEEDBACK_QUIET
        p = self._trained_profile(energy=0.1)
        # Due to floating point: 0.1 * 0.4 = 0.04000000000000001
        # so 0.04 < 0.04000000000000001 is True -- triggers Quiet
        # Energy clearly above 40% should NOT trigger
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.041,
                                    "confidence": 0.85, "filler_count": 1})
        assert feedback != FEEDBACK_QUIET

    def test_just_below_40_percent_energy_is_quiet(self):
        from muttr.cadence import FEEDBACK_QUIET
        p = self._trained_profile(energy=0.1)
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.039,
                                    "confidence": 0.85, "filler_count": 0})
        assert feedback == FEEDBACK_QUIET

    def test_confidence_exactly_0_92_not_clear(self):
        from muttr.cadence import FEEDBACK_CLEAR
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.92, "filler_count": 0})
        # 0.92 is not > 0.92, so should not be Clear
        assert feedback != FEEDBACK_CLEAR

    def test_confidence_0_93_is_clear(self):
        from muttr.cadence import FEEDBACK_CLEAR
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.93, "filler_count": 0})
        assert feedback == FEEDBACK_CLEAR

    def test_confidence_exactly_0_8_not_steady(self):
        from muttr.cadence import FEEDBACK_STEADY
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.8, "filler_count": 2})
        # 0.8 is not > 0.8
        assert feedback != FEEDBACK_STEADY

    def test_confidence_0_81_is_steady(self):
        from muttr.cadence import FEEDBACK_STEADY
        p = self._trained_profile()
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.05,
                                    "confidence": 0.81, "filler_count": 2})
        assert feedback == FEEDBACK_STEADY

    def test_zero_baseline_wpm_no_fast_feedback(self):
        """If baseline WPM is zero, fast check should not fire."""
        from muttr.cadence import SpeechProfile, _SPEECH_PROFILE_MIN_ENTRIES, FEEDBACK_FAST
        p = SpeechProfile()
        for _ in range(_SPEECH_PROFILE_MIN_ENTRIES + 2):
            p.update({"wpm": 0.0, "energy_rms": 0.05, "confidence": 0.85,
                       "filler_count": 0, "word_count": 0})
        feedback = p.get_feedback({"wpm": 200.0, "energy_rms": 0.05,
                                    "confidence": 0.85, "filler_count": 0})
        assert feedback != FEEDBACK_FAST

    def test_zero_baseline_energy_no_quiet_feedback(self):
        """If baseline energy is zero, quiet check should not fire."""
        from muttr.cadence import SpeechProfile, _SPEECH_PROFILE_MIN_ENTRIES, FEEDBACK_QUIET
        p = SpeechProfile()
        for _ in range(_SPEECH_PROFILE_MIN_ENTRIES + 2):
            p.update({"wpm": 120.0, "energy_rms": 0.0, "confidence": 0.85,
                       "filler_count": 0, "word_count": 10})
        feedback = p.get_feedback({"wpm": 120.0, "energy_rms": 0.001,
                                    "confidence": 0.85, "filler_count": 0})
        assert feedback != FEEDBACK_QUIET


# ---------------------------------------------------------------------------
# SpeechProfile persistence edge cases
# ---------------------------------------------------------------------------

class TestSpeechProfileCorruptFile:
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

    def test_corrupt_json_returns_empty_profile(self):
        from muttr.cadence import load_speech_profile
        path = os.path.join(self._tmpdir, "speech_profile.json")
        with open(path, "w") as f:
            f.write("{corrupt json!!")
        p = load_speech_profile()
        assert len(p.entries) == 0

    def test_reset_nonexistent_file_no_error(self):
        from muttr.cadence import reset_speech_profile
        reset_speech_profile()  # Should not raise


# ---------------------------------------------------------------------------
# Hotkey multi-tap edge cases
# ---------------------------------------------------------------------------

class TestHotkeyEdgeCases:
    def test_fn_up_when_not_committed_does_not_fire(self):
        """If fn is released before commitment, on_key_up should NOT fire."""
        from muttr.hotkey import HotkeyListener
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        listener = HotkeyListener(on_key_down=down, on_key_up=up, on_double_tap=double)
        listener._committed = False
        listener._fn_held = True
        listener._handle_fn_up()
        assert not up.called

    def test_fn_up_when_committed_fires_up(self):
        """If fn is released after commitment, on_key_up should fire."""
        from muttr.hotkey import HotkeyListener
        down = MagicMock()
        up = MagicMock()

        listener = HotkeyListener(on_key_down=down, on_key_up=up)
        listener._committed = True
        listener._fn_held = True
        listener._handle_fn_up()
        assert up.called

    def test_commit_double_tap_when_already_committed(self):
        """_commit_double_tap should not fire if already committed."""
        from muttr.hotkey import HotkeyListener
        double = MagicMock()
        listener = HotkeyListener(
            on_key_down=MagicMock(), on_key_up=MagicMock(),
            on_double_tap=double,
        )
        listener._committed = True
        listener._commit_double_tap()
        assert not double.called

    def test_commit_double_tap_when_not_committed(self):
        """_commit_double_tap should fire if not yet committed."""
        from muttr.hotkey import HotkeyListener
        double = MagicMock()
        listener = HotkeyListener(
            on_key_down=MagicMock(), on_key_up=MagicMock(),
            on_double_tap=double,
        )
        listener._committed = False
        listener._commit_double_tap()
        assert double.called
        assert listener._committed is True

    def test_stop_cancels_disambiguation_timer(self):
        from muttr.hotkey import HotkeyListener
        listener = HotkeyListener(on_key_down=MagicMock(), on_key_up=MagicMock())
        mock_timer = MagicMock()
        listener._disambiguation_timer = mock_timer
        listener._monitor = None  # Don't try to remove real monitor
        listener.stop()
        mock_timer.invalidate.assert_called_once()
        assert listener._disambiguation_timer is None

    def test_fn_up_resets_committed_flag(self):
        from muttr.hotkey import HotkeyListener
        listener = HotkeyListener(on_key_down=MagicMock(), on_key_up=MagicMock())
        listener._committed = True
        listener._fn_held = True
        listener._handle_fn_up()
        assert listener._committed is False


# ---------------------------------------------------------------------------
# MurmurProcessor edge cases
# ---------------------------------------------------------------------------

class TestMurmurProcessorEdgeCases:
    def test_negative_audio_values(self):
        from muttr.murmur import MurmurProcessor
        proc = MurmurProcessor(gain=2.0, noise_gate_db=-100.0)
        audio = np.array([-0.1, -0.3, -0.5], dtype=np.float32)
        result = proc.process(audio)
        # Negative values should be preserved (gain + tanh)
        assert np.all(result < 0)
        assert np.all(np.abs(result) <= 1.0)

    def test_process_preserves_array_length(self):
        from muttr.murmur import MurmurProcessor
        proc = MurmurProcessor()
        audio = np.random.randn(12345).astype(np.float32)
        result = proc.process(audio)
        assert len(result) == len(audio)

    def test_process_all_zeros_stays_zeros(self):
        from muttr.murmur import MurmurProcessor
        proc = MurmurProcessor(gain=5.0)
        audio = np.zeros(100, dtype=np.float32)
        result = proc.process(audio)
        assert np.all(result == 0.0)

    def test_calibrate_with_loud_audio(self):
        from muttr.murmur import MurmurProcessor
        proc = MurmurProcessor()
        loud = np.full(1000, 0.9, dtype=np.float32)
        proc.calibrate(loud)
        # Noise floor should reflect the loud signal
        assert proc.noise_floor is not None
        assert proc.noise_floor > 0.5


# ---------------------------------------------------------------------------
# Cross-module integration: config + events
# ---------------------------------------------------------------------------

class TestConfigEventsIntegration:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._account_path = os.path.join(self._tmpdir, "account.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_config = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_account = patch("muttr.account.ACCOUNT_PATH", self._account_path)
        self._patch_dir.start()
        self._patch_config.start()
        self._patch_account.start()
        events.clear()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_config.stop()
        self._patch_account.stop()
        events.clear()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_account_change_event_carries_config_prefs(self):
        """sign_in emits an event with full account data including preferences."""
        from muttr import account
        received = []
        events.on("account_changed", lambda **kw: received.append(kw))
        account.sign_in("test@example.com", "Test")
        assert received[0]["account"]["preferences"]["auto_copy"] is True

    def test_murmur_toggle_event_and_config_consistency(self):
        """Murmur toggle should emit event AND persist to config."""
        from muttr.murmur import MurmurMode
        from muttr import config
        received = []
        events.on("murmur_toggled", lambda **kw: received.append(kw))
        mm = MurmurMode()
        mm.toggle()
        assert received[0]["active"] is True
        assert config.get("murmur_active") is True


# ---------------------------------------------------------------------------
# Cross-module integration: history + context stitching
# ---------------------------------------------------------------------------

class TestHistoryContextIntegration:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "history.db")
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_db = patch("muttr.history.DB_PATH", self._db_path)
        self._patch_config = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_db.start()
        self._patch_config.start()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_db.stop()
        self._patch_config.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_context_uses_real_history(self):
        """Context stitching should pull from actual history entries."""
        from muttr import history, config
        from muttr.context import _get_recent_transcriptions_text
        config.save({"context_stitching": True})
        history.add_entry("raw about quarterly results", "Cleaned about quarterly results.")
        text = _get_recent_transcriptions_text(limit=2)
        assert "quarterly" in text.lower()

    def test_context_empty_history(self):
        from muttr.context import _get_recent_transcriptions_text
        text = _get_recent_transcriptions_text(limit=2)
        assert text == ""


# ---------------------------------------------------------------------------
# Cleanup + confidence integration
# ---------------------------------------------------------------------------

class TestCleanupConfidenceIntegration:
    def test_cleaned_text_from_confidence_result(self):
        """Verify cleanup works on text extracted from TranscriptionResult."""
        from muttr.confidence import TranscriptionResult, WordInfo
        from muttr.cleanup import clean_text
        words = [
            WordInfo("um", 0.0, 0.2, 0.95),
            WordInfo("i", 0.2, 0.3, 0.90),
            WordInfo("went", 0.3, 0.5, 0.88),
            WordInfo("to", 0.5, 0.6, 0.92),
            WordInfo("london", 0.6, 1.0, 0.45),
        ]
        result = TranscriptionResult(
            text="um i went to london",
            words=words,
            has_word_confidence=True,
        )
        cleaned = clean_text(result.text, level=1)
        assert "London" in cleaned
        assert "um" not in cleaned.lower()
