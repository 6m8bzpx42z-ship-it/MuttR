# MuttR Innovation Features

Three unique features that no competitor in the dictation space currently offers.

---

## Feature 1: Ghostwriter -- Voice-Driven Text Replacement in Any App

**One-line pitch:** Double-tap fn to select the current word/sentence behind the cursor and re-dictate it, replacing the original text in-place without touching the mouse.

### How It Works (User Perspective)

The user is typing in any app -- an email, a Slack message, a code comment. They wrote something they want to rephrase. Instead of reaching for the mouse to select the text, they:

1. **Double-tap fn** (two quick presses within 400ms). MuttR detects this as a "replace mode" trigger.
2. MuttR silently selects the current sentence (or paragraph, configurable) behind the cursor by simulating Shift+arrow key presses. The selected text briefly highlights in the target app.
3. The overlay changes to a **red recording indicator** (distinct from the normal blue/white), showing "Re-dictate..."
4. The user speaks their replacement.
5. On release, MuttR transcribes and **replaces the selected text** with the new dictation.

The key insight: no dictation app offers a keyboard-only "undo and rephrase" flow. Every competitor requires the user to manually select text with mouse/trackpad before re-dictating. Ghostwriter makes the entire rephrase-by-voice cycle touchless.

**Selection modes** (configurable in Settings > General):
- **Sentence** (default): Select backward to the previous sentence boundary (period, newline, or start of field)
- **Line**: Select the entire current line (Home to cursor)
- **Word**: Select only the last word (Option+Shift+Left)

### Technical Implementation

**Module:** `muttr/ghostwriter.py`

**Detection (in `hotkey.py`):**

Add a double-tap detector to HotkeyListener. Track timestamps of fn press events. If two fn-down events occur within 400ms with fn-up between them, emit an `on_double_tap()` callback instead of the normal `on_key_down`/`on_key_up` cycle.

- `HotkeyListener` gains a `_last_fn_down_ts` field and `_double_tap_threshold` (default 0.4s).
- On fn-down: if `time.time() - _last_fn_down_ts < threshold`, call `on_double_tap()` instead of `on_key_down()`. Otherwise, start a short timer (~420ms). If fn-up and then fn-down don't occur within that window, fire normal `on_key_down()`.
- The latency cost of the double-tap detection window is absorbed: the user is already thinking about what to say during the brief detection delay.

**Text selection (in `ghostwriter.py`):**

Uses `Quartz.CGEventCreateKeyboardEvent` (same approach as `inserter.py`) to simulate:
- **Sentence mode:** Shift+Cmd+Left (selects to start of line). Refined in v1.1 to use repeated Shift+Left with clipboard inspection to find sentence boundaries.
- **Line mode:** Cmd+Shift+Left (select to line start), then Shift+Cmd+Right if the whole line is desired.
- **Word mode:** Option+Shift+Left (select previous word).

**Replacement flow:**
1. `ghostwriter.select_current_sentence()` simulates the keystrokes to select text.
2. Recording starts (same `Recorder` instance).
3. On fn-up, transcribe via the current `TranscriberBackend`.
4. Clean with `cleanup.clean_text()`.
5. Call `inserter.insert_text()` -- since the target app already has text selected, the paste replaces the selection (standard macOS behavior).
6. No need for special insertion logic; Cmd+V over a selection replaces it.

**Integration with existing architecture:**
- `app.py`: `MuttRApp.__init__` wires a third callback `on_double_tap=self._on_ghostwriter` to `HotkeyListener`.
- `_on_ghostwriter()` calls `ghostwriter.select_current_sentence()`, then starts recording exactly as `_on_fn_down()` does, but sets `self._ghostwriter_active = True`.
- `_on_fn_up()` checks `_ghostwriter_active` and skips clipboard snapshot/restore (since we want to replace the selection, not append).
- Overlay shows distinct "Re-dictate..." state via `overlay.show_ghostwriter()`.

**Config additions:**
- `ghostwriter_mode`: `"sentence"` | `"line"` | `"word"` (default: `"sentence"`)
- `ghostwriter_enabled`: `true` | `false` (default: `true`)

### Why It's Unique and Valuable

