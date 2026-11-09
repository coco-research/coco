#!/usr/bin/env bash
# Guard: scripts/employer-scan.py exempts exactly one line per allowlist entry, once,
# and still fails closed. The pattern is synthetic; no real word appears here.
set -euo pipefail
cd "$(dirname "$0")/.."

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

if command -v shasum >/dev/null 2>&1; then
  hash_line() { printf '%s' "$1" | shasum -a 256 | awk '{print $1}'; }
else
  hash_line() { printf '%s' "$1" | sha256sum | awk '{print $1}'; }
fi

tree="$tmp/tree"
mkdir -p "$tree"
patterns="$tmp/patterns.txt"
printf '%s\n' 'zqxjvlorp' > "$patterns"
chmod 600 "$patterns"
allow="$tmp/allowlist.txt"

cited='Cited title: The Zqxjvlorp Review'
printf '%s  %s\n' "$(hash_line "$cited")" 'a.md' > "$allow"

: > "$tmp/log.txt"
out=""
err=""
rc=0

run() {  # run [patterns] [allowlist] [root]: capture stdout, stderr and the exit code
  local p="${1:-$patterns}" a="${2:-$allow}" r="${3:-$tree}"
  set +e
  out="$(python3 scripts/employer-scan.py --patterns "$p" --allowlist "$a" "$r" 2>"$tmp/err.txt")"
  rc=$?
  set -e
  err="$(cat "$tmp/err.txt")"
  printf '%s\n%s\n' "$out" "$err" >> "$tmp/log.txt"
}

fail=0
ok() { echo "  PASS: $1"; }
bad() { echo "  FAIL: $1"; fail=1; }
expect() { if [ "$rc" -eq "$1" ]; then ok "$2 (exit $1)"; else bad "$2: expected exit $1, got $rc"; fi; }
a_md() { printf '%s\n' "$@" > "$tree/a.md"; }

# a. The allowlisted line is exempt.
a_md "$cited" 'a clean line'
run
expect 0 "allowlisted line passes"
if [ -z "$out" ]; then ok "clean run prints no hits"; else bad "clean run prints no hits: $out"; fi
if printf '%s' "$err" | grep -Fq '0 hit(s) for 1 pattern(s), 1 allowlisted line(s) skipped'; then
  ok "summary counts the exemption"
else
  bad "summary counts the exemption: $err"
fi

# b. A one-character edit to the allowlisted line is a new line: it fails.
a_md 'Cited title: The Zqxjvlorp Reviex' 'a clean line'
run
expect 1 "a changed allowlisted line fails"
if printf '%s' "$out" | grep -Fq 'pattern 1 at a.md:'; then
  ok "the changed line is reported"
else
  bad "the changed line is reported: $out"
fi

# c. A new hit line beside the allowlisted one and d. a duplicate both fail.
a_md "$cited" 'a clean line' 'zqxjvlorp again'
run
expect 1 "an added hit line fails"
a_md "$cited" "$cited" 'a clean line'
run
expect 1 "a second identical copy of the allowlisted line fails"

# e. The entry names a.md, so the same line in b.md is not exempt.
a_md "$cited" 'a clean line'
printf '%s\n' "$cited" > "$tree/b.md"
run
expect 1 "the allowlisted line in another file fails"
rm -f "$tree/b.md"

# f. The scan still fails closed on the patterns file.
run "$tmp/missing-patterns.txt"
expect 2 "missing patterns file fails closed"
printf '%s\n' '# comment only' > "$tmp/empty-patterns.txt"
chmod 600 "$tmp/empty-patterns.txt"
run "$tmp/empty-patterns.txt"
expect 2 "empty patterns file fails closed"

# f2. The scan fails closed when it cannot walk the tree.
run "$patterns" "$allow" "$tmp/no-such-dir"
expect 2 "missing root fails closed"
run "$patterns" "$allow" "$patterns"
expect 2 "a file as root fails closed"

# g. A malformed allowlist line fails closed and names the line.
printf '%s\n' 'not an allowlist entry' > "$tmp/bad-allowlist.txt"
run "$patterns" "$tmp/bad-allowlist.txt"
expect 2 "malformed allowlist line fails closed"
if printf '%s' "$err" | grep -Fq 'employer-scan: FAIL (closed): bad allowlist line 1'; then
  ok "malformed allowlist names the line"
else
  bad "malformed allowlist names the line: $err"
fi

# h. No run may echo the pattern text, in any case.
if grep -qi 'zqxjvlorp' "$tmp/log.txt"; then
  bad "no run printed the pattern text (stdout or stderr)"
  grep -in 'zqxjvlorp' "$tmp/log.txt"
else
  ok "no run printed the pattern text (stdout or stderr)"
fi

# i. The repo's own allowlist entries are well formed.
bad_entries="$(grep -Ev '^$|^#' scripts/employer-scan-allowlist.txt | grep -Ev '^[0-9a-f]{64}  [^ ].*$' || true)"
if [ -z "$bad_entries" ]; then
  ok "repo allowlist entries are well formed"
else
  bad "repo allowlist entries are well formed:"
  printf '%s\n' "$bad_entries"
fi

if [ "$fail" -ne 0 ]; then
  echo "check-employer-scan: FAIL"
  exit 1
fi
echo "check-employer-scan: OK"
