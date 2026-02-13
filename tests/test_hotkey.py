"""Tests for muttr.hotkey -- fn key detection with multi-tap support.

Tests the tap detection logic (double-tap, triple-tap) without requiring
actual NSEvent monitoring. We test the _handle_fn_down/_handle_fn_up methods
directly with mocked timers.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from muttr.hotkey import (
    HotkeyListener,
    DOUBLE_TAP_THRESHOLD,
    TRIPLE_TAP_THRESHOLD,
    TAP_DISAMBIGUATION_DELAY,
)


class TestHotkeyListenerInit:
    def test_basic_callbacks(self):
        down = MagicMock()
        up = MagicMock()
        listener = HotkeyListener(on_key_down=down, on_key_up=up)
        assert listener._on_key_down is down
        assert listener._on_key_up is up
        assert listener._on_double_tap is None
        assert listener._on_triple_tap is None

    def test_multi_tap_callbacks(self):
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()
        triple = MagicMock()
        listener = HotkeyListener(
            on_key_down=down, on_key_up=up,
            on_double_tap=double, on_triple_tap=triple,
        )
        assert listener._on_double_tap is double
        assert listener._on_triple_tap is triple


class TestTapDetectionConstants:
    def test_double_tap_threshold(self):
        assert DOUBLE_TAP_THRESHOLD == 0.4

    def test_triple_tap_threshold(self):
        assert TRIPLE_TAP_THRESHOLD == 0.6

    def test_disambiguation_delay(self):
        assert TAP_DISAMBIGUATION_DELAY == 0.42


class TestSinglePressWithoutMultiTap:
    """When no multi-tap callbacks are registered, fn acts immediately."""

    def test_single_press_fires_on_key_down(self):
        down = MagicMock()
        up = MagicMock()
        listener = HotkeyListener(on_key_down=down, on_key_up=up)

        listener._handle_fn_down()
        assert down.called

    def test_release_fires_on_key_up(self):
        down = MagicMock()
        up = MagicMock()
        listener = HotkeyListener(on_key_down=down, on_key_up=up)

        listener._handle_fn_down()
        listener._handle_fn_up()
        assert up.called


class TestDoubleTapDetection:
    """Test double-tap detection via direct method calls."""

    @patch("muttr.hotkey.Cocoa")
    def test_double_tap_detected(self, mock_cocoa):
        """Two quick fn presses should trigger on_double_tap."""
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        mock_timer = MagicMock()
        mock_cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_.return_value = mock_timer

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up, on_double_tap=double,
        )

        # First tap
        listener._handle_fn_down()
        listener._fn_held = True
        listener._handle_fn_up()
        listener._fn_held = False

        # Second tap quickly
        listener._handle_fn_down()
        listener._fn_held = True

        assert double.called
        assert not down.called  # should NOT have fired single press


class TestTripleTapDetection:
    """Test triple-tap detection via direct method calls."""

    @patch("muttr.hotkey.Cocoa")
    def test_triple_tap_detected(self, mock_cocoa):
        """Three quick fn presses should trigger on_triple_tap."""
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()
        triple = MagicMock()

        mock_timer = MagicMock()
        mock_cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_.return_value = mock_timer

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up,
            on_double_tap=double, on_triple_tap=triple,
        )

        # First tap
        listener._handle_fn_down()
        listener._fn_held = True
        listener._handle_fn_up()
        listener._fn_held = False

        # Second tap
        listener._handle_fn_down()
        listener._fn_held = True
        listener._handle_fn_up()
        listener._fn_held = False

        # Third tap
        listener._handle_fn_down()
        listener._fn_held = True

        assert triple.called
        # Double tap should NOT have fired (triple takes priority)
        assert not double.called
        assert not down.called


class TestTapTimestampTracking:
    """Test that old taps are pruned and timestamps tracked correctly."""

    @patch("muttr.hotkey.Cocoa")
    def test_old_taps_pruned(self, mock_cocoa):
        """Taps outside the threshold window should not count."""
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        mock_timer = MagicMock()
        mock_cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_.return_value = mock_timer

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up, on_double_tap=double,
        )

        # First tap
        listener._handle_fn_down()
        listener._fn_held = True
        listener._handle_fn_up()
        listener._fn_held = False

        # Manually age out the timestamp
        listener._tap_timestamps = [time.monotonic() - 1.0]

        # Second tap after timeout
        listener._handle_fn_down()

        # Should NOT detect double tap because first tap is too old
        assert not double.called


class TestCommitSinglePress:
    """Test the disambiguation timer callback."""

    def test_commit_single_when_held(self):
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up, on_double_tap=double,
        )

        # Simulate: fn is still held when disambiguation timer fires
        listener._fn_held = True
        listener._committed = False
        listener._commit_single_press()

        assert down.called

    def test_no_commit_when_not_held(self):
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up, on_double_tap=double,
        )

        # Simulate: fn was released before disambiguation timer fires
        listener._fn_held = False
        listener._committed = False
        listener._commit_single_press()

        assert not down.called

    def test_no_commit_when_already_committed(self):
        down = MagicMock()
        up = MagicMock()
        double = MagicMock()

        listener = HotkeyListener(
            on_key_down=down, on_key_up=up, on_double_tap=double,
        )

        listener._fn_held = True
        listener._committed = True  # already committed (e.g. double-tap)
        listener._commit_single_press()

        assert not down.called
