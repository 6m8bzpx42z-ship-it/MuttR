"""Sound feedback using macOS system sounds via NSSound."""

import Cocoa


def play_start():
    """Play a short sound when recording starts."""
    sound = Cocoa.NSSound.soundNamed_("Tink")
    if sound:
        sound.play()


def play_stop():
    """Play a short sound when recording stops."""
    sound = Cocoa.NSSound.soundNamed_("Pop")
    if sound:
        sound.play()
