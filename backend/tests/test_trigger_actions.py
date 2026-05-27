"""Light unit tests for the trigger action dispatcher.

These tests exercise pure logic only -- the registry shape, the JSON-string
action_config decoding path, and the unknown-action fallback. Handlers
that touch the DB or process_manager are covered by integration tests.
"""

import asyncio
import json

import pytest

from app.services import trigger_actions
from app.services.trigger_actions import (
    ACTION_HANDLERS,
    _action_config,
    dispatch_action,
    notify,
)


def test_registry_contains_all_expected_actions():
    expected = {
        "spawn_agent",
        "create_todo",
        "notify",
        "run_command",
        "self_improve_auto",
        "podcast_generate",
    }
    assert set(ACTION_HANDLERS.keys()) == expected


def test_action_config_parses_json_string():
    trigger = {"action_config": json.dumps({"message": "hello"})}
    assert _action_config(trigger) == {"message": "hello"}


def test_action_config_handles_dict_passthrough():
    trigger = {"action_config": {"foo": 1}}
    assert _action_config(trigger) == {"foo": 1}


def test_action_config_handles_missing_or_bad_json():
    assert _action_config({}) == {}
    assert _action_config({"action_config": "not json"}) == {}
    assert _action_config({"action_config": None}) == {}


@pytest.mark.asyncio
async def test_dispatch_unknown_action_skipped():
    result = await dispatch_action({"id": "x", "action_type": "no_such_action"})
    assert result["status"] == "skipped"
    assert "Unknown action type" in result["result"]


@pytest.mark.asyncio
async def test_notify_emits_event_and_returns_success(monkeypatch):
    captured: list[tuple[str, dict]] = []

    def fake_emit(event, payload):
        captured.append((event, payload))

    monkeypatch.setattr(trigger_actions.event_bus, "emit", fake_emit)

    trigger = {
        "id": "t1",
        "name": "ping",
        "action_type": "notify",
        "action_config": {"message": "hi there"},
    }
    result = await notify(trigger, ctx={"src": "test"})

    assert result["status"] == "success"
    assert "hi there" in result["result"]
    assert captured and captured[0][0] == "trigger.notification"
    assert captured[0][1]["message"] == "hi there"
    assert captured[0][1]["context"] == {"src": "test"}


@pytest.mark.asyncio
async def test_dispatch_catches_handler_exception(monkeypatch):
    async def boom(_t, _c):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(ACTION_HANDLERS, "notify", boom)
    try:
        result = await dispatch_action({"id": "t", "action_type": "notify"})
        assert result["status"] == "failed"
        assert "kaboom" in result["error"]
    finally:
        # restore real handler so other tests aren't poisoned
        monkeypatch.setitem(ACTION_HANDLERS, "notify", notify)
