"""graph_ops.py — Brain v3 graph repair tooling (Phase 11 / Brain B4).

Operator tooling for the brain knowledge graph: detect drift, repair broken
bidirectional links, dedupe straggler entities, undo wrong merges. Pure
Python + stdlib so it stays unit-testable without DB wiring — the routers
layer (`backend/app/routers/brain_ops.py`) is the surface that wires this to
SQLAlchemy / `platform.db`.

Sources of drift this module catches:

  - Aliases with no canonical person (orphans) — usually a partial undo or
    a failed cascade delete left the alias row behind.
  - Edges where the reverse direction is missing (broken bidirectional).
    The brain stores materialized back-edges per RISK R33 — if one half
    landed but the other did not (crash mid-write), retrieval can lie.
  - Near-duplicate canonical entities (stragglers): two `brain_people`
    rows that should have collapsed but never reached the auto-merge
    threshold (or were rejected and later drifted closer).
  - Recorded merges that turn out to be wrong (R17/R18). Operator hits
    "undo" — we replay the merge_log row, restore the prior canonical
    identity, and mark the merge `undone_at`.

This module reads `entity_resolver.InMemoryStore` for graph state (so it
works against either the production SQL-backed store or the in-memory
store used by tests). All write operations are routed through resolver/
store methods so existing bidirectional-link hooks fire correctly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

from .entity_resolver import (
    Alias,
    AliasType,
    EntityResolver,
    InMemoryStore,
    MergeMethod,
    MergeRecord,
    Person,
    name_similarity,
)


# ---------------------------------------------------------------------------
# Detection result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OrphanedAlias:
    """An alias row whose `canonical_id` no longer points at a Person."""

    alias_id: str
    alias_value: str
    alias_type: str
    missing_canonical_id: str


@dataclass(frozen=True)
class BrokenBidiLink:
    """An edge where the reverse direction is missing.

    For the brain we treat the `(canonical_id, alias_id)` pair from the
    person_documents inverted index as the canonical bidirectional view:
    if a person has a document attached, the document should resolve back
    to that person (via at least one alias). We surface both halves of the
    break so the operator sees what to repair.
    """

    subject_id: str
    subject_type: str        # 'person' | 'document'
    object_id: str
    object_type: str         # 'document' | 'person'
    predicate: str           # 'mentions' / 'authored_by' / inverse name


@dataclass(frozen=True)
class StrayDuplicate:
    """A pair of canonical Persons that look like the same identity."""

    person_a_id: str
    person_b_id: str
    similarity: float
    reason: str              # 'name' | 'shared_domain' | 'name+shared_domain'


@dataclass(frozen=True)
class RepairOutcome:
    """Summary of a repair pass."""

    fixed_count: int
    skipped_count: int
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UndoOutcome:
    """Summary of an undo_merge call."""

    merge_id: str
    canonical_id: str
    aliases_dropped: int
    success: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def detect_orphaned_aliases(store: InMemoryStore) -> list[OrphanedAlias]:
    """Return aliases whose canonical_id is missing from `store.people`.

    O(n) over the alias table.
    """
    out: list[OrphanedAlias] = []
    for alias in store.aliases.values():
        if alias.canonical_id not in store.people:
            out.append(
                OrphanedAlias(
                    alias_id=alias.id,
                    alias_value=alias.alias_value,
                    alias_type=alias.alias_type.value,
                    missing_canonical_id=alias.canonical_id,
                )
            )
    return out


def detect_broken_bidirectional(store: InMemoryStore) -> list[BrokenBidiLink]:
    """Return links where the reverse half is missing.

    The brain materializes back-edges (RISK R33). The canonical
    bidirectional invariant we check here is:

      For every (person_id, document_id) in `store.person_documents`:
        the person must still exist AND have at least one alias.

      For every entry the resolver "knows" about (canonical_id in
      store.people), the inverted index must include any documents the
      caller has registered — i.e., we surface canonicals that have
      aliases but the inverted index lost them (or vice versa).

    The function works on the in-memory store; in production the same
    invariant is implemented against `brain_edges` joined with
    `brain_documents` + `brain_people` by the SQL wrapper in
    `brain_ops` router.
    """
    out: list[BrokenBidiLink] = []
    # 1) person -> document where person is gone (subject missing)
    for pid, docs in store.person_documents.items():
        if pid not in store.people:
            for did in docs:
                out.append(
                    BrokenBidiLink(
                        subject_id=pid,
                        subject_type="person",
                        object_id=did,
                        object_type="document",
                        predicate="authored_by",
                    )
                )
            continue
        # 2) person with documents but no aliases (forward edge exists,
        #    reverse alias lookup will silently miss).
        if not any(a.canonical_id == pid for a in store.aliases.values()):
            for did in docs:
                out.append(
                    BrokenBidiLink(
                        subject_id=did,
                        subject_type="document",
                        object_id=pid,
                        object_type="person",
                        predicate="mentions",
                    )
                )
    return out


def detect_stray_duplicates(
    store: InMemoryStore,
    threshold: float = 0.90,
) -> list[StrayDuplicate]:
    """Return pairs of `brain_people` that look like near-duplicates.

    Surfaces candidates for human review — does NOT auto-merge. Two
    signals contribute:

      - Composite `name_similarity` ≥ threshold
      - Shared email domain on `primary_email`

    Either signal alone above threshold counts as a candidate.
    """
    out: list[StrayDuplicate] = []
    people = list(store.people.values())
    for i in range(len(people)):
        for j in range(i + 1, len(people)):
            a, b = people[i], people[j]
            sim = name_similarity(a.canonical_name, b.canonical_name)

            shared_domain = False
            if a.primary_email and b.primary_email:
                da = a.primary_email.split("@", 1)[-1].lower()
                db = b.primary_email.split("@", 1)[-1].lower()
                shared_domain = bool(da) and (da == db)

            if sim >= threshold and shared_domain:
                reason = "name+shared_domain"
            elif sim >= threshold:
                reason = "name"
            elif shared_domain and sim >= 0.70:
                # weaker pair: domain match + somewhat-similar names
                reason = "shared_domain"
            else:
                continue
            out.append(
                StrayDuplicate(
                    person_a_id=a.id,
                    person_b_id=b.id,
                    similarity=sim,
                    reason=reason,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------


def repair_bidirectional(store: InMemoryStore) -> RepairOutcome:
    """Patch broken bidirectional links.

    Strategy:

      - For broken (person, document) edges where the person no longer
        exists in `store.people`: drop the inverted-index entry. The
        document/edge tables on the SQL side are repaired by the
        accompanying router (see brain_ops.repair_bidirectional). The
        in-memory repair only cleans up the canonical state the resolver
        owns.
      - For canonical persons that have documents in the inverted index
        but no aliases at all, we synthesize a `name_string` alias from
        `canonical_name` so the reverse lookup resolves. This is a
        legitimate self-heal: every canonical person must, by invariant,
        have at least one alias (their canonical_name).

    Returns a `RepairOutcome` summarizing what changed.
    """
    fixed = 0
    skipped = 0
    notes: list[str] = []

    broken = detect_broken_bidirectional(store)
    for link in broken:
        if link.subject_type == "person" and link.subject_id not in store.people:
            # canonical gone — drop inverted-index entry
            docs = store.person_documents.pop(link.subject_id, None)
            if docs:
                fixed += 1
                notes.append(
                    f"dropped orphaned inverted-index entry for {link.subject_id}"
                    f" ({len(docs)} docs)"
                )
            else:
                skipped += 1
            continue

        if link.object_type == "person" and link.object_id in store.people:
            person = store.people[link.object_id]
            if not any(
                a.canonical_id == person.id for a in store.aliases.values()
            ):
                # synthesize the canonical-name alias
                store.add_alias(
                    canonical_id=person.id,
                    alias_value=person.canonical_name,
                    alias_type=AliasType.NAME_STRING,
                    confidence=1.0,
                    source="graph_ops.repair_bidirectional",
                )
                fixed += 1
                notes.append(
                    f"synthesized name_string alias for {person.id}"
                )
                continue
        skipped += 1

    return RepairOutcome(fixed_count=fixed, skipped_count=skipped, notes=notes)


def repair_orphaned_aliases(
    store: InMemoryStore,
    *,
    drop: bool = False,
) -> RepairOutcome:
    """Optionally drop orphaned aliases (default: dry-run).

    Operators usually want to inspect the list first
    (`detect_orphaned_aliases`) before passing `drop=True`. The router
    surfaces the dry-run flag in the admin endpoint.
    """
    orphans = detect_orphaned_aliases(store)
    if not drop:
        return RepairOutcome(
            fixed_count=0,
            skipped_count=len(orphans),
            notes=[f"dry-run: {len(orphans)} orphaned aliases detected"],
        )
    fixed = 0
    for o in orphans:
        # remove_alias is hook-safe; emits "alias_removed"
        store.remove_alias(o.alias_id)
        fixed += 1
    return RepairOutcome(
        fixed_count=fixed,
        skipped_count=0,
        notes=[f"removed {fixed} orphaned aliases"],
    )


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------


def undo_merge(
    resolver: EntityResolver,
    merge_id: str,
    *,
    restored_person_name: Optional[str] = None,
    restored_person_email: Optional[str] = None,
) -> UndoOutcome:
    """Reverse a recorded entity merge.

    Strategy:

      1. Find the merge record in `store.merges`. If absent or already
         undone -> failure.
      2. Drop every alias the merge moved (recorded as comma-joined
         alias ids in `merged_alias_id`).
      3. If the merge had collapsed a second canonical person into the
         first, optionally recreate the second canonical person with
         the supplied `restored_person_name` (defaults to the alias_value
         of the first dropped alias as a best-effort fallback).
      4. Mark the merge `undone_at`.
      5. Flag the original canonical for re-resolve so the resolver
         re-evaluates remaining aliases on next pass.

    NB: This routine intentionally does NOT recompute cluster integrity
    — the operator already declared the merge wrong. Re-resolve will
    happen on the next ingest pass.
    """
    rec = resolver.store.find_merge(merge_id)
    if rec is None:
        return UndoOutcome(
            merge_id=merge_id,
            canonical_id="",
            aliases_dropped=0,
            success=False,
            error="unknown merge_id",
        )
    if rec.undone_at is not None:
        return UndoOutcome(
            merge_id=merge_id,
            canonical_id=rec.canonical_id,
            aliases_dropped=0,
            success=False,
            error="merge already undone",
        )

    # Snapshot dropped alias values BEFORE removal so we can synthesize
    # a restored person if the caller asks for one.
    alias_ids = [aid.strip() for aid in rec.merged_alias_id.split(",")]
    alias_ids = [a for a in alias_ids if a and not a.startswith("<no-aliases")]
    snapshots: list[Alias] = []
    for aid in alias_ids:
        a = resolver.store.get_alias(aid)
        if a is not None:
            snapshots.append(a)

    # Call the resolver's existing undo_merge — this removes the aliases,
    # marks the merge undone, and triggers re_resolve_pending.
    try:
        resolver.undo_merge(merge_id)
    except ValueError as exc:  # pragma: no cover - resolver guards us
        return UndoOutcome(
            merge_id=merge_id,
            canonical_id=rec.canonical_id,
            aliases_dropped=0,
            success=False,
            error=str(exc),
        )

    # Optionally restore the second canonical so the operator can see
    # both people side-by-side again in the UI.
    if restored_person_name or snapshots:
        name = restored_person_name or _best_name(snapshots) or "restored:unknown"
        email = restored_person_email
        restored = resolver.store.upsert_person(
            canonical_name=name,
            primary_email=email,
        )
        # Re-attach the dropped aliases under the restored canonical.
        for snap in snapshots:
            try:
                resolver.store.add_alias(
                    canonical_id=restored.id,
                    alias_value=snap.alias_value,
                    alias_type=snap.alias_type,
                    confidence=snap.confidence,
                    status=snap.status,
                    source="graph_ops.undo_merge",
                )
            except ValueError:
                # alias already re-added under another canonical — skip
                continue

    return UndoOutcome(
        merge_id=merge_id,
        canonical_id=rec.canonical_id,
        aliases_dropped=len(snapshots),
        success=True,
    )


def _best_name(snapshots: list[Alias]) -> Optional[str]:
    """Pick a sensible canonical_name from a list of dropped aliases."""
    # Prefer name_string aliases; fall back to first non-email value.
    for s in snapshots:
        if s.alias_type == AliasType.NAME_STRING:
            return s.alias_value
    for s in snapshots:
        if s.alias_type not in (AliasType.EMAIL, AliasType.SLACK):
            return s.alias_value
    if snapshots:
        return snapshots[0].alias_value
    return None


# ---------------------------------------------------------------------------
# Dedupe stragglers
# ---------------------------------------------------------------------------


def dedupe_strays(
    store: InMemoryStore,
    threshold: float = 0.90,
) -> list[StrayDuplicate]:
    """Surface near-duplicate entity candidates for human review.

    Convenience wrapper over `detect_stray_duplicates` — kept as a
    separate symbol so router code can read intent-revealing names.
    Returns the same list of `StrayDuplicate` candidates.
    """
    return detect_stray_duplicates(store, threshold=threshold)


# ---------------------------------------------------------------------------
# Merge-log persistence helpers (used by the SQL wrapper in brain_ops router)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MergeLogRow:
    """Row shape for the `brain_merge_log` table.

    The router persists one row per merge so the operator UI can show
    history and allow undo within the `reversible_until` window. The
    entity_resolver hook (`record_merge_to_log`) writes a row whenever
    `InMemoryStore.record_merge` runs.
    """

    id: str
    merged_from: str          # canonical id of the person that disappeared
    merged_into: str          # canonical id that survived
    performed_at: str
    performed_by: Optional[str] = None
    reversible_until: Optional[str] = None
    undone_at: Optional[str] = None


# In-process buffer of merge-log rows. Production code mirrors these
# into the `brain_merge_log` SQL table via the router; tests inspect
# this buffer directly.
_MERGE_LOG: list[MergeLogRow] = []


def merge_log_rows() -> list[MergeLogRow]:
    """Return a copy of the in-process merge log (for tests / inspection)."""
    return list(_MERGE_LOG)


def clear_merge_log() -> None:
    """Reset the in-process merge log (test helper)."""
    _MERGE_LOG.clear()


def record_merge_to_log(event: str, payload: dict) -> None:
    """Bidirectional-link hook that mirrors resolver merges into the log.

    Wired up by `entity_resolver` so every `merge_recorded` event lands
    in `_MERGE_LOG`. The SQL-backed router uses the same payload shape
    to write a row to `brain_merge_log`.
    """
    if event != "merge_recorded":
        return
    row = MergeLogRow(
        id=payload["merge_id"],
        merged_from=payload.get("merged_alias_id", ""),
        merged_into=payload["canonical_id"],
        performed_at=datetime.now(timezone.utc).isoformat(),
        performed_by=payload.get("performed_by"),
        reversible_until=payload.get("reversible_until"),
    )
    _MERGE_LOG.append(row)


__all__ = [
    "OrphanedAlias",
    "BrokenBidiLink",
    "StrayDuplicate",
    "RepairOutcome",
    "UndoOutcome",
    "MergeLogRow",
    "detect_orphaned_aliases",
    "detect_broken_bidirectional",
    "detect_stray_duplicates",
    "repair_bidirectional",
    "repair_orphaned_aliases",
    "undo_merge",
    "dedupe_strays",
    "merge_log_rows",
    "clear_merge_log",
    "record_merge_to_log",
]
