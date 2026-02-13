# MuttR Architecture

Unified architecture blueprint for all concurrent feature development.

---

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

1. **No circular imports.** Arrows above are the only allowed directions.
2. `config.py` is a leaf -- it imports nothing from `muttr/`.
3. `history.py` imports only from `config.py` (for `APP_SUPPORT_DIR`).
4. `account.py` imports only from `config.py` (for `APP_SUPPORT_DIR`).
5. `cleanup.py` imports nothing from `muttr/` (pure functions + data).
6. `transcriber.py` imports nothing from `muttr/` (self-contained backends).
7. `events.py` is a new lightweight event bus -- imports nothing from `muttr/`.
8. `menubar.py` may import `config`, `history`, `account` (read-only for display).
9. `app.py` is the only file that wires everything together.

---

## New File/Folder Structure

```
muttr/
    __init__.py
    __main__.py
    app.py               # Orchestrator (wires everything, owns run loop)
    state.py             # State machine (idle/recording/transcribing/inserting/error)
    config.py            # Single source of truth for all settings
    events.py            # NEW -- lightweight callback-based event bus
    hotkey.py            # fn key detection
    recorder.py          # Audio capture
    transcriber.py       # TranscriberBackend protocol + Whisper + Parakeet impls
    cleanup.py           # CleanupPipeline protocol + formatting stages
    inserter.py          # Clipboard paste
    overlay.py           # Recording/transcribing overlay
    menubar.py           # Status bar + settings window (reads config/history/account)
    history.py           # SQLite transcription history
    account.py           # Local account/profile
    permissions.py       # Accessibility + mic checks
    setup_wizard.py      # First-run wizard
    diagnostics.py       # Health checks
```

No subdirectories needed at this scale. All files live flat under `muttr/`.

---

## Event Bus (`events.py`)

Modules communicate without tight coupling through a simple callback registry.

```python
"""Lightweight event bus for decoupled module communication."""

from collections import defaultdict
from typing import Any, Callable

_listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)


def on(event: str, callback: Callable[..., Any]) -> None:
    """Register a callback for an event name."""
    _listeners[event].append(callback)


def off(event: str, callback: Callable[..., Any]) -> None:
    """Unregister a callback."""
    try:
        _listeners[event].remove(callback)
    except ValueError:
        pass


def emit(event: str, **kwargs: Any) -> None:
    """Fire all callbacks registered for this event."""
    for cb in _listeners.get(event, []):
        try:
            cb(**kwargs)
        except Exception:
            pass  # never let a listener break the pipeline


def clear() -> None:
    """Remove all listeners. Useful for tests."""
    _listeners.clear()
```

### Standard Event Names

| Event | Payload | Emitted By | Consumed By |
|-------|---------|------------|-------------|
| `config_changed` | `key: str, value: Any` | `config.py` | `app.py`, `menubar.py` |
| `transcription_complete` | `raw: str, cleaned: str, engine: str, duration: float` | `app.py` | `history.py` listener in `app.py` |
| `engine_changed` | `engine: str` | `config.py` | `app.py` |
| `state_changed` | `old: str, new: str` | `state.py` | `overlay.py`, `menubar.py` |
| `account_changed` | `account: dict` | `account.py` | `menubar.py` |

---

## Protocol/ABC Interfaces

### TranscriberBackend (in `transcriber.py`)

Already exists and is correct. Parakeet-dev must implement this exactly:

```python
class TranscriberBackend(Protocol):
    """Interface that every transcription backend must satisfy."""

    def load(self) -> None: ...
    def transcribe(self, audio: np.ndarray) -> str: ...
    @property
    def name(self) -> str: ...
```

**Factory function** (already exists):
```python
def create_transcriber(engine: str = "whisper", model_size: str = "base.en") -> TranscriberBackend:
    ...
```

The `engine` value comes from `config["transcription_engine"]`. Valid values: `"whisper"`, `"parakeet"`.

### CleanupStage Protocol (in `cleanup.py`)

The cleanup pipeline should be composed of stages. Each stage is a simple callable:

```python
class CleanupStage(Protocol):
    """A single text transformation stage."""
    def __call__(self, text: str) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def min_level(self) -> int: ...
```

The public `clean_text(text, level)` function already works correctly. Internally, formatting-dev should organize the existing functions as stages but keep the same `clean_text()` signature as the public API. The current implementation is fine -- this protocol is for future extensibility, not a required refactor right now.

**Do NOT change the `clean_text(text: str, level: int = 1) -> str` signature.** It is called by `app.py` and must remain stable.

### HistoryStore (in `history.py`)

The current module-level functions are the interface. No class wrapper needed:

```python
# These are the public functions -- their signatures must not change:
def add_entry(raw_text: str, cleaned_text: str, engine: str = "whisper", duration_s: float = 0.0) -> int: ...
def get_recent(limit: int = 50, offset: int = 0) -> list[dict]: ...
def search(query: str, limit: int = 50) -> list[dict]: ...
def delete_entry(entry_id: int) -> None: ...
def clear_all() -> None: ...
def count() -> int: ...
```

### AccountProvider (in `account.py`)

Same -- module-level functions are the interface:

```python
def load_account() -> dict: ...
def save_account(data: dict) -> None: ...
def sign_in(email: str, display_name: str = "") -> dict: ...
def sign_out() -> dict: ...
def update_preferences(prefs: dict) -> dict: ...
```

---

## Unified Config Schema (`config.py`)

`config.py` is the single source of truth. All settings go through it.

