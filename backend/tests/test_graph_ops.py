"""Tests for app.services.brain.graph_ops (Phase 11 / Brain B4).

Coverage:
  1.  detect_orphaned_aliases — happy + edge
  2.  repair_orphaned_aliases — dry-run + drop
  3.  detect_broken_bidirectional — person gone, no aliases
  4.  repair_bidirectional — synthesizes missing name alias
  5.  detect_stray_duplicates — name + shared_domain reasons
  6.  dedupe_strays — threshold gating
  7.  undo_merge — full reversal + restored person
  8.  undo_merge — unknown / already-undone error paths
  9.  merge-log hook fires on resolver merge
 10.  router happy-path (detect + repair + undo via TestClient)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.brain.entity_resolver import (
    AliasType,
    InMemoryStore,
    MergeMethod,
    install_merge_log_hook,
    make_resolver,
    uninstall_merge_log_hook,
)
from app.services.brain.graph_ops import (
    clear_merge_log,
    dedupe_strays,
    detect_broken_bidirectional,
    detect_orphaned_aliases,
    detect_stray_duplicates,
    merge_log_rows,
    repair_bidirectional,
    repair_orphaned_aliases,
    undo_merge,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_two_people() -> tuple[InMemoryStore, str, str]:
    store = InMemoryStore()
    aaron = store.upsert_person("Aaron Gagnon", primary_email="aaron@firm.com")
    rijul = store.upsert_person("Rijul Kalra", primary_email="rijul@firm.com")
    store.add_alias(aaron.id, "aaron@firm.com", AliasType.EMAIL)
    store.add_alias(aaron.id, "Aaron Gagnon", AliasType.NAME_STRING)
    store.add_alias(rijul.id, "rijul@firm.com", AliasType.EMAIL)
    store.add_alias(rijul.id, "Rijul Kalra", AliasType.NAME_STRING)
    return store, aaron.id, rijul.id


@pytest.fixture(autouse=True)
def _reset_hooks():
    clear_merge_log()
    uninstall_merge_log_hook()
    yield
    clear_merge_log()
    uninstall_merge_log_hook()


# ---------------------------------------------------------------------------
# 1. detect_orphaned_aliases
# ---------------------------------------------------------------------------

def test_detect_orphaned_aliases_finds_dangling_rows():
    store, aaron_id, _ = _seed_two_people()
    # Forcibly orphan one alias: drop the canonical without removing aliases.
    store.people.pop(aaron_id)

    orphans = detect_orphaned_aliases(store)

    assert len(orphans) == 2, "both aliases for the deleted person are orphans"
    assert all(o.missing_canonical_id == aaron_id for o in orphans)
    types = {o.alias_type for o in orphans}
    assert {"email", "name_string"} == types


def test_detect_orphaned_aliases_empty_when_consistent():
    store, _, _ = _seed_two_people()
    assert detect_orphaned_aliases(store) == []


# ---------------------------------------------------------------------------
# 2. repair_orphaned_aliases — dry-run + drop
# ---------------------------------------------------------------------------

def test_repair_orphaned_aliases_dry_run():
    store, aaron_id, _ = _seed_two_people()
    store.people.pop(aaron_id)

    outcome = repair_orphaned_aliases(store, drop=False)

    assert outcome.fixed_count == 0
    assert outcome.skipped_count == 2
    # Still orphaned because dry-run didn't touch the store.
    assert len(detect_orphaned_aliases(store)) == 2


def test_repair_orphaned_aliases_drops_when_requested():
    store, aaron_id, _ = _seed_two_people()
    store.people.pop(aaron_id)

    outcome = repair_orphaned_aliases(store, drop=True)

    assert outcome.fixed_count == 2
    assert outcome.skipped_count == 0
    assert detect_orphaned_aliases(store) == []


# ---------------------------------------------------------------------------
# 3. detect_broken_bidirectional
# ---------------------------------------------------------------------------

def _strip_aliases_for(store: InMemoryStore, canonical_id: str) -> None:
    """Hook-safe removal that keeps `_alias_index` consistent."""
    for alias_id in [a.id for a in list(store.aliases.values())
                     if a.canonical_id == canonical_id]:
        store.remove_alias(alias_id)


def test_detect_broken_bidi_person_gone():
    store, aaron_id, _ = _seed_two_people()
    # Aaron authored two docs in the inverted index.
    store.person_documents[aaron_id] = {"doc:1", "doc:2"}
    # Then the person was deleted without cascading.
    store.people.pop(aaron_id)
    # Remove their aliases too so we only test the person-gone path.
    _strip_aliases_for(store, aaron_id)

    broken = detect_broken_bidirectional(store)

    # Two doc edges hanging on the missing person
    person_gone = [b for b in broken if b.subject_type == "person"]
    assert len(person_gone) == 2
    assert all(b.subject_id == aaron_id for b in person_gone)


def test_detect_broken_bidi_person_without_aliases():
    store, aaron_id, _ = _seed_two_people()
    # Strip aaron's aliases but keep the person + their documents.
    _strip_aliases_for(store, aaron_id)
    store.person_documents[aaron_id] = {"doc:42"}

    broken = detect_broken_bidirectional(store)

    # Reverse edge from doc -> person flagged
    assert any(b.predicate == "mentions" and b.object_id == aaron_id
               for b in broken)


# ---------------------------------------------------------------------------
# 4. repair_bidirectional — synthesizes missing alias
# ---------------------------------------------------------------------------

def test_repair_bidirectional_synthesizes_missing_name_alias():
    store, aaron_id, _ = _seed_two_people()
    # Strip aaron's aliases, leave the person + documents intact.
    _strip_aliases_for(store, aaron_id)
    store.person_documents[aaron_id] = {"doc:7"}

    outcome = repair_bidirectional(store)

    assert outcome.fixed_count >= 1
    new_aliases = [a for a in store.aliases.values() if a.canonical_id == aaron_id]
    assert any(a.alias_type == AliasType.NAME_STRING for a in new_aliases)


def test_repair_bidirectional_drops_orphaned_index_entries():
    store, aaron_id, _ = _seed_two_people()
    store.person_documents[aaron_id] = {"doc:1"}
    store.people.pop(aaron_id)
    # Clear aliases so detect doesn't fall into the no-alias branch
    _strip_aliases_for(store, aaron_id)

    outcome = repair_bidirectional(store)

    assert outcome.fixed_count == 1
    assert aaron_id not in store.person_documents


# ---------------------------------------------------------------------------
# 5. detect_stray_duplicates
# ---------------------------------------------------------------------------

def test_detect_stray_duplicates_finds_name_matches():
    store = InMemoryStore()
    store.upsert_person("Aaron Gagnon", primary_email="aaron@firm.com")
    store.upsert_person("Aaron Gagnonn", primary_email="aaron2@other.com")  # typo

    # Calibrated to the live name_similarity weighting (≈0.86 for this pair).
    candidates = detect_stray_duplicates(store, threshold=0.80)

    assert len(candidates) == 1
    assert candidates[0].similarity >= 0.80
    assert candidates[0].reason in {"name", "name+shared_domain"}


def test_detect_stray_duplicates_shared_domain_reason():
    store = InMemoryStore()
    # Different surnames but identical domain — domain-only signal.
    store.upsert_person("Aaron Gagnon", primary_email="aaron@firm.com")
    store.upsert_person("Aaron Gagne", primary_email="ag@firm.com")

    candidates = detect_stray_duplicates(store, threshold=0.95)

    # name_similarity here is ~0.75, just enough for the shared_domain
    # weaker-pair rule but below the strict 'name' rule.
    assert len(candidates) == 1
    assert candidates[0].reason == "shared_domain"


def test_detect_stray_duplicates_skips_unrelated_pairs():
    store = InMemoryStore()
    store.upsert_person("Aaron Gagnon", primary_email="aaron@firm.com")
    store.upsert_person("Bob Lee", primary_email="bob@other.com")
    assert detect_stray_duplicates(store, threshold=0.90) == []


# ---------------------------------------------------------------------------
# 6. dedupe_strays threshold gating
# ---------------------------------------------------------------------------

def test_dedupe_strays_threshold_tighter_returns_fewer():
    store = InMemoryStore()
    store.upsert_person("Aaron Gagnon", primary_email="a@firm.com")
    store.upsert_person("Aaron Gagnonn", primary_email="b@firm.com")

    loose = dedupe_strays(store, threshold=0.80)
    tight = dedupe_strays(store, threshold=0.99)

    assert len(loose) >= len(tight)


# ---------------------------------------------------------------------------
# 7. undo_merge — full reversal + restored person
# ---------------------------------------------------------------------------

def test_undo_merge_reverses_alias_moves_and_restores_person():
    store, resolver = make_resolver()
    aaron = store.upsert_person("Aaron Gagnon", primary_email="aaron@firm.com")
    rijul = store.upsert_person("Rijul Kalra", primary_email="rijul@firm.com")
    store.add_alias(aaron.id, "aaron@firm.com", AliasType.EMAIL)
    store.add_alias(aaron.id, "Aaron Gagnon", AliasType.NAME_STRING)
    store.add_alias(rijul.id, "rijul@firm.com", AliasType.EMAIL)
    store.add_alias(rijul.id, "Rijul Kalra", AliasType.NAME_STRING)

    # Merge rijul -> aaron (operator action). Rijul vanishes.
    rec = resolver.merge(
        aaron.id, rijul.id, method=MergeMethod.USER_CONFIRMED,
    )
    assert rijul.id not in store.people

    # Now undo with explicit restore name.
    outcome = undo_merge(
        resolver,
        rec.id,
        restored_person_name="Rijul Kalra",
        restored_person_email="rijul@firm.com",
    )

    assert outcome.success
    assert outcome.aliases_dropped >= 1
    # A new canonical for Rijul should exist again.
    restored = [p for p in store.people.values()
                if p.canonical_name == "Rijul Kalra" and p.id != aaron.id]
    assert len(restored) == 1


# ---------------------------------------------------------------------------
# 8. undo_merge — error paths
# ---------------------------------------------------------------------------

def test_undo_merge_unknown_id_returns_failure():
    _store, resolver = make_resolver()
    outcome = undo_merge(resolver, "merge:nonexistent")
    assert not outcome.success
    assert outcome.error == "unknown merge_id"


def test_undo_merge_idempotent_on_already_undone():
    store, resolver = make_resolver()
    a = store.upsert_person("A One", primary_email="a@f.com")
    b = store.upsert_person("B Two", primary_email="b@f.com")
    store.add_alias(a.id, "a@f.com", AliasType.EMAIL)
    store.add_alias(b.id, "b@f.com", AliasType.EMAIL)
    rec = resolver.merge(a.id, b.id)

    first = undo_merge(resolver, rec.id, restored_person_name="B Two")
    assert first.success

    second = undo_merge(resolver, rec.id)
    assert not second.success
    assert second.error == "merge already undone"


# ---------------------------------------------------------------------------
# 9. merge-log hook
# ---------------------------------------------------------------------------

def test_install_merge_log_hook_captures_resolver_merges():
    install_merge_log_hook()

    store, resolver = make_resolver()
    a = store.upsert_person("A One", primary_email="a@f.com")
    b = store.upsert_person("B Two", primary_email="b@f.com")
    store.add_alias(a.id, "a@f.com", AliasType.EMAIL)
    store.add_alias(b.id, "b@f.com", AliasType.EMAIL)

    assert merge_log_rows() == []
    rec = resolver.merge(a.id, b.id)

    rows = merge_log_rows()
    assert len(rows) == 1
    assert rows[0].id == rec.id
    assert rows[0].merged_into == a.id


# ---------------------------------------------------------------------------
# 10. Router happy-path
# ---------------------------------------------------------------------------

def _client_with_clean_resolver():
    """Build a TestClient with a fresh InMemoryStore wired into the router."""
    from app.main import app
    from app.routers import brain_ops as brain_ops_router

    store, resolver = make_resolver()
    brain_ops_router.set_resolver(store, resolver)
    return TestClient(app), store, resolver


def test_router_detect_repair_undo_happy_path():
    client, store, resolver = _client_with_clean_resolver()
    a = store.upsert_person("A One", primary_email="a@f.com")
    b = store.upsert_person("B Two", primary_email="b@f.com")
    store.add_alias(a.id, "a@f.com", AliasType.EMAIL)
    store.add_alias(b.id, "b@f.com", AliasType.EMAIL)

    # Create an orphan: delete person, leave alias dangling.
    extra = store.upsert_person("Ghost", primary_email="ghost@f.com")
    store.add_alias(extra.id, "ghost@f.com", AliasType.EMAIL)
    store.people.pop(extra.id)

    # detect
    r = client.get("/api/brain/ops/detect")
    assert r.status_code == 200, r.text
    payload = r.json()
    assert len(payload["orphaned_aliases"]) == 1
    assert payload["merge_log_size"] >= 0

    # repair orphans (drop)
    r = client.post(
        "/api/brain/ops/repair",
        json={"kind": "orphaned_aliases", "drop_orphans": True},
    )
    assert r.status_code == 200, r.text
    assert r.json()["fixed_count"] == 1

    # merge then undo via endpoint
    rec = resolver.merge(a.id, b.id)
    r = client.post(
        "/api/brain/ops/undo",
        json={
            "merge_id": rec.id,
            "restored_person_name": "B Two",
            "restored_person_email": "b@f.com",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["merge_id"] == rec.id


def test_router_undo_unknown_merge_returns_404():
    client, _store, _resolver = _client_with_clean_resolver()
    r = client.post("/api/brain/ops/undo", json={"merge_id": "merge:missing"})
    assert r.status_code == 404
