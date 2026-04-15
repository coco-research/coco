#!/usr/bin/env python3
"""Stage 2 person reclassification: email-verified + heuristic + Claude API.

Stage 1 (already done): Noise-word filter removed 4,432 obvious non-persons.
Stage 2 (this script):
  A. Extract ground truth from 9,298 email From/To/CC fields
  B. Cross-reference: keep email-matched entities as definitively person
  C. Keep first-name-matched entities as likely person
  D. For no-match entities: apply heuristic, reclassify obvious noise
  E. For ambiguous no-match entities: batch classify via Claude API

Usage:
    python3 scripts/reclassify_stage2.py --dry-run
    python3 scripts/reclassify_stage2.py --apply
"""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

KNOWLEDGE_DB = Path.home() / ".coco" / "knowledge" / "knowledge.db"
EMAIL_DIR = Path.home() / ".coco" / "knowledge" / "emails"

# -------------------------------------------------------------------
# Stage A: Extract email names
# -------------------------------------------------------------------

def extract_email_names() -> tuple[set[str], set[str]]:
    """Returns (full_names, first_names) from email headers."""
    full_names = set()
    first_names = set()

    def email_to_name(addr):
        local = addr.split('@')[0]
        parts = re.split(r'[._]', local)
        parts = [p.capitalize() for p in parts if len(p) > 1 and p.isalpha()]
        return ' '.join(parts) if len(parts) >= 2 else None

    for f in EMAIL_DIR.glob('**/*.json'):
        try:
            data = json.load(open(f))
        except Exception:
            continue
        # from_name field
        fn = data.get('from_name', '')
        if fn and len(fn) > 3:
            clean = re.sub(r'\s*\(.*\)\s*$', '', fn).strip()
            if clean and ' ' in clean:
                full_names.add(clean)
                first_names.add(clean.split()[0].lower())
        # All addresses
        for addr in [data.get('from_address', '')] + data.get('to', []) + data.get('cc', []):
            if not addr:
                continue
            n = email_to_name(addr)
            if n:
                full_names.add(n)
                first_names.add(n.split()[0].lower())

    return full_names, first_names

# -------------------------------------------------------------------
# Stage D: Heuristic for obvious noise
# -------------------------------------------------------------------

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
    'live', 'client', 'github', 'execute', 'commitment', 'apps', 'type', 'definition',
    'scope', 'objects', 'scan', 'frequency', 'transfer', 'rating', 'comparative',
    'epics', 'courtesy', 'biz', 'sprint', 'phase', 'reporting', 'consolidated',
    'controllership', 'dialogue', 'staffing', 'functional', 'requirements', 'snowflake',
    'case', 'operator', 'charge', 'code', 'service', 'external', 'worker', 'street',
    'current', 'state', 'start', 'date', 'hi', 'hello', 'dear', 'regards', 'cheers',
    'arabia', 'lanka', 'canada', 'toronto', 'london', 'india', 'china', 'japan',
    'brazil', 'mexico', 'kong', 'singapore', 'australia', 'zealand', 'africa',
    'europe', 'america', 'kingdom', 'republic', 'islands', 'amsterdam', 'netherlands',
    'macedonia', 'northern', 'southern', 'eastern', 'western', 'central',
    'solutions', 'consulting', 'partners', 'holdings', 'associates', 'services',
    'technologies', 'corporation', 'institute', 'foundation', 'council',
    'optimize', 'project', 'program', 'initiative', 'framework', 'strategy',
    'overview', 'summary', 'update', 'status', 'agenda', 'minutes', 'notes',
    'how', 'tips', 'priority', 'troubleshooting', 'please', 'click', 'here',
    'welcome', 'join', 'info', 'fyi', 'asap', 'tbd', 'todo', 'done',
    'original', 'appointment', 'additional', 'information', 'description',
    'standard', 'advanced', 'basic', 'general', 'specific', 'related',
    # Additional round 2
    'survey', 'highlights', 'assurance', 'policy', 'demo', 'availability',
    'vulnerable', 'regular', 'detailed', 'failback', 'estimated', 'minimum',
    'gartner', 'magic', 'timeline', 'impact', 'senior', 'advisors', 'session',
    'chief', 'ethics', 'supported', 'versions', 'tuesday', 'dec', 'billing',
    'cycle', 'request', 'title', 'actual', 'duration', 'informational',
    'purposes', 'business', 'requirement', 'corresponding', 'coursework',
    'strengthen', 'my', 'does', 'versions', 'purposes',
}


