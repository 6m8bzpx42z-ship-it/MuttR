"""Tests for muttr.transcriber -- Whisper transcription backend."""

from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from muttr.transcriber import (
    WhisperBackend,
    Transcriber,
    create_transcriber,
    DEFAULT_MODEL,
    SAMPLE_RATE,
)


class TestWhisperBackend:
    def test_name_is_whisper(self):
        backend = WhisperBackend()
        assert backend.name == "whisper"

    def test_default_model_size(self):
        backend = WhisperBackend()
        assert backend._model_size == DEFAULT_MODEL

    def test_custom_model_size(self):
        backend = WhisperBackend(model_size="small.en")
        assert backend._model_size == "small.en"

    def test_model_not_loaded_initially(self):
        backend = WhisperBackend()
        assert backend._model is None

    @patch("muttr.transcriber.WhisperBackend.load")
    def test_transcribe_auto_loads_model(self, mock_load):
        backend = WhisperBackend()
        # After calling load, simulate a model being set
        def set_model():
            backend._model = MagicMock()
            # Set up mock to return segments
            mock_seg = MagicMock()
            mock_seg.text = " hello world "
            backend._model.transcribe.return_value = ([mock_seg], None)
        mock_load.side_effect = set_model

        audio = np.zeros(16000, dtype=np.float32)
        result = backend.transcribe(audio)
        mock_load.assert_called_once()
        assert "hello world" in result


class TestCreateTranscriber:
    def test_default_creates_whisper(self):
        backend = create_transcriber()
        assert isinstance(backend, WhisperBackend)

    def test_explicit_whisper(self):
        backend = create_transcriber(engine="whisper")
        assert isinstance(backend, WhisperBackend)

    def test_whisper_with_model_size(self):
        backend = create_transcriber(engine="whisper", model_size="small.en")
        assert isinstance(backend, WhisperBackend)
        assert backend._model_size == "small.en"

    def test_unknown_engine_creates_whisper(self):
        backend = create_transcriber(engine="unknown_engine")
        assert isinstance(backend, WhisperBackend)


class TestTranscriberLegacyWrapper:
    def test_default_engine_is_whisper(self):
        t = Transcriber()
        assert t.name == "whisper"

    def test_name_property(self):
        t = Transcriber(engine="whisper")
        assert t.name == "whisper"

    def test_delegates_load(self):
        t = Transcriber()
        t._backend = MagicMock()
        t.load()
        t._backend.load.assert_called_once()

    def test_delegates_transcribe(self):
        t = Transcriber()
        t._backend = MagicMock()
        t._backend.transcribe.return_value = "hello"
        audio = np.zeros(16000, dtype=np.float32)
        result = t.transcribe(audio)
        assert result == "hello"
        t._backend.transcribe.assert_called_once()

    def test_transcribe_passes_kwargs(self):
        t = Transcriber()
        t._backend = MagicMock()
        t._backend.transcribe.return_value = "hello"
        audio = np.zeros(16000, dtype=np.float32)
        t.transcribe(audio, initial_prompt="test", word_timestamps=True)
        _, kwargs = t._backend.transcribe.call_args
        assert kwargs["initial_prompt"] == "test"
        assert kwargs["word_timestamps"] is True


class TestSampleRateConstant:
    def test_sample_rate_is_16k(self):
        assert SAMPLE_RATE == 16000

    def test_default_model_is_base_en(self):
        assert DEFAULT_MODEL == "base.en"
