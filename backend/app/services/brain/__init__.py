"""Brain v3 services — identity resolution, knowledge graph, retrieval.

Phase 7 lands the entity resolver (Brain B3) — alias→canonical person
resolution with reversible merges, secondary-signal gating, and
bidirectional alias maintenance hooked into the Phase 5 ingest pipeline.

Production wiring later swaps `InMemoryStore` for a SQLAlchemy-backed
store against `platform.db`; the public surface is identical.
"""

from app.services.brain.entity_resolver import (
    Alias,
    AliasType,
    EntityResolver,
    InMemoryStore,
    MergeMethod,
    MergeRecord,
    MergeStatus,
    Person,
    ResolveResult,
    levenshtein,
    levenshtein_similarity,
    make_resolver,
    name_similarity,
    normalize_name,
    register_bidirectional_link_hook,
    resolve_person_for_ingest,
    token_overlap,
)

__all__ = [
    "Alias",
    "AliasType",
    "EntityResolver",
    "InMemoryStore",
    "MergeMethod",
    "MergeRecord",
    "MergeStatus",
    "Person",
    "ResolveResult",
    "levenshtein",
    "levenshtein_similarity",
    "make_resolver",
    "name_similarity",
    "normalize_name",
    "register_bidirectional_link_hook",
    "resolve_person_for_ingest",
    "token_overlap",
]
