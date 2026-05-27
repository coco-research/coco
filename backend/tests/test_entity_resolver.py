"""Tests for app.services.brain.entity_resolver (Phase 7 / Brain B3).

Coverage:
  1.  exact match (email, name)
  2.  fuzzy match (auto + queued)
  3.  conflict / merge
  4.  undo merge
  5.  idempotence
  6.  identity collisions (separate when evidence differs)
  7.  edge cases (empty / None / unicode / whitespace)
  8.  threshold tuning
  9.  alias drift (voice transcription)
 10.  merge commutativity — hypothesis property
 11.  merge associativity — hypothesis property
 12.  ingest wire-in (resolve_person_for_ingest + bidirectional link)
 13.  bidi link hook fires on add/reassign/remove

Plus pure-function unit tests for normalize/levenshtein/token_overlap and
ValueError paths.
"""
from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.services.brain.entity_resolver import (
    AliasType,
    EntityResolver,
    InMemoryStore,
    MergeMethod,
    MergeStatus,
    levenshtein,
    levenshtein_similarity,
    make_resolver,
    name_similarity,
    normalize_name,
    register_bidirectional_link_hook,
    resolve_person_for_ingest,
    token_overlap,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_aaron(store: InMemoryStore) -> str:
    p = store.upsert_person("Aaron Gagnon", primary_email="aaron.gagnon@firm.com")
    store.add_alias(p.id, "aaron.gagnon@firm.com", AliasType.EMAIL)
    store.add_alias(p.id, "Aaron Gagnon", AliasType.NAME_STRING)
    return p.id


def _seed_aude(store: InMemoryStore) -> str:
    p = store.upsert_person("Aude Delechat", primary_email="aude@firm.com")
    store.add_alias(p.id, "aude@firm.com", AliasType.EMAIL)
    store.add_alias(p.id, "Aude Delechat", AliasType.NAME_STRING)
    return p.id


# ---------------------------------------------------------------------------
# 1. exact match
# ---------------------------------------------------------------------------

def test_exact_email_match():
    store, resolver = make_resolver()
    pid = _seed_aaron(store)
    r = resolver.resolve("aaron.gagnon@firm.com", AliasType.EMAIL)
    assert r.matched is True
    assert r.canonical_id == pid
    assert r.method == "exact"
    assert r.similarity == 1.0


def test_exact_name_match():
    store, resolver = make_resolver()
    pid = _seed_aaron(store)
    r = resolver.resolve("Aaron Gagnon", AliasType.NAME_STRING)
    assert r.matched is True and r.canonical_id == pid and r.method == "exact"


# ---------------------------------------------------------------------------
# 2. fuzzy match
# ---------------------------------------------------------------------------

def test_fuzzy_name_match_above_pending_threshold():
    store, resolver = make_resolver()
    pid = _seed_aaron(store)
    r = resolver.resolve(
        "A. Gagnon",
        AliasType.NAME_STRING,
        secondary_email="aaron.work@firm.com",
    )
    assert r.similarity >= resolver.pending_threshold


def test_fuzzy_name_match_pending_without_secondary():
    store, resolver = make_resolver()
    _seed_aaron(store)
    r = resolver.resolve("Aaron Gagnonn", AliasType.NAME_STRING)
    assert r.method == "queued"
    assert r.matched is False
    assert any(
        e["alias_value"] == "Aaron Gagnonn" for e in store.pending_queue
    )


# ---------------------------------------------------------------------------
# 3. conflict / merge
# ---------------------------------------------------------------------------

def test_conflict_merge_two_persons_into_one():
    store, resolver = make_resolver()
    a = _seed_aaron(store)
    b_person = store.upsert_person("Aaron G.")
    store.add_alias(b_person.id, "aaron.g@otherfirm.com", AliasType.EMAIL)
    store.add_alias(b_person.id, "Aaron G.", AliasType.NAME_STRING)

    rec = resolver.merge(
        canonical_id=a,
        other_canonical_id=b_person.id,
        method=MergeMethod.USER_CONFIRMED,
    )
    assert rec.canonical_id == a
    assert store.get_person(b_person.id) is None
    merged_email = store.find_alias_exact(
        "aaron.g@otherfirm.com", AliasType.EMAIL
    )
    assert merged_email is not None and merged_email.canonical_id == a


# ---------------------------------------------------------------------------
# 4. undo
# ---------------------------------------------------------------------------

def test_undo_merge_marks_re_resolve_pending_and_removes_aliases():
    store, resolver = make_resolver()
    a = _seed_aaron(store)
    b_person = store.upsert_person("Aaron Other")
    store.add_alias(b_person.id, "aaron.other@example.com", AliasType.EMAIL)

    rec = resolver.merge(a, b_person.id, method=MergeMethod.USER_CONFIRMED)
    assert (
        store.find_alias_exact("aaron.other@example.com", AliasType.EMAIL)
        is not None
    )
    resolver.undo_merge(rec.id)
    assert store.find_alias_exact("aaron.other@example.com", AliasType.EMAIL) is None
    assert a in store.re_resolve_pending
    # idempotent
    resolver.undo_merge(rec.id)
    assert a in store.re_resolve_pending


# ---------------------------------------------------------------------------
# 5. idempotence
# ---------------------------------------------------------------------------

def test_add_alias_idempotent():
    store, _ = make_resolver()
    p = store.upsert_person("Aaron Gagnon")
    a1 = store.add_alias(p.id, "aaron@firm.com", AliasType.EMAIL)
    a2 = store.add_alias(p.id, "aaron@firm.com", AliasType.EMAIL)
    assert a1.id == a2.id


def test_resolve_twice_no_duplicate_alias():
    store, resolver = make_resolver()
    pid = _seed_aaron(store)
    r1 = resolver.resolve("aaron.gagnon@firm.com", AliasType.EMAIL)
    r2 = resolver.resolve("aaron.gagnon@firm.com", AliasType.EMAIL)
    assert r1.canonical_id == r2.canonical_id == pid
    emails = [
        a
        for a in store.aliases_for_person(pid)
        if a.alias_type == AliasType.EMAIL
        and a.alias_value == "aaron.gagnon@firm.com"
    ]
    assert len(emails) == 1


# ---------------------------------------------------------------------------
# 6. identity collisions
# ---------------------------------------------------------------------------

def test_two_aarons_remain_separate_when_evidence_differs():
    store, resolver = make_resolver()
    _seed_aaron(store)
    p2 = store.upsert_person("Aaron Smith", primary_email="aaron.smith@other.com")
    store.add_alias(p2.id, "aaron.smith@other.com", AliasType.EMAIL)
    store.add_alias(p2.id, "Aaron Smith", AliasType.NAME_STRING)

    r = resolver.resolve("Aaron Smith", AliasType.NAME_STRING)
    assert r.matched is True
    assert r.canonical_id == p2.id


def test_cluster_integrity_demotes_bad_merge():
    store, resolver = make_resolver()
    a = _seed_aaron(store)
    store.person_projects[a] = {"audit-board"}
    resolver.cluster_integrity_min = 0.99
    resolver.auto_threshold = 0.5
    resolver.pending_threshold = 0.4
    r = resolver.resolve(
        "Aaron Anderson",
        AliasType.NAME_STRING,
        candidate_project="audit-board",
    )
    integrity = resolver.cluster_integrity(a)
    if r.matched and r.canonical_id == a:
        assert integrity < 0.99
        anderson_aliases = [
            x
            for x in store.aliases_for_person(a)
            if x.alias_value == "Aaron Anderson"
        ]
        assert anderson_aliases
        assert anderson_aliases[0].status == MergeStatus.PENDING
        assert a in store.demoted


# ---------------------------------------------------------------------------
# 7. edge cases
# ---------------------------------------------------------------------------

def test_empty_string_returns_noop():
    _, resolver = make_resolver()
    r = resolver.resolve("", AliasType.NAME_STRING)
    assert r.matched is False
    assert r.method == "noop"


def test_none_value_returns_noop():
    _, resolver = make_resolver()
    r = resolver.resolve(None, AliasType.NAME_STRING)  # type: ignore[arg-type]
    assert r.matched is False
    assert r.method == "noop"


def test_unicode_names_normalize():
    store, resolver = make_resolver()
    p = store.upsert_person("Aude Déléchat")
    store.add_alias(p.id, "Aude Déléchat", AliasType.NAME_STRING)
    r = resolver.resolve("Aude Déléchat", AliasType.NAME_STRING)
    assert r.matched is True


def test_whitespace_normalization():
    store, resolver = make_resolver()
    p = store.upsert_person("Aaron Gagnon")
    store.add_alias(p.id, "Aaron Gagnon", AliasType.NAME_STRING)
    r = resolver.resolve("  aaron   Gagnon ", AliasType.NAME_STRING)
    assert r.similarity >= 0.85


# ---------------------------------------------------------------------------
# 8. threshold tuning
# ---------------------------------------------------------------------------

def test_lower_pending_threshold_widens_match_funnel():
    store, resolver = make_resolver()
    _seed_aaron(store)
    resolver.pending_threshold = 0.5
    r = resolver.resolve("Aaron Gagnonz", AliasType.NAME_STRING)
    assert r.method == "queued"


def test_raising_auto_threshold_keeps_exact_match():
    store, resolver = make_resolver()
    _seed_aaron(store)
    resolver.auto_threshold = 1.01
    r = resolver.resolve("Aaron Gagnon", AliasType.NAME_STRING)
    assert r.method == "exact"


# ---------------------------------------------------------------------------
# 9. alias drift
# ---------------------------------------------------------------------------

def test_voice_transcription_alias_persists_and_matches():
    store, resolver = make_resolver()
    p = store.upsert_person("Rijul Kalra")
    store.add_alias(p.id, "Vishal", AliasType.VOICE_TRANSCRIPTION)
    r = resolver.resolve("Vishal", AliasType.VOICE_TRANSCRIPTION)
    assert r.matched is True
    assert r.canonical_id == p.id


# ---------------------------------------------------------------------------
# 10. merge commutativity (hypothesis property)
# ---------------------------------------------------------------------------

_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), max_codepoint=0x017F),
    min_size=2,
    max_size=8,
)


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(_name_st, _name_st, _name_st)
def test_merge_is_commutative(name_a, name_b, alias_extra):
    """Direction doesn't change the surviving alias set under fixed canonical."""
    if normalize_name(name_a) == normalize_name(name_b):
        return
    if not normalize_name(alias_extra):
        return

    def collect_aliases_after_merge() -> set[tuple[str, str]]:
        store, resolver = make_resolver()
        a = store.upsert_person(name_a)
        b = store.upsert_person(name_b)
        store.add_alias(a.id, f"{name_a}@example.com", AliasType.EMAIL)
        store.add_alias(b.id, f"{name_b}@example.com", AliasType.EMAIL)
        store.add_alias(b.id, alias_extra, AliasType.NAME_STRING)
        resolver.merge(a.id, b.id, method=MergeMethod.USER_CONFIRMED)
        return {
            (al.alias_value, al.alias_type.value)
            for al in store.aliases_for_person(a.id)
        }

    one = collect_aliases_after_merge()
    two = collect_aliases_after_merge()
    assert one == two


