# MuttR Implementation Plan

## Goal
Build a system-wide macOS push-to-talk dictation app that runs 100% locally with Whisper (or Parakeet-MLX). Hold `fn` to record, release to transcribe and insert cleaned text into the active app. No API keys, no cloud, no recurring cost.

## Product Decisions (Locked)
- Trigger key is `fn` only (no remapping, no fallback hotkey).
- First shared release format is an unsigned local `.app` bundle.
- Cleanup aggressiveness is user-controlled by a slider.
- Slider lives in a tabbed Settings window accessible from the menu bar.
- First-run setup assistant is required and must validate permissions + basic pipeline.

## Non-Goals (v1)
- No cloud transcription or LLM cleanup.
- No multilingual UI.
- No signed/notarized distribution in v1.
- No custom hotkey remapping.

## Target Platform
- macOS 14+ (Apple Silicon primary target; Intel support best-effort).
- Python 3.11+ runtime embedded or bundled in app packaging flow.

## Competitive Positioning

MuttR occupies a clear niche: the simplest possible local dictation app for macOS. The landscape splits into overbuilt apps (OpenWhispr, VoiceInk -- accounts, subscriptions, AI chat, dozens of settings) and script-level tools (foges/whisper-dictation, nerd-dictation -- require terminal comfort and manual setup). MuttR's sweet spot is between these: a polished `.app` bundle that does one thing well (hold fn, speak, text appears) with minimal configuration.

Key competitive advantages:
- **Dual transcription engine** -- both faster-whisper and Parakeet-MLX, user-selectable. Matches Handy, VoiceInk, and OpenWhispr which also offer multiple backends.
- **Whisper Confidence Heatmap** -- no competitor surfaces per-word confidence data. MuttR lets users see and correct low-confidence words.
- **Clipboard-Aware Context Stitching** -- uses local clipboard + history as Whisper prompt context. VoiceInk screenshots the screen and sends to cloud LLM; MuttR achieves similar accuracy improvements with zero latency and zero privacy cost.
- **Dictation Cadence Fingerprinting** -- learns each user's speaking rhythm for adaptive silence thresholds. Competitors (Handy) use fixed Silero VAD thresholds.
- **Rich text formatting** -- proper noun capitalization, bullet/numbered list formatting, and paragraph control via voice commands. No competitor offers this depth of deterministic formatting without an LLM.
- **Transcription history with search** -- SQLite-backed, accessible from the Settings window. Comparable to OpenWhispr and OpenSuperWhisper but without cloud sync overhead.

Closest competitor: ashwin-pc/whisper-dictation (same fn-key concept, same Python stack, 24 stars). MuttR is positioned to be the definitive fn-key dictation app for macOS.

## Tech Stack
- **Language:** Python 3.11+
- **Transcription:** `faster-whisper` (CTranslate2 backend) and `parakeet-mlx` (NVIDIA Parakeet on Apple MLX)
- **macOS APIs:** `PyObjC` (event loop, permissions checks, UI, paste simulation)
- **Audio:** `sounddevice`
- **Persistence:** SQLite (`history.db`) for transcription history; JSON for config and account
- **Event system:** Lightweight callback-based event bus (`events.py`) for decoupled module communication
- **Packaging:** `py2app` for unsigned `.app` output (future); `setup.py` with `setuptools` for development
- **Config persistence:** JSON (`~/Library/Application Support/MuttR/config.json`)
- **Account persistence:** JSON (`~/Library/Application Support/MuttR/account.json`)
- **History persistence:** SQLite (`~/Library/Application Support/MuttR/history.db`)
- **Cadence persistence:** JSON (`~/Library/Application Support/MuttR/cadence.json`)
- **Logging:** Python `logging` to `~/Library/Logs/MuttR/muttr.log`

