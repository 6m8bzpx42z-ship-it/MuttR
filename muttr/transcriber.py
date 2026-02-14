"""Transcription backend: Whisper (faster-whisper)."""

import logging
from typing import Protocol

import numpy as np

log = logging.getLogger(__name__)

DEFAULT_MODEL = "base.en"
SAMPLE_RATE = 16000


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------

class TranscriberBackend(Protocol):
    """Interface that every transcription backend must satisfy."""

    def load(self) -> None: ...
    def transcribe(self, audio: np.ndarray, **kwargs) -> str: ...
    @property
    def name(self) -> str: ...


# ---------------------------------------------------------------------------
# Whisper backend (faster-whisper / CTranslate2)
# ---------------------------------------------------------------------------

class WhisperBackend:
    """Wraps faster-whisper for local CPU transcription."""

    def __init__(self, model_size: str = DEFAULT_MODEL):
        self._model_size = model_size
        self._model = None

    @property
    def name(self) -> str:
        return "whisper"

    def load(self) -> None:
        from faster_whisper import WhisperModel

        log.info("Loading Whisper model %s ...", self._model_size)
        self._model = WhisperModel(
            self._model_size,
            device="cpu",
            compute_type="int8",
        )
        log.info("Whisper model loaded.")

    def transcribe(self, audio: np.ndarray, **kwargs) -> str:
        if self._model is None:
            self.load()

        initial_prompt = kwargs.get("initial_prompt") or None
        word_timestamps = kwargs.get("word_timestamps", False)

        segments, _ = self._model.transcribe(
            audio,
            beam_size=5,
            language="en",
            vad_filter=True,
            initial_prompt=initial_prompt,
            word_timestamps=word_timestamps,
        )
        segment_list = list(segments)

        # If word_timestamps requested, return segments for confidence analysis
        if word_timestamps and kwargs.get("_return_segments"):
            return segment_list

        return " ".join(segment.text.strip() for segment in segment_list)


# ---------------------------------------------------------------------------
# Legacy compat wrapper
# ---------------------------------------------------------------------------

class Transcriber:
    """Drop-in replacement for the old single-engine Transcriber class.

    Wraps a backend and delegates load/transcribe calls.  app.py can still
    instantiate ``Transcriber()`` without changes, but new code should prefer
    ``create_transcriber()`` for explicit backend selection.
    """

    def __init__(self, model_size: str = DEFAULT_MODEL, engine: str = "whisper"):
        self._backend = create_transcriber(engine=engine, model_size=model_size)

    def load(self) -> None:
        self._backend.load()

    def transcribe(self, audio: np.ndarray, **kwargs) -> str:
        return self._backend.transcribe(audio, **kwargs)

    @property
    def name(self) -> str:
        return self._backend.name


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_transcriber(
    engine: str = "whisper",
    model_size: str = DEFAULT_MODEL,
) -> TranscriberBackend:
    """Create a Whisper transcription backend."""
    return WhisperBackend(model_size=model_size)