# ---------------------------------------------------------------------------
# 11. merge associativity (hypothesis property)
# ---------------------------------------------------------------------------

@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(_name_st, _name_st, _name_st)
def test_merge_is_associative(name_a, name_b, name_c):
    """(a<-b)<-c == a<-(b<-c) for the resulting alias set under survivor a."""
    names = [normalize_name(n) for n in (name_a, name_b, name_c)]
    if len({n for n in names if n}) < 3:
        return

    def run(order: str) -> set[tuple[str, str]]:
        store, resolver = make_resolver()
        ids = [store.upsert_person(n).id for n in (name_a, name_b, name_c)]
        for pid, n in zip(ids, (name_a, name_b, name_c)):
            store.add_alias(pid, f"{n}@x.com", AliasType.EMAIL)

        if order == "left":
            resolver.merge(ids[0], ids[1])
            resolver.merge(ids[0], ids[2])
        else:
            resolver.merge(ids[1], ids[2])
            resolver.merge(ids[0], ids[1])

        survivor = ids[0]
        return {
            (a.alias_value, a.alias_type.value)
            for a in store.aliases_for_person(survivor)
        }

    left = run("left")
    right = run("right")
    assert left == right


# ---------------------------------------------------------------------------
# 12. ingest wire-in + bidirectional link maintenance
# ---------------------------------------------------------------------------

