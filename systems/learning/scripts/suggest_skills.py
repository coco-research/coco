#!/usr/bin/env python3
"""Suggest three repeated local workflows without changing the learning store."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import tempfile


def suggestions(store, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    counts = Counter()
    if store.is_symlink() or not store.is_dir():
        return []
    projects = store / 'projects'
    if projects.is_symlink() or not projects.is_dir():
        return []
    for project in sorted(projects.iterdir()):
        if project.is_symlink() or not project.is_dir():
            continue
        source = project / 'observations.jsonl'
        if source.is_symlink() or not source.is_file():
            continue
        with source.open(encoding='utf-8', errors='replace') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        continue
                    stamp = datetime.fromisoformat(row.get('timestamp', '').replace('Z', '+00:00'))
                    if stamp.tzinfo is None:
                        continue
                    pattern = row.get('input_summary')
                    if not isinstance(pattern, str) or not cutoff <= stamp <= now:
                        continue
                    pattern = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', pattern)
                    pattern = ' '.join(pattern.split()).casefold()[:400]
                    if pattern:
                        counts[pattern] += 1
                except (ValueError, TypeError, AttributeError):
                    continue
    return sorted(((p, n) for p, n in counts.items() if n >= 3),
                  key=lambda pair: (-pair[1], pair[0]))[:3]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, default=Path(
        os.environ.get('COCO_LEARNING_DIR', str(Path.home() / '.coco' / 'learning'))))
    parser.add_argument('--draft', action='store_true', help='write stubs in a new temporary folder')
    args = parser.parse_args(argv)
    try:
        found = suggestions(args.store)
    except OSError as error:
        parser.exit(1, 'Cannot read learning store: %s\n' % error)
    if not found:
        print('nothing repeated yet')
        return 0
    for pattern, count in found:
        print('seen %d times this week · %s · could be a skill' %
              (count, json.dumps(pattern, ensure_ascii=False)))
    if args.draft:
        folder = Path(tempfile.mkdtemp(prefix='coco-skill-drafts-'))
        for index, (pattern, count) in enumerate(found, 1):
            destination = folder / ('pattern-%d' % index)
            destination.mkdir()
            (destination / 'SKILL.md').write_text(
                '---\nname: suggested-pattern-%d\ndescription: %s\n---\n\n'
                '# Suggested workflow\n\nObserved %d times this week.\n\n'
                '## Steps\n\nDescribe and verify the steps before using this skill.\n' %
                (index, json.dumps(pattern, ensure_ascii=False), count), encoding='utf-8')
        print('Drafts: %s' % folder)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