## Project Structure
```text
MuttR/
├── muttr/
│   ├── __init__.py
│   ├── __main__.py           # CLI entry: calls app.main()
│   ├── app.py                 # Main entry point and orchestration (NSApplication run loop)
│   ├── state.py               # Explicit app state machine
│   ├── config.py              # Load/save config defaults (single source of truth)
│   ├── events.py              # Lightweight callback-based event bus
│   ├── hotkey.py              # fn key detection via NSEvent global monitoring
│   ├── recorder.py            # Mic capture + level metering (sounddevice)
│   ├── transcriber.py         # TranscriberBackend protocol + Whisper + Parakeet backends
│   ├── cleanup.py             # Deterministic cleanup pipeline (proper nouns, lists, paragraphs)
│   ├── inserter.py            # Clipboard snapshot/paste/restore insertion
│   ├── overlay.py             # Recording/transcribing/error overlay (NSPanel + waveform)
│   ├── menubar.py             # Status bar item + tabbed Settings window (General/History/Account)
│   ├── history.py             # SQLite transcription history
│   ├── account.py             # Local account/profile with preferences
│   ├── context.py             # Clipboard-aware context stitching (builds Whisper initial_prompt)
│   ├── cadence.py             # Dictation cadence fingerprinting (adaptive silence threshold)
│   ├── permissions.py         # Accessibility + microphone checks/prompts
│   ├── setup_wizard.py        # First-run guided checks
│   └── diagnostics.py         # Health checks and debug self-test hooks
├── requirements.txt
├── setup.py
├── scripts/
│   ├── run_dev.sh
│   └── build_app.sh
├── tests/
│   ├── __init__.py
│   ├── test_cleanup.py
│   ├── test_state_machine.py
│   ├── test_config.py
│   ├── test_history.py
│   ├── test_account.py
│   ├── test_transcriber.py
│   ├── test_events.py
│   ├── test_context.py
│   └── test_cadence.py
├── PLAN.md
├── RESEARCH.md
├── INNOVATION.md
├── ARCHITECTURE.md
└── .gitignore
```

## Module Dependency Graph

```
                          app.py (Orchestrator)
                         /    |    \        \
                        /     |     \        \
                 hotkey.py  overlay.py  menubar.py  events.py
                       |                  |
                       v                  v
                    state.py        config.py (single source of truth)
                       |           /    |     \
                       v          /     |      \
                  recorder.py    /      |       \
                       |        /       |        \
                       v       v        v         v
               transcriber.py  cleanup.py  history.py  account.py
               /          \
              v            v
    WhisperBackend   ParakeetBackend
```

### Dependency Rules
1. No circular imports. Arrows above are the only allowed directions.
2. `config.py` is a leaf -- it imports nothing from `muttr/`.
3. `events.py` is a leaf -- it imports nothing from `muttr/`.
4. `history.py` imports only from `config.py` (for `APP_SUPPORT_DIR`).
5. `account.py` imports only from `config.py` (for `APP_SUPPORT_DIR`).
6. `cleanup.py` imports nothing from `muttr/` (pure functions + data).
7. `transcriber.py` imports nothing from `muttr/` (self-contained backends).
8. `menubar.py` may import `config`, `history`, `account` (read-only for display).
9. `app.py` is the only file that wires everything together.

## Runtime State Machine
States must be explicit and enforced:
1. `idle`
2. `recording`
3. `transcribing`
4. `inserting`
5. `error`

Rules:
- `fn down` is only accepted in `idle`.
- `fn up` is only accepted in `recording`.
- Additional `fn` events during `transcribing`/`inserting` are ignored.
- Any exception transitions to `error` with user-visible reason and recovery action.
- Successful insertion always returns to `idle`.

## Event Bus (`events.py`)

Modules communicate without tight coupling through a simple callback registry.

### Standard Event Names

| Event | Payload | Emitted By | Consumed By |
|-------|---------|------------|-------------|
| `config_changed` | `key: str, value: Any` | `config.py` | `app.py`, `menubar.py` |
| `transcription_complete` | `raw: str, cleaned: str, engine: str, duration: float` | `app.py` | `history.py` listener in `app.py` |
| `engine_changed` | `engine: str` | `config.py` | `app.py` |
| `state_changed` | `old: str, new: str` | `state.py` | `overlay.py`, `menubar.py` |
| `account_changed` | `account: dict` | `account.py` | `menubar.py` |

