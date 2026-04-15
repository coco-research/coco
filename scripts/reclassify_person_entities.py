#!/usr/bin/env python3
"""Reclassify misclassified 'person' entities in knowledge.db.

The entity extraction pipeline incorrectly classified ~80% of person entities.
This script identifies noise entities and reclassifies them to the correct type
or marks them as 'noise' for removal.

Usage:
    python3 scripts/reclassify_person_entities.py --dry-run    # preview changes
    python3 scripts/reclassify_person_entities.py --apply       # apply changes
"""

import sqlite3
import re
import sys
from pathlib import Path

KNOWLEDGE_DB = Path.home() / ".coco" / "knowledge" / "knowledge.db"

# Same noise words as the backend filter, kept in sync
NOISE_WORDS = {
    'system', 'platform', 'module', 'dashboard', 'report', 'compliance', 'process',
    'contract', 'tool', 'tracker', 'filing', 'database', 'control', 'data', 'template',
    'integration', 'application', 'coverage', 'settings', 'document', 'workflow',
    'notification', 'analytics', 'security', 'table', 'amount', 'package', 'phone',
    'configuration', 'archive', 'extension', 'cookie', 'mobile', 'automated',
    'filter', 'metric', 'audit', 'risk', 'entity', 'access', 'review', 'action',
    'global', 'primary', 'core', 'technical', 'hub', 'operating', 'success', 'facing',
    'save', 'view', 'confirm', 'virtual', 'statutory', 'verification', 'support',
    'new', 'year', 'thanks', 'call', 'distributed', 'denial', 'trust', 'deep',
    'live', 'client', 'french', 'canadian', 'github', 'execute', 'time', 'commitment',
    'apps', 'type', 'definition', 'scope', 'objects', 'scan', 'frequency', 'transfer',
    'rating', 'comparative', 'epics', 'courtesy', 'biz', 'sprint', 'phase',
    'reporting', 'consolidated', 'controllership', 'dialogue', 'staffing', 'functional',
    'requirements', 'snowflake', 'case', 'operator', 'charge', 'code', 'service',
    'external', 'worker', 'street', 'current', 'state', 'start', 'date', 'hi',
    'hello', 'dear', 'regards', 'sincerely', 'cheers',
    'arabia', 'lanka', 'canada', 'toronto', 'london', 'york', 'india', 'china',
    'japan', 'brazil', 'mexico', 'kong', 'singapore', 'australia', 'zealand',
    'africa', 'europe', 'america', 'kingdom', 'republic', 'islands', 'rico',
    'beijing', 'shanghai', 'mumbai', 'delhi', 'paris', 'berlin', 'madrid',
    'solutions', 'consulting', 'partners', 'holdings', 'associates', 'services',
    'technologies', 'corporation', 'group', 'institute', 'foundation', 'council',
    'optimize', 'project', 'program', 'initiative', 'framework', 'strategy',
    'overview', 'summary', 'update', 'status', 'agenda', 'minutes', 'notes',
    'northern', 'southern', 'eastern', 'western', 'central', 'amsterdam',
    'netherlands', 'macedonia',
    'how', 'tips', 'priority', 'troubleshooting', 'please', 'click', 'here',
    'welcome', 'join', 'info', 'fyi', 'asap', 'tbd', 'todo', 'done',
    'jones', 'dow',
    'original', 'appointment', 'additional', 'information', 'description',
    'standard', 'advanced', 'basic', 'general', 'specific', 'related',
}

# Patterns for reclassification targets
SYSTEM_PATTERNS = re.compile(
    r'\b(system|platform|tool|tracker|dashboard|module|database|application|'
    r'integration|notification|filter|configuration|api|server|endpoint)\b', re.I
)
LOCATION_PATTERNS = re.compile(
    r'\b(arabia|lanka|canada|toronto|london|york|india|china|japan|brazil|'
    r'mexico|kong|singapore|australia|zealand|africa|europe|america|'
    r'kingdom|republic|amsterdam|netherlands|macedonia|beijing|shanghai|'
    r'mumbai|delhi|paris|berlin|madrid|northern|southern|eastern|western)\b', re.I
)
ROLE_PATTERNS = re.compile(
    r'\b(manager|admin|lead|director|analyst|coordinator|specialist|officer|'
    r'controller|worker|operator|staffing)\b', re.I
)


def classify_noise(name: str) -> str | None:
    """Return the correct type for a misclassified person entity, or None if it's a real person."""
    words = name.split()

    # Single word or too short/long
    if len(words) < 2 or len(words) > 4:
        return 'document'
    if len(name) < 5 or len(name) > 40:
        return 'document'
    # Double spaces = parsing artifact
    if '  ' in name:
        return 'document'
    # Check if words are properly capitalized alphabetic
    for w in words:
        if not w or not w[0].isupper():
            return 'document'
        alpha = sum(1 for c in w if c.isalpha())
        if alpha < len(w) * 0.7:
            return 'document'
    # Noise words check
    # Valid types: person, team, role, system, module, org_unit, document, product
    lower_words = {w.lower() for w in words}
    if lower_words & NOISE_WORDS:
        # Try to classify more specifically
        if SYSTEM_PATTERNS.search(name):
            return 'system'
        if LOCATION_PATTERNS.search(name):
            return 'org_unit'  # locations → org_unit (closest valid type)
        if ROLE_PATTERNS.search(name):
            return 'role'
        return 'document'  # catch-all for text fragments

    return None  # Looks like a real person


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('--dry-run', '--apply'):
        print(__doc__)
        sys.exit(1)

    dry_run = sys.argv[1] == '--dry-run'

    if not KNOWLEDGE_DB.exists():
        print(f"ERROR: {KNOWLEDGE_DB} not found")
        sys.exit(1)

    conn = sqlite3.connect(str(KNOWLEDGE_DB))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT gid, canonical_name FROM global_entities WHERE type = 'person'"
    ).fetchall()

    total = len(rows)
    reclassifications: dict[str, list[tuple[str, str]]] = {}
    real_count = 0

    for r in rows:
        gid, name = r['gid'], r['canonical_name']
        new_type = classify_noise(name)
        if new_type is None:
            real_count += 1
        else:
            reclassifications.setdefault(new_type, []).append((gid, name))

    # Report
    print(f"{'DRY RUN' if dry_run else 'APPLYING'}: Person Entity Reclassification")
    print(f"{'=' * 60}")
    print(f"Total person entities:  {total:>6,}")
    print(f"Real people (keeping):  {real_count:>6,}")
    print(f"Reclassifying:          {total - real_count:>6,}")
    print()

    for new_type in sorted(reclassifications.keys()):
        items = reclassifications[new_type]
        print(f"  -> {new_type:10}  {len(items):>5,} entities")
        for _, name in items[:5]:
            print(f"       e.g. {name}")
        if len(items) > 5:
            print(f"       ... and {len(items) - 5} more")
    print()

    if dry_run:
        print("Run with --apply to execute these changes.")
        conn.close()
        return

    # Apply changes
    for new_type, items in reclassifications.items():
        gids = [gid for gid, _ in items]
        # Batch update in chunks of 500
        for i in range(0, len(gids), 500):
            chunk = gids[i:i + 500]
            placeholders = ','.join('?' for _ in chunk)
            conn.execute(
                f"UPDATE global_entities SET type = ? WHERE gid IN ({placeholders})",
                [new_type] + chunk,
            )
    conn.commit()
    conn.close()

    print(f"Done. {total - real_count:,} entities reclassified.")
    print(f"Real people remaining: {real_count:,}")


if __name__ == '__main__':
    main()
