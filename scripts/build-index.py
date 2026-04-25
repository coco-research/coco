#!/usr/bin/env python3
"""Auto-generate INDEX.md files from frontmatter.

Generates:
  skills/INDEX.md                    — full skill catalog
  commands/INDEX.md                  — full command catalog
  agents/INDEX.md                    — agent catalog
  systems/INDEX.md                   — system bundle catalog
  docs/by-domain/<domain>.md         — domain-filtered skill listings

Run from repo root:
  python3 scripts/build-index.py
"""

import sys
import pathlib
import yaml
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent.parent.resolve()


def parse_frontmatter(path):
    text = path.read_text()
    if not text.startswith('---'):
        return None
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None


def collect_skills():
    skills = []
    for p in sorted(ROOT.glob('skills/*/SKILL.md')):
        fm = parse_frontmatter(p) or {}
        name = fm.get('name', p.parent.name)
        desc = fm.get('description', '').strip().strip('"').strip("'")
        domain = fm.get('domain', 'unspecified')
        skills.append({'name': name, 'desc': desc, 'domain': domain, 'path': p.relative_to(ROOT)})

    for p in sorted(ROOT.glob('systems/*/skills/*/SKILL.md')):
        fm = parse_frontmatter(p) or {}
        name = fm.get('name', p.parent.name)
        desc = fm.get('description', '').strip().strip('"').strip("'")
        bundle = p.parents[2].name
        skills.append({'name': name, 'desc': desc, 'domain': f'system:{bundle}', 'path': p.relative_to(ROOT), 'bundle': bundle})
    return skills


def collect_commands():
    commands = []
    for p in sorted(ROOT.glob('commands/*/*.md')):
        fm = parse_frontmatter(p) or {}
        ns = p.parent.name
        cname = p.stem
        if cname == '_index':
            slash = f'/{ns}'
        else:
            slash = f'/{ns}:{cname}'
        desc = fm.get('description', '').strip().strip('"').strip("'") if fm else ''
        commands.append({'slash': slash, 'namespace': ns, 'name': cname, 'desc': desc, 'path': p.relative_to(ROOT)})
    return commands


def collect_agents():
    agents = []
    for p in sorted(ROOT.glob('agents/*.md')):
        if p.name in ('README.md', 'INDEX.md'):
            continue
        text = p.read_text()
        first_line = ''
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('---') and not line.startswith('#'):
                first_line = line[:200]
                break
        agents.append({'name': p.stem, 'desc': first_line, 'path': p.relative_to(ROOT)})

    for p in sorted(ROOT.glob('systems/*/agents/*.md')):
        bundle = p.parents[2].name
        text = p.read_text()
        first_line = ''
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('---') and not line.startswith('#'):
                first_line = line[:200]
                break
        agents.append({'name': p.stem, 'desc': first_line, 'path': p.relative_to(ROOT), 'bundle': bundle})
    return agents


def write_skills_index(skills):
    out = ROOT / 'skills' / 'INDEX.md'
    by_domain = defaultdict(list)
    for s in skills:
        if 'bundle' in s:
            continue
        by_domain[s['domain']].append(s)

    lines = ['# Skills Index', '',
             f'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             f'**Total: {sum(len(v) for v in by_domain.values())} skills** (top-level only — see `systems/<bundle>/skills/` for bundle-only skills).', '']

    for domain in sorted(by_domain.keys()):
        lines.append(f'## {domain.title()}')
        lines.append('')
        lines.append('| Skill | Description |')
        lines.append('|-------|-------------|')
        for s in sorted(by_domain[domain], key=lambda x: x['name']):
            link = f'[{s["name"]}]({s["name"]}/SKILL.md)'
            desc = s['desc'].replace('\n', ' ').replace('|', '\\|')[:160]
            lines.append(f'| {link} | {desc} |')
        lines.append('')

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


def write_commands_index(commands):
    out = ROOT / 'commands' / 'INDEX.md'
    by_ns = defaultdict(list)
    for c in commands:
        by_ns[c['namespace']].append(c)

    lines = ['# Commands Index', '',
             f'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '',
             f'**Total: {len(commands)} commands across {len(by_ns)} namespaces.**', '']

    for ns in sorted(by_ns.keys()):
        lines.append(f'## {ns}')
        lines.append('')
        lines.append('| Slash | Description |')
        lines.append('|-------|-------------|')
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
             f'Auto-generated. Run `python3 scripts/build-index.py` to refresh.', '']

    if top:
        lines += [f'## Core agents ({len(top)})', '',
                  '| Agent | Description |',
                  '|-------|-------------|']
        for a in sorted(top, key=lambda x: x['name']):
            desc = a['desc'].replace('|', '\\|')[:160]
            lines.append(f'| [{a["name"]}]({a["name"]}.md) | {desc} |')
        lines.append('')

    for bundle in sorted(by_bundle.keys()):
        lines += [f'## Bundle: {bundle} ({len(by_bundle[bundle])} agents)', '',
                  '| Agent | Description |',
                  '|-------|-------------|']
        for a in sorted(by_bundle[bundle], key=lambda x: x['name']):
            desc = a['desc'].replace('|', '\\|')[:160]
            link = f'[{a["name"]}](../systems/{bundle}/agents/{a["name"]}.md)'
            lines.append(f'| {link} | {desc} |')
        lines.append('')

    out.write_text('\n'.join(lines))
    print(f'Wrote {out.relative_to(ROOT)}')


def write_by_domain_views(skills):
    out_dir = ROOT / 'docs' / 'by-domain'
    out_dir.mkdir(parents=True, exist_ok=True)
    by_domain = defaultdict(list)
    for s in skills:
        if 'bundle' in s:
            continue
        by_domain[s['domain']].append(s)

    for domain, items in by_domain.items():
        if domain == 'unspecified':
            continue
        slug = domain.replace('/', '-')
        out = out_dir / f'{slug}.md'
        lines = [f'# {domain.title()} skills', '',
                 f'Auto-generated view. Filtered to `domain: {domain}` skills.', '',
                 f'**{len(items)} skills.**', '',
                 '| Skill | Description |',
                 '|-------|-------------|']
        for s in sorted(items, key=lambda x: x['name']):
            desc = s['desc'].replace('|', '\\|')[:200]
            link = f'[{s["name"]}](../../skills/{s["name"]}/SKILL.md)'
            lines.append(f'| {link} | {desc} |')
        out.write_text('\n'.join(lines))
        print(f'Wrote {out.relative_to(ROOT)}')


def main():
    skills = collect_skills()
    commands = collect_commands()
    agents = collect_agents()

    write_skills_index(skills)
    write_commands_index(commands)
    write_agents_index(agents)
    write_by_domain_views(skills)
    print(f'\nDone. Skills: {len(skills)} · Commands: {len(commands)} · Agents: {len(agents)}')


if __name__ == '__main__':
    main()
