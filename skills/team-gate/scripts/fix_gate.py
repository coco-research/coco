#!/usr/bin/env python3
"""Aggregate the fix-pipeline gates into a single verdict, and answer
whether a given stage of that pipeline may open. Same shape as
ship_gate.py, scaled to the /team:fix pipeline instead of /team:ship.

Subcommands:
  check --repo-root DIR [--json]
      "May this fix run be considered done?" Reads every required gate
      file the wave-two scripts write for this run, plus the receipt
      chain. Writes this pipeline's own gate file and appends its
      gate-result receipt. Prints one line per failing item in the form
      "<stage>: <file or receipt>: <reason>" and exits 0 (PASS or
      PASS_WITH_OVERRIDE), 1 (BLOCK), or 2 (fix_gate itself could not
      measure). With --json, the stage rows are also printed as JSON.
  stage N --repo-root DIR
      A pure query: "may fix-pipeline stage N's artifact be written
      now?" Writes nothing. Checks only that stages 1..N-1 already
      satisfy their own required gates. Prints one JSON object
      {"stage", "allowed", "missing", "failing", "overridden", "reason"}
      and exits 0 when allowed, 1 when not, 2 when unmeasurable.
  --self-test
      Regenerates the fixtures under fixtures/fix_gate/ and exercises
      both subcommands against each one.

Exit contract: 0 = PASS or PASS_WITH_OVERRIDE, 1 = BLOCK, 2 = UNRUNNABLE.
Exit 2 is reserved for fix_gate's own inability to measure: the run
directory, run.json, HEAD, or the receipt chain file are unreadable. A
required gate file that itself exited 2 is reported as UNVERIFIED and
blocks the run like any other failure; it never raises fix_gate's own
exit 2.

Stage list, derived from commands/team/fix.md and REVIEW-OPUS.md section
1.16 (1.16 wins where the two disagree), and fixed to the required-gates
list in WAVE3-BRIEFS.md's Task 12b, which is authoritative for what this
script actually checks:

  0 map           gates/handoff-1-map.json The brownfield repository map,
                  the first step of the pipeline. Written by
                  brownfield_map.py at the start of the run before any
                  commit. Head comparison is special for this stage: the
                  recorded head must be an ancestor of the current HEAD
                  (computed with git merge-base --is-ancestor), since the
                  map is written at run start before any fix work.
  1 discover      gates/7-discover.json   fix.md:46 "Run the authoritative
                  gate per the Test Evidence Protocol"; 1.16 F6 "The
                  authoritative gate ran per the evidence protocol".
                  Written by run_gate.py discover.
  2 run           gates/8.json            Same fix.md:46 / F6 citation.
                  Written by run_gate.py run.
  3 red-green     gates/9.json            fix.md:45 "write a failing test
                  first...prove it is RED for the right reason...then
                  fix, then prove it is GREEN"; 1.16 F5 "A failing
                  regression test comes first, red for the right reason,
                  then green". Written by prove_red.py prove.
  4 recheck       gates/9-recheck.json    WAVE3-BRIEFS.md Task 12b names
                  this gate directly. The mechanism is the AST re-hash
                  from PLAN.md section 4, "Red for the right reason":
                  "the test function's AST is hashed at red-proof time
                  and rechecked at green and at Stage 11". 1.16 F11
                  "Coverage for the fixed path is confirmed against
                  EVIDENCE.md, not test descriptions" names the intent
                  this stage serves, through a verify-check subcommand
                  that does not exist in this build; cite F11 for the
                  intent only, not the mechanism, which is the AST
                  rehash, not coverage attribution. Written by
                  prove_red.py recheck. This stage also enforces that
                  its own gate-result receipt is not older than
                  gates/9.json's, since a recheck cannot vouch for a
                  proof that ran after it.
  5 matrix        gates/11-matrix.json    Neither fix.md nor 1.16 names a
                  distinct matrix gate; carried over unchanged from
                  claim_evidence.py's matrix subcommand because
                  WAVE3-BRIEFS.md Task 12b's required-gates list is
                  authoritative and names it explicitly.
  6 evidence-check gates/12.json          Neither fix.md nor 1.16 names
                  this gate either. It is the ship pipeline's
                  claim-against-evidence gate (REVIEW-OPUS.md 1.9,
                  ship.md:154-156), carried into the fix pipeline
                  unchanged by WAVE3-BRIEFS.md Task 12b, the same
                  reasoning as stage 5. Written by claim_evidence.py
                  check.

This is a strict subset of ship_gate.py's fourteen stages: no handoff
docs (fix.md has no document handoff chain), no parity or coverage gate
(gates/7.json, gates/10.json), no independent-verifier gate
(gates/8-verifier.json, gates/11.json), no CI-mirror stage, and no final
render_evidence check, because /team:fix produces commits, not a pull
request.

Overrides, the receipt chain, head comparison, block receipts, and
gate-timeout receipts behave exactly as in ship_gate.py: an override
receipt naming a required gate by its key or its stage number covers a
missing or failing gate and yields PASS_WITH_OVERRIDE; a broken chain or
a block receipt can never be overridden. An override receipt that never
matched a missing or failing gate is unused; it is listed under
gates/fix.json's "unused_overrides" and printed as one "unused override:
<gate>" line on stdout, and it never changes the verdict, exactly as in
ship_gate.py.

When gates/9.json itself blocks (state "failed", not missing or
UNVERIFIED), the printed line and the row's own reason name the first
test in its "tests" list whose verdict is BLOCK, by nodeid and by why it
blocked (its red class, or "green-fails" when the green run itself
failed): "3: gates/9.json: BLOCK (exit 1): tests/test_x.py::test_y
never-red".

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) puts this
script's own directory first, so `import gate_state` and `import
ship_gate` resolve to the committed scripts next to this one. Several
generic helpers (_read_receipts, _scan_receipts, _override_for,
_read_json_file, _evaluate_gate_item, _atomic_write_json, and the
Unmeasurable exception) are shared by importing them from ship_gate
rather than being redefined here. _override_for now takes a `used: set`
argument (ship_gate's own current shape); this script passes one
`used_overrides` set per check or stage run so an override that matched
nothing can be reported.

A seventh row named "rounds" follows the stage rows: it reads
build_rounds from gate_state.derive_status (stage-opened receipts for
stage 6) and exits 1 when more than three build rounds have opened,
with the reason "build_rounds <n> exceeds 3". An override receipt naming
gate "rounds" covers it like any other row and the verdict becomes
PASS_WITH_OVERRIDE. The row's "stage" key carries the string "rounds".

No em dash, no section sign, stdlib only, exit() called only in the main guard.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state
import ship_gate


# (stage, key, path relative to the run directory). key is the identifier an
# override receipt names to cover this one file; the stage number as a
# string is always accepted too.
FIX_REQUIRED_GATES: List[Tuple[int, str, str]] = [
    (0, "map", "gates/handoff-1-map.json"),
    (1, "7-discover", "gates/7-discover.json"),
    (2, "8", "gates/8.json"),
    (3, "9", "gates/9.json"),
    (4, "9-recheck", "gates/9-recheck.json"),
    (5, "11-matrix", "gates/11-matrix.json"),
    (6, "12", "gates/12.json"),
]
FIX_STAGE_NAMES: Dict[int, str] = {
    0: "map", 1: "discover", 2: "run", 3: "red-green", 4: "recheck",
    5: "matrix", 6: "evidence-check",
}
FIX_STAGE_COUNT = 7


# ---------------------------------------------------------------------------
# Context resolution (own copy: the literal "git rev-parse HEAD" call lives
# here rather than only inside ship_gate, since this script must be able to
# resolve HEAD on its own).
# ---------------------------------------------------------------------------

def _git_head(path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    head = result.stdout.strip()
    return head or None


def _resolve(repo_root_arg: str) -> Tuple[Path, Path, str]:
    """Resolve (repo_root, run_dir, head) or raise ship_gate.Unmeasurable."""
    repo_root = Path(repo_root_arg).resolve()

    run_dir = gate_state.find_run(repo_root)
    if run_dir is None:
        raise ship_gate.Unmeasurable(f"no active run found under {repo_root}")

    run_json_path = run_dir / "run.json"
    try:
        run_obj = json.loads(run_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ship_gate.Unmeasurable(f"run.json unreadable: {exc}")

    head_cwd = _git_head(repo_root)
    if head_cwd is None:
        raise ship_gate.Unmeasurable(f"cannot resolve HEAD for {repo_root}")

    recorded_root_str = run_obj.get("repo_root")
    if recorded_root_str:
        recorded_root = Path(recorded_root_str)
        head_recorded = _git_head(recorded_root)
        if head_recorded is None:
            raise ship_gate.Unmeasurable(f"cannot resolve HEAD for {recorded_root}")
        if head_recorded != head_cwd:
            raise ship_gate.Unmeasurable(
                f"head mismatch: run.json repo_root {recorded_root} is at "
                f"{head_recorded}, {repo_root} is at {head_cwd}"
            )

    return repo_root, run_dir, head_cwd


# ---------------------------------------------------------------------------
# Per-stage evaluation
# ---------------------------------------------------------------------------

def _latest_gate_seqs(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Highest seq of any gate-result receipt, keyed by gate_file. Mirrors
    gate_state.verify_chain's own "latest wins" grouping, done here again
    because fix_gate needs the seq value itself, not just the winner."""
    latest: Dict[str, int] = {}
    for record in records:
        if record.get("kind") != "gate-result":
            continue
        detail = record.get("detail") or {}
        gate_file = detail.get("gate_file")
        seq = record.get("seq")
        if not gate_file or not isinstance(seq, int):
            continue
        if gate_file not in latest or seq > latest[gate_file]:
            latest[gate_file] = seq
    return latest