def is_obvious_noise(name: str) -> bool:
    """Return True if name is definitely NOT a person."""
    if '  ' in name:
        return True
    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return True
    if len(name) < 5 or len(name) > 40:
        return True
    for w in words:
        if not w or not w[0].isupper():
            return True
        alpha = sum(1 for c in w if c.isalpha())
        if alpha < len(w) * 0.7:
            return True
    lower_words = {w.lower() for w in words}
    if lower_words & NOISE_WORDS:
        return True
    return False


# -------------------------------------------------------------------
# Stage E: Claude API batch classification
# -------------------------------------------------------------------

def _load_qb_gateway_credentials():
    """Load QB AI Gateway credentials from ~/.coco/.qb-gateway-key."""
    key_file = Path.home() / ".coco" / ".qb-gateway-key"
    if not key_file.exists():
        return None, None
    api_key = key_file.read_text().strip()
    qb_project = "39867e95-6e22-4c1b-b20d-aba44c739c72"
    base_url = f"https://anthropic.prod.ai-gateway.quantumblack.com/{qb_project}"
    return api_key, base_url


def classify_with_claude(names: list[str], batch_size: int = 200) -> dict[str, bool]:
    """Classify names as person/not-person using Claude API via QB AI Gateway."""
    try:
        import anthropic
    except ImportError:
        print("WARNING: anthropic SDK not installed. Skipping Claude classification.")
        return {}

    # Load QB AI Gateway credentials
    api_key, base_url = _load_qb_gateway_credentials()
    if not api_key:
        # Fallback to env var
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip() or None
    if not api_key:
        print("WARNING: No API key found (checked ~/.coco/.qb-gateway-key and ANTHROPIC_API_KEY). Skipping.")
        return {}

    print(f"  Using {'QB AI Gateway' if base_url and 'quantumblack' in base_url else 'Anthropic API'}")
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
    results = {}

    import time as _time
    for i in range(0, len(names), batch_size):
        batch = names[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(names) + batch_size - 1) // batch_size
        print(f"  Claude batch {batch_num}/{total_batches} ({len(batch)} names)...")

        # Rate limit: wait between batches to avoid 429
        if batch_num > 1:
            _time.sleep(1.5)

        numbered = "\n".join(f"{j+1}. {n}" for j, n in enumerate(batch))
        prompt = f"""You are classifying entity names from a McKinsey & Company knowledge base.
For each name below, respond with ONLY the number followed by P (person) or N (not a person).

Rules:
- Real person names (first + last name): P
- Company/org names: N
- Locations/countries/cities: N
- Job titles/roles without a name: N
- Business concepts/processes: N
- System/tool names: N
- Text fragments/nonsense: N

Names:
{numbered}

Respond with one classification per line, format: "1. P" or "1. N". Nothing else."""

        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text
                for line in text.strip().split('\n'):
                    m = re.match(r'(\d+)\.\s*([PN])', line.strip())
                    if m:
                        idx = int(m.group(1)) - 1
                        if 0 <= idx < len(batch):
                            results[batch[idx]] = m.group(2) == 'P'
                break  # success
            except anthropic.RateLimitError:
                wait = 10 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s (attempt {attempt + 1}/3)...")
                _time.sleep(wait)
            except Exception as e:
                print(f"    ERROR: {e}")
                break

    return results


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('--dry-run', '--apply'):
        print(__doc__)
        sys.exit(1)

    dry_run = sys.argv[1] == '--dry-run'
    use_claude = '--no-claude' not in sys.argv

    print("Stage A: Extracting email names...")
    email_full, email_first = extract_email_names()
    email_normalized = {re.sub(r'[^a-z ]', '', n.lower()).strip() for n in email_full}
    print(f"  {len(email_full):,} full names, {len(email_first):,} first names")

    print("Stage B+C: Cross-referencing with DB...")
    conn = sqlite3.connect(str(KNOWLEDGE_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT gid, canonical_name FROM global_entities WHERE type='person'").fetchall()

    email_verified = []  # Stage B: exact email match
    firstname_verified = []  # Stage C: first-name match
    noise_by_heuristic = []  # Stage D: obvious noise
    ambiguous = []  # Stage E: needs Claude

    for r in rows:
        gid, name = r['gid'], r['canonical_name']
        norm = re.sub(r'[^a-z ]', '', name.lower()).strip()

        if norm in email_normalized:
            email_verified.append((gid, name))
        elif len(name.split()) >= 2 and name.split()[0].lower() in email_first:
            firstname_verified.append((gid, name))
        elif is_obvious_noise(name):
            noise_by_heuristic.append((gid, name))
        else:
            ambiguous.append((gid, name))

    print(f"\n{'DRY RUN' if dry_run else 'APPLYING'}: Stage 2 Reclassification")
    print(f"{'=' * 60}")
    print(f"Total person entities:      {len(rows):>6,}")
    print(f"  Email-verified (keep):    {len(email_verified):>6,}")
    print(f"  First-name match (keep):  {len(firstname_verified):>6,}")
    print(f"  Noise by heuristic:       {len(noise_by_heuristic):>6,}  -> reclassify as 'document'")
    print(f"  Ambiguous:                {len(ambiguous):>6,}  -> {'Claude API' if use_claude else 'keep as person'}")

    # Stage D: Reclassify obvious noise
    noise_gids = [gid for gid, _ in noise_by_heuristic]

    # Stage E: Claude classification
    claude_reclassify = []
    if use_claude and ambiguous:
        print(f"\nStage E: Classifying {len(ambiguous):,} ambiguous names with Claude API...")
        ambiguous_names = [name for _, name in ambiguous]
        classifications = classify_with_claude(ambiguous_names)

        for gid, name in ambiguous:
            if name in classifications and not classifications[name]:
                claude_reclassify.append((gid, name))

        print(f"  Claude says NOT person: {len(claude_reclassify):,}")
        print(f"  Claude says person:     {len(ambiguous) - len(claude_reclassify):,}")

    total_reclassify = len(noise_gids) + len(claude_reclassify)
    remaining = len(rows) - total_reclassify
    print(f"\nTotal to reclassify:        {total_reclassify:>6,}")
    print(f"Real people remaining:      {remaining:>6,}")

    if dry_run:
        print("\nSample noise (first 10):")
        for _, name in noise_by_heuristic[:10]:
            print(f"  [noise] {name}")
        if claude_reclassify:
            print("Sample Claude NOT-person (first 10):")
            for _, name in claude_reclassify[:10]:
                print(f"  [claude:N] {name}")
        print("\nRun with --apply to execute.")
        conn.close()
        return

    # Apply
    all_reclassify_gids = noise_gids + [gid for gid, _ in claude_reclassify]
    for i in range(0, len(all_reclassify_gids), 500):
        chunk = all_reclassify_gids[i:i + 500]
        placeholders = ','.join('?' for _ in chunk)
        conn.execute(
            f"UPDATE global_entities SET type = 'document' WHERE gid IN ({placeholders})",
            chunk,
        )
    conn.commit()
    conn.close()

    print(f"\nDone. {total_reclassify:,} entities reclassified to 'document'.")
    print(f"Real people remaining: {remaining:,}")


if __name__ == '__main__':
    main()
