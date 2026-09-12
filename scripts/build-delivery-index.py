#!/usr/bin/env python3
"""Generate adapters/INDEX.md — what each adapter actually delivers.

Every other index in this repo is built by reading files. This one is built by
*running* the installers: each adapter is installed into a throwaway HOME at its
widest advertised configuration, and the result is counted.

That distinction is the point. The install surface is not derivable from the
directory listing, because the largest single piece of it does not exist as files
at all: the Super Intelligence command family (242 commands) is generated at
install time by `systems/superintelligence/*/scripts/build_commands.py`, and an
adapter that does not call those generators ships 38 commands where the README
advertises 280. Nothing in the tree said so; running the adapters says so.

Run from repo root:
    python3 scripts/build-delivery-index.py

The output is committed and gated in CI, so an adapter that silently stops
delivering a surface shows up as a diff.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).parent.parent.resolve()
OUT = ROOT / 'adapters' / 'INDEX.md'

# Readme says 38 core commands + 242 generated. Kept here so the generated table
# can show the gap rather than requiring the reader to hold both numbers.
ADVERTISED = {'commands': 280, 'skills': 185}

BUNDLE_UNIVERSE = ('gsd', 'brain', 'cognee', 'hyperframes', 'superintelligence', 'm0')


def manifest_bundles(adapter):
    """The bundles one adapter advertises, restricted to bundles that exist.

    Per adapter rather than global: Cursor declares `supports_systems: []`, and
    passing it a bundle it does not claim makes it exit non-zero rather than
    deliver nothing, which would misreport a deliberate claim as a failure.
    """
    manifest = ROOT / 'adapters' / adapter / 'manifest.json'
    try:
        data = json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return sorted(b for b in (data.get('supports_systems') or [])
                  if (ROOT / 'systems' / b).is_dir())


def advertised_bundles():
    """The union across adapters, for the report header."""
    bundles = set()
    for manifest in sorted((ROOT / 'adapters').glob('*/manifest.json')):
        bundles |= set(manifest_bundles(manifest.parent.name))
    return sorted(bundles)


def walk(root):
    """Walk a delivered HOME, following symlinks and skipping VCS internals."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        dirnames[:] = [d for d in dirnames if d != '.git']
        yield pathlib.Path(dirpath), filenames


def count_md(root, segments):
    """Count distinct delivered *.md files that live under one of `segments`.

    Deduplicated by resolved path: adapters link into the checkout, so the same
    file reached twice must count once. Symlinks are followed, which is the whole
    reason this is not a `find -type f`.
    """
    seen = set()
    for dirpath, filenames in walk(root):
        # Counting is scoped to the adapter's own target roots. A skill may ship
        # its own commands/ directory (visual-explainer has seven), and walking the
        # skills symlink into the checkout would otherwise count those as delivered
        # slash commands and overstate the surface.
        if 'skills' in dirpath.parts:
            continue
        if not (set(dirpath.parts) & segments):
            continue
        for name in filenames:
            # INDEX.md and README.md are catalogs sitting in the same directory,
            # not delivered commands or agents.
            if name.endswith('.md') and name not in ('INDEX.md', 'README.md'):
                seen.add(str((dirpath / name).resolve()))
    return len(seen)


def count_skills(root):
    """A delivered skill is a directory holding a SKILL.md, symlinked or not."""
    seen = set()
    for dirpath, filenames in walk(root):
        if 'SKILL.md' in filenames:
            seen.add(str(dirpath.resolve()))
    return len(seen)


def count_generated(root):
    """How many delivered commands came from the Super Intelligence generators."""
    seen = set()
    for dirpath, filenames in walk(root):
        if 'skills' in dirpath.parts:
            continue
        for name in filenames:
            if name.endswith('.md') and (name == 'SI.md' or name.startswith('SI-')):
                seen.add(str((dirpath / name).resolve()))
    return len(seen)


def install(adapter, bundles, timeout=900):
    """Install one adapter into a temp HOME and count what arrived."""
    home = tempfile.mkdtemp(prefix=f'deliv-{adapter}-')
    cwd = tempfile.mkdtemp(prefix=f'deliv-cwd-{adapter}-')
    # The VS Code adapter links core commands into the editor's user profile, which
    # a bare temp HOME does not have. Create the two standard locations so the
    # measurement reflects a machine with the editor installed.
    for profile in ('Library/Application Support/Code/User', '.config/Code/User'):
        (pathlib.Path(home) / profile).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env['HOME'] = home
    for var in ('CLAUDE_HOME', 'CURSOR_HOME', 'COPILOT_HOME', 'PI_AGENT_HOME', 'AGENTS_HOME'):
        env.pop(var, None)
    cmd = ['bash', str(ROOT / 'adapters' / adapter / 'install.sh')]
    if bundles:
        cmd += ['--systems', ','.join(bundles)]
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                              text=True, timeout=timeout)
        rc, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        rc, output = 124, 'timed out'
    finally:
        pass

    result = {
        'adapter': adapter,
        'exit': rc,
        'commands': count_md(home, {'commands', 'prompts', 'si-commands'}),
        'skills': count_skills(home),
        'agents': count_md(home, {'agents', 'subagents'}),
        'generated_commands': count_generated(home),
        'bundles': bundles,
        'agents_md': (pathlib.Path(cwd) / 'AGENTS.md').exists(),
        'bundles': bundles,
        'tail': ' | '.join([ln for ln in output.strip().splitlines() if ln.strip()][-1:]),
    }
    shutil.rmtree(home, ignore_errors=True)
    shutil.rmtree(cwd, ignore_errors=True)
    return result