## Component Specifications

### 1. `app.py` (Orchestrator)
- Start `NSApplication` with accessory activation policy (no Dock icon).
- Initialize logger, config, model preload, menu bar, overlay, and setup wizard.
- Wire deterministic pipeline: `hotkey -> recorder -> transcriber -> cleanup -> inserter`.
- Ensure all UI updates happen on main thread; CPU-heavy work on background worker thread.
- On fn-press, call `reload_engine_if_changed()` to hot-swap transcription backend if the user changed engine in Settings.
- After transcription, log to `history.add_entry()` with engine name and duration.
- React to `config_changed` events to swap engines or update settings dynamically.

### 2. `hotkey.py` (fn-only)
- Use `NSEvent.addGlobalMonitorForEventsMatchingMask_handler_` with `NSEventMaskFlagsChanged` to detect `NSEventModifierFlagFunction`.
- Emit edge transitions (`pressed`, `released`) with de-bounce to avoid duplicate firings.
- Do not implement remapping logic.
- If `fn` cannot be observed on current system configuration, show setup wizard guidance.

### 3. `permissions.py`
- Programmatically check:
  - Accessibility trust status.
  - Microphone authorization status.
- Expose `check_all()` returning per-permission status and human-readable fix steps.
- Provide deep-link/open instructions to System Settings when possible.

### 4. `setup_wizard.py` (Required First Run)
- Launch automatically on first run before normal operation.
- Steps:
  1. Explain required permissions and `fn` usage expectation.
  2. Verify Accessibility (pass/fail with retry button).
  3. Verify Microphone (pass/fail with retry button).
  4. Verify model availability/download.
  5. Run 3-second test recording/transcription.
  6. Run safe insertion test into wizard text box.
- Persist completion flag in config; user can re-open wizard from menu bar.

### 5. `recorder.py`
- Capture 16kHz mono float32 audio via `sounddevice.InputStream`.
- Buffer audio in memory only (no disk writes).
- Export real-time RMS level (read via `recorder.level` property) for overlay waveform.
- Guardrails:
  - Minimum utterance duration: 0.1 s (< 1600 samples -> ignore and return `idle`).
  - Maximum utterance duration: 30 s (auto-stop and transcribe).
  - Handle device disconnect by transitioning to `error`.

### 6. `transcriber.py` (Multi-Backend)

#### TranscriberBackend Protocol
```python
class TranscriberBackend(Protocol):
    def load(self) -> None: ...
    def transcribe(self, audio: np.ndarray) -> str: ...
    @property
    def name(self) -> str: ...
```

#### WhisperBackend (faster-whisper / CTranslate2)
- Load model once at startup; fail fast with actionable error if unavailable.
- Default model: `base.en`; optional config setting for `small.en`.
- Device/compute policy: `device="cpu"`, `compute_type="int8"`.
- Uses `vad_filter=True` and `beam_size=5` for quality.
- Timeout policy: if transcription exceeds configured timeout (default 20 s), abort and surface error.
- Return plain text + confidence metadata for diagnostics.

#### ParakeetBackend (parakeet-mlx)
- Uses `mlx-community/parakeet-tdt-0.6b-v3` model via `parakeet_mlx.from_pretrained()`.
- Accepts numpy float32 audio, writes temp WAV for the parakeet-mlx API, cleans up after.
- Falls back to Whisper if `parakeet-mlx` is not installed (`_parakeet_available()` check).

#### Factory Function
```python
def create_transcriber(engine: str = "whisper", model_size: str = "base.en") -> TranscriberBackend:
```
- The `engine` value comes from `config["transcription_engine"]`. Valid values: `"whisper"`, `"parakeet"`.
- Falls back to Whisper if Parakeet is requested but not installed.

#### Legacy Compat
- `Transcriber` class wraps a backend via `create_transcriber()` for backward compatibility with older `app.py` code.

### 7. `cleanup.py` (Slider-Driven Profiles + Enhanced Formatting)

