#!/usr/bin/env python3
"""Every generated SI command carries the approved persona attribution.

Runs both command generators into a temp directory (no network) and checks
the wording against systems/superintelligence/templates/attribution.md:

  * the label sentence ("**<Name> persona**: an AI simulation based on ..."),
  * the report footer (the paragraph starting "Personas are AI simulations
    modeled on"), and
  * the [extrapolated] rule (such content is never put in quotation marks),

must appear in every generated command, and no generator template may
instruct a banned form ("<Name> says", "<Name> thinks", "<Name> believes",
"<Name>'s view is", "<Name> endorses", "<Name> would recommend", first-person
"I, <Name>") outside a negating "never"/"do not" sentence.

The wording is read from attribution.md, never duplicated here, so a legal
wording change edits that file alone. The generators must read the file,
not copy the sentences. --self-test plants each defect class in a temp copy
and asserts every rule fires (like check-packs.py).

Run from repo root:
  python3 tests/check-persona-attribution.py              # check the real tree
  python3 tests/check-persona-attribution.py --self-test  # prove every rule fires
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTRIBUTION = ROOT / "systems" / "superintelligence" / "templates" / "attribution.md"
GENERATORS = (
    ROOT / "systems" / "superintelligence" / "ai" / "scripts" / "build_commands.py",
    ROOT / "systems" / "superintelligence" / "scripts" / "build_meta_commands.py",
)

# Banned forms in generator templates, outside a negating "never"/"do not" sentence.
BANNED = re.compile(
    r"<Name>\s+(?:says|thinks|believes|endorses|would recommend)\b"
    r"|<Name>'s view is\b"
    r"|I,\s*<Name>\b"
)
NEGATION = re.compile(r"\b(never|do not|don't|must not|without|banned)\b", re.I)

fail = 0


def fail_(msg: str) -> None:
    global fail
    print(f"  FAIL: {msg}")
    fail = 1


def pass_(msg: str) -> None:
    print(f"  PASS: {msg}")


def extract_wording(shared: str) -> tuple[str, str, str]:
    """Pull the label, the footer and the [extrapolated] rule from attribution.md."""
    label = re.search(r"\*\*<Name> persona\*\*: [^\n]*", shared)
    footer = re.search(r"^Personas are AI simulations modeled on[^\n]*", shared, re.M)
    extrap = re.search(
        r"^[^\n]*\[extrapolated\][^\n]*never put in quotation marks[^\n]*$", shared, re.M
    )
    missing = [
        name
        for name, m in (("label", label), ("footer", footer), ("[extrapolated] rule", extrap))
        if not m
    ]
    if missing:
        raise SystemExit(f"attribution.md is missing the approved {', '.join(missing)}")
    return label.group(0).strip(), footer.group(0).strip(), extrap.group(0).strip()


def banned_lines(text: str) -> list[str]:
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if BANNED.search(line) and not NEGATION.search(line):
            hits.append(f"L{n}: {line.strip()}")
    return hits


def template_defects(source: str, label: str, footer: str) -> list[str]:
    """Problems with a generator's source, given the approved wording."""
    defects = []
    if "attribution.md" not in source:
        defects.append("does not read templates/attribution.md")
    if label in source or footer in source:
        defects.append("copies the wording; read templates/attribution.md")
    hits = banned_lines(source)
    if hits:
        defects.append(f"banned form: {hits[0]}")
    return defects


def command_defects(text: str, label: str, footer: str, extrap: str) -> list[str]:
    """What an exported command is missing, given the approved wording."""
    return [
        f"missing {name}"
        for name, s in (("label", label), ("footer", footer), ("[extrapolated] rule", extrap))
        if s not in text
    ]


def run_generator(script: Path, dest: Path) -> None:
    env = os.environ.copy()
    env["COCO_SI_COMMANDS_DIR"] = str(dest)
    env.pop("COCO_SI_REPO", None)
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        fail_(f"{script.relative_to(ROOT)} exited {proc.returncode}")
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)


