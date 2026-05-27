"""entity_resolver.py — Brain v3 identity resolution (Phase 7 / Brain B3).

Resolves alias strings (emails, slack handles, name variants, voice
transcription tokens) to a canonical Person ID. Implements the D07 decision:

- Tier 1: exact match on `(alias_value, alias_type)`
- Tier 2: fuzzy name match (Levenshtein-normalized + token overlap)
- Confidence gates:
    >= 0.95 + secondary signal (email domain or project overlap) -> auto-merge
    0.85 <= sim < 0.95                                            -> decision_queue
    < 0.85                                                        -> no-op

Reversibility: merges are `person:aliased_as:person` edges, never deletes.
Undo = delete edge + mark cluster `re_resolve_pending`.

Ported from `.planning/v3/brain/REFERENCE-IMPL/entity_resolver.py` with two
additions for Phase 7 wire-in:

  - `register_bidirectional_link_hook(fn)` — register a callback that fires
    whenever an alias is added/reassigned so external indexes (e.g. the
    `brain_documents` table, the inverted "person → docs" map) can be kept
    in sync.
  - `resolve_person_for_ingest(...)` — convenience wrapper invoked by the
    Phase 5 ingest router to resolve sender → canonical person before
    persisting a document.

Module is pure-Python + stdlib so it stays unit-testable without DB wiring.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Iterable, Optional


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class AliasType(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    NAME_STRING = "name_string"
    VOICE_TRANSCRIPTION = "voice_transcription"
    JIRA_HANDLE = "jira_handle"


class MergeMethod(str, Enum):
    AUTO = "auto"
    USER_CONFIRMED = "user_confirmed"
    RULE = "rule"


class MergeStatus(str, Enum):
    AUTO = "auto"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass(frozen=True)
class Person:
    id: str
    canonical_name: str
    primary_email: Optional[str] = None


@dataclass(frozen=True)
class Alias:
    id: str
    canonical_id: str
    alias_value: str
    alias_type: AliasType
    confidence: float = 1.0
    status: MergeStatus = MergeStatus.AUTO
    source: Optional[str] = None


@dataclass(frozen=True)
class MergeRecord:
    id: str
    canonical_id: str
    merged_alias_id: str
    method: MergeMethod
    similarity: Optional[float]
    secondary_signal: Optional[str]
    merged_at: str
    undone_at: Optional[str] = None


@dataclass
class ResolveResult:
    matched: bool
    canonical_id: Optional[str]
    similarity: float
    method: str                 # 'exact' | 'fuzzy' | 'queued' | 'noop'
    candidate_aliases: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Bidirectional-link hooks (used by ingest pipeline)
# ---------------------------------------------------------------------------

# Hook signature: fn(event: str, payload: dict) -> None
# Events emitted:
#   "alias_added"      payload = {canonical_id, alias_id, alias_value, alias_type, source}
#   "alias_reassigned" payload = {alias_id, old_canonical_id, new_canonical_id}
#   "alias_removed"    payload = {alias_id, canonical_id, alias_value, alias_type}
#   "merge_recorded"   payload = {merge_id, canonical_id, merged_alias_id, method}
#   "merge_undone"     payload = {merge_id, canonical_id}

_BIDI_HOOKS: list[Callable[[str, dict], None]] = []


def register_bidirectional_link_hook(
    fn: Callable[[str, dict], None],
) -> Callable[[], None]:
    """Register a bidirectional-link maintenance callback.

    Returns an `unregister` function so tests / callers can clean up.
    """
    _BIDI_HOOKS.append(fn)

    def _unregister() -> None:
        try:
            _BIDI_HOOKS.remove(fn)
        except ValueError:  # pragma: no cover
            pass

    return _unregister


def _emit_link(event: str, payload: dict) -> None:
    for hook in list(_BIDI_HOOKS):
        try:
            hook(event, payload)
        except Exception:  # pragma: no cover - hook errors must not break resolver
            pass


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_name(s: str) -> str:
    """Normalize a name string for comparison.

    - NFKC normalize unicode (handles accented + width variants).
    - Lowercase.
    - Strip leading/trailing whitespace.
    - Collapse internal whitespace.
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def levenshtein(a: str, b: str) -> int:
    """Plain DP Levenshtein. O(len(a) * len(b)) time."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def levenshtein_similarity(a: str, b: str) -> float:
    """Normalized 1.0-best Levenshtein similarity."""
    a, b = normalize_name(a), normalize_name(b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    d = levenshtein(a, b)
    return 1.0 - (d / max(len(a), len(b)))


def token_overlap(a: str, b: str) -> float:
    """Jaccard token overlap (case-insensitive, alnum tokens)."""
    ta = set(_TOKEN_RE.findall(normalize_name(a)))
    tb = set(_TOKEN_RE.findall(normalize_name(b)))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def name_similarity(a: str, b: str) -> float:
    """Composite name similarity, surname-weighted.

    Designed for the canonical test cases:

      - identical normalized strings           -> 1.0
      - "Aaron Gagnon" / "A. Gagnon"           -> >= 0.85
      - "Aaron Gagnon" / "aaron gagnon"        -> 1.0 (case-only diff)
      - "Aaron Gagnonn" / "Aaron Gagnon"       -> in [0.85, 0.95)
      - "Aaron Wu" / "Aaron Lu"                -> < 0.95
      - "Aaron Smith" / "Aaron Gagnon"         -> < 0.85
      - completely different strings           -> < 0.4

    Heuristic: when both names have >=2 tokens, the last token is the
    surname. We compute a surname Levenshtein similarity and a given-name
    overlap, and weight the surname twice as heavily as the rest.
    """
    full_lev = levenshtein_similarity(a, b)
    full_tok = token_overlap(a, b)
    base = (full_lev + full_tok) / 2.0

    ta = _TOKEN_RE.findall(normalize_name(a))
    tb = _TOKEN_RE.findall(normalize_name(b))

    if len(ta) >= 2 and len(tb) >= 2:
        surname_sim = levenshtein_similarity(ta[-1], tb[-1])
        first_a, first_b = ta[0], tb[0]
        if first_a == first_b:
            given_sim = 1.0
        elif first_a.startswith(first_b) or first_b.startswith(first_a):
            given_sim = 0.9
        else:
            given_sim = levenshtein_similarity(first_a, first_b)
        weighted = (2 * surname_sim + given_sim) / 3.0
        return weighted * 0.85 + base * 0.15
    return base


# ---------------------------------------------------------------------------
# Store interface (in-memory; production swaps for SQLAlchemy)
# ---------------------------------------------------------------------------

class InMemoryStore:
    """Pure-Python store with the same surface the SQL-backed store will
    provide. Production version maps these methods onto platform.db.
    """

    def __init__(self) -> None:
        self.people: dict[str, Person] = {}
        self.aliases: dict[str, Alias] = {}
        self.merges: dict[str, MergeRecord] = {}
        # idempotency: (alias_value, alias_type) -> alias_id
        self._alias_index: dict[tuple[str, str], str] = {}
        # email-domain index for secondary-signal lookup
        self._domain_index: dict[str, set[str]] = {}
        # project-overlap (person_id -> set[project_id])
        self.person_projects: dict[str, set[str]] = {}
        # cluster decision queue for pending merges
        self.pending_queue: list[dict] = []
        # demoted clusters (after integrity demotion)
        self.demoted: set[str] = set()
        # re-resolve flag after undo
        self.re_resolve_pending: set[str] = set()
        # Bidirectional inverted index: person_id -> set[document_id]
        # Maintained by the default bidi-link hook below.
        self.person_documents: dict[str, set[str]] = {}

    # ----- people -----

    def upsert_person(
        self,
        canonical_name: str,
        primary_email: Optional[str] = None,
        person_id: Optional[str] = None,
    ) -> Person:
        pid = person_id or f"person:{uuid.uuid4().hex[:12]}"
        p = Person(id=pid, canonical_name=canonical_name, primary_email=primary_email)
        self.people[pid] = p
        return p

    def get_person(self, pid: str) -> Optional[Person]:
        return self.people.get(pid)

    def all_people(self) -> list[Person]:
        return list(self.people.values())

    # ----- aliases -----

    @staticmethod
    def _alias_key(alias_value: str, alias_type: AliasType) -> tuple[str, str]:
        """Normalize the (value, type) into the index key used for exact match.

        Name-string and voice-transcription types collapse to normalize_name.
        Email/slack/jira handles normalize to lowercase + strip.
        """
        if alias_type in (AliasType.NAME_STRING, AliasType.VOICE_TRANSCRIPTION):
            return (normalize_name(alias_value), alias_type.value)
        return ((alias_value or "").strip().lower(), alias_type.value)

    def add_alias(
        self,
        canonical_id: str,
        alias_value: str,
        alias_type: AliasType,
        confidence: float = 1.0,
        status: MergeStatus = MergeStatus.AUTO,
        source: Optional[str] = None,
    ) -> Alias:
        if canonical_id not in self.people:
            raise ValueError(f"unknown canonical_id {canonical_id}")
        key = self._alias_key(alias_value, alias_type)
        if key in self._alias_index:
            return self.aliases[self._alias_index[key]]
        aid = f"alias:{uuid.uuid4().hex[:12]}"
        a = Alias(
            id=aid,
            canonical_id=canonical_id,
            alias_value=alias_value,
            alias_type=alias_type,
            confidence=confidence,
            status=status,
            source=source,
        )
        self.aliases[aid] = a
        self._alias_index[key] = aid
        if alias_type == AliasType.EMAIL and "@" in alias_value:
            domain = alias_value.split("@", 1)[1].lower()
            self._domain_index.setdefault(domain, set()).add(canonical_id)
        _emit_link(
            "alias_added",
            {
                "canonical_id": canonical_id,
                "alias_id": aid,
                "alias_value": alias_value,
                "alias_type": alias_type.value,
                "source": source,
            },
        )
        return a

    def get_alias(self, alias_id: str) -> Optional[Alias]:
        return self.aliases.get(alias_id)

    def find_alias_exact(
        self, alias_value: str, alias_type: AliasType
    ) -> Optional[Alias]:
        aid = self._alias_index.get(self._alias_key(alias_value, alias_type))
        return self.aliases.get(aid) if aid else None

    def aliases_for_person(self, canonical_id: str) -> list[Alias]:
        return [a for a in self.aliases.values() if a.canonical_id == canonical_id]

    def remove_alias(self, alias_id: str) -> None:
        a = self.aliases.pop(alias_id, None)
        if a is None:
            return
        self._alias_index.pop(self._alias_key(a.alias_value, a.alias_type), None)
        if a.alias_type == AliasType.EMAIL and "@" in a.alias_value:
            domain = a.alias_value.split("@", 1)[1].lower()
            if domain in self._domain_index:
                self._domain_index[domain].discard(a.canonical_id)
                if not self._domain_index[domain]:
                    self._domain_index.pop(domain, None)
        _emit_link(
            "alias_removed",
            {
                "alias_id": alias_id,
                "canonical_id": a.canonical_id,
                "alias_value": a.alias_value,
                "alias_type": a.alias_type.value,
            },
        )

    def reassign_alias(self, alias_id: str, new_canonical_id: str) -> Optional[Alias]:
        """Move an existing alias under a different canonical person."""
        a = self.aliases.get(alias_id)
        if a is None:
            return None
        if new_canonical_id not in self.people:
            raise ValueError(f"unknown canonical {new_canonical_id}")
        old_canonical = a.canonical_id
        new_a = Alias(
            id=a.id,
            canonical_id=new_canonical_id,
            alias_value=a.alias_value,
            alias_type=a.alias_type,
            confidence=a.confidence,
            status=a.status,
            source=a.source,
        )
        self.aliases[a.id] = new_a
        if a.alias_type == AliasType.EMAIL and "@" in a.alias_value:
            domain = a.alias_value.split("@", 1)[1].lower()
            if domain in self._domain_index:
                still_has = any(
                    other.canonical_id == a.canonical_id
                    and other.alias_type == AliasType.EMAIL
                    and "@" in other.alias_value
                    and other.alias_value.split("@", 1)[1].lower() == domain
                    and other.id != a.id
                    for other in self.aliases.values()
                )
                if not still_has:
                    self._domain_index[domain].discard(a.canonical_id)
                self._domain_index[domain].add(new_canonical_id)
        # Migrate bidirectional inverted index entries
        docs = self.person_documents.pop(old_canonical, None)
        if docs:
            self.person_documents.setdefault(new_canonical_id, set()).update(docs)
        _emit_link(
            "alias_reassigned",
            {
                "alias_id": a.id,
                "old_canonical_id": old_canonical,
                "new_canonical_id": new_canonical_id,
            },
        )
        return new_a

    # ----- secondary-signal helpers -----

    def people_sharing_domain(self, email: str) -> set[str]:
        if "@" not in email:
            return set()
        domain = email.split("@", 1)[1].lower()
        return set(self._domain_index.get(domain, set()))

    def projects_overlap(self, person_a: str, person_b: str) -> bool:
        a = self.person_projects.get(person_a, set())
        b = self.person_projects.get(person_b, set())
        return bool(a & b)

    # ----- bidirectional links: person <-> document -----

    def link_document(self, canonical_id: str, document_id: str) -> None:
        """Maintain inverted index: person_id -> {document_id}.

        Hooked from the ingest router after a document is persisted with a
        resolved sender. Idempotent — adding the same (person, doc) twice is
        a no-op.
        """
        self.person_documents.setdefault(canonical_id, set()).add(document_id)

    def documents_for_person(self, canonical_id: str) -> set[str]:
        return set(self.person_documents.get(canonical_id, set()))

    # ----- merges -----

    def record_merge(
        self,
        canonical_id: str,
        merged_alias_id: str,
        method: MergeMethod,
        similarity: Optional[float],
        secondary_signal: Optional[str],
    ) -> MergeRecord:
        mid = f"merge:{uuid.uuid4().hex[:12]}"
        rec = MergeRecord(
            id=mid,
            canonical_id=canonical_id,
            merged_alias_id=merged_alias_id,
            method=method,
            similarity=similarity,
            secondary_signal=secondary_signal,
            merged_at=datetime.now(timezone.utc).isoformat(),
        )
        self.merges[mid] = rec
        _emit_link(
            "merge_recorded",
            {
                "merge_id": mid,
                "canonical_id": canonical_id,
                "merged_alias_id": merged_alias_id,
                "method": method.value,
            },
        )
        return rec

    def find_merge(self, merge_id: str) -> Optional[MergeRecord]:
        return self.merges.get(merge_id)


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

DEFAULT_AUTO_THRESHOLD = 0.95
DEFAULT_PENDING_THRESHOLD = 0.85
DEFAULT_CLUSTER_INTEGRITY_MIN = 0.95


class EntityResolver:
    """Background-worker style resolver. All state held in InMemoryStore."""

    def __init__(
        self,
        store: InMemoryStore,
        auto_threshold: float = DEFAULT_AUTO_THRESHOLD,
        pending_threshold: float = DEFAULT_PENDING_THRESHOLD,
        cluster_integrity_min: float = DEFAULT_CLUSTER_INTEGRITY_MIN,
    ) -> None:
        self.store = store
        self.auto_threshold = auto_threshold
        self.pending_threshold = pending_threshold
        self.cluster_integrity_min = cluster_integrity_min

    # ----- core resolve -----

    def resolve(
        self,
        alias_value: str,
        alias_type: AliasType,
        secondary_email: Optional[str] = None,
        candidate_project: Optional[str] = None,
    ) -> ResolveResult:
        if alias_value is None or alias_value == "":
            return ResolveResult(False, None, 0.0, "noop")

        # Tier 1 — exact
        hit = self.store.find_alias_exact(alias_value, alias_type)
        if hit is not None:
            return ResolveResult(True, hit.canonical_id, 1.0, "exact")

        # Tier 2 — fuzzy.
        best_score = 0.0
        best_canonical: Optional[str] = None
        best_alias_id: Optional[str] = None
        candidates: list[tuple[float, str, str]] = []
        for a in self.store.aliases.values():
            if a.alias_type != alias_type:
                continue
            score = name_similarity(alias_value, a.alias_value)
            if score > best_score:
                best_score = score
                best_canonical = a.canonical_id
                best_alias_id = a.id
            if score >= self.pending_threshold:
                candidates.append((score, a.canonical_id, a.id))

        if best_canonical is None or best_score < self.pending_threshold:
            return ResolveResult(False, None, best_score, "noop")

        if best_score < self.auto_threshold:
            self.store.pending_queue.append(
                dict(
                    alias_value=alias_value,
                    alias_type=alias_type.value,
                    candidate_canonical=best_canonical,
                    similarity=best_score,
                )
            )
            return ResolveResult(
                False,
                best_canonical,
                best_score,
                "queued",
                candidate_aliases=[c[2] for c in candidates],
            )

        # Auto range — need secondary signal
        secondary = None
        if secondary_email:
            shared = self.store.people_sharing_domain(secondary_email)
            if best_canonical in shared:
                secondary = "email_domain"
        if (
            secondary is None
            and candidate_project is not None
            and candidate_project
            in self.store.person_projects.get(best_canonical, set())
        ):
            secondary = "project_overlap"

        if secondary is None:
            self.store.pending_queue.append(
                dict(
                    alias_value=alias_value,
                    alias_type=alias_type.value,
                    candidate_canonical=best_canonical,
                    similarity=best_score,
                    reason="auto_threshold_met_but_no_secondary_signal",
                )
            )
            return ResolveResult(
                False, best_canonical, best_score, "queued",
                candidate_aliases=[c[2] for c in candidates],
            )

        # Auto-merge: add alias under canonical, record merge
        new_alias = self.store.add_alias(
            canonical_id=best_canonical,
            alias_value=alias_value,
            alias_type=alias_type,
            confidence=best_score,
            status=MergeStatus.AUTO,
            source="resolver",
        )
        self.store.record_merge(
            canonical_id=best_canonical,
            merged_alias_id=new_alias.id,
            method=MergeMethod.AUTO,
            similarity=best_score,
            secondary_signal=secondary,
        )

        integrity = self.cluster_integrity(best_canonical)
        if integrity < self.cluster_integrity_min:
            self.store.aliases[new_alias.id] = Alias(
                id=new_alias.id,
                canonical_id=new_alias.canonical_id,
                alias_value=new_alias.alias_value,
                alias_type=new_alias.alias_type,
                confidence=new_alias.confidence,
                status=MergeStatus.PENDING,
                source=new_alias.source,
            )
            self.store.demoted.add(best_canonical)

        return ResolveResult(True, best_canonical, best_score, "fuzzy",
                             candidate_aliases=[new_alias.id])

    # ----- merge / undo -----

    def merge(
        self,
        canonical_id: str,
        other_canonical_id: str,
        method: MergeMethod = MergeMethod.USER_CONFIRMED,
        similarity: Optional[float] = None,
        secondary_signal: Optional[str] = None,
    ) -> MergeRecord:
        if canonical_id == other_canonical_id:
            raise ValueError("cannot merge a person into themselves")
        if canonical_id not in self.store.people:
            raise ValueError(f"unknown canonical {canonical_id}")
        if other_canonical_id not in self.store.people:
            raise ValueError(f"unknown other {other_canonical_id}")

        moved_alias_ids: list[str] = []
        for a in list(self.store.aliases_for_person(other_canonical_id)):
            existing = self.store.find_alias_exact(a.alias_value, a.alias_type)
            if existing is not None and existing.canonical_id == canonical_id:
                self.store.remove_alias(a.id)
                moved_alias_ids.append(existing.id)
                continue
            self.store.reassign_alias(a.id, canonical_id)
            moved_alias_ids.append(a.id)

        other_person = self.store.get_person(other_canonical_id)
        if other_person is not None:
            name_alias = self.store.find_alias_exact(
                other_person.canonical_name, AliasType.NAME_STRING
            )
            if name_alias is None:
                new_alias = self.store.add_alias(
                    canonical_id=canonical_id,
                    alias_value=other_person.canonical_name,
                    alias_type=AliasType.NAME_STRING,
                    confidence=1.0,
                    status=MergeStatus.CONFIRMED,
                    source=f"merge_from:{other_canonical_id}",
                )
                moved_alias_ids.append(new_alias.id)
            others = self.store.person_projects.pop(other_canonical_id, set())
            self.store.person_projects.setdefault(canonical_id, set()).update(others)
            # Migrate inverted-index doc memberships too
            docs = self.store.person_documents.pop(other_canonical_id, None)
            if docs:
                self.store.person_documents.setdefault(canonical_id, set()).update(
                    docs
                )

        self.store.people.pop(other_canonical_id, None)

        rec = self.store.record_merge(
            canonical_id=canonical_id,
            merged_alias_id=",".join(moved_alias_ids)
            or f"<no-aliases:{other_canonical_id}>",
            method=method,
            similarity=similarity,
            secondary_signal=secondary_signal,
        )
        return rec

    def undo_merge(self, merge_id: str) -> None:
        rec = self.store.find_merge(merge_id)
        if rec is None:
            raise ValueError(f"unknown merge {merge_id}")
        if rec.undone_at is not None:
            return
        for aid in rec.merged_alias_id.split(","):
            aid = aid.strip()
            if aid.startswith("<no-aliases"):
                continue
            self.store.remove_alias(aid)
        self.store.merges[merge_id] = MergeRecord(
            id=rec.id,
            canonical_id=rec.canonical_id,
            merged_alias_id=rec.merged_alias_id,
            method=rec.method,
            similarity=rec.similarity,
            secondary_signal=rec.secondary_signal,
            merged_at=rec.merged_at,
            undone_at=datetime.now(timezone.utc).isoformat(),
        )
        self.store.re_resolve_pending.add(rec.canonical_id)
        _emit_link(
            "merge_undone",
            {"merge_id": merge_id, "canonical_id": rec.canonical_id},
        )

    # ----- cluster integrity -----

    def cluster_integrity(self, canonical_id: str) -> float:
        names = [
            a.alias_value
            for a in self.store.aliases_for_person(canonical_id)
            if a.alias_type
            in (AliasType.NAME_STRING, AliasType.VOICE_TRANSCRIPTION)
        ]
        person = self.store.get_person(canonical_id)
        if person is not None:
            names.append(person.canonical_name)
        if len(names) < 2:
            return 1.0
        min_sim = 1.0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                s = name_similarity(names[i], names[j])
                if s < min_sim:
                    min_sim = s
        return min_sim


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_resolver() -> tuple[InMemoryStore, EntityResolver]:
    store = InMemoryStore()
    resolver = EntityResolver(store)
    return store, resolver


# ---------------------------------------------------------------------------
# Ingest convenience: called from app.services.ingest.router
# ---------------------------------------------------------------------------

def resolve_person_for_ingest(
    resolver: EntityResolver,
    *,
    sender_email: Optional[str] = None,
    sender_handle: Optional[str] = None,
    sender_name: Optional[str] = None,
    candidate_project: Optional[str] = None,
) -> Optional[str]:
    """Resolve an ingest envelope's sender to a canonical person_id.

    Tries email first (highest signal), then slack handle, then name. Returns
    the canonical_id of the best match, or None if nothing reached the
    pending threshold or all signals were empty.

    Used by the Phase 5 ingest router as a `before-persist` hook.
    """
    for value, atype in (
        (sender_email, AliasType.EMAIL),
        (sender_handle, AliasType.SLACK),
        (sender_name, AliasType.NAME_STRING),
    ):
        if not value:
            continue
        r = resolver.resolve(
            value,
            atype,
            secondary_email=sender_email if atype != AliasType.EMAIL else None,
            candidate_project=candidate_project,
        )
        if r.matched and r.canonical_id:
            return r.canonical_id
    return None


__all__ = [
    "AliasType",
    "MergeMethod",
    "MergeStatus",
    "Person",
    "Alias",
    "MergeRecord",
    "ResolveResult",
    "InMemoryStore",
    "EntityResolver",
    "normalize_name",
    "levenshtein",
    "levenshtein_similarity",
    "token_overlap",
    "name_similarity",
    "make_resolver",
    "register_bidirectional_link_hook",
    "resolve_person_for_ingest",
]
