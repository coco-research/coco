"""Regression tests for EventBus synchronous listener API.

Covers the fix for the self-improve scheduler bug where
``register_event_listeners()`` monkey-patched ``event_bus.emit`` by wrapping
it, so repeated calls (app restart in tests, reloads) stacked wrappers and
fired the completion handler multiple times with growing call depth.

The fix replaces monkey-patching with an idempotent ``EventBus.on()`` listener
registry invoked inside ``emit()``.
"""

from __future__ import annotations

import pytest

from app.services.event_bus import EventBus, event_bus
from app.services import self_improve_scheduler as sched


def _make_bus(monkeypatch) -> EventBus:
    """Fresh bus with persistence/file bridges stubbed out (pure-unit)."""
    bus = EventBus()
    monkeypatch.setattr(bus, "_persist", lambda *a, **k: None)
    monkeypatch.setattr(bus, "_append_jsonl", lambda *a, **k: None)
    return bus


def test_on_invokes_only_matching_event(monkeypatch):
    bus = _make_bus(monkeypatch)
    seen: list[dict] = []
    bus.on("x.evt", lambda d: seen.append(d))

    bus.emit("x.evt", {"v": 1})
    bus.emit("other.evt", {"v": 2})

    assert seen == [{"v": 1}]


def test_on_is_idempotent(monkeypatch):
    """Registering the same (event_type, callback) repeatedly fires once."""
    bus = _make_bus(monkeypatch)
    calls: list[dict] = []

    def cb(d: dict) -> None:
        calls.append(d)

    bus.on("x.evt", cb)
    bus.on("x.evt", cb)
    bus.on("x.evt", cb)

    bus.emit("x.evt", {"v": 1})

    assert len(calls) == 1


def test_wildcard_listener_receives_all(monkeypatch):
    bus = _make_bus(monkeypatch)
    seen: list[dict] = []
    bus.on(None, lambda d: seen.append(d))

    bus.emit("a", {"n": 1})
    bus.emit("b", {"n": 2})

    assert len(seen) == 2


def test_listener_error_does_not_break_emit(monkeypatch):
    bus = _make_bus(monkeypatch)
    ok: list[dict] = []

    def boom(_d: dict) -> None:
        raise RuntimeError("listener blew up")

    bus.on("e", boom)
    bus.on("e", lambda d: ok.append(d))

    # Must not raise even though the first listener throws.
    bus.emit("e", {})

    assert len(ok) == 1


def test_off_removes_listener(monkeypatch):
    bus = _make_bus(monkeypatch)
    seen: list[dict] = []

    def cb(d: dict) -> None:
        seen.append(d)

    bus.on("e", cb)
    bus.off("e", cb)
    bus.emit("e", {})

    assert seen == []


def test_reentrant_emit_in_listener_is_safe(monkeypatch):
    """A listener that emits another event must not corrupt iteration."""
    bus = _make_bus(monkeypatch)
    outer: list[dict] = []
    inner: list[dict] = []

    bus.on("inner", lambda d: inner.append(d))
    bus.on("outer", lambda d: (outer.append(d), bus.emit("inner", {"from": "outer"})))

    bus.emit("outer", {"v": 1})

    assert len(outer) == 1
    assert inner == [{"from": "outer"}]


def test_register_event_listeners_is_idempotent(monkeypatch):
    """The real scheduler hook must not stack on repeated startup calls."""
    monkeypatch.setattr(event_bus, "_persist", lambda *a, **k: None)
    monkeypatch.setattr(event_bus, "_append_jsonl", lambda *a, **k: None)
    monkeypatch.setattr(event_bus, "_listeners", [])

    calls: list[dict] = []
    monkeypatch.setattr(sched, "on_cycle_completed", lambda d: calls.append(d))

    sched.register_event_listeners()
    sched.register_event_listeners()  # second startup must not double-register

    event_bus.emit("self_improve.cycle_completed", {"cycle_id": "abc"})

    assert len(calls) == 1
