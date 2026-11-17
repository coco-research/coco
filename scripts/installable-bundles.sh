#!/usr/bin/env bash
# Print the bundles installed by default, comma-separated on one line.
#
# This is an explicit allow-list, not a scan of systems/. A scan would silently
# add any bundle that ships a SKILL.md or an agent as soon as it landed under
# systems/ — including systems/reverse-skill, a vendored reverse-engineering and
# security-testing bundle that must never be part of a default install. Naming
# the bundles here means adding one to the default set is a reviewed, one-line
# change to this file rather than an automatic side effect of adding a directory.
#
# reverse-skill is deliberately absent. It stays installable on request via
# --systems reverse-skill (see adapters/pi-desktop/install.sh --help), which the
# allow-list below has no effect on.
#
# tests/check-default-bundle-allowlist.sh gates this file: it fails if a bundle
# under systems/ ships something installable but is not accounted for here,
# so a new bundle cannot silently join (or silently fail to join) the default.
#
# Usage:
#   bash scripts/installable-bundles.sh                # prints "brain,cognee,..."
#   bash scripts/installable-bundles.sh --one-per-line

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Keep in sync with tests/check-default-bundle-allowlist.sh and with the
# supports_systems lists in adapters/*/manifest.json.
DEFAULT_BUNDLES=(gsd brain cognee hyperframes superintelligence m0)

case "${1:-}" in
  --picker-line|--all-bundles|--resolve-install|--resolve-uninstall)
    exec python3 - "$REPO_ROOT" "$1" "${2:-}" "${DEFAULT_BUNDLES[@]}" <<'PY'
import json, pathlib, sys

root, mode, csv, defaults = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4:]
packs = {}
for f in sorted((root / "systems").glob("*/pack.json")):
    d = f.parent.name
    if d == "replica":
        continue
    data = json.loads(f.read_text(encoding="utf-8"))
    if not data.get("pointer_only"):
        packs[d] = data

ordered = [(n, True) for n in defaults if n in packs and not packs[n].get("explicit_only")]
seen = {n for n, _ in ordered}
ordered += [(n, False) for n in sorted(packs) if n not in seen]

if mode == "--picker-line":
    items = [("core", True)] + [("si" if n == "superintelligence" else packs[n].get("name", n), t) for n, t in ordered]
    boxes = " ".join(f"[{'x' if t else ' '}] {lbl}" for lbl, t in items)
    sys.stdout.write(f"Packs: {boxes} · Install {sum(1 for _, t in items if t)} packs? [Y/n] ")
elif mode == "--all-bundles":
    print(",".join(n for n, _ in ordered))
else:
    aliases = {"core": "core", "si": "superintelligence", **{n: n for n in packs}, **{packs[n].get("name", n): n for n in packs}}
    tokens = [t.strip() for t in csv.split(",") if t.strip()]
    if not tokens:
        sys.exit("Error: --packs requires at least one pack name")
    out = []
    for tok in tokens:
        if tok not in aliases:
            sys.exit(f"Unknown pack: {tok}")
        if aliases[tok] not in out:
            out.append(aliases[tok])
    if mode == "--resolve-install":
        bundles = [n for n in out if n != "core"]
        print("--core-only" if not bundles else ",".join(bundles))
    else:
        print(",".join(out))
PY
    ;;
esac

ONE_PER_LINE=0
[[ "${1:-}" == "--one-per-line" ]] && ONE_PER_LINE=1

if [[ "$ONE_PER_LINE" -eq 1 ]]; then
  printf '%s\n' "${DEFAULT_BUNDLES[@]}"
else
  ( IFS=,; printf '%s\n' "${DEFAULT_BUNDLES[*]}" )
fi