def main():
    bundles = advertised_bundles()
    adapters = sorted(p.name for p in (ROOT / 'adapters').iterdir() if p.is_dir())
    rows = [install(a, manifest_bundles(a)) for a in adapters]

    lines = [
        '# Install Adapters — Delivery Index',
        '',
        'Auto-generated by `python3 scripts/build-delivery-index.py`. Do not hand-edit.',
        '',
        'Each adapter was installed into a throwaway `HOME` with every bundle it advertises',
        f'(`--systems {",".join(bundles)}`) and the result counted. Counts include symlinks,',
        'because most adapters link into the checkout rather than copying.',
        '',
        '| Adapter | Commands | of which generated | Skills | Agents | AGENTS.md | Exit |',
        '|---|---:|---:|---:|---:|:--:|---:|',
    ]
    for r in rows:
        ag = 'yes' if r['agents_md'] else '—'
        lines.append(
            f"| `{r['adapter']}` | {r['commands']} | {r['generated_commands']} | "
            f"{r['skills']} | {r['agents']} | {ag} | {r['exit']} |"
        )

    lines += [
        '',
        '## Widest install, against the published totals',
        '',
        '| Surface | Best adapter | Advertised |',
        '|---|---:|---:|',
    ]
    best_cmd = max(r['commands'] for r in rows)
    best_skill = max(r['skills'] for r in rows)
    lines.append(f"| Slash commands | {best_cmd} | {ADVERTISED['commands']} |")
    lines.append(f"| Skills | {best_skill} | {ADVERTISED['skills']} |")

    # Only adapters that install into a config directory and were given bundles are
    # comparable. An AGENTS.md producer emits one file by design, and an adapter
    # whose manifest declares no bundles cannot reach the generated family at all.
    def comparable(r):
        return not (r['agents_md'] and r['commands'] == 0)

    gaps = [r for r in rows if comparable(r) and r['commands'] < best_cmd]
    exempt = [r for r in rows if not comparable(r)]
    lines += [
        '',
        '## Adapters below the command ceiling',
        '',
        'The Super Intelligence family is generated at install time, not committed, so an',
        'adapter that does not invoke the generators delivers 38 commands instead of 280.',
        'This section is the standing list of who is short and by how much.',
        '',
    ]
    if gaps:
        lines += ['| Adapter | Commands | Short by | Cause |', '|---|---:|---:|---|']
        for r in sorted(gaps, key=lambda x: x['commands']):
            cause = ('declares `supports_systems: []`' if not r['bundles']
                     else 'does not invoke the SI generators')
            lines.append(f"| `{r['adapter']}` | {r['commands']} | "
                         f"{best_cmd - r['commands']} | {cause} |")
    else:
        lines.append('None — every adapter delivers the full command surface.')
    if exempt:
        lines += ['', 'Not comparable (AGENTS.md producers rather than tree installers): '
                  + ', '.join(f"`{r['adapter']}`" for r in exempt) + '.']

    note = []
    for r in rows:
        if r['exit'] != 0:
            note.append(f"- `{r['adapter']}` exited {r['exit']}: {r['tail']}")
    if note:
        lines += ['', '## Adapters that did not install cleanly', ''] + note

    lines += [
        '',
        '## Measurement notes',
        '',
        'Read the table with these in mind; each is a property of the adapter, not a',
        'bug in the measurement.',
        '',
        '- **Cursor declares `supports_systems: []`.** It can install the core only, so',
        '  it can never reach the Super Intelligence family. That is a declared claim,',
        '  checked by the bundle gate, not an oversight.',
        '- **Codex and generic emit one `AGENTS.md`** and nothing else. They are',
        '  AGENTS.md producers; the tree-side surfaces are not their job.',
        '- **The VS Code adapter needs a profile to exist.** It links core commands into',
        '  the editor user profile, so the measurement creates the two standard profile',
        '  directories inside the throwaway HOME first. Without them it reports only the',
        '  generated family.',
        '- **Skills stop at 171, not 185.** Five skills live under `adapters/cursor/skills`',
        '  and are Cursor-only; the rest of the 185 figure is the repository inventory',
        '  rather than what any single adapter installs.',
        '- **Counts include symlinks.** Most adapters link into the checkout instead of',
        '  copying, and are deduplicated by resolved path.',
        '',
    ]

    lines += [
        '',
        '## Regenerating',
        '',
        '```bash',
        'python3 scripts/build-delivery-index.py',
        '```',
        '',
        'This runs real installers, so it takes a minute. It only ever writes inside a',
        'temporary HOME that it deletes afterwards.',
        '',
    ]

    if '--check' in sys.argv:
        current = OUT.read_text() if OUT.exists() else ''
        if current != '\n'.join(lines) + '\n':
            print('adapters/INDEX.md is out of date. Run: python3 scripts/build-delivery-index.py')
            return 1
        print('adapters/INDEX.md is up to date.')
        return 0

    OUT.write_text('\n'.join(lines) + '\n')
    print(f'Wrote {OUT.relative_to(ROOT)}')
    for r in rows:
        print(f"  {r['adapter']:14s} commands={r['commands']:4d} "
              f"generated={r['generated_commands']:4d} skills={r['skills']:4d} "
              f"agents={r['agents']:3d} exit={r['exit']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
