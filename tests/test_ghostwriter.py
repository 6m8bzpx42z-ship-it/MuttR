"""Tests for muttr.ghostwriter -- voice-driven text replacement."""

from unittest.mock import patch, MagicMock
import pytest

from muttr.ghostwriter import (
    get_mode,
    is_enabled,
    select_behind_cursor,
    MODE_SENTENCE,
    MODE_LINE,
    MODE_WORD,
    VALID_MODES,
    kVK_LeftArrow,
)


# -- Mode and config tests ---


class TestGetMode:
    @patch("muttr.config.load")
    def test_default_mode_is_sentence(self, mock_load):
        mock_load.return_value = {}
        assert get_mode() == MODE_SENTENCE

    @patch("muttr.config.load")
    def test_sentence_mode(self, mock_load):
        mock_load.return_value = {"ghostwriter_mode": "sentence"}
        assert get_mode() == MODE_SENTENCE

    @patch("muttr.config.load")
    def test_word_mode(self, mock_load):
        mock_load.return_value = {"ghostwriter_mode": "word"}
        assert get_mode() == MODE_WORD

    @patch("muttr.config.load")
    def test_line_mode(self, mock_load):
        mock_load.return_value = {"ghostwriter_mode": "line"}
        assert get_mode() == MODE_LINE

    @patch("muttr.config.load")
    def test_invalid_mode_falls_back_to_sentence(self, mock_load):
        mock_load.return_value = {"ghostwriter_mode": "paragraph"}
        assert get_mode() == MODE_SENTENCE


class TestIsEnabled:
    @patch("muttr.config.load")
    def test_enabled_by_default(self, mock_load):
        mock_load.return_value = {}
        assert is_enabled() is True

    @patch("muttr.config.load")
    def test_explicitly_enabled(self, mock_load):
        mock_load.return_value = {"ghostwriter_enabled": True}
        assert is_enabled() is True

    @patch("muttr.config.load")
    def test_disabled(self, mock_load):
        mock_load.return_value = {"ghostwriter_enabled": False}
        assert is_enabled() is False


class TestValidModes:
    def test_all_modes_present(self):
        assert MODE_SENTENCE in VALID_MODES
        assert MODE_LINE in VALID_MODES
        assert MODE_WORD in VALID_MODES
        assert len(VALID_MODES) == 3


class TestSelectBehindCursor:
    @patch("muttr.ghostwriter._press_key")
    @patch("muttr.ghostwriter.time")
    @patch("muttr.config.load")
    def test_sentence_mode_uses_cmd_shift_left(self, mock_load, mock_time, mock_press):
        mock_load.return_value = {"ghostwriter_mode": "sentence"}
        mock_time.sleep = MagicMock()
        select_behind_cursor(mode=MODE_SENTENCE)
        assert mock_press.called
        call_args = mock_press.call_args
        assert call_args[0][0] == kVK_LeftArrow

    @patch("muttr.ghostwriter._press_key")
    @patch("muttr.ghostwriter.time")
    @patch("muttr.config.load")
    def test_word_mode_uses_option_shift_left(self, mock_load, mock_time, mock_press):
        mock_load.return_value = {"ghostwriter_mode": "word"}
        mock_time.sleep = MagicMock()
        select_behind_cursor(mode=MODE_WORD)
        assert mock_press.called
        call_args = mock_press.call_args
        assert call_args[0][0] == kVK_LeftArrow

    @patch("muttr.ghostwriter._press_key")
    @patch("muttr.ghostwriter.time")
    @patch("muttr.config.load")
    def test_line_mode_uses_cmd_shift_left(self, mock_load, mock_time, mock_press):
        mock_load.return_value = {"ghostwriter_mode": "line"}
        mock_time.sleep = MagicMock()
        select_behind_cursor(mode=MODE_LINE)
        assert mock_press.called

    @patch("muttr.ghostwriter._press_key")
    @patch("muttr.ghostwriter.time")
    @patch("muttr.config.load")
    def test_none_mode_reads_from_config(self, mock_load, mock_time, mock_press):
        mock_load.return_value = {"ghostwriter_mode": "word"}
        mock_time.sleep = MagicMock()
        select_behind_cursor(mode=None)
        assert mock_press.called

    @patch("muttr.ghostwriter._press_key")
    @patch("muttr.ghostwriter.time")
    def test_invalid_mode_falls_back_to_sentence(self, mock_time, mock_press):
        mock_time.sleep = MagicMock()
        select_behind_cursor(mode="invalid_mode")
        assert mock_press.called