No competitor offers a keyboard-only rephrase flow. The closest feature is ashwin-pc/whisper-dictation's "edit selected text," but that requires the user to manually select text first with the mouse and then speak an instruction that gets sent to a cloud LLM. Ghostwriter is:
- **Fully local** -- no cloud LLM needed, just re-dictation.
- **Keyboard-only** -- the user never leaves the keyboard.
- **Instant** -- no LLM roundtrip, just the normal transcription pipeline.
- **Universally compatible** -- works in any macOS app that supports standard text selection and paste.

This is a genuine "wow" feature for power users who dictate entire emails or documents and want to fix mistakes without breaking flow.

---

## Feature 2: Cadence -- Adaptive Transcription Speed Coaching

**One-line pitch:** MuttR listens to how you speak and gives you real-time feedback to improve your dictation clarity, building a personal speaking profile over time.

### How It Works (User Perspective)

After transcription, MuttR silently analyzes the audio characteristics and transcript quality. Over time, it builds a **personal speech profile**. The user sees:

1. **Post-dictation micro-feedback** (optional, in the overlay): After each transcription, the overlay briefly flashes a one-word indicator:
   - Green "Clear" -- your speech was well-paced and cleanly transcribed
   - Yellow "Fast" -- you spoke too quickly; the transcript had low-confidence segments
   - Yellow "Quiet" -- your audio levels were too low
   - No indicator -- normal/acceptable (most dictations show nothing, to avoid annoyance)

2. **Speaking Stats in Settings > History**: Each transcription entry shows:
   - Words per minute (WPM)
   - Average audio energy (loudness)
   - Confidence score (from the transcription engine)
   - Filler word count (from cleanup analysis)

3. **Weekly Digest** (in the menu bar popover): A one-line summary like "This week: 847 words dictated, avg 142 WPM, 12% fewer fillers than last week."

4. **Personal Baselines**: MuttR learns the user's natural speaking pace and only flags deviations from *their* baseline, not an absolute threshold. Someone who normally speaks at 160 WPM gets flagged at 190, not at 140.

### Technical Implementation

**Module:** `muttr/cadence.py`

**Audio analysis (computed in `_transcribe_and_insert`):**

```python
class SpeechMetrics:
    """Compute speech quality metrics from audio + transcript."""

    def analyze(self, audio: np.ndarray, transcript: str,
                duration_s: float, confidence: float) -> dict:
        word_count = len(transcript.split())
        wpm = (word_count / duration_s) * 60 if duration_s > 0 else 0
        avg_energy = float(np.sqrt(np.mean(audio ** 2)))  # RMS energy
        filler_count = len(FILLER_PATTERN.findall(transcript))

        return {
            "wpm": round(wpm, 1),
            "energy_rms": round(avg_energy, 4),
            "confidence": round(confidence, 3),
            "filler_count": filler_count,
            "word_count": word_count,
        }
```

**Baseline computation (in `cadence.py`):**

```python
class SpeechProfile:
    """Maintains rolling statistics of the user's speaking patterns."""

    PROFILE_PATH = os.path.join(APP_SUPPORT_DIR, "speech_profile.json")
    ROLLING_WINDOW = 100  # last 100 dictations

    def update(self, metrics: dict) -> None:
        """Add new metrics and recompute baselines."""
        ...

    def get_feedback(self, metrics: dict) -> Optional[str]:
        """Compare current metrics against personal baseline.
        Returns None (normal), 'fast', 'quiet', or 'clear'."""
        if metrics["wpm"] > self.baseline_wpm * 1.25:
            return "fast"
        if metrics["energy_rms"] < self.baseline_energy * 0.4:
            return "quiet"
        if metrics["confidence"] > 0.92 and metrics["filler_count"] == 0:
            return "clear"
        return None
```

**Storage:** Speech metrics are stored alongside each transcription in the existing SQLite `history.db`. The `transcriptions` table gains new columns:
- `wpm REAL`
- `energy_rms REAL`
- `confidence REAL`
- `filler_count INTEGER`

The `speech_profile.json` file stores the rolling baseline (mean + std dev of each metric over the last 100 entries).

**Overlay integration:**
- `overlay.py` gains a `show_feedback(feedback_type)` method that briefly (600ms) shows a small colored dot or word after the success checkmark.
- Only triggers if the user has `cadence_feedback` enabled in config (default: `true`).