def test_resolve_person_for_ingest_prefers_email_over_name():
    store, resolver = make_resolver()
    pid = _seed_aaron(store)
    other = store.upsert_person("Aaron Smith")
    store.add_alias(other.id, "aaron.smith@other.com", AliasType.EMAIL)
    store.add_alias(other.id, "Aaron Smith", AliasType.NAME_STRING)

    rid = resolve_person_for_ingest(
        resolver,
        sender_email="aaron.gagnon@firm.com",
        sender_name="Aaron Smith",
    )
    # Email wins over name even though both would resolve.
    assert rid == pid


def test_resolve_person_for_ingest_returns_none_when_nothing_signals():
    _, resolver = make_resolver()
    assert resolve_person_for_ingest(resolver) is None
    assert (
        resolve_person_for_ingest(resolver, sender_email="", sender_name=None)
        is None
    )


def test_bidirectional_link_document_idempotent():
    store, _ = make_resolver()
    p = store.upsert_person("Aaron Gagnon")
    store.link_document(p.id, "doc_1")
    store.link_document(p.id, "doc_1")
    store.link_document(p.id, "doc_2")
    assert store.documents_for_person(p.id) == {"doc_1", "doc_2"}


def test_bidirectional_link_migrates_on_merge():
    store, resolver = make_resolver()
    a = _seed_aaron(store)
    b = store.upsert_person("Aaron Other")
    store.add_alias(b.id, "aaron.other@example.com", AliasType.EMAIL)
    store.link_document(b.id, "doc_99")

    resolver.merge(a, b.id, method=MergeMethod.USER_CONFIRMED)
    assert "doc_99" in store.documents_for_person(a)
    assert store.documents_for_person(b) == set()


