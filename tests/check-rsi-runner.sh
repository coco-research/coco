#!/usr/bin/env bash
# Hermetic verification for unattended RSI turn runner (`scripts/rsi-turn.sh` / `evals/skills/turn.py`).
# Compatible with bash 3.2 and bash 5. No network, no model server, no PR opened.
set -euo pipefail

SRC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
cleanup() { rm -rf "$T"; }
trap cleanup EXIT

USER_HOME="$T/userdir"
REPO="$T/repo"
BIN="$T/bin"
mkdir -p "$USER_HOME" "$REPO" "$BIN"

fail() { echo "FAIL: $*" >&2; exit 1; }

# Guard against any accidental `gh` invocation in tests.
cat > "$BIN/gh" <<EOF
#!/bin/sh
touch "$T/gh-called"
exit 99
EOF
chmod +x "$BIN/gh"

# Copy the real evals harness and runner into the throwaway repo.
for rel in \
  evals/paired.py \
  evals/skills/score.py \
  evals/skills/run.py \
  evals/skills/improve.py \
  evals/skills/turn.py \
  evals/routing/check_regression.py \
  systems/superintelligence/scripts/local_http.py \
  scripts/rsi-turn.sh
do
  mkdir -p "$REPO/$(dirname "$rel")"
  cp "$SRC_ROOT/$rel" "$REPO/$rel"
done
chmod +x "$REPO/scripts/rsi-turn.sh"

# Offline stub executor: reacts deterministically to SKILL.md rules and split tags.
cat > "$T/stub_exec.py" <<'PY'
def stub(skill_md, user_input, **kw):
    if "- rule: good" in skill_md:
        return "GOOD_HIT"
    if "- mode: overfit-dev" in skill_md:
        return "GOOD_HIT" if "split:dev" in user_input else "BAD_MISS"
    if "- mode: balanced" in skill_md:
        return "BAD_MISS" if "split:dev" in user_input else "GOOD_HIT"
    return "BAD_MISS"
PY

# Offline stub proposer: proposes a genuine improvement for `humanizer`, an overfit edit
# (dev up, held-out down) for `overfit`, and a non-improving edit for the other 3 skills.
cat > "$T/stub_proposer.py" <<'PY'
import sys

prompt = sys.stdin.read()
start = prompt.find("<skill_md>\n")
end = prompt.find("\n</skill_md>")
base = prompt[start + len("<skill_md>\n"):end] if (start >= 0 and end > start) else ""

if "name: humanizer" in base:
    cand = base.replace("- rule: base", "- rule: good")
elif "name: overfit" in base:
    cand = base.replace("- mode: balanced", "- mode: overfit-dev")
else:
    cand = base.replace("- rule: base", "- rule: neutral")

sys.stdout.write("````\n" + cand.rstrip("\n") + "\n````\n")
PY

# Seed 5 baseline-ready skills + 1 unbaselined skill (`writing-plans` without runs/).
python3 - "$REPO" "$T/stub_exec.py" <<'PY'
import importlib.util
import json
import pathlib
import subprocess
import sys

repo = pathlib.Path(sys.argv[1]).resolve()
stub_path = pathlib.Path(sys.argv[2]).resolve()

sys.path.insert(0, str(repo / "evals" / "skills"))
import run  # noqa: E402
import score  # noqa: E402

