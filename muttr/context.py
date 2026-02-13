"""Clipboard-aware context stitching for Whisper initial_prompt priming.

Assembles context from the clipboard, recent transcriptions, and the user's
custom dictionary to prime Whisper with relevant vocabulary before transcription.
All data stays local -- nothing leaves the machine.
"""

import re
import logging

log = logging.getLogger(__name__)

# Maximum characters to pull from each context source
_CLIPBOARD_MAX_CHARS = 200
_HISTORY_MAX_CHARS = 200
# Whisper's initial_prompt is limited to ~224 tokens; keep well under that
_PROMPT_MAX_CHARS = 400


def _read_clipboard_text() -> str:
    """Read plain text from the system clipboard. Returns empty string on failure."""
    try:
        import Cocoa
        pb = Cocoa.NSPasteboard.generalPasteboard()
        text = pb.stringForType_(Cocoa.NSPasteboardTypeString)
        return str(text) if text else ""
    except Exception:
        return ""


def _is_prose(text: str) -> bool:
    """Heuristic: return True if text looks like natural language prose.

    Skip clipboard content that is code, URLs, or non-prose (too many special
    chars, no spaces, etc.).
    """
    if not text or len(text.strip()) < 5:
        return False
    # Too many special characters relative to length
    special = sum(1 for c in text if c in "{}[]()<>|&;$#@!~`^\\=+*")
    if special / max(len(text), 1) > 0.15:
        return False
    # No spaces => probably a URL, path, or token
    if " " not in text.strip():
        return False
    # Looks like a URL
    if re.match(r"https?://", text.strip()):
        return False
    return True


def _get_recent_transcriptions_text(limit: int = 2) -> str:
    """Fetch the last N transcriptions from history and return concatenated text."""
    try:
        from muttr import history
        entries = history.get_recent(limit=limit)
        texts = [e.get("cleaned_text") or e.get("raw_text", "") for e in entries]
        return " ".join(t.strip() for t in texts if t.strip())
    except Exception:
        return ""


def _get_custom_dictionary_terms() -> str:
    """Return custom dictionary terms as a hint string."""
    try:
        from muttr.cleanup import CUSTOM_PROPER_NOUNS
        if CUSTOM_PROPER_NOUNS:
            terms = list(CUSTOM_PROPER_NOUNS.values())[:30]
            return "Names: " + ", ".join(terms)
    except Exception:
        pass
    return ""


def build_context_prompt() -> str:
    """Assemble a Whisper initial_prompt from clipboard + history + dictionary.

    Returns an empty string if context stitching is disabled or no useful
    context is available.
    """
    try:
        from muttr import config
        cfg = config.load()
        if not cfg.get("context_stitching", True):
            return ""
    except Exception:
        pass

    parts = []

    # 1. Clipboard text
    clip = _read_clipboard_text()
    if _is_prose(clip):
        parts.append(clip[-_CLIPBOARD_MAX_CHARS:])

    # 2. Recent transcriptions
    recent = _get_recent_transcriptions_text(limit=2)
    if recent:
        parts.append(recent[-_HISTORY_MAX_CHARS:])

    # 3. Custom dictionary terms
    terms = _get_custom_dictionary_terms()
    if terms:
        parts.append(terms)

    if not parts:
        return ""

    context = " ".join(parts)
    # Trim to max prompt length
    if len(context) > _PROMPT_MAX_CHARS:
        context = context[-_PROMPT_MAX_CHARS:]

    return f"Continue: {context}"
