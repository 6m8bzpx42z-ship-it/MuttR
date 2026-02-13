"""Audio recording via sounddevice."""

import threading

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024


class Recorder:
    def __init__(self):
        self._chunks = []
        self._stream = None
        self._lock = threading.Lock()
        self._current_level = 0.0

    def start(self):
        self._chunks = []
        self._current_level = 0.0
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._chunks:
                return None
            audio = np.concatenate(self._chunks, axis=0).flatten()
            self._chunks = []

        return audio

    @property
    def level(self):
        return self._current_level

    def _audio_callback(self, indata, frames, time_info, status):
        with self._lock:
            self._chunks.append(indata.copy())
        self._current_level = float(np.abs(indata).mean())
