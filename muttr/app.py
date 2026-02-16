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
from muttr.cadence import (
    CadenceTracker, SpeechMetrics, SpeechProfile,
    load_speech_profile, save_speech_profile,
)
from muttr.confidence import (
    TranscriptionResult, WordInfo, extract_word_confidence, should_show_review,
)
from muttr.murmur import MurmurMode
from muttr import sounds
from muttr import config, history, account, budget, ghostwriter


class AppDelegate(Cocoa.NSObject):
    """Keeps the app alive when launched as a .app bundle."""

    def applicationShouldTerminate_(self, sender):
        return Cocoa.NSTerminateNow

    def applicationDidFinishLaunching_(self, notification):
        pass


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
            on_double_tap=self._on_double_tap,
            on_triple_tap=self._on_triple_tap,
        )
        self._record_start = None
        self._model_ready = threading.Event()
        self._cadence_tracker: CadenceTracker | None = None
        self._murmur = MurmurMode()
        self._ghostwriter_active = False

    @property
    def cleanup_level(self):
        return config.get("cleanup_level", 1)

    def run(self):
        app = Cocoa.NSApplication.sharedApplication()
        app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyAccessory)

        # Set delegate to keep the app alive when launched as .app bundle
        self._delegate = AppDelegate.alloc().init()
        app.setDelegate_(self._delegate)

        # Load Whisper model in background
        print(f"MuttR: Loading Whisper model ({self._model_size})...")
        def _load_model():
            self.transcriber.load()
            self._model_ready.set()
            print("MuttR: Model loaded and ready.")
        threading.Thread(target=_load_model, daemon=True).start()

        self.overlay.setup()
        self.menubar.setup()

        if not config.get("onboarding_completed", False):
            from muttr.onboarding import OnboardingWindowController
            self._onboarding = OnboardingWindowController.alloc().init()
            self._onboarding.show()

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
        self._model_ready.clear()
        self.transcriber = create_transcriber(engine=new_engine, model_size=new_model)
        def _load_model():
            self.transcriber.load()
            self._model_ready.set()
            print("MuttR: Model loaded and ready.")
        threading.Thread(target=_load_model, daemon=True).start()

    # ------------------------------------------------------------------
    # Hotkey callbacks
    # ------------------------------------------------------------------

    def _on_fn_down(self):
        """Called when fn key is pressed — start recording."""
        if not self._model_ready.is_set():
            print("MuttR: Model still loading, please wait...")
            return
        self.reload_engine_if_changed()
        self._record_start = _time.time()
        # Start cadence tracking for this session
        # update_interval_ms ~64ms matches the recorder's block size at 16kHz
        self._cadence_tracker = CadenceTracker(update_interval_ms=64.0)

        # Murmur mode: calibrate noise floor from initial silence
        if self._murmur.active and self._murmur.processor is not None:
            # Calibration happens when first audio chunk arrives
            pass

        # Sound feedback
        prefs = account.load_account()["preferences"]
        if prefs.get("sound_feedback", False):
            sounds.play_start()

        self.recorder.start()

        # Overlay toggle
        if prefs.get("show_overlay", True):
            self.overlay.show_recording()
        self._start_level_updates()

    def _on_fn_up(self):
        """Called when fn key is released — stop recording, transcribe, insert."""
        duration = _time.time() - self._record_start if self._record_start else 0.0
        self._record_start = None
        audio = self.recorder.stop()
        self._stop_level_updates()

        prefs = account.load_account()["preferences"]

        # Sound feedback
        if prefs.get("sound_feedback", False):
            sounds.play_stop()

        # Overlay toggle
        if prefs.get("show_overlay", True):
            self.overlay.show_transcribing()

        if audio is None or len(audio) < 1600:  # < 0.1s of audio
            self.overlay.hide()
            return

        # Murmur mode: calibrate and process audio
        if self._murmur.active and self._murmur.processor is not None:
            try:
                self._murmur.processor.calibrate(audio[:8000])
                audio = self._murmur.processor.process(audio)
            except Exception:
                pass

        is_replace = self._ghostwriter_active
        self._ghostwriter_active = False

        # Transcribe in background to keep UI responsive
        threading.Thread(
            target=self._transcribe_and_insert,
            args=(audio, duration, is_replace),
            daemon=True,
        ).start()

    def _on_double_tap(self):
        """Called on double-tap fn — Ghostwriter mode."""
        if not ghostwriter.is_enabled():
            return

        print("MuttR: Ghostwriter — select and re-dictate")
        ghostwriter.select_behind_cursor()
        self._ghostwriter_active = True
        # Start recording in replace mode (reuse _on_fn_down logic)
        self._on_fn_down()

    def _on_triple_tap(self):
        """Called on triple-tap fn — toggle Murmur Mode."""
        active = self._murmur.toggle()
        state = "ON" if active else "OFF"
        print(f"MuttR: Murmur Mode {state}")

        # Brief overlay indicator
        self._perform_on_main(lambda: self._show_murmur_indicator(active))

    def _show_murmur_indicator(self, active):
        """Show a brief overlay message for murmur mode toggle."""
        label = "Murmur ON" if active else "Murmur OFF"
        self.overlay.show_transcribing()
        # Reuse transcribing state for brief text display, hide after 1s
        Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0, False, lambda timer: self.overlay.hide()
        )

    # ------------------------------------------------------------------
    # Transcription pipeline
    # ------------------------------------------------------------------

    def _transcribe_and_insert(self, audio, duration, is_replace=False):
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

            # Transcribe with optional context prompt
            kwargs = {}
            if initial_prompt:
                kwargs["initial_prompt"] = initial_prompt

            raw_result = self.transcriber.transcribe(audio, **kwargs)

            raw_text = raw_result if isinstance(raw_result, str) else str(raw_result)
            result = TranscriptionResult(text=raw_text)

            cleaned = clean_text(result.text, level=self.cleanup_level)

            if not cleaned or not cleaned.strip():
                return  # nothing to insert or log

            # Log to history
            try:
                history.add_entry(
                    raw_text=result.text or "",
                    cleaned_text=cleaned,
                    engine=engine,
                    duration_s=round(duration, 2),
                )
            except Exception:
                pass  # never let history logging break the pipeline

            # Cadence coaching feedback
            try:
                if config.get("cadence_feedback", True):
                    metrics = SpeechMetrics.analyze(audio, cleaned, duration)
                    profile = load_speech_profile()
                    profile.update(metrics)
                    feedback = profile.get_feedback(metrics)
                    if feedback:
                        print(f"MuttR: Speech feedback — {feedback}")
                    save_speech_profile(profile)
            except Exception:
                pass

            # Check word budget before inserting
            word_count = len(cleaned.split())
            if budget.is_over_budget():
                print("MuttR: Word budget exceeded — upgrade for more words")
                self._perform_on_main(self._show_budget_exceeded)
                return

            self._perform_on_main(lambda: insert_text(cleaned))

            # Record usage after successful insert
            try:
                budget.record_usage(word_count)
            except Exception:
                pass

        except Exception as e:
            print(f"MuttR: Transcription error: {e}")
        finally:
            self._perform_on_main(self.overlay.hide)

    def _show_budget_exceeded(self):
        """Show a notification that the word budget has been exceeded."""
        remaining = budget.words_remaining_today()
        alert = Cocoa.NSAlert.alloc().init()
        alert.setMessageText_("Word Limit Reached")
        alert.setInformativeText_(
            "You've used all your words for today. "
            "Upgrade your plan for more words, or wait until tomorrow."
        )
        alert.addButtonWithTitle_("OK")
        alert.setAlertStyle_(Cocoa.NSAlertStyleInformational)
        alert.runModal()

    # ------------------------------------------------------------------
    # Level updates
    # ------------------------------------------------------------------

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