**Weekly digest:**
- Computed on-the-fly when the user opens the menu bar popover.
- `cadence.py` exports `weekly_summary() -> str` that queries the last 7 days from history.db and computes aggregate stats.
- `menubar.py` shows this one-liner at the top of the settings window or as a tooltip on the menu bar item.

**Integration with existing architecture:**
- `transcriber.py`: The `TranscriberBackend` protocol gains an optional `segments` return value. `WhisperBackend.transcribe()` already has access to segment confidence via faster-whisper's segment metadata. The method returns text and average confidence.
- `app.py`: After transcription in `_transcribe_and_insert()`, compute `SpeechMetrics.analyze()`, call `SpeechProfile.update()`, get feedback, and dispatch overlay feedback if non-None.
- `history.py`: `add_entry()` gains optional `metrics: dict` parameter; new columns stored alongside each entry.

**Config additions:**
- `cadence_feedback`: `true` | `false` (default: `true`)
- `cadence_feedback_threshold`: `"sensitive"` | `"normal"` | `"quiet"` (default: `"normal"`)

### Why It's Unique and Valuable

No dictation app provides speaking quality feedback. Transcription apps treat each dictation as isolated input. Cadence turns MuttR into a tool that makes the user a better dictator over time. This is a unique selling point that:
- **Creates long-term engagement** -- users check their stats and try to improve.
- **Actually improves transcription quality** -- if the user speaks more clearly, they get better results, creating a virtuous cycle.
- **Costs nothing computationally** -- all metrics are byproducts of data already computed during normal transcription (audio RMS, word count, segment confidence).
- **Respects privacy** -- all analysis is local, no audio leaves the machine.

---

## Feature 3: Murmur Mode -- Whisper-Quiet Dictation for Shared Spaces

**One-line pitch:** A dedicated low-volume dictation mode that automatically boosts microphone gain and applies noise gating, so you can dictate at a murmur in open offices, libraries, and coffee shops without disturbing others.

### How It Works (User Perspective)

The user is in a shared space -- an open office, a library, a coffee shop. They want to dictate but don't want to speak at normal volume. They:

1. **Triple-tap fn** (three quick presses within 600ms) to toggle Murmur Mode, OR toggle it from the menu bar dropdown.
2. The **menu bar icon changes** from "M" to "m" (lowercase, italicized) to indicate Murmur Mode is active.
3. The **overlay color shifts** to a muted purple/indigo tint (instead of the default dark gray) so the user has a constant subtle visual reminder.
4. MuttR internally:
   - **Boosts microphone gain** by amplifying the audio buffer (configurable 2x-6x, default 3x).
   - **Lowers the minimum utterance threshold** from 150ms to 80ms (quieter speech tends to have softer onsets).
   - **Applies a noise gate** that strips ambient noise below a threshold before sending to the transcriber, since gain amplification also amplifies background noise.
   - **Calibrates on initial silence** -- uses the first 200ms of each recording to estimate the ambient noise floor.
   - Optionally **switches to the small.en model** which handles low-energy audio better than base.en (user-configurable).
5. The user speaks at a murmur. MuttR handles the rest.
6. **Triple-tap fn** again (or menu bar toggle) to return to normal mode.

### Technical Implementation

**Module:** `muttr/murmur.py`

**Audio processing pipeline:**

```python
class MurmurProcessor:
    """Audio preprocessing for low-volume dictation."""

    def __init__(self, gain: float = 3.0, noise_gate_db: float = -50.0):
        self.gain = gain
        self.noise_gate_threshold = 10 ** (noise_gate_db / 20)
        self._enabled = False
        self._noise_floor = None

    def calibrate(self, audio_chunk: np.ndarray) -> None:
        """Estimate ambient noise floor from initial silence."""
        self._noise_floor = float(np.percentile(np.abs(audio_chunk), 85))

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply gain boost and noise gating."""
        if not self._enabled:
            return audio

        # Noise gate: zero out samples below threshold
        gate_threshold = max(self.noise_gate_threshold,
                           (self._noise_floor or 0) * 1.5)
        gated = np.where(np.abs(audio) < gate_threshold, 0.0, audio)

        # Apply gain
        boosted = gated * self.gain

        # Soft clip to prevent distortion
        boosted = np.tanh(boosted)

        return boosted.astype(np.float32)
```

