"""fn key detection via NSEvent global monitoring.

Supports single press (hold-to-record), double-tap (Ghostwriter),
and triple-tap (Murmur Mode toggle) detection.
"""

import time

import Cocoa


NSEventMaskFlagsChanged = 1 << 12
NSEventModifierFlagFunction = 0x800000

# Tap detection thresholds (seconds)
DOUBLE_TAP_THRESHOLD = 0.4
TRIPLE_TAP_THRESHOLD = 0.6
# How long to wait after first tap before committing to single-press
TAP_DISAMBIGUATION_DELAY = 0.42


class HotkeyListener:
    def __init__(self, on_key_down, on_key_up,
                 on_double_tap=None, on_triple_tap=None):
        self._on_key_down = on_key_down
        self._on_key_up = on_key_up
        self._on_double_tap = on_double_tap
        self._on_triple_tap = on_triple_tap
        self._fn_held = False
        self._monitor = None

        # Tap tracking
        self._tap_timestamps: list[float] = []
        self._pending_single = False
        self._disambiguation_timer = None
        self._committed = False  # True once we decide single/double/triple

    def start(self):
        self._monitor = Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskFlagsChanged, self._handle_flags_changed
        )

    def stop(self):
        if self._monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._monitor)
            self._monitor = None
        self._cancel_disambiguation_timer()

    def _cancel_disambiguation_timer(self):
        if self._disambiguation_timer is not None:
            self._disambiguation_timer.invalidate()
            self._disambiguation_timer = None

    def _handle_flags_changed(self, event):
        fn_pressed = bool(event.modifierFlags() & NSEventModifierFlagFunction)

        if fn_pressed and not self._fn_held:
            self._fn_held = True
            self._handle_fn_down()
        elif not fn_pressed and self._fn_held:
            self._fn_held = False
            self._handle_fn_up()

    def _handle_fn_down(self):
        now = time.monotonic()

        # Prune old taps outside the triple-tap window
        self._tap_timestamps = [
            t for t in self._tap_timestamps
            if now - t < TRIPLE_TAP_THRESHOLD
        ]
        self._tap_timestamps.append(now)

        tap_count = len(self._tap_timestamps)

        # Check for triple-tap (highest priority)
        if tap_count >= 3 and self._on_triple_tap is not None:
            span = now - self._tap_timestamps[-3]
            if span <= TRIPLE_TAP_THRESHOLD:
                self._cancel_disambiguation_timer()
                self._tap_timestamps.clear()
                self._committed = True
                self._on_triple_tap()
                return

        # Check for double-tap
        if tap_count >= 2 and self._on_double_tap is not None:
            span = now - self._tap_timestamps[-2]
            if span <= DOUBLE_TAP_THRESHOLD:
                # If triple-tap is also registered, defer the double-tap
                # briefly to allow a third tap to arrive
                if self._on_triple_tap is not None:
                    self._cancel_disambiguation_timer()
                    self._committed = False
                    self._disambiguation_timer = (
                        Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                            DOUBLE_TAP_THRESHOLD,
                            False,
                            lambda timer: self._commit_double_tap(),
                        )
                    )
                    return
                # No triple-tap callback: fire double-tap immediately
                self._cancel_disambiguation_timer()
                self._tap_timestamps.clear()
                self._committed = True
                self._on_double_tap()
                return

        # First tap: wait for disambiguation
        self._committed = False
        self._cancel_disambiguation_timer()

        if self._on_double_tap is not None or self._on_triple_tap is not None:
            self._pending_single = True
            self._disambiguation_timer = (
                Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                    TAP_DISAMBIGUATION_DELAY,
                    False,
                    lambda timer: self._commit_single_press(),
                )
            )
        else:
            # No multi-tap callbacks registered, fire immediately
            self._committed = True
            self._on_key_down()

    def _commit_double_tap(self):
        """Called after double-tap disambiguation delay -- no third tap arrived."""
        self._disambiguation_timer = None
        if not self._committed:
            self._tap_timestamps.clear()
            self._committed = True
            self._on_double_tap()

    def _commit_single_press(self):
        """Called after disambiguation delay -- this is a real single press."""
        self._disambiguation_timer = None
        self._pending_single = False
        if not self._committed and self._fn_held:
            self._committed = True
            self._on_key_down()

    def _handle_fn_up(self):
        if self._committed:
            self._on_key_up()
        # If not committed (quick tap during disambiguation), just ignore the up
        self._committed = False
