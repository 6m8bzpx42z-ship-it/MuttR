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
