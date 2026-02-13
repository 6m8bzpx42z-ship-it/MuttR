"""Main entry point — NSApplication run loop wiring all components."""

import threading
import time as _time

import Cocoa

from muttr.hotkey import HotkeyListener
from muttr.recorder import Recorder
from muttr.transcriber import create_transcriber
from muttr.cleanup import clean_text
from muttr.inserter import insert_text
from muttr.overlay import Overlay
from muttr.menubar import MenuBar
from muttr.context import build_context_prompt
from muttr.cadence import CadenceTracker
from muttr.confidence import (
    TranscriptionResult, WordInfo, extract_word_confidence, should_show_review,
)
from muttr import config, history


class MuttRApp:
    def __init__(self):
        self._cfg = config.load()
        self.recorder = Recorder()
        self._engine_name = self._cfg.get("transcription_engine", "whisper")
        self._model_size = self._cfg.get("model", "base.en")
        self.transcriber = create_transcriber(
            engine=self._engine_name,
            model_size=self._model_size,
        )
        self.overlay = Overlay()
        self.menubar = MenuBar.alloc().init()
        self.hotkey = HotkeyListener(
            on_key_down=self._on_fn_down,
            on_key_up=self._on_fn_up,
        )
        self._record_start = None
        self._cadence_tracker: CadenceTracker | None = None

    @property
    def cleanup_level(self):
        return config.get("cleanup_level", 1)

    def run(self):
        app = Cocoa.NSApplication.sharedApplication()
        app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)

        # Load selected engine first, then preload the other in background
        engine_label = self.transcriber.name.capitalize()
        print(f"MuttR: Loading {engine_label} model...")
        threading.Thread(target=self.transcriber.load, daemon=True).start()

        # Preload the other engine so switching is instant
        def _preload_other():
            from muttr.transcriber import (
                WhisperBackend, ParakeetBackend, _parakeet_available,
            )
            if self.transcriber.name != "whisper":
                try:
                    print("MuttR: Pre-downloading Whisper model in background...")
                    wb = WhisperBackend(model_size=self._model_size)
                    wb.load()
                except Exception:
                    pass
            if self.transcriber.name != "parakeet" and _parakeet_available():
                try:
                    print("MuttR: Pre-downloading Parakeet model in background...")
                    pb = ParakeetBackend()
                    pb.load()
                except Exception:
                    pass
        threading.Thread(target=_preload_other, daemon=True).start()

        self.overlay.setup()
        self.menubar.setup()
        self.hotkey.start()

        print("MuttR: Ready. Hold fn to record, release to transcribe.")
        print("MuttR: Requires Accessibility + Microphone permissions.")

        app.run()

    def reload_engine_if_changed(self):
        """Check config and swap the transcription backend if the user changed it."""
        cfg = config.load()
        new_engine = cfg.get("transcription_engine", "whisper")
        new_model = cfg.get("model", "base.en")
        if new_engine == self._engine_name and new_model == self._model_size:
            return
        print(f"MuttR: Switching engine {self._engine_name} -> {new_engine}")
        self._engine_name = new_engine
        self._model_size = new_model
        self.transcriber = create_transcriber(engine=new_engine, model_size=new_model)
        threading.Thread(target=self.transcriber.load, daemon=True).start()

    def _on_fn_down(self):
        """Called when fn key is pressed — start recording."""
        self.reload_engine_if_changed()
        self._record_start = _time.time()
        # Start cadence tracking for this session
        # update_interval_ms ~64ms matches the recorder's block size at 16kHz
        self._cadence_tracker = CadenceTracker(update_interval_ms=64.0)
        self.recorder.start()
        self.overlay.show_recording()
        self._start_level_updates()

    def _on_fn_up(self):
        """Called when fn key is released — stop recording, transcribe, insert."""
        duration = _time.time() - self._record_start if self._record_start else 0.0
        self._record_start = None
        audio = self.recorder.stop()
        self._stop_level_updates()
        self.overlay.show_transcribing()

        if audio is None or len(audio) < 1600:  # < 0.1s of audio
            self.overlay.hide()
            return

        # Transcribe in background to keep UI responsive
        threading.Thread(
            target=self._transcribe_and_insert,
            args=(audio, duration),
            daemon=True,
        ).start()

    def _transcribe_and_insert(self, audio, duration):
        """Run transcription and insertion off the main thread."""
        try:
            engine = self.transcriber.name

            # Finish cadence tracking for this session
            cadence = self._cadence_tracker
            self._cadence_tracker = None
            if cadence is not None:
                try:
                    cadence.finish_session()
                except Exception:
                    pass

            # Context stitching: build initial_prompt from clipboard + history
            initial_prompt = ""
            try:
                initial_prompt = build_context_prompt()
            except Exception:
                pass

            # Check if confidence review is enabled for Whisper
            cfg = config.load()
            want_confidence = (
                cfg.get("confidence_review", False)
                and engine == "whisper"
            )

            # Transcribe with optional context prompt and word timestamps
            kwargs = {}
            if initial_prompt:
                kwargs["initial_prompt"] = initial_prompt
            if want_confidence:
                kwargs["word_timestamps"] = True
                kwargs["_return_segments"] = True

            raw_result = self.transcriber.transcribe(audio, **kwargs)

            # Build TranscriptionResult with confidence data if available
            if want_confidence and isinstance(raw_result, list):
                segments = raw_result
                words = extract_word_confidence(segments)
                raw_text = " ".join(
                    seg.text.strip() for seg in segments
                )
                result = TranscriptionResult(
                    text=raw_text,
                    words=words,
                    has_word_confidence=bool(words),
                )
            else:
                raw_text = raw_result if isinstance(raw_result, str) else str(raw_result)
                result = TranscriptionResult(text=raw_text)

            cleaned = clean_text(result.text, level=self.cleanup_level)

            # Log to history
            try:
                history.add_entry(
                    raw_text=result.text or "",
                    cleaned_text=cleaned or "",
                    engine=engine,
                    duration_s=round(duration, 2),
                )
            except Exception:
                pass  # never let history logging break the pipeline

            if cleaned:
                self._perform_on_main(lambda: insert_text(cleaned))

        except Exception as e:
            print(f"MuttR: Transcription error: {e}")
        finally:
            self._perform_on_main(self.overlay.hide)

    def _start_level_updates(self):
        """Periodically push audio levels to the overlay and cadence tracker."""
        def update_level(timer):
            level = self.recorder.level
            self.overlay.update_level(level)
            # Feed level to cadence tracker
            if self._cadence_tracker is not None:
                self._cadence_tracker.update(level)

        self._level_timer = Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0 / 30, True, update_level
        )

    def _stop_level_updates(self):
        if hasattr(self, "_level_timer") and self._level_timer is not None:
            self._level_timer.invalidate()
            self._level_timer = None

    def _perform_on_main(self, func):
        """Run a function on the main thread."""
        Cocoa.NSOperationQueue.mainQueue().addOperationWithBlock_(func)


def main():
    MuttRApp().run()


if __name__ == "__main__":
    main()
