#!/usr/bin/env python3
"""Auto-generate INDEX.md files from frontmatter.

Generates:
  skills/INDEX.md                    — full skill catalog (core, grouped by domain,
                                       then one section per bundle)
  commands/INDEX.md                  — full command catalog
  agents/INDEX.md                    — agent catalog
  systems/INDEX.md                   — system bundle catalog
  docs/by-domain/<domain>.md         — domain-filtered skill listings

Run from repo root:
  python3 scripts/build-index.py

Counting rule: the only trustworthy oracle for "how many skills exist" is a walk of
the whole tree. Narrow globs have twice produced undercounts here, because skills live
in four structurally different places:

  skills/<name>/SKILL.md                     core
  systems/<bundle>/skills/<name>/SKILL.md    conventional bundle
  systems/<bundle>/<name>/SKILL.md           superintelligence (no skills/ subdir)
  adapters/<adapter>/skills/<name>/SKILL.md  adapter-specific

If you add a fifth shape, add it to SKILL_SOURCES below, and check the printed total
against `find . -name 'SKILL.md' -not -path './.git/*' | wc -l`.
"""

import json
import os
import sys
import pathlib
import yaml
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent.parent.resolve()

# (glob, index of the parent directory that names the bundle, or None for core skills)
# Depths differ per shape, so the bundle index is declared alongside its glob rather
# than assumed. Assuming one depth for all shapes is what produced a bundle literally
# named "systems".
SKILL_SOURCES = [
    ('skills/*/SKILL.md', None),
    ('systems/*/skills/*/SKILL.md', 2),
    ('systems/*/*/SKILL.md', 1),
    ('adapters/*/skills/*/SKILL.md', 2),
]


# Display names for the six declared domains. `str.title()` renders "pm" as "Pm",
# which is wrong for an initialism and is user-facing in every generated index.
DOMAIN_LABELS = {
    'foundational': 'Foundational',
    'pm': 'PM',
    'engineering': 'Engineering',
    'design': 'Design',
    'ops': 'Ops',
    'meta': 'Meta',
}


def domain_label(slug):
    return DOMAIN_LABELS.get(slug, slug.replace('-', ' ').title())


def parse_frontmatter(path, strict=True):
    """Return the frontmatter mapping, or None when there is no frontmatter block.

    A YAML syntax error is reported rather than swallowed. Returning None on a parse
    error is indistinguishable from "this file has no frontmatter", which silently
    produced blank description rows in the generated catalogs.
    """
    text = path.read_text()
    if not text.startswith('---'):
        return None
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        rel = path.relative_to(ROOT)
        msg = str(exc).replace('\n', ' ')
        if strict:
            print(f'ERROR: {rel}: malformed YAML frontmatter: {msg}', file=sys.stderr)
            raise SystemExit(1)
        print(f'WARNING: {rel}: malformed YAML frontmatter: {msg}', file=sys.stderr)
        return None


def link_from(index_dir, target_path):
    """Relative link from a generated index to a repo-relative target path."""
    return os.path.relpath(target_path, index_dir)


def collect_skills():
    skills = []
    seen = set()
    for glob, bundle_at in SKILL_SOURCES:
        for p in sorted(ROOT.glob(glob)):
            if p in seen:
                continue
            seen.add(p)
            fm = parse_frontmatter(p) or {}
            directory = p.parent.name
            entry = {
                # `name` is display text only, never a path. 26 skills have a
                # frontmatter name that differs from their directory and 3 have none,
                # which is what produced dead links when name was used as the href.
                'name': fm.get('name') or directory,
                'dir': directory,
                'desc': (fm.get('description') or '').strip().strip('"').strip("'"),
                'domain': fm.get('domain', 'unspecified'),
                'path': p.relative_to(ROOT),
            }
            if bundle_at is not None:
                entry['bundle'] = p.parents[bundle_at].name
            skills.append(entry)
    return skills


def collect_commands():
    commands = []
    for p in sorted(ROOT.glob('commands/*/*.md')):
        fm = parse_frontmatter(p) or {}
        ns = p.parent.name
        cname = p.stem
        slash = f'/{ns}' if cname == '_index' else f'/{ns}:{cname}'
        desc = (fm.get('description') or '').strip().strip('"').strip("'") if fm else ''
        commands.append({'slash': slash, 'namespace': ns, 'name': cname,
                         'desc': desc, 'path': p.relative_to(ROOT)})
    return commands


def _first_prose_line(path):
    for line in path.read_text().split('\n'):
        line = line.strip()
        if line and not line.startswith('---') and not line.startswith('#'):
            return line[:200]
    return ''


