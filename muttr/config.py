"""Load/save config with validated defaults."""

import json
import os

APP_SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/MuttR")
CONFIG_PATH = os.path.join(APP_SUPPORT_DIR, "config.json")

DEFAULTS = {
    "cleanup_level": 1,
    "model": "base.en",
    "paste_delay_ms": 60,
    "transcription_engine": "whisper",
    # Context stitching: use clipboard + history to prime Whisper
    "context_stitching": True,
    # Adaptive silence: learn user's speaking cadence for auto-stop
    "adaptive_silence": True,
    # Ghostwriter: voice-driven text replacement
    "ghostwriter_enabled": True,
    "ghostwriter_mode": "sentence",  # "sentence", "line", or "word"
    # Cadence coaching: speech quality feedback
    "cadence_feedback": True,
    # Murmur mode: low-volume dictation
    "murmur_gain": 3.0,
    "murmur_noise_gate_db": -50.0,
    "murmur_min_utterance_ms": 80,
    # First-run onboarding
    "onboarding_completed": False,
}

VALID_MODELS = {"base.en", "small.en"}
VALID_ENGINES = {"whisper"}


def _ensure_dir():
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)


def load():
    """Load config from disk, returning validated dict with defaults applied."""
    _ensure_dir()
    data = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                stored = json.load(f)
            data.update(stored)
        except (json.JSONDecodeError, OSError):
            pass

    # Coerce and validate
    data["cleanup_level"] = max(0, min(2, int(data.get("cleanup_level", 1))))
    if data.get("model") not in VALID_MODELS:
        data["model"] = DEFAULTS["model"]
    if data.get("transcription_engine") not in VALID_ENGINES:
        data["transcription_engine"] = DEFAULTS["transcription_engine"]
    data["paste_delay_ms"] = max(10, min(500, int(data.get("paste_delay_ms", 60))))

    return data


def save(data):
    """Persist config dict to disk."""
    _ensure_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get(key, default=None):
    """Read a single config value."""
    data = load()
    return data.get(key, default)


def set_value(key, value):
    """Update a single config value and persist."""
    data = load()
    data[key] = value
    save(data)