Deterministic rule sets only, no LLM. Organized as a pipeline of stages.

#### Proper Noun Capitalization (All Levels)
- Days of the week, months, common first names (100+ entries)
- Brand names / tech terms with correct casing: `iPhone`, `macOS`, `GitHub`, `YouTube`, `ChatGPT`, `JavaScript`, `Wi-Fi`, `API`, `URL`, `JSON`, etc. (90+ entries)
- Countries, cities, and US states including multi-word names (`New York`, `San Francisco`, `Salt Lake City`, etc.)
- Extensible user dictionary via `add_proper_nouns()` and `CUSTOM_PROPER_NOUNS`

#### Paragraph / Line-Break Commands (All Levels)
- "period new paragraph" -> `. \n\n`
- "new paragraph" / "next paragraph" -> `\n\n`
- "new line" / "next line" -> `\n`

#### Bullet List Formatting (Moderate+)
- Detects spoken markers: "bullet point one/two/three...", "bullet ...", "dash ...", "next item"
- Converts to formatted `- Item` list with sentence-cased items
- Requires 2+ markers to trigger (avoids false positives like "bullet proof vest")

#### Numbered List Formatting (Moderate+)
- Detects spoken patterns:
  - "number one ... number two ..." (word cardinals)
  - "number 1 ... number 2 ..." (digits)
  - "first ... second ... third ..." (ordinals)
  - "one) ... two) ..." (cardinal with parens)
  - "1. ... 2. ..." (already-formatted digits)
- Converts to formatted `1. Item` list with sentence-cased items
- Preserves preamble text before the list

#### Slider Profiles
1. `0` Light:
   - Paragraph/line-break commands
   - Proper noun capitalization
   - Normalize whitespace
   - Collapse immediate repeated words
   - Sentence-case first letter of each paragraph/sentence
   - Terminal punctuation normalization
2. `1` Moderate:
   - All Light rules
   - Remove common fillers (`um`, `uh`, `you know`, `like`, `basically`, `actually`, `literally`, `I mean`, `sort of`, `kind of`)
   - Bullet list formatting
   - Numbered list formatting
3. `2` Aggressive:
   - All Moderate rules
   - Remove false starts and duplicated short phrases
   - Stronger punctuation smoothing (double periods, space-before-punctuation, comma-period combos)

#### Safety Rules
- Never output empty text if raw transcript has non-whitespace content; fall back to raw transcript.
- Preserve URLs, emails, and backtick-code tokens from destructive cleanup via placeholder extraction/restoration.

### 8. `inserter.py`
- Primary path:
  1. Snapshot clipboard contents (all types)
  2. Set cleaned text to pasteboard
  3. Short delay (50 ms default)
  4. Send Cmd+V via `CGEventCreateKeyboardEvent` + `CGEventPost`
  5. Restore prior clipboard within 100 ms
- Reliability:
  - If insertion fails, text remains in clipboard so user can paste manually.

### 9. `overlay.py`
- Non-activating always-on-top `NSPanel` with borderless style.
- `WaveformView` (custom `NSView`) renders:
  - Recording: mic icon + 5 animated waveform bars driven by audio level + sine-wave animation at 30 fps
  - Transcribing: centered "Transcribing..." text
  - Idle: hidden
- Position: horizontally centered, 80px above screen bottom (above Dock area).
- Joins all Spaces and is stationary.
- Ignores mouse events (non-interactive in current implementation; will become interactive for confidence heatmap feature).

### 10. `menubar.py` (Status Bar + Tabbed Settings Window)

#### Status Bar Item
- `NSStatusBar` item with bold "M" title.
- Dropdown menu: Settings..., separator, Quit MuttR.

#### Settings Window (560x480, tabbed)
- **General tab:**
  - Cleanup aggressiveness slider (Light / Moderate / Aggressive) with live label
  - Transcription Engine dropdown (Whisper / Parakeet-MLX)
  - Whisper Model Size dropdown (base.en / small.en)
  - Paste Delay field (ms) with Save button
