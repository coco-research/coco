#!/usr/bin/env python3
"""
Meta-orchestrator Stage-A selector (deterministic, local nomic-embed). Given a prompt,
embeds it against each built team's profile (name + description + cell descriptions) and
ranks → top 1-4 relevant teams + candidate cells + relevance weights (for proportional
budget). Replaces the keyword-scoring shell. Free/local. The LIGHT layer — never loads
persona records; /SI-Orchestrate drills into only the selected teams afterward.

When the local embedding endpoint is unavailable, FALL BACK to keyword overlap
(same shape JSON, method=keyword). Product (Mira): this is a *supported degraded
production path* — not dogfood-only / unsupported.

Honesty bar: surface method=keyword + degraded; never claim keyword ≡ embed cosine;
NEVER auto-delegate on keyword; warn loudly; if keyword also cannot run, fail closed.
Do not reuse embed FLOOR/DELEGATE_MARGIN as if Jaccard were commensurate with cosine.

M0: with COCO_ROUTER_M0=1, each select() call writes one row to the local M0 sqlite
store (M0_DB, default ~/.local/share/coco-m0/thread.db): an HMAC-SHA256 of the prompt
keyed by a per-install salt (never the text), team keys, delegate. Off by default;
nothing leaves the machine. Outcome rows are append-only and point at a decision
(kept, overridden, rerouted, or bad) with no prompt and no HMAC. The same prompt
routed again within 600s records rerouted for the previous decision.

    python3 superintelligence/scripts/meta_select.py "should we ship an AI compliance product?"
    -> JSON {prompt, method, teams:[{team_id,short,score,weight,cells:[{cell,score}]}], delegate}
"""
import os, sys, json, math, re, hashlib, hmac, urllib.request, urllib.error, pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Any local OpenAI-compatible endpoint (LM Studio by default; Ollama in CI). Local only.
# Literal defaults stay greppable for tests/check-si-counts.py; env overrides below.
EMBED_URL = "http://127.0.0.1:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
EMBED_URL = os.environ.get("COCO_EMBED_URL", EMBED_URL)
EMBED_MODEL = os.environ.get("COCO_EMBED_MODEL", EMBED_MODEL)
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def _check_embed_host(url):
    """The prompt body goes to EMBED_URL, so refuse non-loopback hosts unless
    COCO_EMBED_ALLOW_REMOTE=1 is set explicitly."""
    import urllib.parse
    host = urllib.parse.urlparse(url).hostname
    if host not in _LOOPBACK and os.environ.get("COCO_EMBED_ALLOW_REMOTE") != "1":
        raise PermissionError(f"refusing non-loopback embedding host {host!r} (set COCO_EMBED_ALLOW_REMOTE=1 to allow)")
META = json.loads((ROOT / "registry.json").read_text())
FLOOR = 0.55          # cosine relevance floor for a team to be considered (embed only)
DELEGATE_MARGIN = 0.12  # if top team beats 2nd by this much -> single-domain delegate (embed only)
MAX_TEAMS = 4
# Keyword scores are Jaccard-ish on a different scale than cosine — never reuse FLOOR.
KEYWORD_MAX_TEAMS = 4


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        err = urllib.error.HTTPError(req.full_url, code, msg, headers, fp)
        err.close()
        raise err


