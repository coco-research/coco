"""Null-safety tests for _build_briefing (app.routers.home)."""
from unittest.mock import patch

import pytest

from app.routers.home import _build_briefing


@pytest.fixture(autouse=True)
def _no_snapshot():
    """Disable snapshot read/write so tests are pure unit tests."""
    with patch("app.routers.home._read_snapshot", return_value=None), \
         patch("app.routers.home._write_snapshot"):
        yield


def _assert_shape(result):
    assert isinstance(result, dict)
    assert "script" in result and isinstance(result["script"], str)
    assert "scenes" in result and isinstance(result["scenes"], list)
    assert len(result["scenes"]) >= 1


def test_briefing_with_none_input_does_not_crash():
    """Function must tolerate a None input."""
    result = _build_briefing(None)
    _assert_shape(result)


def test_briefing_with_empty_dict():
    result = _build_briefing({})
    _assert_shape(result)


def test_briefing_with_none_subfields():
    """All known top-level keys may be None."""
    result = _build_briefing({
        "since_last_session": None,
        "attention": None,
        "health": None,
        "todos": None,
        "projects": None,
    })
    _assert_shape(result)


def test_briefing_with_none_entries_in_lists():
    """Individual list entries may be None or have missing keys."""
    result = _build_briefing({
        "since_last_session": {"hours_ago": None},
        "attention": {"overdue_todos": None, "pending_drafts": None},
        "health": [None, {}, {"source": None, "stale_hours": None}, {"source": "jira", "stale_hours": 100}],
        "todos": {"total_open": None, "high_priority": None},
        "projects": [None, {}, {"id": None, "name": None, "active": True, "todo_open": 10}],
    })
    _assert_shape(result)


def test_briefing_with_prev_snapshot_none_fields():
    """Comparison branch with None-filled previous snapshot must not crash."""
    prev = {
        "attention": None,
        "todos": None,
        "health": [None, {"source": None, "stale_hours": None}],
        "projects": [None, {"id": None, "todo_open": None}],
    }
    with patch("app.routers.home._read_snapshot", return_value=prev):
        result = _build_briefing({
            "since_last_session": None,
            "attention": {"overdue_todos": 2, "pending_drafts": 1},
            "health": [{"source": "jira", "stale_hours": 200}],
            "todos": {"total_open": 5, "high_priority": [{"id": 1}, {"id": 2}]},
            "projects": [{"id": 1, "name": "P", "active": True, "todo_open": 7}],
        })
        _assert_shape(result)


def test_briefing_with_top_project_missing_name():
    """Spotlight scene should fall back when project name is None."""
    result = _build_briefing({
        "projects": [{"id": 1, "name": None, "active": True, "todo_open": 8}],
    })
    _assert_shape(result)
    # ensure no literal "None" leaked into the script
    assert "None is picking up" not in result["script"]
