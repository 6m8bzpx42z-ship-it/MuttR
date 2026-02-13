"""Dictation cadence fingerprinting -- adaptive silence threshold + speech coaching.

Learns the user's speaking cadence over time and adapts silence detection
thresholds to match their natural rhythm. Stores only numeric timing data;
no audio or transcript content is persisted.

Cadence Coaching additions:
- SpeechMetrics: compute WPM, audio energy, filler count from transcription data
- SpeechProfile: rolling baseline of speaking patterns for micro-feedback
- Feedback labels: "Fast", "Quiet", "Clear", "Steady" emitted after transcription
"""

import json
import logging
import os
import re
import time

import numpy as np

log = logging.getLogger(__name__)

# Pause detection: RMS below this floor for > _MIN_PAUSE_MS = a pause
_RMS_FLOOR = 0.005
_MIN_PAUSE_MS = 100  # minimum duration to count as an intra-speech pause

# EMA smoothing factor -- adapts slowly over sessions
_EMA_ALPHA = 0.1

# Minimum samples before the profile is considered trained
_MIN_SAMPLES = 20

# Absolute bounds on the auto-stop threshold
_FLOOR_MS = 800
_CEILING_MS = 3000
_DEFAULT_AUTO_STOP_MS = 2000

# Speaking pace categories
PACE_FAST = "Fast"
PACE_AVERAGE = "Average"
PACE_DELIBERATE = "Deliberate"


def _cadence_path() -> str:
    from muttr.config import APP_SUPPORT_DIR
    return os.path.join(APP_SUPPORT_DIR, "cadence.json")


class CadenceProfile:
    """Persistent cadence statistics."""

    def __init__(
        self,
        mean_pause_ms: float = 0.0,
        p75_pause_ms: float = 0.0,
        p90_pause_ms: float = 0.0,
        sample_count: int = 0,
    ):
        self.mean_pause_ms = mean_pause_ms
        self.p75_pause_ms = p75_pause_ms
        self.p90_pause_ms = p90_pause_ms
        self.sample_count = sample_count

    @property
    def is_trained(self) -> bool:
        return self.sample_count >= _MIN_SAMPLES

    @property
    def pace_label(self) -> str:
        if not self.is_trained:
            return PACE_AVERAGE
        if self.mean_pause_ms < 300:
            return PACE_FAST
        if self.mean_pause_ms <= 600:
            return PACE_AVERAGE
        return PACE_DELIBERATE

    def to_dict(self) -> dict:
        return {
            "mean_pause_ms": round(self.mean_pause_ms, 1),
            "p75_pause_ms": round(self.p75_pause_ms, 1),
            "p90_pause_ms": round(self.p90_pause_ms, 1),
            "sample_count": self.sample_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CadenceProfile":
        return cls(
            mean_pause_ms=float(d.get("mean_pause_ms", 0)),
            p75_pause_ms=float(d.get("p75_pause_ms", 0)),
            p90_pause_ms=float(d.get("p90_pause_ms", 0)),
            sample_count=int(d.get("sample_count", 0)),
        )


def load_profile() -> CadenceProfile:
    """Load the cadence profile from disk."""
    path = _cadence_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return CadenceProfile.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError, KeyError):
            pass
    return CadenceProfile()


def save_profile(profile: CadenceProfile) -> None:
    """Persist the cadence profile to disk."""
    path = _cadence_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile.to_dict(), f, indent=2)


def reset_profile() -> None:
    """Delete the cadence profile so the user can start fresh."""
    path = _cadence_path()
    try:
        os.remove(path)
    except OSError:
        pass


def get_auto_stop_ms() -> int:
    """Return the adaptive auto-stop threshold in milliseconds.

    Uses 2x the user's 90th-percentile pause duration, clamped to
    [800, 3000] ms. Returns the default 2000 ms if the profile is not
    yet trained.
    """
    try:
        from muttr import config
        cfg = config.load()
        if not cfg.get("adaptive_silence", True):
            return _DEFAULT_AUTO_STOP_MS
    except Exception:
        pass

    profile = load_profile()
    if not profile.is_trained:
        return _DEFAULT_AUTO_STOP_MS

    raw = profile.p90_pause_ms * 2.0
    return max(_FLOOR_MS, min(_CEILING_MS, int(raw)))


