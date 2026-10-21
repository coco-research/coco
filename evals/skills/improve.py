#!/usr/bin/env python3
"""Run one automatic improvement round on one agent skill. Stdlib only.

One round proposes edits, probes them on the dev items, and composes the
winners. The chosen candidate gets one held-out peek and is kept only when
the delta is positive and a one-sided bootstrap p is below PEEK_ALPHA. The
ledger caps those peeks at MAX_TOTAL_PEEKS per held-out set (items.jsonl hash).
Stub executor rounds do not spend that cap.
--apply is off by default.

    python3 evals/skills/improve.py --skill NAME [--executor ollama|stub]
"""
import argparse
import contextlib
import datetime
import difflib
import hashlib
import io
import json
import os
import pathlib
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import types

import run, score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
import paired

K_DEFAULT, K_MAX = 4, 8
DEV_MARGIN, MIN_WINS, WIN_EPS = 0.05, 2, 0.01
MIN_HELDOUT = 20  # below this, the held-out bootstrap p is noise; pilot skills have 24
MAX_CHANGED_LINES, MAX_GROWTH_BYTES = 30, 4000
MAX_FAILURES, CASE_CHARS = 6, 2000
PROPOSER_TIMEOUT, PROPOSER_MAX_BYTES = 900, 200_000
ALPHA, N_BOOT, BOOT_SEED = 0.05, 10000, 0
MAX_TOTAL_PEEKS = 5  # life-time peeks per held-out set (items.jsonl hash); stub rounds do not count
PEEK_ALPHA = ALPHA / MAX_TOTAL_PEEKS  # Bonferroni split across those peeks
ROUTER_TIMEOUT = 1800
RUNS_DIR, ROUNDS_DIR = "runs", "_rounds"


class Reject(Exception):
    """A proposal that must not be scored. str(e) is the reason."""