score.ROOT = repo
spec = importlib.util.spec_from_file_location("_seed_stub", str(stub_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
run.stub = mod.stub

GRADER = (
    "def grade(item, output):\n"
    "    ok = item['want'] in output\n"
    "    return {'score': 1.0 if ok else 0.0, 'notes': ['ok' if ok else 'miss: need ' + item['want']]}\n"
)

skills = [
    ("c4-architecture", "- rule: base"),
    ("code-verification", "- rule: base"),
    ("humanizer", "- rule: base"),
    ("overfit", "- mode: balanced"),
    ("prd-generator", "- rule: base"),
]

for name, marker in skills:
    sdir = repo / "skills" / name
    edir = repo / "evals" / "skills" / name
    sdir.mkdir(parents=True, exist_ok=True)
    (edir / "runs").mkdir(parents=True, exist_ok=True)
    (sdir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Fixture {name}.\n---\n# {name}\n\nGuidance:\n{marker}\n",
        encoding="utf-8",
    )
    (edir / "grader.py").write_text(GRADER, encoding="utf-8")
    rows = []
    for i in range(1, 5):
        rows.append({"id": f"d{i}", "split": "dev", "input": f"split:dev case:{name}:{i}", "want": "GOOD_HIT"})
    for i in range(1, 21):
        rows.append({"id": f"h{i}", "split": "heldout", "input": f"split:heldout case:{name}:{i}", "want": "GOOD_HIT"})
    (edir / "items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

# Unbaselined skill (items.jsonl + grader.py, no runs/): must be skipped cleanly.
wp_s = repo / "skills" / "writing-plans"
wp_e = repo / "evals" / "skills" / "writing-plans"
wp_s.mkdir(parents=True, exist_ok=True)
wp_e.mkdir(parents=True, exist_ok=True)
(wp_s / "SKILL.md").write_text("---\nname: writing-plans\ndescription: Unbaselined.\n---\n# WP\n", encoding="utf-8")
(wp_e / "grader.py").write_text(GRADER, encoding="utf-8")
(wp_e / "items.jsonl").write_text(json.dumps({"id": "d1", "split": "dev", "input": "x", "want": "GOOD_HIT"}) + "\n", encoding="utf-8")

subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
subprocess.run(
    ["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "seed"],
    check=True,
)

for name, _ in skills:
    edir = repo / "evals" / "skills" / name
    sfile = repo / "skills" / name / "SKILL.md"
    rec = score.score_run(
        name, "heldout", "stub", edir / "items.jsonl", edir / "grader.py", sfile,
        model=None, seed=score.SEED, url=run.DEFAULT_URL,
    )
    (edir / "runs" / "baseline-heldout.json").write_text(score.record_json(rec), encoding="utf-8")

subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
subprocess.run(
    ["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "baselines"],
    check=True,
)
subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
PY

TURN_OUT="$(
  HOME="$USER_HOME" \
  PATH="$BIN:$PATH" \
  COCO_PROPOSER_CMD="python3 $T/stub_proposer.py" \
  COCO_ROUTER_GATE_CMD="python3 -c pass" \
  bash "$REPO/scripts/rsi-turn.sh" \
    --root "$REPO" \
    --executor stub \
    --stub-script "$T/stub_exec.py" \
    --max-proposals 1
)"

EXPECTED_TURN="turn: 5 skills · kept 1 (humanizer) · rejected 1 (overfit) · no change 3"
[ "$TURN_OUT" = "$EXPECTED_TURN" ] || fail "unexpected turn output: $TURN_OUT"
[ ! -e "$T/gh-called" ] || fail "runner invoked gh pr create in test"

# Verify ledger records, branch creation for kept change, and rejection of overfit change.
python3 - "$REPO" <<'PY'
import json
import pathlib
import subprocess
import sys

repo = pathlib.Path(sys.argv[1])
for s in ("c4-architecture", "code-verification", "humanizer", "overfit", "prd-generator"):
    rfile = repo / "evals" / "skills" / "_rounds" / s / "r001.json"
    assert rfile.is_file(), f"missing {rfile}"
    rec = json.loads(rfile.read_text(encoding="utf-8"))
    assert rec["schema"] == 1 and rec["round"] == "r001", f"bad header in {s}"

hum = json.loads((repo / "evals/skills/_rounds/humanizer/r001.json").read_text(encoding="utf-8"))
assert hum["outcome"] == "kept" and hum["gate"]["peek"]["delta"] > 0, "humanizer not kept"

ovf = json.loads((repo / "evals/skills/_rounds/overfit/r001.json").read_text(encoding="utf-8"))
assert ovf["outcome"] == "no change" and ovf["peek_count"] == 1 and ovf["gate"]["peek"]["delta"] < 0, "overfit not rejected at heldout"

branches = subprocess.run(["git", "-C", str(repo), "branch", "--list", "rsi/*"], capture_output=True, text=True, check=True).stdout
assert "rsi/humanizer-r001" in branches, f"missing kept branch in {branches!r}"
assert "overfit" not in branches, f"unexpected branch for rejected overfit in {branches!r}"

kept_skill = subprocess.run(
    ["git", "-C", str(repo), "show", "rsi/humanizer-r001:skills/humanizer/SKILL.md"],
    capture_output=True, text=True, check=True,
).stdout
assert "- rule: good" in kept_skill, "kept branch lacks updated SKILL.md"
assert "- rule: base" in (repo / "skills/humanizer/SKILL.md").read_text(encoding="utf-8"), "working tree SKILL.md was mutated"

# Verify --open-pr stays off by default, and a kept round turned into rejected at held-out
# updates the ledger record with outcome="no change" and the rejection reason.
sys.path.insert(0, str(repo / "evals" / "skills"))
import improve  # noqa: E402
import turn  # noqa: E402

parsed = turn.build_parser().parse_args([])
assert parsed.open_pr is False, "--open-pr must default to False"

orig_improve_main = improve.main
try:
    def fake_kept_below_baseline(argv):
        rfile = repo / "evals" / "skills" / "_rounds" / "overfit" / "r002.json"
        rfile.parent.mkdir(parents=True, exist_ok=True)
        rfile.write_text(json.dumps({
            "schema": 1,
            "round": "r002",
            "skill": "overfit",
            "outcome": "kept",
            "reason": "held-out delta +0.050, p 0.010, n 20",
            "peek_count": 1,
            "gate": {"peek": {"cand_mean": 0.45, "base_mean": 0.50, "delta": -0.05}},
        }, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"skill": "overfit", "round": "r002", "outcome": "kept"}))

    improve.main = fake_kept_below_baseline
    args = turn.build_parser().parse_args(["--root", str(repo), "--executor", "stub"])
    status, rid, branch = turn.run_one_skill(repo, "overfit", args)
    assert (status, rid, branch) == ("rejected", "r002", None), f"expected rejected round, got {(status, rid, branch)}"
    rewritten = json.loads((repo / "evals/skills/_rounds/overfit/r002.json").read_text(encoding="utf-8"))
    assert rewritten["outcome"] == "no change", f"expected ledger outcome 'no change', got {rewritten['outcome']!r}"
    assert rewritten["reason"] == "held-out gate not met: cand 0.450 < base 0.500", f"unexpected ledger reason: {rewritten['reason']!r}"
    branches_after = subprocess.run(["git", "-C", str(repo), "branch", "--list", "rsi/overfit-*"], capture_output=True, text=True, check=True).stdout
    assert not branches_after.strip(), f"unexpected branch created for rejected round: {branches_after!r}"
finally:
    improve.main = orig_improve_main
PY

# Verify RSI.OFF stops the runner before any proposer or model call and exits 0 with "off".
cat > "$T/fail_proposer.py" <<EOF
import pathlib, sys
pathlib.Path("$T/proposer-called").write_text("1")
sys.exit(99)
EOF
touch "$REPO/RSI.OFF"

OFF_OUT="$(
  HOME="$USER_HOME" \
  PATH="$BIN:$PATH" \
  COCO_PROPOSER_CMD="python3 $T/fail_proposer.py" \
  bash "$REPO/scripts/rsi-turn.sh" --root "$REPO" --executor stub
)"
[ ! -e "$T/proposer-called" ] || fail "proposer ran despite RSI.OFF"
printf '%s\n' "$OFF_OUT" | grep -q "off" || fail "RSI.OFF output missing 'off': $OFF_OUT"

echo "${TURN_OUT} · RSI.OFF honoured"