class CadenceTracker:
    """Tracks intra-speech pauses during a recording session.

    Feed it audio levels via ``update(rms_level)`` at a regular interval
    (e.g. every audio block). After the recording session, call
    ``finish_session()`` to persist the aggregated stats.
    """

    def __init__(self, update_interval_ms: float = 64.0):
        self._interval_ms = update_interval_ms
        self._in_pause = False
        self._pause_start: float | None = None
        self._had_speech = False
        self._pauses_ms: list[float] = []

    def update(self, rms_level: float) -> None:
        """Called with the current RMS audio level for each block."""
        now = time.monotonic()

        if rms_level < _RMS_FLOOR:
            # Silence
            if not self._in_pause:
                self._in_pause = True
                self._pause_start = now
        else:
            # Speech
            if self._in_pause and self._pause_start is not None and self._had_speech:
                pause_ms = (now - self._pause_start) * 1000
                if pause_ms >= _MIN_PAUSE_MS:
                    self._pauses_ms.append(pause_ms)
            self._in_pause = False
            self._pause_start = None
            self._had_speech = True

    @property
    def session_pauses(self) -> list[float]:
        """Pause durations collected in this session (ms)."""
        return list(self._pauses_ms)

    def finish_session(self) -> CadenceProfile:
        """Merge this session's pause data into the persistent profile using EMA.

        Returns the updated profile.
        """
        profile = load_profile()

        if not self._pauses_ms:
            return profile

        # Compute session stats
        sorted_pauses = sorted(self._pauses_ms)
        n = len(sorted_pauses)
        session_mean = sum(sorted_pauses) / n
        session_p75 = sorted_pauses[int(n * 0.75)] if n >= 4 else session_mean
        session_p90 = sorted_pauses[int(n * 0.9)] if n >= 10 else session_p75

        # Merge via EMA
        if profile.sample_count == 0:
            profile.mean_pause_ms = session_mean
            profile.p75_pause_ms = session_p75
            profile.p90_pause_ms = session_p90
        else:
            a = _EMA_ALPHA
            profile.mean_pause_ms = (1 - a) * profile.mean_pause_ms + a * session_mean
            profile.p75_pause_ms = (1 - a) * profile.p75_pause_ms + a * session_p75
            profile.p90_pause_ms = (1 - a) * profile.p90_pause_ms + a * session_p90

        profile.sample_count += n

        save_profile(profile)
        return profile


# ---------------------------------------------------------------------------
# Cadence Coaching: Speech Metrics + Feedback
# ---------------------------------------------------------------------------

# Filler pattern for counting (mirrors cleanup.py but standalone for decoupling)
_FILLER_WORDS = [
    r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b",
    r"\bbasically\b", r"\bactually\b", r"\bliterally\b",
    r"\bI mean\b", r"\bsort of\b", r"\bkind of\b",
]
_FILLER_PATTERN = re.compile(
    "|".join(_FILLER_WORDS),
    re.IGNORECASE,
)

# Feedback labels
FEEDBACK_FAST = "Fast"
FEEDBACK_QUIET = "Quiet"
FEEDBACK_CLEAR = "Clear"
FEEDBACK_STEADY = "Steady"

# Speech profile rolling window size
_SPEECH_PROFILE_WINDOW = 100

# Minimum entries before speech profile produces feedback
_SPEECH_PROFILE_MIN_ENTRIES = 5


def _speech_profile_path() -> str:
    from muttr.config import APP_SUPPORT_DIR
    return os.path.join(APP_SUPPORT_DIR, "speech_profile.json")


