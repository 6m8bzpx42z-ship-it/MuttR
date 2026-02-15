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
        print("MuttR: auto_copy disabled, skipping paste")
        return  # auto-copy disabled; user can paste from history manually

    print(f"MuttR: Inserting text ({len(text)} chars)")
    pasteboard = Cocoa.NSPasteboard.generalPasteboard()

    # Set clipboard to our text (leave it there so user can re-paste)
    pasteboard.clearContents()
    pasteboard.setString_forType_(text, Cocoa.NSPasteboardTypeString)

    # Small delay to ensure clipboard is ready
    time.sleep(config.get("paste_delay_ms", 60) / 1000.0)

    # Simulate Cmd+V
    print("MuttR: Simulating Cmd+V")
    _simulate_cmd_v()
    print("MuttR: Cmd+V sent")


def _simulate_cmd_v():
    """Simulate pressing Cmd+V."""
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateCombinedSessionState)

    # Key down
    cmd_v_down = Quartz.CGEventCreateKeyboardEvent(source, kVK_V, True)
    Quartz.CGEventSetFlags(cmd_v_down, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, cmd_v_down)

    # Key up
    cmd_v_up = Quartz.CGEventCreateKeyboardEvent(source, kVK_V, False)
    Quartz.CGEventSetFlags(cmd_v_up, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, cmd_v_up)
