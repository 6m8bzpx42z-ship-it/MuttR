"""Text insertion via clipboard + simulated Cmd+V."""

import time

import Cocoa
import Quartz

from muttr import config, account


# Virtual keycode for 'V'
kVK_V = 0x09


def insert_text(text):
    """Insert text into the active app by pasting from clipboard."""
    prefs = account.load_account()["preferences"]
    if not prefs.get("auto_copy", True):
        return  # auto-copy disabled; user can paste from history manually

    pasteboard = Cocoa.NSPasteboard.generalPasteboard()

    # Save original clipboard contents
    old_types = pasteboard.types()
    old_data = {}
    if old_types:
        for t in old_types:
            data = pasteboard.dataForType_(t)
            if data:
                old_data[t] = data

    # Set clipboard to our text
    pasteboard.clearContents()
    pasteboard.setString_forType_(text, Cocoa.NSPasteboardTypeString)

    # Small delay to ensure clipboard is ready
    time.sleep(config.get("paste_delay_ms", 60) / 1000.0)

    # Simulate Cmd+V
    _simulate_cmd_v()

    # Wait for paste to complete, then restore clipboard
    time.sleep(config.get("paste_delay_ms", 60) / 1000.0)
    _restore_clipboard(pasteboard, old_data)


def _simulate_cmd_v():
    """Simulate pressing Cmd+V."""
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)

    # Key down
    cmd_v_down = Quartz.CGEventCreateKeyboardEvent(source, kVK_V, True)
    Quartz.CGEventSetFlags(cmd_v_down, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, cmd_v_down)

    # Key up
    cmd_v_up = Quartz.CGEventCreateKeyboardEvent(source, kVK_V, False)
    Quartz.CGEventSetFlags(cmd_v_up, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, cmd_v_up)


def _restore_clipboard(pasteboard, old_data):
    """Restore original clipboard contents."""
    if not old_data:
        return

    pasteboard.clearContents()
    for ptype, data in old_data.items():
        pasteboard.setData_forType_(data, ptype)