```python
DEFAULTS = {
    # Existing
    "cleanup_level": 1,                # 0=Light, 1=Moderate, 2=Aggressive
    "model": "base.en",                # Whisper model size
    "paste_delay_ms": 60,              # Delay before Cmd+V
    "transcription_timeout_s": 20,     # Max transcription time
    "setup_complete": False,           # First-run wizard completed
    "transcription_engine": "whisper", # "whisper" or "parakeet"
}

VALID_MODELS = {"base.en", "small.en"}
VALID_ENGINES = {"whisper", "parakeet"}
```

### Rules for Adding New Config Keys

1. Add the key + default to `DEFAULTS` in `config.py`.
2. Add validation in `load()` if the value needs coercion.
3. Add the key to `VALID_*` sets if it has enumerated values.
4. Never store config in `account.json` -- account preferences (`auto_copy`, `sound_feedback`, `show_overlay`) live in the account file since they are per-user, but engine/model/cleanup config is in `config.json`.

### Config Change Notifications

When code calls `config.set_value(key, value)`, it should emit an event so other modules can react:

```python
def set_value(key, value):
    data = load()
    data[key] = value
    save(data)
    from muttr import events
    events.emit("config_changed", key=key, value=value)
```

---

## Database Schema (`history.db`)

SQLite database at `~/Library/Application Support/MuttR/history.db`.

### `transcriptions` table (already exists)

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

This schema is correct and sufficient. No changes needed.

### Account storage

Account data lives in `account.json` (not SQLite). This is correct for the current local-only model.

Path: `~/Library/Application Support/MuttR/account.json`

---

## Data Flow

The complete pipeline from keypress to inserted text:

```
1. fn key down (hotkey.py)
       |
2. state: idle -> recording (state.py)
       |
3. recorder.start() -> captures audio chunks (recorder.py)
       |
4. fn key up (hotkey.py)
       |
5. state: recording -> transcribing (state.py)
       |
6. audio = recorder.stop() -> numpy array (recorder.py)
       |
7. raw_text = transcriber.transcribe(audio) (transcriber.py)
       |      dispatches to WhisperBackend or ParakeetBackend
       |      based on config["transcription_engine"]
       |
8. cleaned_text = clean_text(raw_text, level=config["cleanup_level"]) (cleanup.py)
       |
9. state: transcribing -> inserting (state.py)
       |
10. insert_text(cleaned_text) (inserter.py)
       |
11. history.add_entry(raw_text, cleaned_text, engine, duration) (history.py)
       |
12. state: inserting -> idle (state.py)
```

Steps 7-11 run on a background thread. Steps 10's actual paste happens via `_perform_on_main()`.

---

## How `app.py` Stays Thin

`app.py` is the orchestrator, not a god object. Its responsibilities:

1. **Initialize** all components (config, recorder, transcriber, overlay, menubar, hotkey).
2. **Wire callbacks**: hotkey events -> record/stop/transcribe pipeline.
3. **Delegate** all work to the appropriate module.
4. **React to events**: listen for `config_changed` to swap transcriber engines.

`app.py` should NOT contain:
- UI layout code (that goes in `menubar.py` and `overlay.py`)
- Database queries (that goes in `history.py`)
- Text processing logic (that goes in `cleanup.py`)
- Account logic (that goes in `account.py`)

The current `app.py` already follows this pattern. Keep it this way.

---

## Merge Conflict Avoidance

Each agent owns specific files. Do NOT edit files owned by another agent.

| Agent | Owns (can edit) | Must NOT edit |
|-------|----------------|---------------|
| **ui-developer** | `menubar.py`, `account.py`, `history.py` | `transcriber.py`, `cleanup.py`, `app.py` |
| **parakeet-dev** | `transcriber.py` (ParakeetBackend class + factory) | `cleanup.py`, `menubar.py`, `history.py`, `account.py` |
| **formatting-dev** | `cleanup.py` | `transcriber.py`, `menubar.py`, `history.py`, `account.py` |
| **overflow-dev** | New files only (TBD) | All existing files unless coordinated |
| **architect** | `ARCHITECTURE.md`, `events.py`, `config.py` | Feature files |

### Shared files (coordinate changes)

- **`app.py`**: Only architect or team-lead should modify. If an agent needs `app.py` changes, request them via message.
- **`config.py`**: Adding new keys to DEFAULTS is safe (append-only). Modifying existing keys requires coordination.
- **`requirements.txt`** / **`setup.py`**: Adding new dependencies is safe (append-only).

---

## Integration Points

### How Settings UI reads/writes config

`menubar.py` already does this correctly:
- Read: `config.load()` returns the full dict
- Write: `config.set_value(key, value)` persists a single key
- The settings window reads on open, writes on change

### How engine selection flows

1. User selects engine in Settings > General > Transcription Engine dropdown
2. `menubar.py` calls `config.set_value("transcription_engine", "parakeet")`
3. On next fn-press, `app.py` calls `reload_engine_if_changed()` which:
   - Reads config
   - If engine changed, calls `create_transcriber(engine=new_engine)`
   - Loads new model in background thread

### How history integrates

1. After transcription, `app.py` calls `history.add_entry(...)`
2. When user opens Settings > History tab, `menubar.py` calls `history.get_recent()`
3. Search uses `history.search(query)`
4. Clear uses `history.clear_all()` (with confirmation dialog)

### How account integrates

1. Account tab in settings reads/writes via `account.load_account()` / `account.sign_in()` / `account.sign_out()`
2. Account preferences (auto_copy, sound_feedback, show_overlay) stored in `account.json`
3. These preferences are per-user settings, separate from app-level config in `config.json`
