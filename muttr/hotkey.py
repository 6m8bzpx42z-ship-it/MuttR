"""fn key detection via NSEvent global monitoring."""

import Cocoa


NSEventMaskFlagsChanged = 1 << 12
NSEventModifierFlagFunction = 0x800000


class HotkeyListener:
    def __init__(self, on_key_down, on_key_up):
        self._on_key_down = on_key_down
        self._on_key_up = on_key_up
        self._fn_held = False
        self._monitor = None

    def start(self):
        self._monitor = Cocoa.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskFlagsChanged, self._handle_flags_changed
        )

    def stop(self):
        if self._monitor is not None:
            Cocoa.NSEvent.removeMonitor_(self._monitor)
            self._monitor = None

    def _handle_flags_changed(self, event):
        fn_pressed = bool(event.modifierFlags() & NSEventModifierFlagFunction)

        if fn_pressed and not self._fn_held:
            self._fn_held = True
            self._on_key_down()
        elif not fn_pressed and self._fn_held:
            self._fn_held = False
            self._on_key_up()
