# MuttR Implementation Plan

## Goal
Build a system-wide macOS push-to-talk dictation app that runs 100% locally with Whisper. Hold `fn` to record, release to transcribe and insert cleaned text into the active app. No API keys, no cloud, no recurring cost.

## Product Decisions (Locked)
- Trigger key is `fn` only (no remapping, no fallback hotkey).
- First shared release format is an unsigned local `.app` bundle.
- Cleanup aggressiveness is user-controlled by a slider.
- Slider lives in a menu bar popover.
- First-run setup assistant is required and must validate permissions + basic pipeline.

## Non-Goals (v1)
- No cloud transcription or LLM cleanup.
- No multilingual UI.
- No signed/notarized distribution in v1.
- No custom hotkey remapping.

## Target Platform
- macOS 14+ (Apple Silicon primary target; Intel support best-effort).
- Python 3.11+ runtime embedded or bundled in app packaging flow.

## Tech Stack
- Language: Python 3.11+
- Transcription: `faster-whisper` (CTranslate2 backend)
- macOS APIs: `PyObjC` (event loop, permissions checks, UI, paste simulation)
- Audio: `sounddevice`
- Packaging: `py2app` for unsigned `.app` output
- Config persistence: JSON (`~/Library/Application Support/MuttR/config.json`)
- Logging: Python `logging` to `~/Library/Logs/MuttR/muttr.log`

## Project Structure
```text
MuttR/
├── muttr/
│   ├── __init__.py
│   ├── app.py                 # Main entry point and orchestration
│   ├── state.py               # Explicit app state machine
│   ├── hotkey.py              # fn detection only
│   ├── permissions.py         # Accessibility + microphone checks/prompts
│   ├── recorder.py            # Mic capture + level metering
│   ├── transcriber.py         # faster-whisper wrapper
│   ├── cleanup.py             # Deterministic cleanup profiles
│   ├── inserter.py            # Clipboard/paste insertion
│   ├── overlay.py             # Recording/transcribing/error bubble
│   ├── menubar.py             # Status bar + settings popover (slider)
│   ├── setup_wizard.py        # First-run guided checks
│   ├── config.py              # Load/save config defaults
│   └── diagnostics.py         # Health checks and debug self-test hooks
├── requirements.txt
├── setup.py
├── pyproject.toml
├── scripts/
│   ├── run_dev.sh
│   └── build_app.sh
├── tests/
│   ├── test_cleanup.py
│   ├── test_state_machine.py
│   └── test_config.py
└── .gitignore
```

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

## Component Specifications

### 1. `app.py` (Orchestrator)
- Start `NSApplication` with accessory activation policy (no Dock icon).
- Initialize logger, config, model preload, menu bar, overlay, and setup wizard.
- Wire deterministic pipeline: `hotkey -> recorder -> transcriber -> cleanup -> inserter`.
- Ensure all UI updates happen on main thread; CPU-heavy work on background worker thread.

### 2. `hotkey.py` (fn-only)
- Use flags-changed event monitoring and detect `NSEventModifierFlagFunction`.
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
- Buffer audio in memory only.
- Export real-time RMS level (10-20 Hz sampling) for overlay waveform.
- Guardrails:
  - Minimum utterance duration: 150 ms (below this -> ignore and return `idle`).
  - Maximum utterance duration: 30 s (auto-stop and transcribe).
  - Handle device disconnect by transitioning to `error`.

### 6. `transcriber.py`
- Load model once at startup; fail fast with actionable error if unavailable.
- Default model: `base.en`; optional config setting for `small.en`.
- Device/compute policy:
  - Apple Silicon: `device="cpu"`, `compute_type="int8_float16"` or best supported.
  - Fallback to safe compute type if unsupported.
- Timeout policy:
  - If transcription exceeds configured timeout (default 20 s), abort and surface error.
- Return plain text + confidence metadata for diagnostics (not shown to user by default).

### 7. `cleanup.py` (Slider-Driven Profiles)
Deterministic rule sets only, no LLM.

Slider values map to profiles:
1. `0` Light:
  - normalize whitespace
  - collapse immediate repeated words
  - sentence-case first letter
  - terminal punctuation normalization
