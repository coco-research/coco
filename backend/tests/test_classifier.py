"""Tests for app.services.auto_classifier.

Phase-1 KG audit (2026-05-26) coverage:
  * Jira-key router: deterministic prefix -> project mapping, including
    titles wrapped in Re:/Fwd: prefixes.
  * acc keyword demotion: narrow positive matches + anti-keyword guards
    that suppress false positives against reg-coe / tax / auditboard
    content.
  * Single-assignment invariant: when multiple projects match, the
    highest-confidence candidate wins and alternates are surfaced.
"""
from __future__ import annotations

import pytest

from app.services import auto_classifier as ac


# ---------------------------------------------------------------------------
# 1. Jira-key router — 5 cases covering each prefix family + Re:/Fwd:
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "title,expected_project",
    [
        ("CROSSRISK-3094: Bridger ETL fix", "reg-coe"),
        ("GRC-4128 — AuditBoard control test", "audit-board"),
        ("SAIHUB-158 EY contract review", "audit-board-tax"),
        ("MPM-1075 Aravo intake form", "optimize"),
        ("SPD-1883 transfer pricing inventory", "optimize"),
        ("AIM-5708 OKR realignment", "tcre"),
        ("UCF-4290 DSAR backlog", "privacy"),
        # Re:/Fwd: handling — reply chains must still route deterministically.
        ("Re: CROSSRISK-2918 sanctions update", "reg-coe"),
        ("Fwd: GRC-9999 audit board working session", "audit-board"),
    ],
)
def test_jira_key_router_routes_known_prefix(title, expected_project):
    result = ac._jira_key_route(title)
    assert result is not None, f"expected match for {title!r}"
    assert result["project_id"] == expected_project
    assert result["method"] == "jira_key_router"
    assert result["confidence"] == 1.0


def test_jira_key_router_returns_none_for_unknown_prefix():
    assert ac._jira_key_route("NOPE-1234 random ticket") is None
    assert ac._jira_key_route("no jira key at all") is None
    assert ac._jira_key_route("") is None
    assert ac._jira_key_route(None) is None  # type: ignore[arg-type]


def test_classify_single_short_circuits_on_jira_key(monkeypatch):
    # Even if rule-based would return something, jira router wins.
    def _boom(*_a, **_kw):  # pragma: no cover - should not be called
        raise AssertionError("rule classifier must not run when jira key matches")

    monkeypatch.setattr(ac, "_rule_based_classify", _boom)
    monkeypatch.setattr(ac, "_llm_classify", _boom)

    result = ac.classify_single(
        content_id="c1",
        title="CROSSRISK-3094 Bridger fix",
        body="some body",
        source="jira",
        sender="someone",
    )
    assert result["project_id"] == "reg-coe"
    assert result["method"] == "jira_key_router"


# ---------------------------------------------------------------------------
# 2. acc keyword demotion — 3 cases: positive match, anti-keyword block,
#    and broad-keyword no-match (the regressions the audit flagged).
# ---------------------------------------------------------------------------


def _stub_rules(monkeypatch, rules):
    monkeypatch.setattr(ac, "_load_classification_rules", lambda: rules)


def test_acc_positive_match_on_literal_keyword(monkeypatch):
    # Override-only rules: simulate the post-fix world.
    _stub_rules(monkeypatch, {
        "acc": {
            "keywords": list(ac.PROJECT_KEYWORD_OVERRIDES["acc"]),
            "senders": [],
            "jira_key": "",
            "anti_keywords": list(ac.PROJECT_ANTI_KEYWORDS["acc"]),
        },
    })
    result = ac._rule_based_classify(
        title="FCPA training rollout for Q3",
        body=None,
        source="email",
        sender=None,
    )
    assert result is not None
    assert result["project_id"] == "acc"
    assert result["confidence"] >= ac.SUGGEST_THRESHOLD


def test_acc_anti_keyword_blocks_tax_content(monkeypatch):
    # Body mentions "anti-corruption" (positive) AND "tax" (anti) — anti wins.
    _stub_rules(monkeypatch, {
        "acc": {
            "keywords": list(ac.PROJECT_KEYWORD_OVERRIDES["acc"]),
            "senders": [],
            "jira_key": "",
            "anti_keywords": list(ac.PROJECT_ANTI_KEYWORDS["acc"]),
        },
    })
    result = ac._rule_based_classify(
        title="Tax compliance — anti-corruption clause review",
        body="quarterly tax filing",
        source="email",
        sender=None,
    )
    assert result is None, "acc must be disqualified by 'tax' anti-keyword"


def test_acc_does_not_match_broad_keywords(monkeypatch):
    # Pre-fix the auto-derived 'case' / 'management' keywords would have
    # matched generic content. With overrides, no acc keyword should hit.
    _stub_rules(monkeypatch, {
        "acc": {
            "keywords": list(ac.PROJECT_KEYWORD_OVERRIDES["acc"]),
            "senders": [],
            "jira_key": "",
            "anti_keywords": list(ac.PROJECT_ANTI_KEYWORDS["acc"]),
        },
    })
    result = ac._rule_based_classify(
        title="Weekly case management sync",
        body="management discussion",
        source="email",
        sender=None,
    )
    assert result is None


# ---------------------------------------------------------------------------
# 3. Single-assignment invariant — highest confidence wins, alternates logged.
# ---------------------------------------------------------------------------


def test_single_assignment_picks_highest_and_logs_alternates(monkeypatch):
    # Two projects both match positively. Higher-confidence one must win,
    # the loser should appear in `alternates` + `reasoning`.
    _stub_rules(monkeypatch, {
        "alpha": {
            "keywords": ["alphaword"],
            "senders": [],
            "jira_key": "",
        },
        "beta": {
            "keywords": ["betaword", "anotherbeta"],  # two matches -> higher conf
            "senders": [],
            "jira_key": "",
        },
    })
    result = ac._rule_based_classify(
        title="alphaword betaword anotherbeta in one title",
        body=None,
        source="email",
        sender=None,
    )
    assert result is not None
    assert result["project_id"] == "beta"
    assert "alternates" in result
    alt_ids = [a["project_id"] for a in result["alternates"]]
    assert "alpha" in alt_ids
    assert "alternates:" in result["reasoning"]


def test_single_assignment_deterministic_tiebreak(monkeypatch):
    # Equal confidence -> sorted by project_id ascending. Deterministic across runs.
    _stub_rules(monkeypatch, {
        "zeta": {"keywords": ["sharedword"], "senders": [], "jira_key": ""},
        "alpha": {"keywords": ["sharedword"], "senders": [], "jira_key": ""},
        "mu": {"keywords": ["sharedword"], "senders": [], "jira_key": ""},
    })
    result = ac._rule_based_classify(
        title="sharedword present", body=None, source="email", sender=None,
    )
    assert result is not None
    assert result["project_id"] == "alpha"  # lexicographic tiebreak
