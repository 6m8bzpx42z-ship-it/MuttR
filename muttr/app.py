"""Main entry point — NSApplication run loop wiring all components."""

import threading

import Cocoa

from muttr.hotkey import HotkeyListener
from muttr.recorder import Recorder
from muttr.transcriber import Transcriber
from muttr.cleanup import clean_text
from muttr.inserter import insert_text
from muttr.overlay import Overlay


class MuttRApp:
    def __init__(self):
        self.recorder = Recorder()
        self.transcriber = Transcriber()
        self.overlay = Overlay()
        self.hotkey = HotkeyListener(
            on_key_down=self._on_fn_down,
            on_key_up=self._on_fn_up,
        )

    def run(self):
        app = Cocoa.NSApplication.sharedApplication()
        app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)

        # Load Whisper model in background so startup isn't blocked
        print("MuttR: Loading Whisper model...")
        threading.Thread(target=self.transcriber.load, daemon=True).start()

        self.overlay.setup()
        self.hotkey.start()

        print("MuttR: Ready. Hold fn to record, release to transcribe.")
        print("MuttR: Requires Accessibility + Microphone permissions.")

        app.run()

    def _on_fn_down(self):
        """Called when fn key is pressed — start recording."""
        self.recorder.start()
        self.overlay.show_recording()
        self._start_level_updates()

    def _on_fn_up(self):
        """Called when fn key is released — stop recording, transcribe, insert."""
        audio = self.recorder.stop()
        self._stop_level_updates()
        self.overlay.show_transcribing()

        if audio is None or len(audio) < 1600:  # < 0.1s of audio
            self.overlay.hide()
            return

        # Transcribe in background to keep UI responsive
        threading.Thread(
            target=self._transcribe_and_insert, args=(audio,), daemon=True
        ).start()

    def _transcribe_and_insert(self, audio):
        """Run transcription and insertion off the main thread."""
        raw_text = self.transcriber.transcribe(audio)
        cleaned = clean_text(raw_text)

        if cleaned:
            self._perform_on_main(lambda: insert_text(cleaned))

        self._perform_on_main(self.overlay.hide)

    def _start_level_updates(self):
        """Periodically push audio levels to the overlay."""
        def update_level(timer):
            self.overlay.update_level(self.recorder.level)

        self._level_timer = Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0 / 30, True, update_level
        )

    def _stop_level_updates(self):
        if hasattr(self, "_level_timer") and self._level_timer is not None:
            self._level_timer.invalidate()
            self._level_timer = None

    def _perform_on_main(self, func):
        """Run a function on the main thread."""
        # Use a simple dispatch approach compatible with PyObjC
        Cocoa.NSOperationQueue.mainQueue().addOperationWithBlock_(func)


def main():
    MuttRApp().run()


if __name__ == "__main__":
    main()