class SpeechMetrics:
    """Compute speech quality metrics from audio + transcript."""

    @staticmethod
    def analyze(audio: np.ndarray, transcript: str,
                duration_s: float, confidence: float = 0.0) -> dict:
        """Analyze a transcription and return quality metrics.

        Args:
            audio: Raw audio numpy array.
            transcript: Transcribed text.
            duration_s: Duration of the recording in seconds.
            confidence: Average transcription confidence (0-1).

        Returns:
            Dict with keys: wpm, energy_rms, confidence, filler_count, word_count.
        """
        word_count = len(transcript.split()) if transcript.strip() else 0
        wpm = (word_count / duration_s) * 60 if duration_s > 0 else 0.0
        avg_energy = float(np.sqrt(np.mean(audio ** 2))) if len(audio) > 0 else 0.0
        filler_count = len(_FILLER_PATTERN.findall(transcript))

        return {
            "wpm": round(wpm, 1),
            "energy_rms": round(avg_energy, 4),
            "confidence": round(confidence, 3),
            "filler_count": filler_count,
            "word_count": word_count,
        }


class SpeechProfile:
    """Maintains rolling statistics of the user's speaking patterns.

    Stores the last N metric entries and computes baselines (mean)
    for WPM and energy. Provides micro-feedback comparing current
    metrics against the personal baseline.
    """

    def __init__(self):
        self.entries: list[dict] = []
        self.baseline_wpm: float = 0.0
        self.baseline_energy: float = 0.0

    def to_dict(self) -> dict:
        return {
            "entries": self.entries[-_SPEECH_PROFILE_WINDOW:],
            "baseline_wpm": round(self.baseline_wpm, 1),
            "baseline_energy": round(self.baseline_energy, 4),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SpeechProfile":
        p = cls()
        p.entries = d.get("entries", [])[-_SPEECH_PROFILE_WINDOW:]
        p.baseline_wpm = float(d.get("baseline_wpm", 0))
        p.baseline_energy = float(d.get("baseline_energy", 0))
        return p

    def update(self, metrics: dict) -> None:
        """Add new metrics and recompute baselines."""
        self.entries.append(metrics)
        # Trim to rolling window
        if len(self.entries) > _SPEECH_PROFILE_WINDOW:
            self.entries = self.entries[-_SPEECH_PROFILE_WINDOW:]
        self._recompute_baselines()

    def _recompute_baselines(self) -> None:
        """Recompute baseline averages from stored entries."""
        if not self.entries:
            return
        wpm_vals = [e["wpm"] for e in self.entries if e.get("wpm", 0) > 0]
        energy_vals = [e["energy_rms"] for e in self.entries if e.get("energy_rms", 0) > 0]
        self.baseline_wpm = sum(wpm_vals) / len(wpm_vals) if wpm_vals else 0.0
        self.baseline_energy = sum(energy_vals) / len(energy_vals) if energy_vals else 0.0

    @property
    def has_baseline(self) -> bool:
        """True if we have enough data to provide meaningful feedback."""
        return len(self.entries) >= _SPEECH_PROFILE_MIN_ENTRIES

    def get_feedback(self, metrics: dict) -> str | None:
        """Compare current metrics against personal baseline.

        Returns None (normal), 'Fast', 'Quiet', 'Clear', or 'Steady'.
        Only provides feedback when we have a trained baseline.
        """
        if not self.has_baseline:
            return None

        # Fast: WPM > 125% of baseline
        if self.baseline_wpm > 0 and metrics.get("wpm", 0) > self.baseline_wpm * 1.25:
            return FEEDBACK_FAST

        # Quiet: energy < 40% of baseline
        if self.baseline_energy > 0 and metrics.get("energy_rms", 0) < self.baseline_energy * 0.4:
            return FEEDBACK_QUIET

        # Clear: high confidence and no fillers
        if metrics.get("confidence", 0) > 0.92 and metrics.get("filler_count", 0) == 0:
            return FEEDBACK_CLEAR

        # Steady: within normal range, decent confidence
        if metrics.get("confidence", 0) > 0.8:
            return FEEDBACK_STEADY

        return None


def load_speech_profile() -> SpeechProfile:
    """Load the speech profile from disk."""
    path = _speech_profile_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return SpeechProfile.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError, KeyError):
            pass
    return SpeechProfile()


def save_speech_profile(profile: SpeechProfile) -> None:
    """Persist the speech profile to disk."""
    path = _speech_profile_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile.to_dict(), f, indent=2)


def reset_speech_profile() -> None:
    """Delete the speech profile."""
    path = _speech_profile_path()
    try:
        os.remove(path)
    except OSError:
        pass