def _is_ancestor(recorded_head: str, current_head: str, repo_root: Path) -> bool:
    """Check if recorded_head is an ancestor of current_head using
    git merge-base --is-ancestor. Returns False on error."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor",
             recorded_head, current_head],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _recheck_order_reason(records: List[Dict[str, Any]]) -> Optional[str]:
    """None when gates/9-recheck.json's latest gate-result receipt has a
    higher seq than gates/9.json's; otherwise the block reason naming
    both seqs. None also when either gate has no gate-result receipt at
    all, since that is an ordinary missing-file condition instead."""
    seqs = _latest_gate_seqs(records)
    proof_seq = seqs.get("gates/9.json")
    recheck_seq = seqs.get("gates/9-recheck.json")
    if proof_seq is None or recheck_seq is None:
        return None
    if recheck_seq > proof_seq:
        return None
    return f"recheck predates the proof it rechecks (seq {recheck_seq} before seq {proof_seq})"


def _first_block_test_descriptor(gate9_data: Optional[Dict[str, Any]]) -> Optional[str]:
    """"<nodeid> <why>" for the first test in gates/9.json's "tests" list
    whose verdict is BLOCK, or None when there is no such test (or the
    file could not be read). "why" is the test's red class (never-red,
    invalid-red) when that is why it blocked, else "green-fails"."""
    if not gate9_data:
        return None
    for test in gate9_data.get("tests", []):
        if test.get("verdict") != "BLOCK":
            continue
        nodeid = test.get("nodeid")
        red = test.get("red") or {}
        red_class = red.get("class")
        if red_class in ("never-red", "invalid-red"):
            why = red_class
        else:
            green = test.get("green") or {}
            why = "green-fails" if green.get("outcome") != "pass" else (red_class or "block")
        return f"{nodeid} {why}" if nodeid else why
    return None


def _evaluate_rounds(
    run_dir: Path, overrides: List[Dict[str, Any]], used: set
) -> Tuple[Dict[str, Any], Optional[Tuple[Union[int, str], str, str]], Optional[Tuple[Union[int, str], str, Dict[str, Any]]]]:
    """Evaluate the build rounds limit. Returns (row, blocking, override).

    The "rounds" row checks that build_rounds does not exceed 3.
    It is overridable by an override naming "rounds".
    """
    derive = gate_state.derive_status(run_dir)
    build_rounds = derive.get("build_rounds", 0)

    row_exit = 1 if build_rounds > 3 else 0
    reason = f"build_rounds {build_rounds} exceeds 3" if build_rounds > 3 else f"build_rounds {build_rounds}"

    override = ship_gate._override_for(overrides, used, "rounds")
    if override:
        row = {
            "stage": "rounds", "required": True, "present": True,
            "exit": 0, "head_ok": True, "overridden": True,
            "reason": f"OVERRIDDEN: {override.get('instruction', '')}",
        }
        return row, None, ("rounds", "derive_status", override)

    if row_exit == 0:
        row = {
            "stage": "rounds", "required": True, "present": True,
            "exit": 0, "head_ok": True, "overridden": False,
            "reason": reason,
        }
        return row, None, None

    row = {
        "stage": "rounds", "required": True, "present": True,
        "exit": 1, "head_ok": True, "overridden": False,
        "reason": reason,
    }
    return row, ("rounds", "derive_status", reason), None


def _compute_stages(
    run_dir: Path, head: str, repo_root: Path, overrides: List[Dict[str, Any]], used: set,
    records: List[Dict[str, Any]],
) -> Tuple[
    Dict[Union[int, str], Dict[str, Any]],
    List[Tuple[Union[int, str], str, str]],
    List[Tuple[Union[int, str], str, str]],
    List[Tuple[Union[int, str], str, Dict[str, Any]]],
]:
    """Evaluate every one of the seven fix-pipeline stages.

    Returns (stage_rows, unconditional, blocking, overridden_detail), where
    unconditional and blocking are lists of (stage, file, reason) and
    overridden_detail is a list of (stage, key, override_receipt_detail).
    """
    stage_rows: Dict[int, Dict[str, Any]] = {}
    unconditional: List[Tuple[int, str, str]] = []
    blocking: List[Tuple[int, str, str]] = []
    overridden_detail: List[Tuple[int, str, Dict[str, Any]]] = []

    for stage, key, relpath in FIX_REQUIRED_GATES:
        name = FIX_STAGE_NAMES.get(stage)
        label = f"{name}: " if name else ""
        info = ship_gate._evaluate_gate_item(run_dir, relpath, head)
        state = info["state"]

        # For stage 0 (map), special head rule: recorded head must be ancestor of HEAD
        if stage == 0 and state == "head-drift":
            recorded = info.get("head")
            if recorded and _is_ancestor(recorded, head, repo_root):
                state = "ok"

        order_reason = None
        if relpath == "gates/9-recheck.json" and state not in ("missing", "head-drift"):
            order_reason = _recheck_order_reason(records)

        if state == "head-drift":
            reason = f"head drift: {relpath} recorded {info['head']}, HEAD is {head}"
            unconditional.append((stage, relpath, reason))
            stage_rows[stage] = {
                "stage": stage, "required": [relpath], "present": False,
                "exit": info["exit"], "head_ok": False, "overridden": False,
                "reason": label + reason,
            }
            continue

        if state == "ok" and order_reason is None:
            stage_rows[stage] = {
                "stage": stage, "required": [relpath], "present": True,
                "exit": 0, "head_ok": True, "overridden": False,
                "reason": label + "PASS",
            }
            continue

        override = ship_gate._override_for(overrides, used, key, str(stage))
        if override:
            overridden_detail.append((stage, key, override))
            stage_rows[stage] = {
                "stage": stage, "required": [relpath], "present": True,
                "exit": 0, "head_ok": True, "overridden": True,
                "reason": label + "OVERRIDDEN",
            }
            continue

        if order_reason is not None:
            reason = f"{relpath}: {order_reason}"
            blocking.append((stage, relpath, order_reason))
            row_exit: Optional[int] = 1
        elif state == "missing":
            reason = f"{relpath}: missing"
            blocking.append((stage, relpath, "missing"))
            row_exit = None
        elif state == "unverified":
            reason = f"{relpath}: UNVERIFIED (exit 2)"
            blocking.append((stage, relpath, "UNVERIFIED (exit 2)"))
            row_exit = 2
        else:
            descriptor = None
            if relpath == "gates/9.json":
                descriptor = _first_block_test_descriptor(ship_gate._read_json_file(run_dir / relpath))
            block_text = f"BLOCK (exit {info['exit']})"
            if descriptor:
                block_text = f"{block_text}: {descriptor}"
            reason = f"{relpath}: {block_text}"
            blocking.append((stage, relpath, block_text))
            row_exit = info["exit"]

        stage_rows[stage] = {
            "stage": stage, "required": [relpath], "present": False,
            "exit": row_exit, "head_ok": True, "overridden": False,
            "reason": label + reason,
        }

    return stage_rows, unconditional, blocking, overridden_detail


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def cmd_check(repo_root_arg: str, json_output: bool) -> int:
    try:
        repo_root, run_dir, head = _resolve(repo_root_arg)

        chain_result = gate_state.verify_chain(run_dir)
        if chain_result.status == "unrunnable":
            raise ship_gate.Unmeasurable(f"receipt chain unreadable: {chain_result.reason}")

        records = ship_gate._read_receipts(run_dir)
        if records is None:
            raise ship_gate.Unmeasurable("receipts.jsonl unreadable")
    except ship_gate.Unmeasurable as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        return 2

    _approval_present, block_receipts, overrides = ship_gate._scan_receipts(records)
    used_overrides: set = set()

    stage_rows, unconditional, blocking, overridden_detail = _compute_stages(
        run_dir, head, repo_root, overrides, used_overrides, records,
    )

    rounds_row, rounds_blocking, rounds_override = _evaluate_rounds(run_dir, overrides, used_overrides)
    stage_rows["rounds"] = rounds_row
    if rounds_blocking:
        blocking.append(rounds_blocking)
    if rounds_override:
        overridden_detail.append(rounds_override)

    if chain_result.status == "broken":
        unconditional.append((0, "receipts.jsonl", f"chain broken: {chain_result.reason}"))
    for detail in block_receipts:
        reason = detail.get("reason", "block receipt present")
        unconditional.append((0, "receipts.jsonl", f"block receipt: {reason}"))

    unconditional_lines = [f"{stage}: {name}: {reason}" for stage, name, reason in unconditional]
    blocking_lines = [f"{stage}: {name}: {reason}" for stage, name, reason in blocking]
    all_lines = unconditional_lines + blocking_lines

    has_hard_block = bool(unconditional) or any(
        "UNVERIFIED" not in reason for _, _, reason in blocking
    )
    has_unverified_only = bool(blocking) and not has_hard_block and not unconditional

    if all_lines:
        verdict = "UNVERIFIED" if has_unverified_only else "BLOCK"
        exit_code = 1
    elif overridden_detail:
        verdict = "PASS_WITH_OVERRIDE"
        exit_code = 0
    else:
        verdict = "PASS"
        exit_code = 0

    summary = "; ".join(all_lines) if all_lines else verdict

    overrides_out = [
        {"stage": stage, "gate": key, "instruction": detail.get("instruction", ""), "by": detail.get("by")}
        for stage, key, detail in overridden_detail
    ]

    # An override receipt that never matched a missing or failing gate is
    # unused; listed so a stale or misspelled override is visible rather
    # than silently doing nothing.
    unused = [detail for i, detail in enumerate(overrides) if i not in used_overrides]
    unused_overrides_out = [
        {"gate": detail.get("gate"), "instruction": detail.get("instruction", ""), "by": detail.get("by")}
        for detail in unused
    ]

    stages_list = [stage_rows[n] for n in range(0, FIX_STAGE_COUNT)]
    if "rounds" in stage_rows:
        stages_list.append(stage_rows["rounds"])

    gate_data = {
        "argv": sys.argv, "cwd": os.getcwd(), "head": head, "exit": exit_code,
        "summary": summary, "verdict": verdict,
        "stages": stages_list,
        "overrides": overrides_out,
        "unused_overrides": unused_overrides_out,
    }

    gate_path = run_dir / "gates" / "fix.json"
    content = ship_gate._atomic_write_json(gate_path, gate_data)
    gate_sha256 = hashlib.sha256(content).hexdigest()
    try:
        gate_state.append_receipt(run_dir, "gate-result", {
            "gate": "fix-gate", "gate_file": "gates/fix.json",
            "gate_sha256": gate_sha256, "exit": exit_code, "summary": summary,
        })
    except Exception as exc:
        print(f"ERROR: cannot append receipt: {exc}", file=sys.stderr)
        return 2

    for line in all_lines:
        print(line, file=sys.stderr)
    for detail in unused:
        print(f"unused override: {detail.get('gate')}")

    if json_output:
        print(json.dumps(gate_data["stages"]))

    return exit_code


# ---------------------------------------------------------------------------
# stage <n>
# ---------------------------------------------------------------------------

def cmd_stage(repo_root_arg: str, n: int) -> int:
    try:
        if not (1 <= n < FIX_STAGE_COUNT):
            raise ship_gate.Unmeasurable(f"invalid stage number: {n}")

        repo_root, run_dir, head = _resolve(repo_root_arg)

        chain_result = gate_state.verify_chain(run_dir)
        if chain_result.status == "unrunnable":
            raise ship_gate.Unmeasurable(f"receipt chain unreadable: {chain_result.reason}")

        records = ship_gate._read_receipts(run_dir)
        if records is None:
            raise ship_gate.Unmeasurable("receipts.jsonl unreadable")
    except ship_gate.Unmeasurable as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        return 2

    _approval_present, block_receipts, overrides = ship_gate._scan_receipts(records)
    used_overrides: set = set()

    missing: List[str] = []
    failing: List[str] = []
    overridden: List[str] = []
    extra_reasons: List[str] = []

    if chain_result.status == "broken":
        extra_reasons.append(f"chain broken: {chain_result.reason}")
    for detail in block_receipts:
        extra_reasons.append(f"block receipt: {detail.get('reason', 'present')}")

    for stage, key, relpath in FIX_REQUIRED_GATES:
        if stage >= n:
            continue
        info = ship_gate._evaluate_gate_item(run_dir, relpath, head)
        state = info["state"]

        order_reason = None
        if relpath == "gates/9-recheck.json" and state not in ("missing", "head-drift"):
            order_reason = _recheck_order_reason(records)

        if state == "head-drift":
            failing.append(relpath)
            extra_reasons.append(f"{relpath}: head drift")
            continue
        if state == "ok" and order_reason is None:
            continue
        override = ship_gate._override_for(overrides, used_overrides, key, str(stage))
        if override:
            overridden.append(relpath)
            continue
        if order_reason is not None:
            failing.append(relpath)
            extra_reasons.append(f"{relpath}: {order_reason}")
        elif state == "missing":
            missing.append(relpath)
        else:
            failing.append(relpath)

    allowed = (
        not missing and not failing and chain_result.status == "ok" and not block_receipts
    )
    exit_code = 0 if allowed else 1

    reason_parts = []
    if missing:
        reason_parts.append("missing: " + ", ".join(missing))
    if failing:
        reason_parts.append("failing: " + ", ".join(failing))
    reason_parts.extend(extra_reasons)
    reason = "; ".join(reason_parts) if reason_parts else "allowed"

    result = {
        "stage": n, "allowed": allowed, "missing": missing,
        "failing": failing, "overridden": overridden, "reason": reason,
    }
    print(json.dumps(result))
    return exit_code


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

_SELF_TEST_CASES: List[Tuple[str, int, Optional[str]]] = [
    ("all-green", 0, None),
    ("map-missing", 1, "gates/handoff-1-map.json"),
    ("map-overridden", 0, None),
    ("map-earlier-head", 0, None),
    ("map-foreign-head", 1, "head drift"),
    ("red-green-never-red", 1, "gates/9.json"),
    ("recheck-hash-changed", 1, "gates/9-recheck.json"),
    ("matrix-not-met", 1, "gates/11-matrix.json"),
    ("claim-uncited", 1, "gates/12.json"),
    ("override-covers-matrix", 0, None),
    ("chain-broken", 1, None),
    ("recheck-before-proof", 1, "recheck predates the proof it rechecks"),
    ("rounds-exceeded", 1, "exceeds 3"),
    ("rounds-overridden", 0, None),
    ("rounds-three", 0, None),
]


def _copy_fixture(build_dir: Path, name: str, tmp_root: Path) -> Tuple[Path, Path]:
    """Copy one fixture's repo and state into a fresh tmp directory and
    return (repo, state_root), so that running check/stage against the
    copy never writes into the checked-in fixtures under _build."""
    copy_dir = tmp_root / name
    shutil.copytree(build_dir / name, copy_dir, symlinks=True)
    return copy_dir / "repo", copy_dir / "state"


def _run_check(repo: Path, state_root: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, TEAM_STATE_ROOT=str(state_root))
    return subprocess.run([sys.executable, __file__, "check", "--repo-root", str(repo)],
                           capture_output=True, text=True, timeout=60, env=env)


def _run_gate_fix(state_root: Path) -> Optional[Dict[str, Any]]:
    run_dirs = list(state_root.glob("*"))
    if not run_dirs:
        return None
    gate_path = run_dirs[0] / "gates" / "fix.json"
    if not gate_path.is_file():
        return None
    return json.loads(gate_path.read_text(encoding="utf-8"))


def _self_test_fixed_cases(build_dir: Path) -> List[str]:
    lines: List[str] = []
    all_ok = True

    with tempfile.TemporaryDirectory(prefix="fix_gate_selftest_") as tmp:
        tmp_root = Path(tmp)

        for name, expected_exit, expected_substr in _SELF_TEST_CASES:
            if not (build_dir / name).is_dir():
                lines.append(f"{name}: FAIL fixture not found")
                all_ok = False
                continue

            repo, state_root = _copy_fixture(build_dir, name, tmp_root)
            proc = _run_check(repo, state_root)
            exit_ok = proc.returncode == expected_exit
            combined = proc.stdout + proc.stderr
            substr_ok = expected_substr is None or expected_substr in combined
            status = "OK" if (exit_ok and substr_ok) else "FAIL"
            if status == "FAIL":
                all_ok = False
            detail = f" substring {expected_substr!r} present={substr_ok}" if expected_substr else ""
            lines.append(f"{name}: expected {expected_exit} got {proc.returncode}{detail} {status}")

            if name in ("all-green", "map-overridden", "override-covers-matrix"):
                expected_verdict = "PASS" if name == "all-green" else "PASS_WITH_OVERRIDE"
                gate_fix = _run_gate_fix(state_root)
                verdict_ok = gate_fix is not None and gate_fix.get("verdict") == expected_verdict
                v_status = "OK" if verdict_ok else "FAIL"
                if v_status == "FAIL":
                    all_ok = False
                actual = gate_fix.get("verdict") if gate_fix else None
                lines.append(f"{name}-verdict: expected {expected_verdict} got {actual} {v_status}")

                if name == "map-overridden":
                    instruction_ok = gate_fix is not None and (
                        "map-overridden instruction text" in json.dumps(gate_fix)
                    )
                    i_status = "OK" if instruction_ok else "FAIL"
                    if i_status == "FAIL":
                        all_ok = False
                    lines.append(f"map-overridden-instruction: present in gates/fix.json {i_status}")

                if name == "override-covers-matrix":
                    instruction_ok = gate_fix is not None and (
                        "override-covers-matrix instruction text" in json.dumps(gate_fix)
                    )
                    i_status = "OK" if instruction_ok else "FAIL"
                    if i_status == "FAIL":
                        all_ok = False
                    lines.append(f"override-covers-matrix-instruction: present in gates/fix.json {i_status}")

        # unused-override: an override receipt naming a gate that never
        # fails or is missing must be reported unused, without affecting
        # the verdict.
        if (build_dir / "unused-override").is_dir():
            repo, state_root = _copy_fixture(build_dir, "unused-override", tmp_root)
            proc = _run_check(repo, state_root)
            gate_fix = _run_gate_fix(state_root)
            unused_ok = (
                proc.returncode == 0
                and gate_fix is not None
                and gate_fix.get("verdict") == "PASS"
                and any(u.get("gate") == "8" for u in gate_fix.get("unused_overrides", []))
                and "unused override: 8" in proc.stdout
            )
            status = "OK" if unused_ok else "FAIL"
            if status == "FAIL":
                all_ok = False
            lines.append(f"unused-override: expected 0 got {proc.returncode} {status}")
        else:
            lines.append("unused-override: FAIL fixture not found")
            all_ok = False

        # stage-query-allowed / stage-query-blocked, both queried at the fix
        # pipeline's own last stage (6), since stage n never looks at its own
        # required file, only at the stages before it.
        for name, expected_exit, expects_missing in (
            ("stage-query-allowed", 0, None),
            ("stage-query-blocked", 1, "gates/7-discover.json"),
        ):
            repo, state_root = _copy_fixture(build_dir, name, tmp_root)
            env = dict(os.environ, TEAM_STATE_ROOT=str(state_root))
            proc = subprocess.run(
                [sys.executable, __file__, "stage", str(FIX_STAGE_COUNT - 1), "--repo-root", str(repo)],
                capture_output=True, text=True, timeout=60, env=env,
            )
            exit_ok = proc.returncode == expected_exit
            result_ok = True
            if expects_missing:
                try:
                    parsed = json.loads(proc.stdout.strip())
                    result_ok = expects_missing in parsed.get("missing", [])
                except json.JSONDecodeError:
                    result_ok = False
            status = "OK" if (exit_ok and result_ok) else "FAIL"
            if status == "FAIL":
                all_ok = False
            lines.append(f"{name}: expected {expected_exit} got {proc.returncode} {status}")

        # no-run: a generated fixture repo with no run ever started against it
        if (build_dir / "no-run").is_dir():
            no_run_repo, no_run_state = _copy_fixture(build_dir, "no-run", tmp_root)
            env = dict(os.environ, TEAM_STATE_ROOT=str(no_run_state))
            proc = subprocess.run(
                [sys.executable, __file__, "check", "--repo-root", str(no_run_repo)],
                capture_output=True, text=True, timeout=30, env=env,
            )
            status = "OK" if proc.returncode == 2 else "FAIL"
            if status == "FAIL":
                all_ok = False
            lines.append(f"no-run: expected 2 got {proc.returncode} {status}")
        else:
            lines.append("no-run: FAIL fixture not found")
            all_ok = False

    if not all_ok:
        lines.append("FIXED-CASES: FAIL")
    else:
        lines.append("FIXED-CASES: OK")
    return lines


def cmd_self_test() -> int:
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "fix_gate"
    make_fixtures = fixtures_dir / "make_fixtures.py"

    result = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"make_fixtures.py failed: {result.stderr}", file=sys.stderr)
        return 2

    build_dir = fixtures_dir / "_build"
    lines = _self_test_fixed_cases(build_dir)

    for line in lines:
        print(line)

    all_ok = all("FAIL" not in line for line in lines)
    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true", help="run self-test on fixtures")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--repo-root", default=".")
    check_parser.add_argument("--json", action="store_true")

    stage_parser = subparsers.add_parser("stage")
    stage_parser.add_argument("n", type=int)
    stage_parser.add_argument("--repo-root", default=".")

    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    if args.command == "check":
        return cmd_check(args.repo_root, args.json)
    if args.command == "stage":
        return cmd_stage(args.repo_root, args.n)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