def die(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frontmatter(text):
    m = re.match(r"---\n.*?\n---\n", text, re.S)
    return m.group(0) if m else ""


def strip_outer_fence(text):
    lines = text.strip("\n").split("\n")
    m = re.match(r"(`{3,}|~{3,})[\w+.-]*\s*$", lines[0])
    if m and len(lines) > 2:
        ends = [i for i, l in enumerate(lines) if i > 0 and l.strip() == m.group(1)]
        if ends:
            return "\n".join(lines[1:ends[-1]]) + "\n"
    return text.strip("\n") + "\n"


_DIFF_START = re.compile(
    r"(?:diff --git [^\n]*\n)?(?:index [^\n]*\n)?--- [^\n]+\n\+\+\+ [^\n]+\n@@ ")
_HUNK = re.compile(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")


def apply_diff(base_lines, diff_text, skill):
    allowed = {"SKILL.md", "skills/%s/SKILL.md" % skill}
    lines = diff_text.rstrip("\n").split("\n")
    hunks, cur, k = [], None, 0          # hunk = [declared_start, old_lines, new_lines]
    while k < len(lines):
        line = lines[k]
        if line.startswith("--- ") and k + 1 < len(lines) and lines[k + 1].startswith("+++ "):
            for hdr in (line[4:], lines[k + 1][4:]):
                name = hdr.split("\t")[0].strip()
                if name == "/dev/null":
                    raise Reject("diff creates, deletes or renames a file")
                if name[:2] in ("a/", "b/"):
                    name = name[2:]
                if name not in allowed:
                    raise Reject("diff touches another file: " + name)
            cur = None
            k += 2
            continue
        m = _HUNK.match(line)
        if m:
            cur = [int(m.group(1)), [], []]
            hunks.append(cur)
        elif cur is not None and (line == "" or line[:1] in (" ", "-", "+")):
            tag, text = (line[:1], line[1:]) if line else (" ", "")
            if tag != "+":
                cur[1].append(text)
            if tag != "-":
                cur[2].append(text)
        elif line.startswith(("new file", "deleted file", "rename ", "Binary")):
            raise Reject("diff creates, deletes or renames a file")
        elif line.startswith("\\") or line.startswith(("diff --git", "index ", "similarity")):
            pass
        elif cur is None:
            pass                          # prose before the first hunk
        else:
            raise Reject("unexpected line in diff")
        k += 1
    if not hunks:
        raise Reject("diff has no hunks")
    out, pos = [], 0
    for n, (start, old, new) in enumerate(hunks, 1):
        if not old or old == new:
            raise Reject("hunk %d has no context or no change" % n)
        hits = [p for p in range(len(base_lines) - len(old) + 1)
                if base_lines[p:p + len(old)] == old]
        if not hits:
            raise Reject("hunk %d does not match SKILL.md" % n)
        hits.sort(key=lambda p: abs(p - (start - 1)))
        if len(hits) > 1 and abs(hits[0] - (start - 1)) == abs(hits[1] - (start - 1)):
            raise Reject("hunk %d is ambiguous" % n)
        if hits[0] < pos:
            raise Reject("hunks overlap or are out of order")
        out.extend(base_lines[pos:hits[0]])
        out.extend(new)
        pos = hits[0] + len(old)
    out.extend(base_lines[pos:])
    return out


def edit_script(base_lines, new_lines):
    sm = difflib.SequenceMatcher(None, base_lines, new_lines, autojunk=False)
    return [(i1, i2, tuple(new_lines[j1:j2]))
            for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def n_changed(edits):
    return sum((i2 - i1) + len(new) for i1, i2, new in edits)


def conflict(e, f):
    return e != f and e[0] <= f[1] and f[0] <= e[1]


def apply_edits(base_lines, edits):
    out, pos = [], 0
    for i1, i2, new in sorted(set(edits)):
        out.extend(base_lines[pos:i1])
        out.extend(new)
        pos = i2
    out.extend(base_lines[pos:])
    return out


def compose(base_lines, ranked, cap):
    """ranked: [(proposal_id, edits)] best first. Returns (lines, used_ids, dropped)."""
    kept, dropped, union = [], [], set()
    for pid, edits in ranked:
        clash = next((q for q, qe in kept
                      if any(conflict(e, f) for e in edits for f in qe)), None)
        if clash:
            dropped.append({"id": pid, "why": "conflicts with " + clash})
        elif n_changed(union | set(edits)) > cap:
            dropped.append({"id": pid, "why": "over the composed cap"})
        else:
            kept.append((pid, edits))
            union |= set(edits)
    return apply_edits(base_lines, union), [q for q, _ in kept], dropped


def dev_verdict(base, cand, margin, min_wins):
    ids = sorted(base)
    d = [cand[i] - base[i] for i in ids]
    wins = sum(1 for x in d if x >= WIN_EPS)
    losses = sum(1 for x in d if x <= -WIN_EPS)
    gain = sum(d) / len(d)
    return {"mean": sum(cand[i] for i in ids) / len(ids), "gain": gain,
            "wins": wins, "losses": losses,
            "pass": gain >= margin and wins >= min_wins and wins > losses}


def peek_stats(base, cand, alpha=PEEK_ALPHA):
    delta, lo, hi = paired.paired_bootstrap(base, cand, N_BOOT, BOOT_SEED)
    p = paired.boot_p_greater([c - b for b, c in zip(base, cand)], N_BOOT, BOOT_SEED)
    return {"n": len(base), "base_mean": sum(base) / len(base), "cand_mean": sum(cand) / len(cand),
            "delta": delta, "ci95": [lo, hi], "p_one_sided": p, "alpha": alpha,
            "pass": delta > 0 and p < alpha}


def parse_proposal(raw, base, skill, max_changed=MAX_CHANGED_LINES):
    text = raw.replace("\r\n", "\n").strip("\n")
    if not text.strip():
        raise Reject("empty reply")
    body = strip_outer_fence(text)
    if _DIFF_START.match(body):
        new = "\n".join(apply_diff(base.split("\n"), body, skill))
    else:
        new = body
    new = new.rstrip("\n") + "\n"
    if "\x00" in new:
        raise Reject("NUL byte")
    edits = edit_script(base.split("\n"), new.split("\n"))
    if not edits:
        return base, []
    if frontmatter(new) != frontmatter(base):
        raise Reject("front matter changed")
    if n_changed(edits) > max_changed:
        raise Reject("too many changed lines: %d > %d" % (n_changed(edits), max_changed))
    if len(new.encode()) - len(base.encode()) > MAX_GROWTH_BYTES:
        raise Reject("too large: grows by more than %d bytes" % MAX_GROWTH_BYTES)
    return new, edits


def others_check(changed, skill):
    own = "skills/%s/SKILL.md" % skill
    shared = sorted(p for p in changed if p != own)
    if not shared:
        return {"status": "skipped", "reason": "only " + own + " changed"}
    return {"status": "failed", "reason": "shared files changed: " + ", ".join(shared)}


_PROMPT = """\
You are improving an agent skill file named SKILL.md. A small language model is given the whole
file as its system prompt, followed by a user request. Below are the file and some test cases where
that model scored poorly, with what it wrote and the grader's notes.

Propose ONE small, targeted edit to SKILL.md that should help the model on cases like these in
general, not only on these cases.

Rules:
- Change at most {max_changed} lines in total (lines added plus lines removed).
- Keep the front matter (the block between the first two "---" lines) exactly as it is.
- Do not copy text from the cases into the file, and do not mention cases, scores or graders.
- Prefer one short, concrete instruction or one short example over general advice.
- Do not break what already works: {n_pass} of {n_dev} dev cases already score 1.0.
- Treat the folder as read-only: do not create, change or delete any file. Put the new SKILL.md in your reply only.

Reply with the complete new SKILL.md inside one fenced block and nothing else. Use four backticks
as the outer fence so that code blocks inside the file survive. (A unified diff against the file
below is also accepted.)

<skill_md>
{skill_md}</skill_md>

<focus_case number="{i}" of="{k}">
{focus_block}</focus_case>

<other_cases>
{other_blocks}</other_cases>
"""


def _write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def require_proposer_cmd():
    """argv of COCO_PROPOSER_CMD, split without a shell, with argv[0] made absolute.

    The command runs inside a temp workspace, so give script arguments as absolute paths.
    """
    try:
        argv = shlex.split(os.environ.get("COCO_PROPOSER_CMD", ""))
    except ValueError as e:
        die("COCO_PROPOSER_CMD is not a valid command line: %s" % e)
    if not argv:
        die("COCO_PROPOSER_CMD is not set")
    found = shutil.which(argv[0])
    if not found:
        die("COCO_PROPOSER_CMD: command not found: %s" % argv[0])
    argv[0] = os.path.abspath(found)
    return argv


def load_dev_rows(items_path):
    return [r for r in score.load_items(items_path) if r["split"] == "dev"]


def check_split_overlap(items_path):
    rows = score.load_items(items_path)
    held = {r["input"] for r in rows if r["split"] == "heldout"}
    shared = sorted(r["id"] for r in rows if r["split"] == "dev" and r["input"] in held)
    if shared:
        die("dev and held-out share an input (dev ids: %s)" % ", ".join(shared))


def failures_from(dev_rows, dev_record):
    per_item = dev_record["per_item"]
    bad = [{"id": r["id"], "score": per_item[r["id"]], "input": r["input"],
            "output": dev_record["outputs"][r["id"]], "notes": dev_record["notes"][r["id"]]}
           for r in dev_rows if per_item[r["id"]] < 1.0]
    bad.sort(key=lambda f: (f["score"], f["id"]))
    return bad[:MAX_FAILURES]


def _cut(text):
    return text if len(text) <= CASE_CHARS else text[:CASE_CHARS] + "[cut]"


def _case_block(f):
    notes = "".join("- %s\n" % n for n in f["notes"])
    return "id: %s\nscore: %.2f\nrequest:\n%s\nmodel_output:\n%s\ngrader_notes:\n%s\n" % (
        f["id"], f["score"], _cut(f["input"]), _cut(f["output"]), notes)


def build_prompt(skill_md, failures, focus_index, k, n_dev, n_pass, max_changed):
    """focus_index is the 0-based call number: its focus case is failures[focus_index % len]."""
    pos = focus_index % len(failures)
    return _PROMPT.format(
        max_changed=max_changed, n_pass=n_pass, n_dev=n_dev,
        skill_md=skill_md if skill_md.endswith("\n") else skill_md + "\n",
        i=focus_index + 1, k=k, focus_block=_case_block(failures[pos]),
        other_blocks="".join(_case_block(f) for f in failures[:pos] + failures[pos + 1:]))


def _require_dev(dev_rows, dev_record):
    if dev_record.get("split") != "dev" or any(r.get("split") != "dev" for r in dev_rows):
        raise ValueError("the proposer workspace takes dev material only")


def make_workspace(dest, skill_md, dev_rows, dev_record):
    """Create dest with SKILL.md, dev_items.jsonl and dev_run.json. Returns {name: sha256}."""
    _require_dev(dev_rows, dev_record)
    files = {
        "SKILL.md": skill_md,
        "dev_items.jsonl": "".join(
            json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in dev_rows),
        "dev_run.json": score.record_json(dev_record),
    }
    pathlib.Path(dest).mkdir(parents=True)
    for name, text in files.items():
        _write(pathlib.Path(dest) / name, text)
    return {name: sha256_text(text) for name, text in files.items()}


def snapshot(dirpath):
    """{relative posix path: sha256, "dir", "other", or "unreadable"} for everything under dirpath."""
    snap = {}
    for here, dirs, names in os.walk(dirpath):
        for name in dirs + names:
            p = pathlib.Path(here, name)
            mode = p.lstat().st_mode
            if stat.S_ISDIR(mode):
                val = "dir"
            elif stat.S_ISREG(mode):
                try:
                    val = score.sha256_file(p)
                except OSError:
                    val = "unreadable"
            else:
                val = "other"             # a link or special file: only its presence counts
            snap[p.relative_to(dirpath).as_posix()] = val
    return snap


def run_proposer(argv, prompt, ws, index, state):
    """Run the proposer once: prompt on stdin, cwd ws. Returns (stdout text, None) or (None, why)."""
    if state["peeked"]:
        raise RuntimeError("proposer called after the held-out peek")
    env = dict(os.environ, COCO_PROPOSER_INDEX=str(index))
    # A new session so a timeout can kill grandchildren. A wrapper proposer
    # (coco-route) leaves them holding the pipes, and the follow-up communicate()
    # then blocks until they exit.
    try:
        p = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=ws, env=env, start_new_session=True)
    except OSError as e:
        return None, "spawn failed: %s" % (
            e.strerror if e.strerror is not None else type(e).__name__)
    try:
        stdout, _stderr = p.communicate(input=prompt.encode("utf-8"), timeout=PROPOSER_TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            p.stdout.close()
            p.stderr.close()
            p.kill()
            p.wait()
        return None, "timeout"
    if p.returncode != 0:
        return None, "exit %d" % p.returncode
    # ponytail: the byte cap is checked after capture, so a runaway proposer sits in memory
    # until the timeout. Upgrade path: read in chunks from Popen and kill at the cap.
    if len(stdout) > PROPOSER_MAX_BYTES:
        return None, "output too large"
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None, "output is not UTF-8"
    if not text.strip():
        return None, "empty reply"
    return text, None


def propose_all(skill, skill_md, dev_rows, dev_record, out, argv, k, max_changed, state):
    """Call the proposer k times on dev material only. Returns one dict per call, p1 to pk."""
    _require_dev(dev_rows, dev_record)
    out = pathlib.Path(out)
    failures = failures_from(dev_rows, dev_record)
    if not failures:
        raise ValueError("propose_all needs at least one dev failure")
    n_pass = sum(1 for r in dev_rows if dev_record["per_item"][r["id"]] >= 1.0)
    results, seen = [], {}
    for i in range(1, k + 1):
        pid = "p%d" % i
        prompt = build_prompt(skill_md, failures, i - 1, k, len(dev_rows), n_pass, max_changed)
        _write(out / "prompts" / (pid + ".txt"), prompt)
        ws = out / "ws" / pid
        make_workspace(ws, skill_md, dev_rows, dev_record)
        before = snapshot(ws)
        text, why = run_proposer(argv, prompt, ws, i, state)
        p = {"id": pid, "focus": failures[(i - 1) % len(failures)]["id"],
             "prompt_sha256": sha256_text(prompt), "status": None, "reason": None,
             "raw_sha256": None, "skill_sha256": None, "changed_lines": None,
             "text": None, "edits": []}
        results.append(p)
        if text is not None:
            _write(out / "proposals" / pid / "raw.txt", text)
            p["raw_sha256"] = sha256_text(text)
        if snapshot(ws) != before:
            p.update(status="rejected", reason="workspace modified")
        elif text is None:
            p.update(status="failed", reason=why)
        else:
            try:
                new, edits = parse_proposal(text, skill_md, skill, max_changed)
            except Reject as e:
                p.update(status="rejected", reason=str(e))
            else:
                p.update(status="ok", text=new, edits=edits, skill_sha256=sha256_text(new),
                         changed_lines=n_changed(edits))
                if not edits:
                    p["status"] = "noop"
                elif new in seen:
                    p.update(status="duplicate", reason="same as " + seen[new])
                else:
                    seen[new] = pid
                    _write(out / "proposals" / pid / "SKILL.md", new)
    return results


def fingerprint(paths):
    """{str(path): sha256 of its bytes} for each path that exists as a file."""
    return {str(p): score.sha256_file(p) for p in paths if pathlib.Path(p).is_file()}


_PROPOSAL_KEYS = ("id", "focus", "status", "reason", "prompt_sha256", "raw_sha256",
                  "skill_sha256", "changed_lines")


def _public_proposal(p):
    row = {k: p.get(k) for k in _PROPOSAL_KEYS}
    if "dev" in p:
        row["dev"] = p["dev"]
    return row


def _rel_to(root, path):
    path, root = pathlib.Path(path).resolve(), pathlib.Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def write_json_atomic(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A unique temp name per writer, so two concurrent rewrites never share one file.
    fd, tmp_name = tempfile.mkstemp(prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp = pathlib.Path(tmp_name)
    try:
        _write(tmp, json.dumps(obj, indent=2) + "\n")
        os.replace(str(tmp), str(path))
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def ledger_records(rounds_dir):
    rounds_dir = pathlib.Path(rounds_dir)
    if not rounds_dir.is_dir():
        return []
    recs = []
    for path in sorted(rounds_dir.glob("r*.json")):
        try:
            rec = json.loads(path.read_text())
        except (OSError, UnicodeError, json.JSONDecodeError):
            die("malformed ledger record %s" % path.name)
        if not isinstance(rec, dict):
            die("malformed ledger record %s" % path.name)
        recs.append(rec)
    return recs


def claim_round(rounds_dir, rec):
    rounds_dir = pathlib.Path(rounds_dir)
    rounds_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, 10000):
        rid = "r%03d" % n
        path = rounds_dir / ("%s.json" % rid)
        rec["round"] = rid
        # A unique temp name per writer, so two concurrent claims never share (or delete) one file.
        fd, tmp_name = tempfile.mkstemp(prefix=".%s." % path.name, suffix=".tmp", dir=str(rounds_dir))
        os.close(fd)
        tmp = pathlib.Path(tmp_name)
        try:
            _write(tmp, json.dumps(rec, indent=2) + "\n")
            try:
                os.link(str(tmp), str(path))
            except FileExistsError:
                continue
            return rid, path
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
    die("too many rounds")


def begin_peek(rec, path, state):
    if rec["peek_count"] != 0:
        raise RuntimeError("held-out peek already started")
    if rec["total_peeks"] >= MAX_TOTAL_PEEKS:
        raise RuntimeError("held-out peek budget exhausted")
    rec["peek_count"] = 1
    rec["total_peeks"] = rec["total_peeks"] + 1
    rec["outcome"] = "peeking"
    state["peeked"] = True
    write_json_atomic(path, rec)


def _baseline_ok(rec, cfg, hashes, n_heldout):
    if not isinstance(rec, dict):
        return False
    want = {"split": "heldout", "skill": cfg.skill, "skill_sha256": hashes["skill"],
            "items_sha256": hashes["items"], "grader_sha256": hashes["grader"],
            "executor": cfg.executor, "model": cfg.model, "seed": score.SEED, "n": n_heldout}
    return all(rec.get(k) == v for k, v in want.items())


def find_baseline_heldout(cfg, hashes, n_heldout):
    def load(path):
        try:
            rec = json.loads(pathlib.Path(path).read_text())
        except (OSError, UnicodeError, json.JSONDecodeError):
            die("baseline held-out record is unreadable")
        if not _baseline_ok(rec, cfg, hashes, n_heldout):
            die("baseline held-out record does not match this skill")
        return pathlib.Path(path), rec

    if cfg.baseline_heldout:
        return load(cfg.baseline_heldout)
    matches = []
    runs = pathlib.Path(cfg.runs_dir)
    if runs.is_dir():
        for path in runs.glob("*.json"):
            try:
                rec = json.loads(path.read_text())
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if _baseline_ok(rec, cfg, hashes, n_heldout):
                date = rec.get("date") if isinstance(rec.get("date"), str) else ""
                matches.append((date, path.name, path, rec))
    if not matches:
        # score.py --out writes the file only; it does not create parent dirs.
        die("no baseline held-out record; mkdir -p %s && "
            "python3 evals/skills/score.py --skill %s --split heldout "
            "--executor %s --out %s/baseline-heldout.json"
            % (cfg.runs_dir, cfg.skill, cfg.executor, cfg.runs_dir))
    matches.sort()
    return matches[-1][2], matches[-1][3]


def base_check(root, ref, rels):
    if ref == "none":
        return "skipped"
    root = pathlib.Path(root)
    for rel in rels:
        local = root / rel
        if not local.is_file():
            die("cannot read %s" % rel)
        got = subprocess.run(
            ["git", "-C", str(root), "show", "%s:%s" % (ref, rel)], capture_output=True)
        if got.returncode != 0:
            die("cannot read %s:%s" % (ref, rel))
        if got.stdout != local.read_bytes():
            die("%s differs from %s" % (rel, ref), code=1)
    return "ok"


def router_gate(root):
    raw = os.environ.get("COCO_ROUTER_GATE_CMD", "")
    if raw.strip():
        try:
            argv = shlex.split(raw)
        except ValueError:
            die("COCO_ROUTER_GATE_CMD is not a valid command line")
        kind = "override"
    else:
        argv = [sys.executable, "evals/routing/check_regression.py"]
        kind = "default"
    try:
        got = subprocess.run(argv, cwd=str(root), capture_output=True, timeout=ROUTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        die("router gate timed out", code=1)
    except OSError:
        die("router gate could not start", code=2)
    text = (got.stdout + got.stderr).decode("utf-8", "replace")
    return {"cmd": kind, "exit": got.returncode, "_tail": text.splitlines()[-2:]}


def score_split(cfg, split, skill_md_path):
    return score.score_run(
        cfg.skill, split, cfg.executor, cfg.items_path, cfg.grader_path, skill_md_path,
        model=cfg.model, seed=score.SEED, url=cfg.url)


def write_branch(out, skill, round_id, cand_text, dev_record, held_record, rec, base_text):
    out = pathlib.Path(out)
    files = {
        "skills/%s/SKILL.md" % skill: cand_text,
        "evals/skills/%s/%s/%s-dev.json" % (skill, RUNS_DIR, round_id): score.record_json(dev_record),
        "evals/skills/%s/%s/%s-heldout.json" % (skill, RUNS_DIR, round_id): score.record_json(held_record),
        "evals/skills/%s/%s/%s.json" % (ROUNDS_DIR, skill, round_id): json.dumps(rec, indent=2) + "\n",
    }
    for rel, text in files.items():
        _write(out / "branch" / rel, text)
    diff = "".join(difflib.unified_diff(
        base_text.splitlines(keepends=True), cand_text.splitlines(keepends=True),
        fromfile="a/skills/%s/SKILL.md" % skill, tofile="b/skills/%s/SKILL.md" % skill))
    _write(out / "skill.diff", diff)


def apply_branch(out, root, skill, base_sha):
    root, out = pathlib.Path(root), pathlib.Path(out)
    target = root / "skills" / skill / "SKILL.md"
    if not target.is_file() or score.sha256_file(target) != base_sha:
        die("SKILL.md no longer matches the round base", code=1)
    branch = out / "branch"
    shutil.copyfile(str(branch / "skills" / skill / "SKILL.md"), str(target))
    dest = root / "evals" / "skills" / skill / RUNS_DIR
    dest.mkdir(parents=True, exist_ok=True)
    for path in sorted((branch / "evals" / "skills" / skill / RUNS_DIR).glob("*.json")):
        shutil.copyfile(str(path), str(dest / path.name))
    # The ledger record is not copied: claim_round already writes it into root's
    # evals/skills/_rounds/<skill>/ (cfg.rounds_dir). The branch/ copy is only for the PR.


def _peeked_in(rounds_dir, sha, this_round, items_hash):
    # Same filter as the life-time cap: this items.jsonl, and not a stub executor.
    for old in ledger_records(rounds_dir):
        if old.get("round") == this_round or not old.get("peek_count"):
            continue
        hashes = old.get("hashes") if isinstance(old.get("hashes"), dict) else {}
        executor = old.get("executor") if isinstance(old.get("executor"), dict) else {}
        if hashes.get("items") != items_hash or executor.get("kind") == "stub":
            continue
        if (old.get("candidate") or {}).get("skill_sha256") == sha:
            return old.get("round")
    return None


def _same_heldout(held, base):
    keys = ("items_sha256", "grader_sha256", "executor", "model", "seed", "n")
    if any(held.get(k) != base.get(k) for k in keys):
        return False
    return set(held.get("per_item") or {}) == set(base.get("per_item") or {})


def _peek_reason(peek, kept):
    core = "delta %+0.3f, p %.3f, n %d" % (peek["delta"], peek["p_one_sided"], peek["n"])
    return ("held-out " + core) if kept else ("held-out gate not met: " + core)


class _TeeStderr(io.StringIO):
    """Keeps what is written (for the ledger reason) and passes it straight through."""

    def __init__(self, real):
        super().__init__()
        self._real = real

    def write(self, text):
        self._real.write(text)
        return super().write(text)


def _exit_reason(buf, exc):
    # str code: run.py executor/config exit (caller re-raises). int: score.die.
    lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
    return lines[-1] if lines else str(exc.code)


def run_round(cfg):
    cfg.proposer_argv = require_proposer_cmd()
    cfg.proposer_id = os.environ.get("COCO_PROPOSER_ID") or None
    if not score._NAME.fullmatch(cfg.skill or ""):
        die("invalid skill name %r" % (cfg.skill,))
    if not 1 <= cfg.k <= K_MAX:
        die("--max-proposals must be from 1 to %d" % K_MAX)
    out = pathlib.Path(cfg.out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        die("--out must be absent or empty")
    out.mkdir(parents=True, exist_ok=True)
    cfg.out = out
    for label, path in (("SKILL.md", cfg.skill_md_path), ("items.jsonl", cfg.items_path),
                        ("grader.py", cfg.grader_path)):
        if not pathlib.Path(path).is_file():
            die("missing %s" % label)
    base_text = pathlib.Path(cfg.skill_md_path).read_text()
    if not base_text.endswith("\n") or base_text.endswith("\n\n"):
        die("SKILL.md must end with exactly one newline")
    rows = score.load_items(cfg.items_path)
    n_dev = sum(1 for r in rows if r["split"] == "dev")
    n_heldout = sum(1 for r in rows if r["split"] == "heldout")
    if n_dev < MIN_WINS or n_heldout < MIN_HELDOUT:
        die("dev and held-out splits are too small: need %d dev and %d held-out"
            % (MIN_WINS, MIN_HELDOUT))
    check_split_overlap(cfg.items_path)
    rels = ["evals/skills/%s/items.jsonl" % cfg.skill, "evals/skills/%s/grader.py" % cfg.skill,
            "evals/skills/score.py", "evals/skills/run.py", "evals/paired.py",
            "evals/skills/improve.py",
            "evals/routing/check_regression.py",
            "systems/superintelligence/scripts/local_http.py"]
    checked = base_check(cfg.root, cfg.base_ref, rels)
    file_hashes = {"items": score.sha256_file(cfg.items_path), "grader": score.sha256_file(cfg.grader_path),
                   "skill": score.sha256_file(cfg.skill_md_path)}
    base_path, base_held = find_baseline_heldout(cfg, file_hashes, n_heldout)
    # ponytail: the cap is a sum read before claim, so two processes can both pass it.
    # Upgrade path: lock the ledger around the check and the claim.
    # Only a real executor's peeks of this items.jsonl count. Stub rounds and any
    # other held-out set (a different items hash) do not spend this set's cap.
    earlier = 0
    for old in ledger_records(cfg.rounds_dir):
        hashes = old.get("hashes") if isinstance(old.get("hashes"), dict) else {}
        executor = old.get("executor") if isinstance(old.get("executor"), dict) else {}
        if hashes.get("items") != file_hashes["items"] or executor.get("kind") == "stub":
            continue
        earlier += int(old.get("peek_count") or 0)
    if earlier >= MAX_TOTAL_PEEKS:
        die("held-out peek cap reached", code=1)
    router = router_gate(cfg.root)
    tail = router.pop("_tail")
    if router["exit"] != 0:
        die("router gate failed: %s" % " | ".join(tail), code=1)
    dev_rows = [r for r in rows if r["split"] == "dev"]
    rec = {
        "schema": 1, "skill": cfg.skill, "round": None, "date": datetime.date.today().isoformat(),
        "commit": score.git_short(), "outcome": "started", "reason": None, "peek_count": 0,
        "total_peeks": earlier, "executor": {"kind": cfg.executor, "model": cfg.model, "seed": score.SEED},
        "proposer": {"id": cfg.proposer_id, "cmd_sha256": sha256_text("\n".join(cfg.proposer_argv)), "calls": 0},
        "params": {"k": cfg.k, "dev_margin": cfg.margin, "min_wins": MIN_WINS, "win_eps": WIN_EPS,
                   "max_changed_lines": cfg.max_changed, "alpha": ALPHA, "peek_alpha": PEEK_ALPHA,
                   "n_boot": N_BOOT},
        "hashes": {"items": file_hashes["items"], "grader": file_hashes["grader"],
                   "score_py": score.sha256_file(score.__file__), "run_py": score.sha256_file(run.__file__),
                   "paired_py": score.sha256_file(paired.__file__),
                   "improve_py": score.sha256_file(pathlib.Path(__file__).resolve()),
                   "router_gate_py": score.sha256_file(
                       cfg.root / "evals" / "routing" / "check_regression.py"),
                   "local_http_py": score.sha256_file(
                       cfg.root / "systems" / "superintelligence" / "scripts" / "local_http.py"),
                   "base_skill": file_hashes["skill"],
                   "baseline_heldout_record": score.sha256_file(base_path)},
        "base_check": checked,
        "baseline": {"dev_mean": None, "heldout_mean": base_held["mean"], "n_dev": n_dev,
                     "n_heldout": n_heldout, "heldout_record": _rel_to(cfg.root, base_path)},
        "workspace": {"SKILL.md": None, "dev_items.jsonl": None, "dev_run.json": None},
        "proposals": [], "compose": None,
        "gate": {"router": router, "others": None, "peek": None}, "candidate": None,
    }
    _rid, ledger_path = claim_round(cfg.rounds_dir, rec)
    proposals, picked = [], {}
    state = {"peeked": False}
    watched = [cfg.items_path, cfg.grader_path, score.__file__, run.__file__, paired.__file__,
               pathlib.Path(__file__).resolve(), cfg.skill_md_path, base_path,
               cfg.root / "evals" / "routing" / "check_regression.py",
               cfg.root / "systems" / "superintelligence" / "scripts" / "local_http.py"]
    fp0 = fingerprint(watched)

    def save():
        rec["proposer"]["calls"] = len(proposals)
        rec["proposals"] = [_public_proposal(p) for p in proposals]
        write_json_atomic(ledger_path, rec)

    def finish(outcome, reason):
        rec["outcome"] = outcome
        rec["reason"] = reason
        save()
        if outcome == "kept":
            write_branch(cfg.out, cfg.skill, rec["round"], picked["text"], picked["dev"],
                         picked["held"], rec, base_text)
            if cfg.apply:
                apply_branch(cfg.out, cfg.root, cfg.skill, file_hashes["skill"])
        print(json.dumps({"skill": cfg.skill, "round": rec["round"], "outcome": outcome,
                          "reason": reason, "peek_count": rec["peek_count"],
                          "total_peeks": rec["total_peeks"], "out": cfg.out.as_posix()}))
        if outcome == "aborted":
            die(reason, code=1)

    base_dev = score_split(cfg, "dev", cfg.skill_md_path)
    _write(cfg.out / "records" / "base-dev.json", score.record_json(base_dev))
    rec["baseline"]["dev_mean"] = base_dev["mean"]
    dev_items = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in dev_rows)
    rec["workspace"] = {"SKILL.md": sha256_text(base_text), "dev_items.jsonl": sha256_text(dev_items),
                        "dev_run.json": sha256_text(score.record_json(base_dev))}
    failures = failures_from(dev_rows, base_dev)
    save()
    if not failures:
        finish("no change", "no dev headroom")
        return
    cache_path = pathlib.Path(run.CACHE)
    cache0 = snapshot(cache_path) if cache_path.is_dir() else {}
    proposals = propose_all(cfg.skill, base_text, dev_rows, base_dev, cfg.out, cfg.proposer_argv,
                            cfg.k, cfg.max_changed, state)
    now = fingerprint(watched)
    if now != fp0:
        changed = [p for p in watched if now.get(str(p)) != fp0.get(str(p))]
        finish("aborted", "eval files changed during the round: " +
               ", ".join(_rel_to(cfg.root, p) for p in changed))
        return
    cache1 = snapshot(cache_path) if cache_path.is_dir() else {}
    if cache1 != cache0:
        finish("aborted", "eval cache changed during the round: " + _rel_to(cfg.root, cache_path))
        return
    save()
    if not any(p["status"] == "ok" for p in proposals):
        finish("no change", "no valid proposals")
        return
    for p in proposals:
        if p["status"] != "ok":
            continue
        buf = _TeeStderr(sys.stderr)
        try:
            with contextlib.redirect_stderr(buf):
                drec = score_split(cfg, "dev", cfg.out / "proposals" / p["id"] / "SKILL.md")
        except SystemExit as e:
            reason = _exit_reason(buf, e)
            if isinstance(e.code, str):
                raise
            p["status"], p["reason"] = "score_failed", reason
            save()
            continue
        if drec.get("skill_sha256") != p["skill_sha256"]:
            p["status"], p["reason"] = "score_failed", "proposal SKILL.md changed during scoring"
            save()
            continue
        p["dev"] = dev_verdict(base_dev["per_item"], drec["per_item"], cfg.margin, MIN_WINS)
        p["status"], p["_drec"] = "scored", drec
        _write(cfg.out / "records" / ("%s-dev.json" % p["id"]), score.record_json(drec))
        save()
    winners = [p for p in proposals if p.get("dev", {}).get("pass")]
    if not winners:
        finish("no change", "no proposal beat baseline dev by the margin")
        return
    winners.sort(key=lambda p: (-p["dev"]["gain"], p["changed_lines"], int(p["id"][1:])))
    lines, used, dropped = compose(
        base_text.split("\n"), [(p["id"], p["edits"]) for p in winners], 2 * cfg.max_changed)
    best, composed_mean, why = winners[0], None, "best single %s" % winners[0]["id"]
    cand_text, cand_dev, chosen = best["text"], best["_drec"], best["id"]
    if len(used) >= 2:
        composed = "\n".join(lines)
        if frontmatter(composed) != frontmatter(base_text):
            why = "composed text changed the front matter"
        elif len(composed.encode()) - len(base_text.encode()) > MAX_GROWTH_BYTES:
            why = "composed text grows by more than %d bytes" % MAX_GROWTH_BYTES
        else:
            cand_path = cfg.out / "candidate" / "SKILL.md"
            _write(cand_path, composed)
            buf = _TeeStderr(sys.stderr)
            try:
                with contextlib.redirect_stderr(buf):
                    crec = score_split(cfg, "dev", cand_path)
            except SystemExit as e:
                reason = _exit_reason(buf, e)
                if isinstance(e.code, str):
                    raise
                why = reason
            else:
                if crec.get("skill_sha256") != sha256_text(composed):
                    why = "proposal SKILL.md changed during scoring"
                else:
                    _write(cfg.out / "records" / "composed-dev.json", score.record_json(crec))
                    composed_mean = crec["mean"]
                    if crec["mean"] > best["dev"]["mean"]:
                        cand_text, cand_dev, chosen = composed, crec, "composed"
                        why = "composed dev mean higher than the best single"
                    else:
                        why = "composed dev mean is not above the best single"
    _write(cfg.out / "candidate" / "SKILL.md", cand_text)
    rec["compose"] = {"winners": [p["id"] for p in winners], "used": used, "dropped": dropped,
                      "composed_dev_mean": composed_mean, "chosen": chosen, "why": why}
    rec["candidate"] = {"id": chosen, "skill_sha256": sha256_text(cand_text), "dev_mean": cand_dev["mean"]}
    save()
    seen = _peeked_in(cfg.rounds_dir, rec["candidate"]["skill_sha256"], rec["round"],
                      file_hashes["items"])
    if seen:
        finish("no change", "candidate already peeked in %s" % seen)
        return
    if fingerprint(watched) != fp0:
        finish("aborted", "eval files changed during the round")
        return
    rec["gate"]["others"] = {
        "status": "not needed",
        "reason": "a round can change only skills/<skill>/SKILL.md",
    }
    save()
    begin_peek(rec, ledger_path, state)
    buf = _TeeStderr(sys.stderr)
    try:
        with contextlib.redirect_stderr(buf):
            held = score_split(cfg, "heldout", cfg.out / "candidate" / "SKILL.md")
    except SystemExit as e:
        # The peek is already spent. Record the abort, then keep the scoring exit
        # (finish dies with code 1, which would hide this SystemExit).
        reason = _exit_reason(buf, e)
        try:
            finish("aborted", "held-out scoring failed after the peek was spent: " + reason)
        except SystemExit:
            pass
        raise
    if held.get("skill_sha256") != rec["candidate"]["skill_sha256"]:
        finish("aborted", "candidate SKILL.md changed during held-out scoring")  # peek spent; exits 1
    if not _same_heldout(held, base_held):
        finish("aborted", "held-out record does not match the baseline")
        return
    _write(cfg.out / "records" / "cand-heldout.json", score.record_json(held))
    ids = sorted(base_held["per_item"])
    peek = peek_stats([base_held["per_item"][i] for i in ids], [held["per_item"][i] for i in ids])
    rec["gate"]["peek"] = peek
    print("PEEK: held-out scored for %s %s (total %d of %d)" % (
        cfg.skill, rec["round"], rec["total_peeks"], MAX_TOTAL_PEEKS), file=sys.stderr)
    picked["text"], picked["dev"], picked["held"] = cand_text, cand_dev, held
    if peek["pass"]:
        finish("kept", _peek_reason(peek, True))
    else:
        finish("no change", _peek_reason(peek, False))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one improvement round on one skill.")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--executor", choices=("ollama", "stub"), default="ollama")
    ap.add_argument("--max-proposals", type=int, default=K_DEFAULT)
    ap.add_argument("--dev-margin", type=float, default=DEV_MARGIN)
    ap.add_argument("--max-changed-lines", type=int, default=MAX_CHANGED_LINES)
    ap.add_argument("--out", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--baseline-heldout", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root) if args.root else ROOT
    if args.executor == "stub":
        url, model = run.DEFAULT_URL, None
    else:
        url, model = run.executor_url(), run.executor_model()
    cfg = types.SimpleNamespace(
        skill=args.skill, root=root,
        skill_md_path=root / "skills" / args.skill / "SKILL.md",
        items_path=root / "evals" / "skills" / args.skill / "items.jsonl",
        grader_path=root / "evals" / "skills" / args.skill / "grader.py",
        rounds_dir=root / "evals" / "skills" / ROUNDS_DIR / args.skill,
        runs_dir=root / "evals" / "skills" / args.skill / RUNS_DIR,
        executor=args.executor, model=model, url=url, k=args.max_proposals, margin=args.dev_margin,
        max_changed=args.max_changed_lines,
        out=pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.mkdtemp(prefix="skill-improve-")),
        base_ref=args.base_ref,
        baseline_heldout=pathlib.Path(args.baseline_heldout) if args.baseline_heldout else None,
        apply=args.apply, proposer_argv=None, proposer_id=None)
    run_round(cfg)


if __name__ == "__main__":
    main()
