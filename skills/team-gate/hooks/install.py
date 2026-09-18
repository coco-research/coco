#!/usr/bin/env python3
"""Register or remove the four team-gate hooks in a Claude Code settings.json.

This repository's own .claude/ is gitignored by convention (IDE-local
config, wired per machine via installers), so the hook registration ships
as this installer rather than as a tracked settings file. install.py is
the tracked artefact; any settings.json it writes is generated, local
state.

Usage:
  install.py --project DIR            merge the four hooks into DIR/.claude/settings.json
  install.py --user                   merge the four hooks into ~/.claude/settings.json
  install.py --project DIR --remove   remove exactly the team-gate entries, leave everything else
  install.py --user --remove          same, for ~/.claude/settings.json
  install.py --project DIR --check    exit 0 if all four are registered, 1 otherwise
  install.py --user --check           same, for ~/.claude/settings.json

The registered command is `node "$CLAUDE_PROJECT_DIR/skills/team-gate/hooks/<name>.js"`
for --project, since $CLAUDE_PROJECT_DIR resolves per session to whichever
project is open. For --user there is no project context, so the command
is `node "<absolute path to this directory>/<name>.js"` instead.

The merge is idempotent: an event/hook_file pair already present anywhere
in that event's array (found by the hook's filename appearing in a
command string, regardless of path style) is left alone, so a second run
changes nothing on disk and every existing hook and setting is untouched,
because entries belonging to this installer are only ever appended, never
merged into an existing entry. Before the first time this installer ever
modifies a given settings.json, it writes <file>.bak-team-gate (a plain
byte copy, no timestamp); later runs never overwrite that backup. Writes
are atomic (temp file plus os.replace).

Exit contract: 0 = done (install, remove, or --check confirms all four
registered), 1 = refused (--check finds at least one missing), 2 =
unrunnable (bad --project directory, or an existing settings.json that is
not valid JSON). Reason on stderr in one line for exit 2.

No em dash, no section sign, stdlib only, sys.exit only in the __main__ guard.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# (event, matcher or None, hook file). The four distinct hook programs are
# team-turn-log.js, team-artifact-guard.js, team-stage-guard.js and
# team-stop-guard.js; two of them register on both PreToolUse and
# PostToolUse, which is six registrations over four files.
REGISTRATIONS = [
    ("UserPromptSubmit", None, "team-turn-log.js"),
    ("PreToolUse", "Write|Edit|MultiEdit", "team-artifact-guard.js"),
    ("PostToolUse", "Write|Edit|MultiEdit", "team-artifact-guard.js"),
    ("PreToolUse", "Bash|Agent", "team-stage-guard.js"),
    ("PostToolUse", "Bash|Agent", "team-stage-guard.js"),
    ("Stop", None, "team-stop-guard.js"),
]
HOOK_FILES = sorted({hook_file for _, _, hook_file in REGISTRATIONS})


def build_command(hook_file: str, project_mode: bool) -> str:
    if project_mode:
        return f'node "$CLAUDE_PROJECT_DIR/skills/team-gate/hooks/{hook_file}"'
    return f'node "{HOOKS_DIR / hook_file}"'


def command_references(command: str, hook_file: str) -> bool:
    return hook_file in (command or "")


def load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def atomic_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(obj, indent=2) + "\n"
    tmp = path.with_name(path.name + ".tmp-team-gate")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(path))


def ensure_backup(path: Path) -> None:
    """Copy the file's current bytes to <file>.bak-team-gate, but only the
    first time: a backup that already exists is never overwritten, so it
    stays the pre-team-gate state rather than the state before the most
    recent run."""
    backup = path.with_name(path.name + ".bak-team-gate")
    if path.is_file() and not backup.is_file():
        shutil.copyfile(str(path), str(backup))


def do_install(settings_path: Path, project_mode: bool) -> bool:
    existed_before = settings_path.is_file()
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})

    changed = False
    for event, matcher, hook_file in REGISTRATIONS:
        arr = hooks.setdefault(event, [])
        already = any(
            command_references(h.get("command", ""), hook_file)
            for entry in arr
            for h in entry.get("hooks", [])
        )
        if already:
            continue
        command = build_command(hook_file, project_mode)
        hook_item = {"type": "command", "command": command, "timeout": 60}
        entry = {"matcher": matcher, "hooks": [hook_item]} if matcher is not None else {"hooks": [hook_item]}
        arr.append(entry)
        changed = True

    if not changed:
        return False

    if existed_before:
        ensure_backup(settings_path)
    atomic_write(settings_path, settings)
    return True


def do_remove(settings_path: Path) -> bool:
    if not settings_path.is_file():
        return False

    settings = load_settings(settings_path)
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        return False

    changed = False
    for event in list(hooks.keys()):
        arr = hooks.get(event)
        if not isinstance(arr, list):
            continue
        new_arr = []
        for entry in arr:
            entry_hooks = entry.get("hooks", [])
            kept_hooks = [
                h for h in entry_hooks
                if not any(command_references(h.get("command", ""), f) for f in HOOK_FILES)
            ]
            if len(kept_hooks) != len(entry_hooks):
                changed = True
            if kept_hooks:
                new_entry = dict(entry)
                new_entry["hooks"] = kept_hooks
                new_arr.append(new_entry)
            # An entry whose every hook belonged to team-gate is dropped
            # entirely rather than kept as an empty hooks list.
        if new_arr:
            hooks[event] = new_arr
        else:
            del hooks[event]

    if not hooks:
        settings.pop("hooks", None)

    if not changed:
        return False

    ensure_backup(settings_path)
    atomic_write(settings_path, settings)
    return True


def do_check(settings_path: Path) -> bool:
    if not settings_path.is_file():
        print("not registered: settings file does not exist")
        return False

    settings = load_settings(settings_path)
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        hooks = {}

    missing = []
    for event, _matcher, hook_file in REGISTRATIONS:
        arr = hooks.get(event, [])
        found = isinstance(arr, list) and any(
            command_references(h.get("command", ""), hook_file)
            for entry in arr
            for h in entry.get("hooks", [])
        )
        if not found:
            missing.append(f"{event}/{hook_file}")

    if missing:
        print("not registered: missing " + ", ".join(missing))
        return False

    print("registered: all four team-gate hooks present")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--project", metavar="DIR", help="project root; writes DIR/.claude/settings.json")
    target.add_argument("--user", action="store_true", help="writes ~/.claude/settings.json")
    action = ap.add_mutually_exclusive_group()
    action.add_argument("--remove", action="store_true", help="remove the team-gate entries")
    action.add_argument("--check", action="store_true", help="check whether all four are registered")
    args = ap.parse_args()

    project_mode = args.project is not None
    if project_mode:
        project_dir = Path(args.project).resolve()
        if not project_dir.is_dir():
            print(f"ERROR: not a directory: {project_dir}", file=sys.stderr)
            return 2
        settings_path = project_dir / ".claude" / "settings.json"
    else:
        settings_path = Path.home() / ".claude" / "settings.json"

    try:
        if args.check:
            return 0 if do_check(settings_path) else 1
        if args.remove:
            do_remove(settings_path)
            return 0
        do_install(settings_path, project_mode)
        return 0
    except json.JSONDecodeError as exc:
        print(f"ERROR: {settings_path} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
