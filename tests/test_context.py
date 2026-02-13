"""Tests for muttr.context -- clipboard-aware context stitching."""

from unittest.mock import patch, MagicMock
import pytest

from muttr.context import (
    _is_prose,
    build_context_prompt,
    _CLIPBOARD_MAX_CHARS,
    _HISTORY_MAX_CHARS,
    _PROMPT_MAX_CHARS,
)


# -- _is_prose heuristic tests ---


class TestIsProse:
    def test_normal_english(self):
        assert _is_prose("Hello, how are you today?") is True

    def test_empty_string(self):
        assert _is_prose("") is False

    def test_none(self):
        assert _is_prose(None) is False

    def test_short_string(self):
        assert _is_prose("hi") is False

    def test_url(self):
        assert _is_prose("https://example.com/path?q=1") is False

    def test_no_spaces(self):
        assert _is_prose("camelCaseVariableName") is False

    def test_code_like(self):
        assert _is_prose("fn(x) { return x + 1; }") is False

    def test_too_many_special_chars(self):
        assert _is_prose("{{#if (eq a b)}}{{/if}}") is False

    def test_normal_sentence_with_punctuation(self):
        assert _is_prose("Dear Mr. Thompson, please review the attached.") is True

    def test_mixed_content_mostly_prose(self):
        assert _is_prose("I need to update the report for the Monday meeting.") is True


# -- build_context_prompt tests ---


class TestBuildContextPrompt:
    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_returns_prompt_with_clipboard(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = "Send the report to John at Acme Corp"
        mock_hist.return_value = ""
        mock_dict.return_value = ""

        result = build_context_prompt()
        assert result.startswith("Continue: ")
        assert "Acme Corp" in result

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_returns_prompt_with_history(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = ""
        mock_hist.return_value = "I need to send the quarterly report"
        mock_dict.return_value = ""

        result = build_context_prompt()
        assert result.startswith("Continue: ")
        assert "quarterly report" in result

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_returns_prompt_with_dictionary(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = ""
        mock_hist.return_value = ""
        mock_dict.return_value = "Names: Paul, MuttR, Acme Corp"

        result = build_context_prompt()
        assert "MuttR" in result

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_combines_all_sources(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = "Dear Mr. Thompson,"
        mock_hist.return_value = "Meeting about the project"
        mock_dict.return_value = "Names: Paul, Sarah"

        result = build_context_prompt()
        assert "Thompson" in result
        assert "project" in result
        assert "Paul" in result

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_disabled_returns_empty(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": False}
        mock_clip.return_value = "Some clipboard text"
        mock_hist.return_value = "Some history"
        mock_dict.return_value = ""

        result = build_context_prompt()
        assert result == ""

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_skips_code_clipboard(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = "fn(x) { return x + 1; }"
        mock_hist.return_value = ""
        mock_dict.return_value = ""

        result = build_context_prompt()
        # Code-like clipboard should be skipped, so no prompt or empty
        assert "fn(x)" not in result

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_no_context_returns_empty(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = ""
        mock_hist.return_value = ""
        mock_dict.return_value = ""

        result = build_context_prompt()
        assert result == ""

    @patch("muttr.context._read_clipboard_text")
    @patch("muttr.context._get_recent_transcriptions_text")
    @patch("muttr.context._get_custom_dictionary_terms")
    @patch("muttr.config.load")
    def test_prompt_length_capped(self, mock_cfg_load, mock_dict, mock_hist, mock_clip):
        mock_cfg_load.return_value = {"context_stitching": True}
        mock_clip.return_value = "word " * 100  # Long clipboard
        mock_hist.return_value = "text " * 100  # Long history
        mock_dict.return_value = ""

        result = build_context_prompt()
        # "Continue: " prefix is 10 chars; total should be under limit + prefix
        assert len(result) <= _PROMPT_MAX_CHARS + 15
