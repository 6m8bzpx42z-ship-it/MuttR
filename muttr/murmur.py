"""Murmur Mode -- whisper-quiet dictation for shared spaces.

Boosts microphone gain, applies noise gating with ambient calibration,
and lowers the minimum utterance threshold so users can dictate at a
murmur in open offices, libraries, and coffee shops.
"""

import numpy as np

from muttr import config, events

# Defaults
DEFAULT_GAIN = 3.0
DEFAULT_NOISE_GATE_DB = -50.0
DEFAULT_MIN_UTTERANCE_MS = 80
CALIBRATION_SAMPLES = 8000  # 500ms at 16kHz


class MurmurProcessor:
    """Audio preprocessing for low-volume dictation.

    Applies gain boost and noise gating to the audio stream.
    Call ``calibrate()`` with an initial silence chunk to establish
    the ambient noise floor before processing real audio.
    """

    def __init__(self, gain: float = DEFAULT_GAIN,
                 noise_gate_db: float = DEFAULT_NOISE_GATE_DB):
        self.gain = gain
        self.noise_gate_threshold = 10 ** (noise_gate_db / 20)
        self._noise_floor: float | None = None

    def calibrate(self, audio_chunk: np.ndarray) -> None:
        """Estimate ambient noise floor from an initial silence chunk.

        Uses the 85th percentile of absolute sample values to capture
        the ambient noise level without being skewed by outliers.
        """
        if audio_chunk is None or len(audio_chunk) == 0:
            return
        self._noise_floor = float(np.percentile(np.abs(audio_chunk), 85))

    @property
    def noise_floor(self) -> float | None:
        return self._noise_floor

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply gain boost and noise gating to an audio chunk.

        1. Noise gate: zero out samples below threshold
        2. Apply gain multiplier
        3. Soft clip via tanh to prevent distortion
        """
        if audio is None or len(audio) == 0:
            return audio

        # Noise gate threshold: max of configured threshold and 1.5x noise floor
        gate_threshold = max(
            self.noise_gate_threshold,
            (self._noise_floor or 0) * 1.5,
        )

        # Apply noise gate
        gated = np.where(np.abs(audio) < gate_threshold, 0.0, audio)

        # Apply gain
        boosted = gated * self.gain

        # Soft clip to prevent distortion
        boosted = np.tanh(boosted)

        return boosted.astype(np.float32)


class MurmurMode:
    """Manages the Murmur Mode state and audio processor.

    Toggle on/off via ``toggle()``. When active, provides a
    ``MurmurProcessor`` for audio preprocessing.
    """

    def __init__(self):
        self._active = False
        self._processor: MurmurProcessor | None = None
        self._load_config()

    def _load_config(self):
        """Load murmur settings from config."""
        cfg = config.load()
        self._gain = cfg.get("murmur_gain", DEFAULT_GAIN)
        self._noise_gate_db = cfg.get("murmur_noise_gate_db", DEFAULT_NOISE_GATE_DB)
        self._min_utterance_ms = cfg.get("murmur_min_utterance_ms", DEFAULT_MIN_UTTERANCE_MS)

    @property
    def active(self) -> bool:
        return self._active

    @property
    def processor(self) -> MurmurProcessor | None:
        """Return the active processor, or None if murmur mode is off."""
        return self._processor if self._active else None

    @property
    def gain(self) -> float:
        return self._gain

    @property
    def min_utterance_ms(self) -> int:
        return self._min_utterance_ms

    def toggle(self) -> bool:
        """Toggle murmur mode on/off. Returns the new state."""
        self._active = not self._active

        if self._active:
            self._load_config()
            self._processor = MurmurProcessor(
                gain=self._gain,
                noise_gate_db=self._noise_gate_db,
            )
            events.emit("murmur_toggled", active=True)
        else:
            self._processor = None
            events.emit("murmur_toggled", active=False)

        # Persist the state
        config.set_value("murmur_active", self._active)
        return self._active

    def activate(self) -> None:
        """Explicitly activate murmur mode."""
        if not self._active:
            self.toggle()

    def deactivate(self) -> None:
        """Explicitly deactivate murmur mode."""
        if self._active:
            self.toggle()