def check_tree() -> int:
    global fail
    fail = 0
    print("=== persona attribution ===")
    if not ATTRIBUTION.is_file():
        fail_(f"missing {ATTRIBUTION.relative_to(ROOT)}")
        return 1
    shared = ATTRIBUTION.read_text(encoding="utf-8")
    label, footer, extrap = extract_wording(shared)
    pass_("attribution.md holds the label, the footer and the [extrapolated] rule")
    for hit in banned_lines(shared):
        fail_(f"attribution.md instructs a banned form: {hit}")

    for script in GENERATORS:
        rel = script.relative_to(ROOT)
        if not script.is_file():
            fail_(f"missing generator {rel}")
            continue
        defects = template_defects(script.read_text(encoding="utf-8"), label, footer)
        for d in defects:
            fail_(f"{rel} {d}")
        if not defects:
            pass_(f"{rel} reads attribution.md and instructs no banned form")

    with tempfile.TemporaryDirectory(prefix="si-attrib-") as tmp:
        dest = Path(tmp)
        for script in GENERATORS:
            if script.is_file():
                run_generator(script, dest)
        commands = sorted(dest.glob("*.md"))
        if not commands:
            fail_("generators wrote no commands")
        else:
            if not (dest / "SI.md").is_file() or not (dest / "SI-AI-Analyse.md").is_file():
                fail_("expected SI.md (meta) and SI-AI-Analyse.md (per-team)")
            bad = {
                p.name: command_defects(p.read_text(encoding="utf-8"), label, footer, extrap)
                for p in commands
            }
            bad = {name: d for name, d in bad.items() if d}
            if bad:
                sample = list(bad.items())[:5]
                extra = f" (+{len(bad) - 5} more)" if len(bad) > 5 else ""
                detail = "; ".join(f"{name}: {'/'.join(d)}" for name, d in sample)
                fail_(f"{len(bad)} of {len(commands)} commands with wording defects: {detail}{extra}")
            else:
                pass_(
                    f"all {len(commands)} generated commands carry the label, "
                    f"the footer and the [extrapolated] rule"
                )

    print()
    if fail:
        return 1
    print("  persona attribution wording is in every generated SI command")
    return 0


def self_test() -> int:
    """Plant each defect class in a temp copy; every rule must fire."""
    label, footer, extrap = extract_wording(ATTRIBUTION.read_text(encoding="utf-8"))
    failures = 0
    with tempfile.TemporaryDirectory(prefix="si-attrib-selftest-") as tmp:
        dest = Path(tmp)
        for script in GENERATORS:  # real generated commands as the fixture
            run_generator(script, dest)
        commands = sorted(dest.glob("*.md"))
        if not commands:
            print("  FAIL: generators wrote no commands for the fixture")
            return 1
        clean_ok = all(
            not command_defects(p.read_text(encoding="utf-8"), label, footer, extrap)
            for p in commands
        ) and all(
            not template_defects(s.read_text(encoding="utf-8"), label, footer)
            for s in GENERATORS
            if s.is_file()
        )
        print(f"  {'PASS' if clean_ok else 'FAIL'}: the clean fixture passes")
        failures += not clean_ok

        # Defect: a template line with "<Name> says" and no negation.
        planted = (
            GENERATORS[0].read_text(encoding="utf-8")
            + "\nWhen asked, the command must echo that <Name> says it.\n"
        )
        ok = any("banned form" in d for d in template_defects(planted, label, footer))
        print(f"  {'PASS' if ok else 'FAIL'}: a template line with \"<Name> says\" (no negation) is rejected")
        failures += not ok
        # The same form inside a negating rule sentence is accepted.
        ok = not template_defects(
            GENERATORS[0].read_text(encoding="utf-8") + '\nNever write "<Name> says".\n',
            label,
            footer,
        )
        print(f"  {'PASS' if ok else 'FAIL'}: the same form inside a negating sentence is accepted")
        failures += not ok

        # Defects: a generated command missing one required piece.
        base = (dest / "SI.md").read_text(encoding="utf-8")
        for what, needle, expect in (
            ("missing the label", label, "label"),
            ("missing the footer", footer, "footer"),
            ("missing the [extrapolated] rule", extrap, "[extrapolated] rule"),
        ):
            defects = command_defects(base.replace(needle, ""), label, footer, extrap)
            ok = defects == [f"missing {expect}"]
            print(f"  {'PASS' if ok else 'FAIL'}: a generated command {what} is rejected")
            failures += not ok

    print("self-test:", "all rules fire" if not failures else f"{failures} rule(s) did not fire")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    return check_tree()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