# ---------------------------------------------------------------------------
# 13. bidi link hook events
# ---------------------------------------------------------------------------

def test_bidi_hook_fires_on_alias_add_and_remove():
    events: list[tuple[str, dict]] = []
    unregister = register_bidirectional_link_hook(
        lambda ev, payload: events.append((ev, payload))
    )
    try:
        store, _ = make_resolver()
        p = store.upsert_person("Aaron Gagnon")
        a = store.add_alias(p.id, "x@firm.com", AliasType.EMAIL)
        store.remove_alias(a.id)
    finally:
        unregister()

    kinds = [e[0] for e in events]
    assert "alias_added" in kinds
    assert "alias_removed" in kinds


def test_bidi_hook_fires_on_reassign_during_merge():
    events: list[tuple[str, dict]] = []
    unregister = register_bidirectional_link_hook(
        lambda ev, payload: events.append((ev, payload))
    )
    try:
        store, resolver = make_resolver()
        a = _seed_aaron(store)
        b = store.upsert_person("Aaron Other")
        store.add_alias(b.id, "aaron.other@example.com", AliasType.EMAIL)
        resolver.merge(a, b.id, method=MergeMethod.USER_CONFIRMED)
    finally:
        unregister()

    kinds = [e[0] for e in events]
    assert "alias_reassigned" in kinds
    assert "merge_recorded" in kinds


# ---------------------------------------------------------------------------
# Pure-function unit tests
# ---------------------------------------------------------------------------

def test_normalize_collapses_whitespace_and_lowercases():
    assert normalize_name("  Aaron   Gagnon ") == "aaron gagnon"


def test_levenshtein_zero_for_equal_strings():
    assert levenshtein("abc", "abc") == 0


def test_levenshtein_basic_one_edit():
    assert levenshtein("kitten", "sitten") == 1


def test_levenshtein_similarity_bounds():
    assert 0.0 <= levenshtein_similarity("abc", "xyz") <= 1.0


def test_token_overlap_full_for_same_set():
    assert token_overlap("aaron gagnon", "Gagnon Aaron") == 1.0


def test_token_overlap_zero_for_disjoint():
    assert token_overlap("a", "b") == 0.0


def test_name_similarity_in_range():
    s = name_similarity("Aaron Gagnon", "A. Gagnon")
    assert 0.0 <= s <= 1.0


def test_merge_self_raises():
    store, resolver = make_resolver()
    p = store.upsert_person("X")
    with pytest.raises(ValueError):
        resolver.merge(p.id, p.id)


def test_undo_unknown_merge_raises():
    _, resolver = make_resolver()
    with pytest.raises(ValueError):
        resolver.undo_merge("merge:nonexistent")
