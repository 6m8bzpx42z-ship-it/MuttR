"""Whisper transcription via faster-whisper."""

import sys

from faster_whisper import WhisperModel

DEFAULT_MODEL = "base.en"
COMPUTE_TYPE = "float16" if sys.platform == "darwin" else "int8"


class Transcriber:
    def __init__(self, model_size=DEFAULT_MODEL):
        self._model_size = model_size
        self._model = None

    def load(self):
        """Load model. Call once at startup (~2s)."""
        self._model = WhisperModel(
            self._model_size,
            device="cpu",
            compute_type="int8",
        )

    def transcribe(self, audio):
        """Transcribe a numpy float32 array at 16kHz. Returns text string."""
        if self._model is None:
            self.load()

        segments, _ = self._model.transcribe(
            audio,
            beam_size=5,
            language="en",
            vad_filter=True,
        )

        return " ".join(segment.text.strip() for segment in segments)
