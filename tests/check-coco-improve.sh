#!/usr/bin/env bash
# /coco improve end to end on the _selftest fixture, offline (--executor stub).
# A known-good proposal must be kept; a planted overfit proposal (raises dev,
# drops held-out) must be rejected at the held-out gate. Bash 3.2 safe.
#
# The stock run.stub ignores SKILL.md, so no proposal could change a score.
# The harness swaps it for a SKILL.md-aware stub, the same hook
# tests/test_skill_improve.py uses, then runs improve.py as __main__.
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
EV="$REPO/evals/skills"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# A mktemp tree holding a copy of the _selftest fixture.
mkdir -p "$T/root/skills/_selftest" "$T/root/evals/skills/_selftest/runs" \
         "$T/root/evals/routing" "$T/root/systems/superintelligence/scripts"
cp "$EV/_selftest/SKILL.md" "$T/root/skills/_selftest/SKILL.md"
cp "$EV/_selftest/grader.py" "$T/root/evals/skills/_selftest/grader.py"
cp "$EV/_selftest/items.jsonl" "$T/root/evals/skills/_selftest/items.jsonl"
# improve.py hashes these two files; their content does not matter here.
echo "# fixture" > "$T/root/evals/routing/check_regression.py"
echo "# fixture" > "$T/root/systems/superintelligence/scripts/local_http.py"

# Pad held-out to improve.py's floor of 20: 9 rows the echo already answers,
# 7 rows that need "blue". Echo rows outnumber the blue rows, so
# a change that drops the echo loses more held-out than it gains.
ITEMS="$T/root/evals/skills/_selftest/items.jsonl"
n=5
while [ "$n" -le 13 ]; do
  printf '{"id": "h%d", "split": "heldout", "input": "oak table", "expect": "oak"}\n' "$n" >> "$ITEMS"
  n=$((n + 1))
done
while [ "$n" -le 20 ]; do
  printf '{"id": "h%d", "split": "heldout", "input": "pine chair", "expect": "blue"}\n' "$n" >> "$ITEMS"
  n=$((n + 1))
done

cat > "$T/harness.py" <<'PY'
import runpy, sys
ev, mode, args = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, ev)
import run, score

def stub(skill_md, user_input, **kw):
    # Echo the input only while the skill says to; the skill text is always visible.
    echo = user_input if "verbatim" in skill_md else ""
    return "stub:" + echo + "\n" + skill_md

run.stub = stub
if mode == "baseline":
    root = args[0]
    rec = score.score_run(
        "_selftest", "heldout", "stub",
        root + "/evals/skills/_selftest/items.jsonl",
        root + "/evals/skills/_selftest/grader.py",
        root + "/skills/_selftest/SKILL.md",
        model=None, seed=score.SEED, url=run.DEFAULT_URL)
    open(root + "/evals/skills/_selftest/runs/baseline-heldout.json", "w").write(score.record_json(rec))
else:
    sys.argv = [ev + "/improve.py"] + args
    runpy.run_path(ev + "/improve.py", run_name="__main__")
PY

python3 "$T/harness.py" "$EV" baseline "$T/root"
BASE_SUM="$(cksum < "$T/root/skills/_selftest/SKILL.md")"

# Good: keeps the echo and adds the two words dev misses.
printf '# Toy skill\nRepeat the user message verbatim.\nAlso name the colour blue and the shape cube.\n' > "$T/good.md"
# Overfit: memorises every dev answer and drops the echo held-out relies on.
printf '# Toy skill\nAnswer with: red blue sphere cube.\n' > "$T/overfit.md"

round() {  # $1 proposal file, $2 out dir name
  COCO_PROPOSER_CMD="cat '$1'" COCO_ROUTER_GATE_CMD="true" \
    python3 "$T/harness.py" "$EV" round --skill _selftest --executor stub \
      --root "$T/root" --out "$T/$2" --base-ref none --max-proposals 1 \
      > "$T/$2.out" 2> "$T/$2.err" || fail "$2 round exited non-zero: $(tail -3 "$T/$2.err")"
  tail -1 "$T/$2.out"
}

GOOD="$(round "$T/good.md" good)"
case "$GOOD" in *'"outcome": "kept"'*) ;; *) fail "good proposal not kept: $GOOD" ;; esac
[ -s "$T/good/skill.diff" ] || fail "good round wrote no skill.diff"
grep -q '^+Also name the colour blue' "$T/good/skill.diff" || fail "skill.diff lacks the good edit"
echo "PASS good proposal kept"

BAD="$(round "$T/overfit.md" overfit)"
case "$BAD" in *'"outcome": "no change"'*'held-out gate not met'*) ;; *) fail "overfit proposal not rejected at the held-out gate: $BAD" ;; esac
[ ! -e "$T/overfit/skill.diff" ] || fail "overfit round wrote a skill.diff"
echo "PASS overfit proposal rejected at the held-out gate"

[ "$(cksum < "$T/root/skills/_selftest/SKILL.md")" = "$BASE_SUM" ] || fail "SKILL.md changed without --apply"
echo "PASS SKILL.md untouched without --apply"
