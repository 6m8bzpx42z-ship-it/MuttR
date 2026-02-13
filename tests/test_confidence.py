"""Tests for muttr.confidence -- Whisper confidence heatmap."""

from unittest.mock import patch, MagicMock
import pytest

from muttr.confidence import (
    WordInfo,
    TranscriptionResult,
    extract_word_confidence,
    should_show_review,
    TIER_HIGH,
    TIER_MEDIUM,
    TIER_LOW,
    DEFAULT_HIGH_THRESHOLD,
    DEFAULT_LOW_THRESHOLD,
)


# -- WordInfo tests ---


class TestWordInfo:
    def test_high_confidence(self):
        w = WordInfo(word="hello", start=0.0, end=0.5, probability=0.9)
        assert w.tier == TIER_HIGH

    def test_medium_confidence(self):
        w = WordInfo(word="Thompson", start=0.5, end=1.0, probability=0.55)
        assert w.tier == TIER_MEDIUM

    def test_low_confidence(self):
        w = WordInfo(word="xyz", start=1.0, end=1.5, probability=0.2)
        assert w.tier == TIER_LOW

    def test_exact_high_threshold(self):
        w = WordInfo(word="test", start=0.0, end=0.5, probability=DEFAULT_HIGH_THRESHOLD)
        assert w.tier == TIER_HIGH

    def test_just_below_high_threshold(self):
        w = WordInfo(word="test", start=0.0, end=0.5, probability=DEFAULT_HIGH_THRESHOLD - 0.01)
        assert w.tier == TIER_MEDIUM

    def test_exact_low_threshold(self):
        w = WordInfo(word="test", start=0.0, end=0.5, probability=DEFAULT_LOW_THRESHOLD)
        assert w.tier == TIER_MEDIUM

    def test_just_below_low_threshold(self):
        w = WordInfo(word="test", start=0.0, end=0.5, probability=DEFAULT_LOW_THRESHOLD - 0.01)
        assert w.tier == TIER_LOW

    def test_zero_probability(self):
        w = WordInfo(word="?", start=0.0, end=0.1, probability=0.0)
        assert w.tier == TIER_LOW

    def test_full_probability(self):
        w = WordInfo(word="the", start=0.0, end=0.1, probability=1.0)
        assert w.tier == TIER_HIGH


# -- TranscriptionResult tests ---


class TestTranscriptionResult:
    def test_plain_text_result(self):
        result = TranscriptionResult(text="hello world")
        assert result.text == "hello world"
        assert not result.has_word_confidence
        assert not result.has_low_confidence_words

    def test_all_high_confidence(self):
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("world", 0.5, 1.0, 0.90),
        ]
        result = TranscriptionResult(text="hello world", words=words, has_word_confidence=True)
        assert not result.has_low_confidence_words
        assert len(result.get_low_confidence_words()) == 0

    def test_mixed_confidence(self):
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("Thompson", 0.5, 1.0, 0.45),
            WordInfo("xyz", 1.0, 1.5, 0.2),
        ]
        result = TranscriptionResult(text="hello Thompson xyz", words=words, has_word_confidence=True)
        assert result.has_low_confidence_words
        low = result.get_low_confidence_words()
        assert len(low) == 2
        assert low[0].word == "Thompson"
        assert low[1].word == "xyz"

    def test_get_text_with_tiers(self):
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("world", 0.5, 1.0, 0.3),
        ]
        result = TranscriptionResult(text="hello world", words=words, has_word_confidence=True)
        tiers = result.get_text_with_tiers()
        assert tiers == [("hello", TIER_HIGH), ("world", TIER_LOW)]

    def test_get_text_with_tiers_no_words(self):
        result = TranscriptionResult(text="hello world")
        tiers = result.get_text_with_tiers()
        assert tiers == [("hello world", TIER_HIGH)]

    def test_replace_word(self):
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("wrold", 0.5, 1.0, 0.3),
        ]
        result = TranscriptionResult(text="hello wrold", words=words, has_word_confidence=True)
        result.replace_word(1, "world")
        assert result.words[1].word == "world"
        assert result.words[1].probability == 1.0
        assert result.text == "hello world"

    def test_replace_word_out_of_bounds(self):
        words = [WordInfo("hello", 0.0, 0.5, 0.95)]
        result = TranscriptionResult(text="hello", words=words, has_word_confidence=True)
        result.replace_word(5, "nope")  # Should not crash
        assert result.text == "hello"


# -- extract_word_confidence tests ---


class TestExtractWordConfidence:
    def test_empty_segments(self):
        assert extract_word_confidence([]) == []

    def test_segments_without_words_attr(self):
        seg = MagicMock()
        seg.words = None
        assert extract_word_confidence([seg]) == []

    def test_segments_with_words(self):
        word1 = MagicMock()
        word1.word = " hello"
        word1.start = 0.0
        word1.end = 0.5
        word1.probability = 0.95

        word2 = MagicMock()
        word2.word = " world "
        word2.start = 0.5
        word2.end = 1.0
        word2.probability = 0.3

        seg = MagicMock()
        seg.words = [word1, word2]

        result = extract_word_confidence([seg])
        assert len(result) == 2
        assert result[0].word == "hello"
        assert result[0].probability == 0.95
        assert result[1].word == "world"
        assert result[1].probability == 0.3

    def test_multiple_segments(self):
        w1 = MagicMock(word="a", start=0.0, end=0.1, probability=0.9)
        w2 = MagicMock(word="b", start=0.1, end=0.2, probability=0.8)
        seg1 = MagicMock(words=[w1])
        seg2 = MagicMock(words=[w2])

        result = extract_word_confidence([seg1, seg2])
        assert len(result) == 2


# -- should_show_review tests ---


class TestShouldShowReview:
    def test_no_word_confidence(self):
        result = TranscriptionResult(text="hello")
        assert not should_show_review(result)

    def test_all_high_confidence_no_review(self):
        words = [WordInfo("hello", 0.0, 0.5, 0.95)]
        result = TranscriptionResult(text="hello", words=words, has_word_confidence=True)
        assert not should_show_review(result)

    @patch("muttr.config.load")
    def test_low_confidence_with_review_enabled(self, mock_cfg_load):
        mock_cfg_load.return_value = {"confidence_review": True}
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("wrold", 0.5, 1.0, 0.3),
        ]
        result = TranscriptionResult(text="hello wrold", words=words, has_word_confidence=True)
        assert should_show_review(result)

    @patch("muttr.config.load")
    def test_low_confidence_with_review_disabled(self, mock_cfg_load):
        mock_cfg_load.return_value = {"confidence_review": False}
        words = [
            WordInfo("hello", 0.0, 0.5, 0.95),
            WordInfo("wrold", 0.5, 1.0, 0.3),
        ]
        result = TranscriptionResult(text="hello wrold", words=words, has_word_confidence=True)
        assert not should_show_review(result)
