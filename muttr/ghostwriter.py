"""Ghostwriter -- voice-driven text replacement in any app.

Double-tap fn to select the current sentence/word/line behind the cursor
and re-dictate it. The replacement text is pasted over the selection using
standard macOS paste (Cmd+V over selected text replaces it).
"""

import time

import Quartz

from muttr import config

# Virtual keycodes
kVK_LeftArrow = 0x7B
kVK_RightArrow = 0x7C

# Selection modes
MODE_SENTENCE = "sentence"
MODE_LINE = "line"
MODE_WORD = "word"

VALID_MODES = {MODE_SENTENCE, MODE_LINE, MODE_WORD}


def _post_key(keycode, flags=0, key_down=True):
    """Post a single keyboard event via CGEvent."""
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    event = Quartz.CGEventCreateKeyboardEvent(source, keycode, key_down)
    if flags:
        Quartz.CGEventSetFlags(event, flags)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, event)


def _press_key(keycode, flags=0):
    """Simulate a full key press (down + up) with optional modifier flags."""
    _post_key(keycode, flags, key_down=True)
    _post_key(keycode, flags, key_down=False)


def select_behind_cursor(mode=None):
    """Select text behind the cursor based on the configured mode.

    Simulates keyboard shortcuts to select text:
    - sentence (default): Cmd+Shift+Left (select to start of line)
    - line: Cmd+Shift+Left (same as sentence for v1)
    - word: Option+Shift+Left (select previous word)
    """
    if mode is None:
        cfg = config.load()
        mode = cfg.get("ghostwriter_mode", MODE_SENTENCE)

    if mode not in VALID_MODES:
        mode = MODE_SENTENCE

    time.sleep(0.05)  # brief pause for key state to settle

    if mode == MODE_WORD:
        # Option+Shift+Left: select previous word
        flags = (
            Quartz.kCGEventFlagMaskAlternate
            | Quartz.kCGEventFlagMaskShift
        )
        _press_key(kVK_LeftArrow, flags)
    else:
        # Cmd+Shift+Left: select to start of line (sentence/line mode)
        flags = (
            Quartz.kCGEventFlagMaskCommand
            | Quartz.kCGEventFlagMaskShift
        )
        _press_key(kVK_LeftArrow, flags)

    time.sleep(0.05)  # let the selection register


def get_mode():
    """Return the current ghostwriter selection mode from config."""
    cfg = config.load()
    mode = cfg.get("ghostwriter_mode", MODE_SENTENCE)
    if mode not in VALID_MODES:
        return MODE_SENTENCE
    return mode


def is_enabled():
    """Check if Ghostwriter is enabled in config."""
    cfg = config.load()
    return cfg.get("ghostwriter_enabled", True)
