#!/usr/bin/env bash
# Hermetic verification for `.github/workflows/vendor-drift.yml` and `scripts/vendor-drift-issues.py`.
# Compatible with bash 3.2 and bash 5. Stubs `gh` in a throwaway PATH; zero network calls.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

WF="$ROOT/.github/workflows/vendor-drift.yml"
[[ -f "$WF" ]] || fail "missing $WF"
grep -q "cron: '0 10 \* \* 1'" "$WF" || fail "workflow missing weekly Mon 10:00 UTC schedule"
grep -q "workflow_dispatch:" "$WF" || fail "workflow missing workflow_dispatch trigger"
grep -q "contents: read" "$WF" || fail "workflow must stay contents: read"
grep -q "issues: write" "$WF" || fail "workflow must declare issues: write"
if grep -qE "pull-requests:\s*write|contents:\s*write|gh pr |git push" "$WF"; then
  fail "workflow must never push or open PRs"
fi

# Stub `gh` storing issues in $T/issues.json and failing if `pr` is ever called.
mkdir -p "$T/bin"
printf '[]\n' >"$T/issues.json"
cat >"$T/bin/gh" <<'PY'
#!/usr/bin/env python3
import json, os, pathlib, sys

state_dir = pathlib.Path(os.environ["STUB_GH_DIR"])
issues_path = state_dir / "issues.json"
log_path = state_dir / "gh.log"

args = sys.argv[1:]
with log_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(args) + "\n")

if not args or args[0] == "pr":
    sys.stderr.write("FORBIDDEN gh pr call\n")
    sys.exit(99)

if args[:2] == ["label", "create"]:
    sys.exit(0)

issues = json.loads(issues_path.read_text(encoding="utf-8"))
if args[:2] == ["issue", "list"]:
    print(json.dumps(issues))
    sys.exit(0)

def arg_val(flag):
    idx = args.index(flag)
    return args[idx + 1]

if args[:2] == ["issue", "create"]:
    title = arg_val("--title")
    body = pathlib.Path(arg_val("--body-file")).read_text(encoding="utf-8")
    num = len(issues) + 1
    issues.append({"number": num, "title": title, "body": body})
    issues_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    print(f"https://example.invalid/issues/{num}")
    sys.exit(0)

if args[:2] == ["issue", "edit"]:
    num = int(args[2])
    title = arg_val("--title")
    body = pathlib.Path(arg_val("--body-file")).read_text(encoding="utf-8")
    for item in issues:
        if item["number"] == num:
            item["title"] = title
            item["body"] = body
    issues_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    sys.exit(0)

sys.stderr.write(f"unexpected gh args: {args}\n")
sys.exit(2)
PY
chmod +x "$T/bin/gh"

cat >"$T/lock.json" <<'JSON'
[
  {"name": "humanizer", "repo": "https://github.com/example/humanizer", "pinned_ref": "v3.1.0", "paths": ["skills/humanizer"]},
  {"name": "current-skill", "repo": "https://github.com/example/current", "pinned_ref": "v1.0.0", "paths": ["skills/current"]}
]
JSON

cat >"$T/report-1.json" <<'JSON'
[
  {"name": "humanizer", "status": "drift", "new_ref": "v4.0.0", "changed_files": 3, "licence_changed": false, "risky_lines": 1},
  {"name": "current-skill", "status": "current", "new_ref": "", "changed_files": 0, "licence_changed": false, "risky_lines": 0}
]
JSON

DRY_OUT=$(STUB_GH_DIR="$T" PATH="$T/bin:$PATH" python3 "$ROOT/scripts/vendor-drift-issues.py" --dry-run --lock "$T/lock.json" --report "$T/report-1.json")
[[ "$DRY_OUT" == "vendor drift: 1 issue (humanizer v3.1.0 → v4.0.0) · 0 licence changes" ]] || fail "unexpected dry-run output: $DRY_OUT"
[[ ! -e "$T/gh.log" ]] || fail "--dry-run invoked gh"

OUT1=$(STUB_GH_DIR="$T" PATH="$T/bin:$PATH" python3 "$ROOT/scripts/vendor-drift-issues.py" --lock "$T/lock.json" --report "$T/report-1.json")
[[ "$OUT1" == "vendor drift: 1 issue (humanizer v3.1.0 → v4.0.0) · 0 licence changes" ]] \
  || fail "unexpected first run output: $OUT1"

# Second run with newer upstream tag updates issue #1 in place instead of opening a duplicate.
cat >"$T/report-2.json" <<'JSON'
[
  {"name": "humanizer", "status": "drift", "new_ref": "v4.1.0", "changed_files": 5, "licence_changed": true, "risky_lines": 2}
]
JSON

OUT2=$(STUB_GH_DIR="$T" PATH="$T/bin:$PATH" python3 "$ROOT/scripts/vendor-drift-issues.py" --lock "$T/lock.json" --report "$T/report-2.json")
[[ "$OUT2" == "vendor drift: 1 issue (humanizer v3.1.0 → v4.1.0) · 1 licence changes" ]] \
  || fail "unexpected second run output: $OUT2"

python3 - "$T/issues.json" <<'PY'
import json, pathlib, sys
issues = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert len(issues) == 1, f"expected 1 updated issue, got {len(issues)}"
issue = issues[0]
assert issue["title"] == "humanizer: v3.1.0 \u2192 v4.1.0", f"bad title: {issue['title']!r}"
for needle in ("`changed_files`:** `5`", "`licence_changed`:** `true`", "`risky_lines`:** `2`"):
    assert needle in issue["body"], f"missing {needle} in body"
PY

echo "$OUT1"
