#!/usr/bin/env bash
# Aider .aider.conf.yml keys must all be real aider option names.
# Repro: adapters/aider/install.sh wrote git_commit_format / auto_commits /
# read_only_files; aider reads the YAML via configargparse, unknown keys become
# CLI args, and aider refuses to start (unrecognized arguments).
# Runs the installer in a temp dir — never the repo root — because the
# installer writes AGENTS.md and .aider.conf.yml into the current directory.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)

tmp=$(mktemp -d)
mkdir -p "$tmp/home"
trap 'rm -rf "$tmp"' EXIT

(cd "$tmp" && HOME="$tmp/home" bash "$ROOT/adapters/aider/install.sh" >/dev/null)

CONF="$tmp/.aider.conf.yml"
if [[ ! -f "$CONF" ]]; then
  echo "FAIL: installer did not create $CONF"
  exit 1
fi

python3 - "$CONF" <<'PY'
import sys, yaml

with open(sys.argv[1]) as f:
    conf = yaml.safe_load(f)

if not isinstance(conf, dict):
    print(f"FAIL: .aider.conf.yml does not parse to a dict: {conf!r}")
    sys.exit(1)

# Real aider long options, subset of https://aider.chat/assets/sample.aider.conf.yml
ALLOWED = {
    "auto-commits", "read", "file", "model", "dirty-commits",
    "attribute-author", "attribute-committer", "commit-prompt",
    "lint-cmd", "test-cmd", "auto-lint", "auto-test",
    "git", "gitignore", "yes-always", "dark-mode", "light-mode",
    "map-tokens", "edit-format", "weak-model", "subtree-only",
    "show-diffs", "vim", "cache-prompts", "check-update", "analytics",
}

for k in ("git_commit_format", "auto_commits", "read_only_files"):
    if k in conf:
        print(f"FAIL: .aider.conf.yml contains a key aider does not recognize: {k}")
        sys.exit(1)

bad_underscore = sorted(k for k in conf if "_" in k)
if bad_underscore:
    print(f"FAIL: .aider.conf.yml has underscore keys (aider options use dashes): {', '.join(bad_underscore)}")
    sys.exit(1)

bad_unknown = sorted(k for k in conf if k not in ALLOWED)
if bad_unknown:
    print(f"FAIL: .aider.conf.yml has keys that are not real aider options: {', '.join(bad_unknown)}")
    sys.exit(1)

if conf.get("auto-commits") is not True:
    print(f"FAIL: auto-commits must be true, got: {conf.get('auto-commits')!r}")
    sys.exit(1)

read = conf.get("read")
if not isinstance(read, list) or "AGENTS.md" not in read:
    print(f"FAIL: read must be a list containing AGENTS.md, got: {read!r}")
    sys.exit(1)

print("PASS: .aider.conf.yml keys are valid aider options")
PY