- **History tab:**
  - Search field with real-time filtering via `history.search()`
  - Clear All button with confirmation dialog
  - Table view with columns: Time, Transcription (truncated to 120 chars), Engine
  - Alternating row backgrounds, horizontal grid lines, 48px row height
- **Account tab:**
  - Sign-in form: email + display name fields
  - Sign In / Sign Out toggle button
  - Account status label ("Signed in as ..." / "Not signed in")
  - Preferences section: Auto-copy, Sound feedback, Show overlay toggles
  - Account data stored in `account.json`, preferences are per-user

### 11. `history.py` (SQLite Transcription History)
- Database at `~/Library/Application Support/MuttR/history.db`
- Schema:
  ```sql
  CREATE TABLE IF NOT EXISTS transcriptions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp REAL NOT NULL,
      raw_text TEXT NOT NULL,
      cleaned_text TEXT NOT NULL,
      engine TEXT NOT NULL DEFAULT 'whisper',
      duration_s REAL NOT NULL DEFAULT 0.0
  );
  ```
- Public API:
  - `add_entry(raw_text, cleaned_text, engine, duration_s) -> int`
  - `get_recent(limit=50, offset=0) -> list[dict]`
  - `search(query, limit=50) -> list[dict]` (LIKE-based search on raw + cleaned text)
  - `delete_entry(entry_id) -> None`
  - `clear_all() -> None`
  - `count() -> int`

### 12. `account.py` (Local Account System)
- Storage at `~/Library/Application Support/MuttR/account.json`
- Default structure:
  ```json
  {
    "email": "",
    "display_name": "",
    "signed_in": false,
    "preferences": {
      "auto_copy": true,
      "sound_feedback": false,
      "show_overlay": true
    }
  }
  ```
- Public API:
  - `load_account() -> dict`
  - `save_account(data) -> None` (emits `account_changed` event)
  - `sign_in(email, display_name) -> dict`
  - `sign_out() -> dict`
  - `update_preferences(prefs) -> dict`

### 13. `config.py` (Unified Configuration)
- Single source of truth for all app settings.
- Defaults:
  ```python
  DEFAULTS = {
      "cleanup_level": 1,                # 0=Light, 1=Moderate, 2=Aggressive
      "model": "base.en",                # Whisper model size
      "paste_delay_ms": 60,              # Delay before Cmd+V
      "transcription_timeout_s": 20,     # Max transcription time
      "setup_complete": False,           # First-run wizard completed
      "transcription_engine": "whisper", # "whisper" or "parakeet"
      "confidence_review": False,        # Enable confidence heatmap review toast
      "confidence_threshold": 0.7,       # Below this = amber highlight
      "confidence_review_timeout_s": 3,  # Auto-insert after N seconds
      "context_stitching": True,         # Enable clipboard/history-aware prompting
      "adaptive_silence": True,          # Use learned cadence for auto-stop
  }
  ```
- Validation: cleanup_level clamped 0-2, model from `VALID_MODELS`, engine from `VALID_ENGINES`, paste_delay_ms clamped 10-500, timeout clamped 5-120.
- `set_value(key, value)` persists and emits `config_changed` event.

### 14. `events.py` (Event Bus)
- Module-level callback registry using `defaultdict(list)`.
- API: `on(event, callback)`, `off(event, callback)`, `emit(event, **kwargs)`, `clear()`.
- Silent exception handling: a listener failure never breaks the pipeline.

### 15. `diagnostics.py`
- Debug command/menu action: run pipeline self-test and report pass/fail per stage.
- Redact transcript content in logs unless explicit debug mode enabled.

## Innovative Features

### Feature A: Whisper Confidence Heatmap with Tap-to-Correct

**Problem:** Users never know which words the model was confident about vs. guessed at. No competitor surfaces per-word confidence data.

**Solution:** After transcription, show a brief "review toast" overlay where low-confidence words are highlighted in amber/red. Users can tap a highlighted word to see alternative transcriptions (beam search candidates) and pick the correct one.