2. `1` Moderate:
  - all Light rules
  - remove common fillers (`um`, `uh`, `you know`, `like` in filler contexts)
3. `2` Aggressive:
  - all Moderate rules
  - remove selected false starts and duplicated short phrases
  - stronger punctuation smoothing

Safety rules:
- Never output empty text if raw transcript has non-whitespace content; fall back to raw transcript.
- Preserve obvious URLs/emails/code-like tokens from destructive cleanup.

### 8. `inserter.py`
- Primary path:
  1. snapshot clipboard contents
  2. set cleaned text to pasteboard
  3. short configurable delay (default 60 ms)
  4. send Cmd+V CGEvents
  5. restore prior clipboard within 300 ms
- Reliability:
  - If insertion fails, show non-blocking error and keep text in clipboard so user can paste manually.
  - Add retry-once path with slightly longer delay (120 ms).

### 9. `overlay.py`
- Non-activating always-on-top `NSPanel`.
- States rendered:
  - recording: mic icon + live waveform
  - transcribing: spinner/text
  - success: brief checkmark flash (<=400 ms)
  - error: concise reason + hint
- Position lower-center above Dock area; adapt to multiple display bounds.

### 10. `menubar.py`
- Status bar item always available.
- Popover includes:
  - cleanup aggressiveness slider (`Light`, `Moderate`, `Aggressive`)
  - model choice (`base.en` / `small.en`)
  - reopen setup assistant
  - open log file location
  - quit action

### 11. `config.py`
- Defaults:
  - cleanup level `1` (Moderate)
  - model `base.en`
  - paste delay `60 ms`
  - transcription timeout `20 s`
- Validate and coerce config values on load; write back sanitized values.

### 12. `diagnostics.py`
- Add debug command/menu action: run pipeline self-test and report pass/fail per stage.
- Redact transcript content in logs unless explicit debug mode enabled.

## Dependencies (`requirements.txt`)
```text
faster-whisper>=1.0.0
sounddevice>=0.4.6
numpy>=1.24.0
pyobjc-core>=10.0
pyobjc-framework-Cocoa>=10.0
pyobjc-framework-Quartz>=10.0
py2app>=0.28.0
```

## Permissions Required
1. Accessibility (global event monitor + key event posting)
2. Microphone (audio capture)

## Build and Packaging Flow
1. Create scaffold and modules.
2. Implement state machine and permission checks first.
3. Implement `fn` hotkey + recorder.
4. Implement transcriber and model preload behavior.
5. Implement cleanup profiles and tests.
6. Implement inserter reliability + clipboard restore.
7. Implement overlay + menu bar UI (including slider).
8. Implement first-run setup assistant.
9. Integrate full app orchestration.
10. Package unsigned `.app` with `py2app`.
11. Smoke-test packaged app on clean user account.

## Test Plan
### Unit
- `cleanup.py`: profile outputs, edge token preservation, non-empty safety fallback.
- `state.py`: legal/illegal transitions and concurrency handling.
- `config.py`: invalid values coercion.

### Integration (manual scripted checklist)
1. Fresh install: wizard appears.
2. Denied permission paths: clear guidance, retry works.
3. Hold/release `fn`: recording indicator transitions correctly.
4. Short utterance (<150 ms): ignored cleanly.
5. Long utterance (>30 s): auto-stop and transcribe.
6. Normal dictation: text inserted and clipboard restored.
7. Target app insertion failure scenario: manual paste fallback works.
8. Slider levels produce expected cleanup differences.

### Performance Targets
- Hotkey press to recording indicator: <100 ms
- Release to inserted text for 3-5 second utterance on Apple Silicon (base.en): <=1.5 s median
- Idle CPU usage: near zero background load

## Acceptance Criteria (v1)
- App launches from unsigned `.app` bundle.
- First-run wizard completes with clear pass/fail signals.
- `fn` hold-to-talk flow works end-to-end in common text fields (Notes, Safari, TextEdit).
- Cleanup slider changes behavior immediately and persists across relaunch.
- Failures are actionable and non-silent.
- Logs are available for troubleshooting without exposing sensitive transcript text by default.