def local_opener():
    """Ignore proxy env vars and refuse redirects, so a request cannot leave the machine."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def embed(texts):
    _check_embed_host(EMBED_URL)
    payload = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(EMBED_URL, data=payload, headers={"Content-Type": "application/json"})
    with local_opener().open(req, timeout=60) as r:
        d = json.loads(r.read())
    return [e["embedding"] for e in d["data"]]


def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def tokenize(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def keyword_overlap(a, b):
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return inter / math.sqrt(len(ta) * len(tb))


def team_profiles():
    """Return [(team_key, team_id, short, profile_text, {cell:desc})] for selectable teams."""
    out = []
    for key, t in META["teams"].items():
        tdir = ROOT / pathlib.Path(t["dir"]).name
        reg = tdir / "registry.json"
        if not reg.exists():
            continue
        r = json.loads(reg.read_text())
        cells = {cid: c.get("description", cid) for cid, c in r.get("cells", {}).items()}
        short = json.loads((tdir / "roster.json").read_text()).get("command_short", key[:4].title()) \
            if (tdir / "roster.json").exists() else key[:4].title()
        profile = f"{r.get('team_name', key)}. {r.get('description', '')} Cells: " + \
                  "; ".join(f"{cid} ({d})" for cid, d in cells.items())
        out.append((key, r.get("team_id", key), short, profile, cells))
    return out


def select_embed(prompt, profs):
    texts = [prompt] + [p[3] for p in profs]
    embs = embed(texts)
    pv = embs[0]
    scored = []
    for (key, tid, short, _prof, cells), tv in zip(profs, embs[1:]):
        scored.append((key, tid, short, cos(pv, tv), cells))
    scored.sort(key=lambda x: -x[3])
    top = [s for s in scored if s[3] >= FLOOR][:MAX_TEAMS] or scored[:1]
    teams_out = []
    tot = sum(s[3] for s in top) or 1.0
    for key, tid, short, score, cells in top:
        cell_scored = []
        if cells:
            cembs = embed([prompt] + list(cells.values()))
            cpv = cembs[0]
            for (cid, _d), cv in zip(cells.items(), cembs[1:]):
                cell_scored.append({"cell": cid, "score": round(cos(cpv, cv), 3)})
            cell_scored.sort(key=lambda x: -x["score"])
        teams_out.append({"team_key": key, "team_id": tid, "short": short,
                          "score": round(score, 3), "weight": round(score / tot, 3),
                          "cells": cell_scored[:4]})
    delegate = len(scored) >= 2 and (scored[0][3] - scored[1][3]) >= DELEGATE_MARGIN and len(top) >= 1
    return {"prompt": prompt,
            "method": "embed",
            "delegate": bool(delegate),
            "delegate_team": top[0][1] if delegate else None,
            "teams": teams_out}


def select_keyword(prompt, profs):
    """Supported degraded production path: top-N keyword overlap; never auto-delegate; warn loudly."""
    scored = []
    for key, tid, short, profile, cells in profs:
        score = keyword_overlap(prompt, profile)
        scored.append((key, tid, short, score, cells))
    scored.sort(key=lambda x: -x[3])
    # Always return top-N — do NOT apply embed FLOOR (Jaccard ≪ cosine; floor collapses to wrong top-1).
    top = scored[:KEYWORD_MAX_TEAMS] or scored[:1]
    tot = sum(max(s[3], 1e-9) for s in top) or 1.0
    teams_out = []
    for key, tid, short, score, cells in top:
        cell_scored = []
        if cells:
            for cid, desc in cells.items():
                cell_scored.append({"cell": cid, "score": round(keyword_overlap(prompt, f"{cid} {desc}"), 3)})
            cell_scored.sort(key=lambda x: -x["score"])
        teams_out.append({"team_key": key, "team_id": tid, "short": short,
                          "score": round(score, 3), "weight": round(max(score, 1e-9) / tot, 3),
                          "cells": cell_scored[:4]})
    warn = (
        "keyword fallback active: embedding endpoint unavailable; "
        "scores are not commensurate with embed cosine; auto-delegate disabled; "
        "treat as degraded Stage A — do not trust single-team collapse"
    )
    print(f"meta_select WARN: {warn}", file=sys.stderr)
    return {"prompt": prompt,
            "method": "keyword",
            "delegate": False,           # LOCKED: never auto-delegate on keyword
            "delegate_team": None,
            "degraded": True,
            "warn": warn,
            "teams": teams_out}


M0_FLAG = "COCO_ROUTER_M0"  # set to 1 to record each decision in the local M0 store
M0_PROJECT = "coco-router"
M0_SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "m0" / "skills" / "m0" / "scripts"


M0_SALT_NAME = "router-salt"
M0_TIMEOUT_MS = 500  # short sqlite busy timeout so a locked store can't stall routing
M0_OUTCOMES = ("kept", "overridden", "rerouted", "bad")
M0_CLI_OUTCOMES = ("kept", "overridden", "bad")  # rerouted is written only by select()
REROUTE_WINDOW_S = 600
IMPLICIT_KEPT_S = 24 * 60 * 60
SUMMARY_LIMIT = 500  # one store page; older than this page is outside the summary


def _m0_store():
    sys.path.insert(0, str(M0_SCRIPTS))
    try:
        import m0_server
    finally:
        sys.path.remove(str(M0_SCRIPTS))
    db = m0_server.default_db_path()  # honours M0_DB; default ~/.local/share/coco-m0/thread.db
    if not db.parent.exists():
        os.makedirs(db.parent, mode=0o700, exist_ok=True)
    return m0_server.Store(db_path=db, timeout_ms=M0_TIMEOUT_MS)


def _m0_salt(data_dir):
    """32-byte per-install salt at <m0 data dir>/router-salt, created once with mode 0600."""
    path = os.path.join(str(data_dir), M0_SALT_NAME)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        with open(path, "rb") as f:
            salt = f.read()
        if len(salt) != 32:
            raise ValueError("router-salt is not 32 bytes")
        return salt
    salt = os.urandom(32)
    try:
        os.write(fd, salt)
    finally:
        os.close(fd)
    return salt


def _age_s(ts, now):
    if not isinstance(ts, str) or not ts:
        return None
    try:
        stamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return (now - stamp).total_seconds()


def _m0_meta(row):
    raw = row.get("meta_json")
    if raw is None:
        raw = row.get("meta")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _entries(page):
    if not isinstance(page, dict):
        return []
    entries = page.get("entries")
    if not isinstance(entries, list):
        return []
    return [row for row in entries if isinstance(row, dict)]


def _is_decision(row):
    meta = _m0_meta(row)
    return "prompt_hmac_sha256" in meta and "outcome" not in meta


def _write_outcome(store, decision_id, outcome):
    """Append one outcome row. No prompt and no HMAC."""
    if outcome not in M0_OUTCOMES:
        raise ValueError(outcome)
    return store.write({
        "project": M0_PROJECT,
        "kind": "ambient_signal",
        "source_tool": "meta_select",
        "text": f"router outcome {outcome} {decision_id[:12]}",
        "meta": {"decision_id": decision_id, "outcome": outcome},
    })


def _maybe_reroute(store, digest):
    """Same prompt again inside 600s → the previous answer did not land."""
    page = store.read(project=M0_PROJECT, limit=50, kind="ambient_signal")
    row = next((r for r in _entries(page) if _is_decision(r)), None)
    if row is None:
        return
    age = _age_s(row.get("ts"), datetime.now(timezone.utc))
    decision_id = row.get("id")
    if (
        age is not None
        and 0 <= age < REROUTE_WINDOW_S
        and _m0_meta(row).get("prompt_hmac_sha256") == digest
        and isinstance(decision_id, str)
        and decision_id
    ):
        _write_outcome(store, decision_id, "rerouted")


def m0_record(prompt, out, store=None):
    """Write one M0 row for a routing decision. Opt-in, local sqlite only.

    Stores an HMAC-SHA256 of the prompt under a per-install salt, never the
    prompt text, so short prompts can't be recovered by dictionary. The same
    prompt again within 600s also appends a rerouted outcome for the previous
    decision. Never raises (SystemExit included): a logging failure must not
    change routing.
    """
    if store is None and os.environ.get(M0_FLAG) != "1":
        return None
    try:
        if store is None:
            store = _m0_store()
        salt = _m0_salt(pathlib.Path(store.db_path).parent)
        digest = hmac.new(salt, prompt.encode("utf-8"), hashlib.sha256).hexdigest()
        try:
            _maybe_reroute(store, digest)
        except (Exception, SystemExit):
            pass  # lookup is best effort; the decision write still happens
        teams = [t.get("team_key") for t in out.get("teams", [])]
        delegate_team = teams[0] if out.get("delegate") and teams else None
        return store.write({
            "project": M0_PROJECT,
            "kind": "ambient_signal",
            "source_tool": "meta_select",
            "text": f"router decision {digest[:12]}",
            "meta": {"prompt_hmac_sha256": digest, "method": out.get("method"), "teams": teams,
                     "delegate": bool(out.get("delegate")), "delegate_team": delegate_team},
        })
    except (Exception, SystemExit) as e:  # noqa: BLE001 - logging is best effort
        print(f"meta_select WARN: M0 write skipped ({type(e).__name__})", file=sys.stderr)
        return None


def _find_decision(store, decision_id=None, limit=SUMMARY_LIMIT):
    page = store.read(project=M0_PROJECT, limit=limit, kind="ambient_signal")
    for row in _entries(page):
        if not _is_decision(row):
            continue
        if decision_id is None or row.get("id") == decision_id:
            return row
    return None


def m0_outcomes_summary(store, days=7, now=None):
    """Count decisions and outcomes in the last `days` days. Read-only."""
    now = now or datetime.now(timezone.utc)
    window = days * 86400
    page = store.read(project=M0_PROJECT, limit=SUMMARY_LIMIT, kind="ambient_signal")
    decisions = []
    counts = {name: 0 for name in M0_OUTCOMES}
    linked = set()
    for row in _entries(page):
        meta = _m0_meta(row)
        age = _age_s(row.get("ts"), now)
        in_window = age is not None and 0 <= age <= window
        if _is_decision(row):
            if in_window:
                decisions.append((row.get("id"), age))
            continue
        outcome = meta.get("outcome")
        if outcome not in counts:
            continue
        decision_id = meta.get("decision_id")
        if isinstance(decision_id, str):
            linked.add(decision_id)
        if in_window:
            counts[outcome] += 1
    implicit = sum(
        1 for did, age in decisions
        if age > IMPLICIT_KEPT_S and isinstance(did, str) and did not in linked
    )
    return {"days": days, "decisions": len(decisions), "outcomes": counts, "no_outcome_kept": implicit}


def _select(prompt):
    profs = team_profiles()
    try:
        return select_embed(prompt, profs)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, json.JSONDecodeError, KeyError, IndexError) as e:
        out = select_keyword(prompt, profs)
        out["fallback_reason"] = f"{type(e).__name__}: {e}"
        return out


def select(prompt):
    out = _select(prompt)
    m0_record(prompt, out)
    return out


def _exit2(msg):
    print(msg)
    raise SystemExit(2)


def _require_m0():
    if os.environ.get(M0_FLAG) != "1":
        _exit2("COCO_ROUTER_M0=1 required")


def _parse_days(args):
    if not args:
        return 7
    if len(args) != 2 or args[0] != "--days":
        _exit2("invalid days")
    try:
        days = int(args[1])
    except ValueError:
        _exit2("invalid days")
    if days < 1:
        _exit2("invalid days")
    return days


def _parse_outcome_args(args):
    outcome = None
    decision = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--decision":
            if decision is not None or i + 1 >= len(args):
                _exit2("no decision found")
            decision = args[i + 1]
            i += 2
            continue
        if arg.startswith("-") or outcome is not None:
            _exit2("unknown outcome")
        outcome = arg
        i += 1
    if outcome is None:
        _exit2("unknown outcome")
    return outcome, decision


def _cli_outcome(args):
    _require_m0()
    outcome, decision_id = _parse_outcome_args(args)
    if outcome not in M0_CLI_OUTCOMES:
        _exit2("unknown outcome")
    store = _m0_store()
    row = _find_decision(store, decision_id)
    if row is None or not isinstance(row.get("id"), str) or not row.get("id"):
        _exit2("no decision found")
    _write_outcome(store, row["id"], outcome)


def _cli_summary(args):
    _require_m0()
    days = _parse_days(args)
    store = _m0_store()
    print(json.dumps(m0_outcomes_summary(store, days=days)))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.exit('usage: meta_select.py "<prompt>"')
    if args[0] == "--outcome":
        _cli_outcome(args[1:])
        return
    if args[0] == "--outcomes-summary":
        _cli_summary(args[1:])
        return
    print(json.dumps(select(" ".join(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