**Specification:**
- **Data source:** faster-whisper's `transcribe()` with `word_timestamps=True` returns per-word probabilities (0.0 to 1.0).
- **Confidence thresholds (configurable):**
  - >= threshold (default 0.7): white (normal)
  - >= 0.4 but < threshold: amber
  - < 0.4: red
- **UI: Review Toast** (320px wide overlay):
  - Appears after transcription with color-coded confidence text (`NSAttributedString`).
  - Auto-inserts after 3 seconds if no interaction (fast path preserved).
  - Clicking a highlighted word shows top 3 beam search alternatives in a dropdown.
  - "Insert" button for immediate acceptance.
  - Overlay temporarily becomes mouse-interactive, then reverts.
- **Graceful degradation:** Parakeet backend skips heatmap (no word-level confidence) and inserts directly.
- **Config:** `confidence_review` (default: off), `confidence_threshold`, `confidence_review_timeout_s`.
- **Implementation:** Modify `transcriber.py` to return `TranscriptionResult(text, words=[WordInfo(word, start, end, probability)])`. Modify `overlay.py` to add `show_review(result)` state.

### Feature B: Clipboard-Aware Context Stitching

**Problem:** Dictation apps treat each recording as isolated. Real writing is iterative -- users dictate fragments that continue prior text. Whisper has no context about what came before.

**Solution:** Before transcription, peek at the clipboard and recent history to build a context prompt. Feed it to Whisper's `initial_prompt` parameter for priming.

**Specification:**
- **Context sources (combined, trimmed to 224 tokens):**
  1. Clipboard text (last 200 chars, if plain text and not code/URLs)
  2. Last 2 transcriptions from history (last 200 chars total)
  3. User's custom dictionary terms from `cleanup.py`
- **Prompt format:** `"Continue: {context}"`
- **Heuristics:** Skip clipboard if it contains too many special characters or no spaces (likely code/URLs).
- **New module:** `muttr/context.py` with `build_context_prompt() -> str`
- **Integration:** `transcriber.py` accepts optional `initial_prompt` parameter, passed through to faster-whisper. `app.py` calls `build_context_prompt()` before transcription.
- **Parakeet:** If Parakeet supports prompting, use it; otherwise skip.
- **Privacy:** Entirely local. Clipboard/history only used as Whisper prompt, never leaves the machine.
- **Config:** `context_stitching` (default: on).

### Feature C: Dictation Cadence Fingerprinting (Adaptive Silence Threshold)

**Problem:** Fixed silence thresholds cause premature cutoffs for slow speakers and unnecessarily long waits for fast speakers. Competitors use one-size-fits-all thresholds.

**Solution:** Learn the user's speaking cadence over time. Track intra-speech pause durations, build a per-user cadence profile, and compute an individualized silence timeout.

**Specification:**
- **Data collection:** During recording, measure gaps between speech segments using RMS-based energy detection (below floor for > 100ms = pause). Record pause durations.
- **Cadence profile storage:** `~/Library/Application Support/MuttR/cadence.json` with `{mean_pause_ms, p75_pause_ms, p90_pause_ms, sample_count}`. Uses exponential moving average (alpha=0.1).
- **Training threshold:** Minimum 20 samples before profile is considered "trained." Default threshold (2000ms) used until then.
- **Adaptive threshold computation:**
  ```python
  auto_stop_threshold_ms = max(800, min(3000, user_p90_pause_ms * 2.0))
  ```
- **New module:** `muttr/cadence.py` with `CadenceTracker` class, `load_profile()`, `save_profile()`, `get_auto_stop_ms()`.
- **UI integration:** Settings > General shows read-only "Your speaking pace: Fast / Average / Deliberate" and "Reset cadence profile" button.
  - Fast: mean < 300ms
  - Average: 300-600ms
  - Deliberate: > 600ms
- **Privacy:** Only numeric timing data stored. No audio or transcript content in cadence profile.
- **Config:** `adaptive_silence` (default: on).

## Data Flow

The complete pipeline from keypress to inserted text:

