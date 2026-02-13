"""Multi-backend transcription: Whisper (faster-whisper) and Parakeet-MLX."""

import logging
import tempfile
import wave
from typing import Protocol

import numpy as np

log = logging.getLogger(__name__)

DEFAULT_MODEL = "base.en"
PARAKEET_MODEL = "mlx-community/parakeet-tdt-0.6b-v3"
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
# Parakeet-MLX backend
# ---------------------------------------------------------------------------

def _parakeet_available() -> bool:
    """Check whether parakeet-mlx can be imported."""
    try:
        import parakeet_mlx  # noqa: F401
        return True
    except ImportError:
        return False


class ParakeetBackend:
    """Wraps parakeet-mlx (NVIDIA Parakeet on Apple MLX)."""

    def __init__(self, model_id: str = PARAKEET_MODEL):
        self._model_id = model_id
        self._model = None
        self._loading = False

    @property
    def name(self) -> str:
        return "parakeet"

    def load(self) -> None:
        from parakeet_mlx import from_pretrained

        self._loading = True
        print(f"MuttR: Downloading/loading Parakeet model {self._model_id} (this may take a while on first use)...")
        log.info("Loading Parakeet model %s ...", self._model_id)
        self._model = from_pretrained(self._model_id)
        self._loading = False
        print("MuttR: Parakeet model ready.")
        log.info("Parakeet model loaded.")

    def transcribe(self, audio: np.ndarray, **kwargs) -> str:
        if self._model is None:
            self.load()

        # parakeet-mlx.transcribe() expects a file path, so write a temp WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(SAMPLE_RATE)
                pcm = (audio * 32767).astype(np.int16)
                wf.writeframes(pcm.tobytes())

        try:
            result = self._model.transcribe(tmp_path)
            return result.text.strip()
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


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
    """Create the right backend based on engine name.

    Falls back to Whisper if Parakeet is requested but not installed.
    """
    if engine == "parakeet":
        if _parakeet_available():
            return ParakeetBackend()
        log.warning(
            "Parakeet-MLX not installed; falling back to Whisper. "
            "Install with: pip install parakeet-mlx"
        )
    return WhisperBackend(model_size=model_size)
