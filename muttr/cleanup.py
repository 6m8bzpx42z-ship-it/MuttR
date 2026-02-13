"""Deterministic text cleanup using regex rules."""

import re

FILLER_WORDS = [
    r"\bum\b",
    r"\buh\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bI mean\b",
    r"\bsort of\b",
    r"\bkind of\b",
]

FILLER_PATTERN = re.compile(
    r",?\s*(?:" + "|".join(FILLER_WORDS) + r")\s*,?\s*",
    re.IGNORECASE,
)


def clean_text(text):
    """Apply all cleanup rules to transcribed text."""
    if not text or not text.strip():
        return ""

    result = text.strip()

    # Remove filler words (with surrounding commas/spaces)
    result = FILLER_PATTERN.sub(" ", result)

    # Remove repeated words: "the the" → "the"
    result = re.sub(r"\b(\w+)(\s+\1)+\b", r"\1", result, flags=re.IGNORECASE)

    # Remove false starts: "I was I was going" → "I was going"
    result = re.sub(
        r"\b(\w+(?:\s+\w+)?)\s+\1\b", r"\1", result, flags=re.IGNORECASE
    )

    # Normalize whitespace
    result = re.sub(r"\s+", " ", result).strip()

    if not result:
        return ""

    # Capitalize first letter
    result = result[0].upper() + result[1:]

    # Ensure sentence-ending punctuation
    if result[-1] not in ".!?":
        result += "."

    return result