**Triple-tap detection (in `hotkey.py`):**
- Extend the double-tap logic for Ghostwriter. Track the last 3 fn-down timestamps.
- If three fn-down events occur within 600ms with brief fn-ups between, emit `on_triple_tap()`.
- The detection hierarchy: triple-tap (checked first) > double-tap > single press.
- Uses a short timer (~620ms) after the first tap to disambiguate.

**Noise calibration:**
- When Murmur Mode is active and recording starts, the first 200ms of audio is used to estimate the ambient noise floor before recording begins.
- The user presses fn and there's a brief moment before they start speaking. This silence window is perfect for calibration.
- `recorder.py` modification: when Murmur Mode is active, `Recorder.start()` stores the first few audio callback chunks for calibration, then passes them to `MurmurProcessor.calibrate()`.

**Recorder integration:**
- `recorder.py`: Add a `set_preprocessor(func)` method. When set, each audio chunk passes through the preprocessor before being appended to `self._chunks`.
- The preprocessor is `MurmurProcessor.process` when Murmur Mode is active, or `None` in normal mode.
- The audio level reported to the overlay is computed *after* preprocessing, so the waveform animation reflects the boosted signal.

**Integration with existing architecture:**
- `app.py`: `MuttRApp.__init__` wires `on_triple_tap=self._toggle_murmur`.
- `_toggle_murmur()` flips `self._murmur_active`, updates the menu bar icon, updates the overlay tint, and configures the recorder's preprocessor.
- `menubar.py`: Add a "Murmur Mode" toggle menu item with a checkmark.
- `overlay.py`: `set_tint(color)` method changes the background color of the overlay bubble. Murmur Mode uses a deep indigo `(0.25, 0.15, 0.35, 0.85)` instead of the default `(0.15, 0.15, 0.15, 0.85)`.
- `recorder.py`: `_audio_callback` optionally routes through the preprocessor.

**Config additions:**
- `murmur_gain`: `float`, range 1.5-6.0 (default: 3.0)
- `murmur_noise_gate_db`: `float`, range -60 to -30 (default: -50)
- `murmur_auto_model`: `true` | `false` (default: `false`)
- `murmur_min_utterance_ms`: `int` (default: 80)

### Why It's Unique and Valuable

No dictation app addresses the social friction of voice input. This is the single biggest reason people don't use dictation apps at work: they feel self-conscious speaking at full volume in shared spaces. Existing solutions tell users to "find a quiet room." Murmur Mode says "stay where you are, just speak quietly."

This is technically non-trivial (gain boosting without amplifying noise requires the noise gate + calibration) but fully feasible with numpy audio processing already in the stack. No competitor has attempted this because:
- VoiceInk, superwhisper, and Handy all assume normal-volume speech.
- The gain + noise gate + calibration pipeline is specific signal processing work that general-purpose dictation apps haven't prioritized.
- The triple-tap activation is a natural extension of the fn-key interaction model that only makes sense for an fn-key-based app like MuttR.

Murmur Mode turns a social limitation of all voice apps into a MuttR differentiator.

---

## Summary

| Feature | Trigger | Core Value | Technical Complexity |
|---------|---------|------------|---------------------|
| **Ghostwriter** | Double-tap fn | Keyboard-only rephrase without mouse | Medium -- key simulation + state tracking |
| **Cadence** | Automatic | Speaking quality feedback over time | Low -- metrics from existing data |
| **Murmur Mode** | Triple-tap fn | Dictate quietly in shared spaces | Medium -- audio gain + noise gate pipeline |

All three features:
- Use the fn key interaction model that defines MuttR's identity
- Are 100% local with no cloud dependencies
- Build on existing modules (`hotkey.py`, `recorder.py`, `transcriber.py`, `overlay.py`)
- Are technically feasible within the Python/PyObjC/numpy stack
- Are genuinely novel -- no competitor offers any of these

## Implementation Priority

| Feature | Complexity | User Impact | Dependencies |
|---------|-----------|-------------|-------------|
| Cadence | Low | Medium-High | Metrics from existing transcription data |
| Ghostwriter | Medium | High | Double-tap detection in hotkey.py, CGEvent key simulation |
| Murmur Mode | Medium | High | numpy audio processing (already in stack) |

**Recommended order:** Cadence (cheapest to build, immediate value) -> Ghostwriter (biggest "wow" factor) -> Murmur Mode (unique market positioning).