```
1.  fn key down (hotkey.py)
        |
2.  state: idle -> recording (state.py)
        |
3.  recorder.start() -> captures audio chunks (recorder.py)
        |   cadence tracker receives audio levels (cadence.py)
        |
4.  fn key up (hotkey.py)
        |
5.  state: recording -> transcribing (state.py)
        |
6.  audio = recorder.stop() -> numpy array (recorder.py)
        |
7.  context_prompt = build_context_prompt() (context.py)
        |   reads clipboard + last 2 history entries + custom dictionary
        |
8.  raw_text = transcriber.transcribe(audio, initial_prompt=context_prompt) (transcriber.py)
        |   dispatches to WhisperBackend or ParakeetBackend
        |   based on config["transcription_engine"]
        |
9.  [if confidence_review enabled] show_review(result) -> user may correct words (overlay.py)
        |
10. cleaned_text = clean_text(raw_text, level=config["cleanup_level"]) (cleanup.py)
        |
11. state: transcribing -> inserting (state.py)
        |
12. insert_text(cleaned_text) (inserter.py)
        |
13. history.add_entry(raw_text, cleaned_text, engine, duration) (history.py)
        |
14. cadence.save_profile() updates cadence stats (cadence.py)
        |
15. state: inserting -> idle (state.py)
```

Steps 7-14 run on a background thread. Step 12's actual paste happens via `_perform_on_main()`.

## Dependencies (`requirements.txt`)
```text
faster-whisper>=1.0.0
sounddevice>=0.4.6
numpy>=1.24.0
pyobjc-core>=10.0
pyobjc-framework-Cocoa>=10.0
pyobjc-framework-Quartz>=10.0

# Optional: Parakeet-MLX for Apple Silicon transcription
# Install with: pip install parakeet-mlx
parakeet-mlx>=0.5.0
```

### Setup.py Extras
```python
extras_require={
    "parakeet": ["parakeet-mlx>=0.5.0"],
}
```

## Permissions Required
1. Accessibility (global event monitor + key event posting)
2. Microphone (audio capture)

## Build and Packaging Flow
1. Create scaffold and modules.
2. Implement state machine and permission checks first.
3. Implement `fn` hotkey + recorder.
4. Implement transcriber (Whisper backend) and model preload behavior.
5. Implement Parakeet-MLX backend with engine toggle and factory.
6. Implement cleanup profiles: proper nouns, lists, paragraphs, and tests.
7. Implement inserter reliability + clipboard restore.
8. Implement overlay + menu bar UI (tabbed Settings window with General/History/Account).
9. Implement transcription history (SQLite) and account system.
10. Implement event bus for decoupled module communication.
11. Implement context stitching (clipboard + history -> Whisper initial_prompt).
12. Implement cadence fingerprinting (adaptive silence threshold).
13. Implement confidence heatmap review toast.
14. Implement first-run setup assistant.
15. Integrate full app orchestration.
16. Package unsigned `.app` with `py2app`.
17. Smoke-test packaged app on clean user account.

## Test Plan

### Unit Tests

#### `test_cleanup.py` (implemented)
- Empty/None/whitespace input safety
- All slider levels accept plain text
- Proper noun capitalization: days, months, first names, brand names, countries, cities, multi-word places, acronyms, tech terms, custom dictionary
- Paragraph commands: new paragraph, next paragraph, new line, next line, period new paragraph, multiple breaks
- Bullet list formatting: bullet point pattern, bullet without point, dash pattern, next item, not at light level, single bullet not formatted
- Numbered list formatting: number word, number digit, ordinal, cardinal paren, digit dot, not at light level, with preamble
- Slider level behavior: level 0 keeps fillers, level 1 removes fillers and "you know", level 2 removes false starts and smooths punctuation
- Sentence casing and terminal punctuation
- URL/email/backtick-code preservation through all cleanup levels
- Mixed formatting scenarios (proper nouns + fillers, paragraphs + proper nouns, lists + proper nouns, lists + fillers, URLs in lists)
- Real-world dictation simulation
- Edge cases: only fillers, single word, already clean text, very long text, mixed case, numbers not confused with lists, default level