def collect_agents():
    agents = []
    for p in sorted(ROOT.glob('agents/*.md')):
        if p.name in ('README.md', 'INDEX.md'):
            continue
        agents.append({'name': p.stem, 'desc': _first_prose_line(p),
                       'path': p.relative_to(ROOT)})

    # systems/<bundle>/agents/<name>.md is three levels deep, so the bundle is
    # parents[1]. parents[2] here yields the literal string "systems", which produced
    # 24 links to a nonexistent systems/systems/agents/ directory.
    for p in sorted(ROOT.glob('systems/*/agents/*.md')):
        if p.name in ('README.md', 'INDEX.md'):
            continue
        agents.append({'name': p.stem, 'desc': _first_prose_line(p),
                       'path': p.relative_to(ROOT), 'bundle': p.parents[1].name})
    return agents


def _skill_table(rows):
    return ['| Skill | Description |', '|-------|-------------|'] + rows


def write_skills_index(skills):
    out = ROOT / 'skills' / 'INDEX.md'
    core = [s for s in skills if 'bundle' not in s]
    by_domain = defaultdict(list)
    for s in core:
        by_domain[s['domain']].append(s)
    by_bundle = defaultdict(list)
    for s in skills:
        if 'bundle' in s:
            by_bundle[s['bundle']].append(s)

    lines = ['# Skills Index', '',
             'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             f'**Total: {len(skills)} skills** — {len(core)} core, '
             f'{len(skills) - len(core)} across {len(by_bundle)} bundles.', '']

    def rows(items):
        built = []
        for s in sorted(items, key=lambda x: x['dir']):
            href = link_from('skills', s['path'])
            desc = s['desc'].replace('\n', ' ').replace('|', '\\|')[:160]
            built.append(f'| [{s["name"]}]({href}) | {desc} |')
        return built

    for domain in sorted(by_domain):
        lines += [f'## {domain_label(domain)} ({len(by_domain[domain])})', '']
        lines += _skill_table(rows(by_domain[domain])) + ['']

    for bundle in sorted(by_bundle):
        lines += [f'## Bundle: {bundle} ({len(by_bundle[bundle])} skills)', '']
        lines += _skill_table(rows(by_bundle[bundle])) + ['']

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


