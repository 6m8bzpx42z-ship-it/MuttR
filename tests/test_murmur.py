"""Tests for muttr.murmur -- Murmur Mode low-volume dictation."""

import json
import os
import tempfile
import shutil
from unittest.mock import patch

import numpy as np
import pytest

from muttr.murmur import (
    MurmurProcessor,
    MurmurMode,
    DEFAULT_GAIN,
    DEFAULT_NOISE_GATE_DB,
    DEFAULT_MIN_UTTERANCE_MS,
    CALIBRATION_SAMPLES,
)
from muttr import events


# -- MurmurProcessor tests ---


class TestMurmurProcessor:
    def test_default_gain(self):
        proc = MurmurProcessor()
        assert proc.gain == DEFAULT_GAIN

    def test_custom_gain(self):
        proc = MurmurProcessor(gain=5.0)
        assert proc.gain == 5.0

    def test_noise_gate_threshold_from_db(self):
        proc = MurmurProcessor(noise_gate_db=-50.0)
        expected = 10 ** (-50.0 / 20)
        assert abs(proc.noise_gate_threshold - expected) < 1e-10

    def test_process_applies_gain(self):
        proc = MurmurProcessor(gain=2.0, noise_gate_db=-100.0)
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        result = proc.process(audio)
        expected = np.tanh(audio * 2.0).astype(np.float32)
        np.testing.assert_allclose(result, expected, atol=1e-6)

    def test_process_noise_gate_zeros_quiet_samples(self):
        proc = MurmurProcessor(gain=3.0, noise_gate_db=-20.0)
        audio = np.array([0.01, 0.05, 0.5], dtype=np.float32)
        result = proc.process(audio)
        assert result[0] == 0.0
        assert result[1] == 0.0
        assert result[2] > 0.0

    def test_process_returns_float32(self):
        proc = MurmurProcessor()
        audio = np.array([0.1, 0.2], dtype=np.float32)
        result = proc.process(audio)
        assert result.dtype == np.float32

    def test_process_soft_clips_via_tanh(self):
        proc = MurmurProcessor(gain=10.0, noise_gate_db=-100.0)
        audio = np.array([0.5], dtype=np.float32)
        result = proc.process(audio)
        assert result[0] < 1.0
        assert result[0] > 0.99

    def test_process_empty_audio(self):
        proc = MurmurProcessor()
        audio = np.array([], dtype=np.float32)
        result = proc.process(audio)
        assert len(result) == 0

    def test_process_none_audio(self):
        proc = MurmurProcessor()
        result = proc.process(None)
        assert result is None

    def test_calibrate_sets_noise_floor(self):
        proc = MurmurProcessor()
        noise = np.random.normal(0, 0.01, 8000).astype(np.float32)
        proc.calibrate(noise)
        assert proc.noise_floor is not None
        assert proc.noise_floor > 0

    def test_calibrate_empty_chunk(self):
        proc = MurmurProcessor()
        proc.calibrate(np.array([], dtype=np.float32))
        assert proc.noise_floor is None

    def test_calibrate_none_chunk(self):
        proc = MurmurProcessor()
        proc.calibrate(None)
        assert proc.noise_floor is None

    def test_noise_floor_affects_gate_threshold(self):
        proc = MurmurProcessor(gain=3.0, noise_gate_db=-100.0)
        audio = np.array([0.005, 0.01, 0.5], dtype=np.float32)
        result_no_cal = proc.process(audio.copy())
        assert result_no_cal[0] != 0.0

        noise = np.full(1000, 0.02, dtype=np.float32)
        proc.calibrate(noise)
        result_with_cal = proc.process(audio.copy())
        assert result_with_cal[0] == 0.0
        assert result_with_cal[1] == 0.0
        assert result_with_cal[2] > 0.0


# -- MurmurMode tests ---


class TestMurmurMode:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        self._patch_dir = patch("muttr.config.APP_SUPPORT_DIR", self._tmpdir)
        self._patch_path = patch("muttr.config.CONFIG_PATH", self._config_path)
        self._patch_dir.start()
        self._patch_path.start()
        events.clear()

    def teardown_method(self):
        self._patch_dir.stop()
        self._patch_path.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        events.clear()

    def test_initially_inactive(self):
        mm = MurmurMode()
        assert not mm.active
        assert mm.processor is None

    def test_toggle_activates(self):
        mm = MurmurMode()
        result = mm.toggle()
        assert result is True
        assert mm.active
        assert mm.processor is not None

    def test_toggle_twice_deactivates(self):
        mm = MurmurMode()
        mm.toggle()
        result = mm.toggle()
        assert result is False
        assert not mm.active
        assert mm.processor is None

    def test_activate_method(self):
        mm = MurmurMode()
        mm.activate()
        assert mm.active

    def test_activate_when_already_active(self):
        mm = MurmurMode()
        mm.activate()
        mm.activate()
        assert mm.active

    def test_deactivate_method(self):
        mm = MurmurMode()
        mm.activate()
        mm.deactivate()
        assert not mm.active

    def test_deactivate_when_already_inactive(self):
        mm = MurmurMode()
        mm.deactivate()
        assert not mm.active

    def test_default_gain(self):
        mm = MurmurMode()
        assert mm.gain == DEFAULT_GAIN

    def test_custom_gain_from_config(self):
        with open(self._config_path, "w") as f:
            json.dump({"murmur_gain": 5.0}, f)
        mm = MurmurMode()
        assert mm.gain == 5.0

    def test_min_utterance_ms(self):
        mm = MurmurMode()
        assert mm.min_utterance_ms == DEFAULT_MIN_UTTERANCE_MS

    def test_toggle_emits_event(self):
        received = []
        events.on("murmur_toggled", lambda **kw: received.append(kw))
        mm = MurmurMode()
        mm.toggle()
        assert len(received) == 1
        assert received[0]["active"] is True
        mm.toggle()
        assert len(received) == 2
        assert received[1]["active"] is False

    def test_toggle_persists_state(self):
        mm = MurmurMode()
        mm.toggle()
        with open(self._config_path, "r") as f:
            stored = json.load(f)
        assert stored.get("murmur_active") is True

    def test_processor_gain_matches_config(self):
        with open(self._config_path, "w") as f:
            json.dump({"murmur_gain": 4.5}, f)
        mm = MurmurMode()
        mm.toggle()
        assert mm.processor.gain == 4.5