#### `test_state_machine.py` (planned)
- Legal/illegal transitions and concurrency handling
- Event emission on state changes

#### `test_config.py` (planned)
- Invalid values coercion
- Default application
- Persistence round-trip
- New key additions

#### `test_history.py` (planned)
- CRUD operations
- Search functionality
- Count and clear operations
- Concurrent access safety

#### `test_account.py` (planned)
- Sign in/out flow
- Preference persistence
- Event emission on changes

#### `test_transcriber.py` (planned)
- Factory function dispatches correctly
- Parakeet fallback when not installed
- Backend protocol compliance

#### `test_events.py` (planned)
- on/off/emit lifecycle
- Multiple listeners
- Exception isolation
- clear() resets state

#### `test_context.py` (planned)
- Context prompt construction from clipboard + history + dictionary
- Code/URL detection and skip logic
- Token limit trimming
- Empty context handling

#### `test_cadence.py` (planned)
- Profile persistence round-trip
- EMA calculation
- Threshold computation with floor/ceiling
- Untrained profile returns default
- Speaking pace classification

### Integration (manual scripted checklist)
1. Fresh install: wizard appears.
2. Denied permission paths: clear guidance, retry works.
3. Hold/release `fn`: recording indicator transitions correctly.
4. Short utterance (<0.1 s): ignored cleanly.
5. Long utterance (>30 s): auto-stop and transcribe.
6. Normal dictation: text inserted and clipboard restored.
7. Target app insertion failure scenario: manual paste fallback works.
8. Slider levels produce expected cleanup differences.
9. Engine toggle: switch between Whisper and Parakeet in Settings, verify both transcribe correctly.
10. Parakeet fallback: with `parakeet-mlx` not installed, selecting Parakeet falls back to Whisper with log warning.
11. Transcription history: entries appear in History tab after dictation, search works, clear all works.
12. Account system: sign in, verify status label updates, sign out, verify fields re-enable.
13. Proper noun capitalization: dictate text with names, brands, cities -- verify correct casing.
14. Bullet/numbered lists: dictate with spoken markers -- verify formatted output.
15. Paragraph commands: dictate with "new paragraph" and "new line" -- verify whitespace.
16. Context stitching: copy text to clipboard, dictate continuation -- verify improved accuracy on names/terms.
17. Cadence fingerprinting: dictate several times with natural pauses -- verify adaptive threshold converges.
18. Confidence heatmap: enable in Settings, dictate ambiguous text -- verify color-coded review toast appears.

### Performance Targets
- Hotkey press to recording indicator: <100 ms
- Release to inserted text for 3-5 second utterance on Apple Silicon (base.en): <=1.5 s median
- Idle CPU usage: near zero background load
- Engine hot-swap (Settings change): model loads in background, no UI freeze
- History search: <50 ms for 1000 entries

## Acceptance Criteria (v1)
- App launches from unsigned `.app` bundle.
- First-run wizard completes with clear pass/fail signals.
- `fn` hold-to-talk flow works end-to-end in common text fields (Notes, Safari, TextEdit).
- Cleanup slider changes behavior immediately and persists across relaunch.
- Both Whisper and Parakeet-MLX backends transcribe correctly when selected.
- Engine toggle in Settings switches backend without restart.
- Parakeet gracefully falls back to Whisper if `parakeet-mlx` is not installed.
- Proper nouns (names, brands, cities) are capitalized correctly in transcribed text.
- Spoken bullet and numbered list markers produce formatted lists at Moderate+ cleanup level.
- Paragraph and line-break voice commands produce correct whitespace.
- Transcription history is recorded and searchable in the Settings History tab.
- Account sign-in/out works and persists user preferences.
- Context stitching uses clipboard + history to improve transcription accuracy.
- Cadence fingerprinting adapts silence threshold to user's speaking pace over time.
- Confidence heatmap (when enabled) displays color-coded review toast with tap-to-correct.
- Failures are actionable and non-silent.
- Logs are available for troubleshooting without exposing sensitive transcript text by default.
- All unit tests pass.
