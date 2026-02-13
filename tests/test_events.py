"""Tests for muttr.events -- lightweight event bus."""

import pytest

from muttr import events


class TestEventBus:
    def setup_method(self):
        events.clear()

    def teardown_method(self):
        events.clear()

    def test_on_and_emit(self):
        received = []
        events.on("test_event", lambda **kw: received.append(kw))
        events.emit("test_event", value=42)
        assert len(received) == 1
        assert received[0]["value"] == 42

    def test_emit_with_no_listeners(self):
        # Should not raise
        events.emit("nonexistent_event", data="hello")

    def test_multiple_listeners(self):
        results = []
        events.on("multi", lambda **kw: results.append("a"))
        events.on("multi", lambda **kw: results.append("b"))
        events.emit("multi")
        assert results == ["a", "b"]

    def test_off_removes_listener(self):
        results = []
        cb = lambda **kw: results.append("called")
        events.on("remove_test", cb)
        events.off("remove_test", cb)
        events.emit("remove_test")
        assert len(results) == 0

    def test_off_nonexistent_listener_no_error(self):
        cb = lambda **kw: None
        # Removing a callback that was never registered should not raise
        events.off("no_such_event", cb)

    def test_off_only_removes_specified_callback(self):
        results = []
        cb1 = lambda **kw: results.append("cb1")
        cb2 = lambda **kw: results.append("cb2")
        events.on("partial", cb1)
        events.on("partial", cb2)
        events.off("partial", cb1)
        events.emit("partial")
        assert results == ["cb2"]

    def test_clear_removes_all(self):
        results = []
        events.on("event_a", lambda **kw: results.append("a"))
        events.on("event_b", lambda **kw: results.append("b"))
        events.clear()
        events.emit("event_a")
        events.emit("event_b")
        assert len(results) == 0

    def test_listener_exception_does_not_break_others(self):
        results = []

        def bad_listener(**kw):
            raise ValueError("boom")

        events.on("error_test", bad_listener)
        events.on("error_test", lambda **kw: results.append("ok"))
        events.emit("error_test")
        # Second listener should still fire despite first raising
        assert results == ["ok"]

    def test_emit_passes_kwargs(self):
        received = {}
        def handler(**kw):
            received.update(kw)
        events.on("kwargs_test", handler)
        events.emit("kwargs_test", a=1, b="two", c=[3])
        assert received == {"a": 1, "b": "two", "c": [3]}

    def test_separate_events_are_isolated(self):
        results_a = []
        results_b = []
        events.on("event_a", lambda **kw: results_a.append(1))
        events.on("event_b", lambda **kw: results_b.append(2))
        events.emit("event_a")
        assert results_a == [1]
        assert results_b == []

    def test_emit_multiple_times(self):
        count = []
        events.on("counter", lambda **kw: count.append(1))
        events.emit("counter")
        events.emit("counter")
        events.emit("counter")
        assert len(count) == 3