def write_commands_index(commands):
    out = ROOT / 'commands' / 'INDEX.md'
    by_ns = defaultdict(list)
    for c in commands:
        by_ns[c['namespace']].append(c)

    lines = ['# Commands Index', '',
             'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             f'**Total: {len(commands)} commands across {len(by_ns)} namespaces.**', '']

    for ns in sorted(by_ns):
        lines += [f'## {ns}', '', '| Slash | Description |', '|-------|-------------|']
        for c in sorted(by_ns[ns], key=lambda x: x['name']):
            link = f'[`{c["slash"]}`]({ns}/{c["name"]}.md)'
            desc = c['desc'].replace('\n', ' ').replace('|', '\\|')[:160]
            lines.append(f'| {link} | {desc} |')
        lines.append('')

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


def write_agents_index(agents):
    out = ROOT / 'agents' / 'INDEX.md'
    top = [a for a in agents if 'bundle' not in a]
    by_bundle = defaultdict(list)
    for a in agents:
        if 'bundle' in a:
            by_bundle[a['bundle']].append(a)

    lines = ['# Agents Index', '',
             'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             f'**Total: {len(agents)} agents** — {len(top)} core, '
             f'{len(agents) - len(top)} across {len(by_bundle)} bundles.', '']

    def emit(heading, items):
        block = [heading, '', '| Agent | Description |', '|-------|-------------|']
        for a in sorted(items, key=lambda x: x['name']):
            href = link_from('agents', a['path'])
            desc = a['desc'].replace('|', '\\|')[:160]
            block.append(f'| [{a["name"]}]({href}) | {desc} |')
        return block + ['']

    if top:
        lines += emit(f'## Core agents ({len(top)})', top)
    for bundle in sorted(by_bundle):
        lines += emit(f'## Bundle: {bundle} ({len(by_bundle[bundle])} agents)',
                      by_bundle[bundle])

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


# Generated artifacts must not be counted. The file tally below feeds systems/INDEX.md,
# which CI checks for freshness, so counting anything a local run can create makes the
# generated file environment-dependent and turns CI red for the wrong reason. Running the
# m0 smoke test, for instance, leaves a __pycache__/*.pyc behind and shifted the m0 row
# from 9 to 10.
_ARTIFACT_DIRS = {'__pycache__', '.git', 'node_modules', '.pytest_cache', '.ruff_cache'}
_ARTIFACT_SUFFIXES = {'.pyc', '.pyo'}


def _ships(path):
    """True when a file is part of the distributable rather than a local artifact."""
    if any(part in _ARTIFACT_DIRS for part in path.parts):
        return False
    if path.suffix in _ARTIFACT_SUFFIXES:
        return False
    return path.name != '.DS_Store'


def write_systems_index(skills, agents):
    """Catalog every bundle-like container under systems/ and adapters/.

    The module docstring promised this file for a long time without it ever being
    written, which left bundles the least legible part of the repository.
    """
    out = ROOT / 'systems' / 'INDEX.md'
    skills_by_bundle = defaultdict(int)
    for s in skills:
        if 'bundle' in s:
            skills_by_bundle[s['bundle']] += 1
    agents_by_bundle = defaultdict(int)
    for a in agents:
        if 'bundle' in a:
            agents_by_bundle[a['bundle']] += 1

    containers = []
    for base in ('systems', 'adapters'):
        base_dir = ROOT / base
        if not base_dir.is_dir():
            continue
        for d in sorted(p for p in base_dir.iterdir() if p.is_dir()):
            n_cmds = (len(list(d.glob('commands/*.md')))
                      + len(list(d.glob('commands/*/*.md'))))
            containers.append({
                'base': base,
                'name': d.name,
                'skills': skills_by_bundle.get(d.name, 0),
                'agents': agents_by_bundle.get(d.name, 0),
                'commands': n_cmds,
                'files': sum(1 for f in d.rglob('*') if f.is_file() and _ships(f)),
            })

    lines = ['# System Bundles Index', '',
             'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             'Bundles under `systems/` are opt-in via `install.sh --systems <name>`. '
             'Directories under `adapters/` ship with their adapter instead and are not '
             'selectable with that flag.', '',
             '| Bundle | Location | Skills | Agents | Commands | Files |',
             '|--------|----------|-------:|-------:|---------:|------:|']
    for c in containers:
        lines.append(f'| {c["name"]} | `{c["base"]}/{c["name"]}/` | {c["skills"]} '
                     f'| {c["agents"]} | {c["commands"]} | {c["files"]} |')
    lines.append('')

    # Only flag inert entries under systems/. An adapter with no bundle skills is
    # normal — adapters install the framework itself and were never --systems targets,
    # so listing them here would misrepresent them as broken.
    inert = [c['name'] for c in containers
             if c['base'] == 'systems'
             and c['skills'] == 0 and c['agents'] == 0 and c['commands'] == 0]
    if inert:
        lines += ['> **Advertised as a bundle but installs no artifacts:** '
                  + ', '.join(f'`{n}`' for n in inert)
                  + '. These directories hold documentation only, so passing them to '
                    '`--systems` has no effect.', '']

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


def write_by_domain_views(skills):
    out_dir = ROOT / 'docs' / 'by-domain'
    out_dir.mkdir(parents=True, exist_ok=True)
    by_domain = defaultdict(list)
    for s in skills:
        by_domain[s['domain']].append(s)

    for domain, items in by_domain.items():
        if domain == 'unspecified' or domain.startswith('system:'):
            continue
        slug = domain.replace('/', '-')
        out = out_dir / f'{slug}.md'
        lines = [f'# {domain_label(domain)} skills', '',
                 f'Auto-generated view. Filtered to `domain: {domain}` skills.', '',
                 f'**{len(items)} skills.**', '',
                 '| Skill | Description |', '|-------|-------------|']
        for s in sorted(items, key=lambda x: x['dir']):
            href = link_from('docs/by-domain', s['path'])
            desc = s['desc'].replace('|', '\\|')[:200]
            lines.append(f'| [{s["name"]}]({href}) | {desc} |')
        out.write_text('\n'.join(lines))
        print(f'Wrote {out.relative_to(ROOT)}')


def write_asset_counts(skills, commands, agents):
    """Emit docs/asset-counts.json — the single source of truth for asset counts.

    The README badge, package.json description, and prose have drifted apart three
    times (149 vs 179 vs the real number). This file is generated from the same walk
    that builds the indexes, so it is correct by construction. A CI gate asserts the
    badge and package.json agree with it.
    """
    core_skills = [s for s in skills if 'bundle' not in s]
    bundle_skills = [s for s in skills if 'bundle' in s]
    core_agents = [a for a in agents if 'bundle' not in a]
    counts = {
        'schema': 1,
        'skills': {
            'total': len(skills),
            'core': len(core_skills),
            'bundle': len(bundle_skills),
        },
        'commands': {'total': len(commands), 'namespaces': len({c['namespace'] for c in commands})},
        'agents': {'total': len(agents), 'core': len(core_agents)},
        'rules': len(list((ROOT / 'rules' / 'cursor-mdc').glob('*.mdc'))),
    }
    out = ROOT / 'docs' / 'asset-counts.json'
    out.write_text(json.dumps(counts, indent=2) + '\n')
    print(f'Wrote {out.relative_to(ROOT)}')


def main():
    skills = collect_skills()
    commands = collect_commands()
    agents = collect_agents()

    write_skills_index(skills)
    write_commands_index(commands)
    write_agents_index(agents)
    write_systems_index(skills, agents)
    write_by_domain_views(skills)
    write_asset_counts(skills, commands, agents)
    print(f'\nDone. Skills: {len(skills)} · Commands: {len(commands)} · '
          f'Agents: {len(agents)}')


if __name__ == '__main__':
    main()
