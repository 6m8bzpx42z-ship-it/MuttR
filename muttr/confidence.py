"""Confidence analysis for transcription results.

Extracts per-word confidence data from faster-whisper's word_timestamps output
and classifies words into confidence tiers for heatmap display.
"""

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# Confidence thresholds (configurable via config)
DEFAULT_HIGH_THRESHOLD = 0.7
DEFAULT_LOW_THRESHOLD = 0.4

# Tier names
TIER_HIGH = "high"      # white / normal
TIER_MEDIUM = "medium"  # amber
TIER_LOW = "low"        # red


@dataclass
class WordInfo:
    """Per-word transcription data with confidence."""
    word: str
    start: float
    end: float
    probability: float

    @property
    def tier(self) -> str:
        if self.probability >= DEFAULT_HIGH_THRESHOLD:
            return TIER_HIGH
        if self.probability >= DEFAULT_LOW_THRESHOLD:
            return TIER_MEDIUM
        return TIER_LOW


@dataclass
class TranscriptionResult:
    """Full transcription result with optional per-word confidence data."""
    text: str
    words: list[WordInfo] = field(default_factory=list)
    has_word_confidence: bool = False

    @property
    def has_low_confidence_words(self) -> bool:
        """True if any words are below the high-confidence threshold."""
        return any(w.tier != TIER_HIGH for w in self.words)

    def get_low_confidence_words(self) -> list[WordInfo]:
        """Return words below the high-confidence threshold."""
        return [w for w in self.words if w.tier != TIER_HIGH]

    def get_text_with_tiers(self) -> list[tuple[str, str]]:
        """Return list of (word, tier) tuples for rendering."""
        if not self.words:
            return [(self.text, TIER_HIGH)]
        return [(w.word, w.tier) for w in self.words]

    def replace_word(self, index: int, new_word: str) -> None:
        """Replace a word at the given index (for tap-to-correct)."""
        if 0 <= index < len(self.words):
            self.words[index] = WordInfo(
                word=new_word,
                start=self.words[index].start,
                end=self.words[index].end,
                probability=1.0,  # user-corrected = full confidence
            )
            self.text = " ".join(w.word for w in self.words)


def extract_word_confidence(segments) -> list[WordInfo]:
    """Extract WordInfo list from faster-whisper segment objects.

    Each segment from faster-whisper (with word_timestamps=True) has a
    ``words`` attribute containing objects with ``word``, ``start``, ``end``,
    and ``probability`` fields.
    """
    words = []
    for segment in segments:
        seg_words = getattr(segment, "words", None)
        if seg_words:
            for w in seg_words:
                words.append(WordInfo(
                    word=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    probability=w.probability,
                ))
    return words


def should_show_review(result: TranscriptionResult) -> bool:
    """Determine whether the confidence review overlay should be shown.

    Only shows if confidence review is enabled in config AND there are
    low-confidence words in the result.
    """
    if not result.has_word_confidence:
        return False
    if not result.has_low_confidence_words:
        return False
    try:
        from muttr import config
        cfg = config.load()
        return cfg.get("confidence_review", False)
    except Exception:
        return False
