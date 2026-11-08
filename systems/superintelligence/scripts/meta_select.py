#!/usr/bin/env python3
"""
Meta-orchestrator Stage-A selector (deterministic, local nomic-embed). Given a prompt,
embeds it against each built team's profile (name + description + cell descriptions) and
ranks → top 1-4 relevant teams + candidate cells + relevance weights (for proportional
budget). Replaces the keyword-scoring shell. Free/local. The LIGHT layer — never loads
persona records; /SI-Orchestrate drills into only the selected teams afterward.

Tries LM Studio (:1234, text-embedding-nomic-embed-text-v1.5), then Ollama
(:11434, nomic-embed-text), unless COCO_EMBED_URL pins one endpoint. When no
embedding server answers, FALL BACK to keyword overlap (same shape JSON,
method=keyword). Product (Mira): this is a *supported degraded production path*
— not dogfood-only / unsupported.

Honesty bar: surface method=keyword + degraded; never claim keyword ≡ embed cosine;
NEVER auto-delegate on keyword; warn loudly; if keyword also cannot run, fail closed.
Do not reuse embed FLOOR/DELEGATE_MARGIN as if Jaccard were commensurate with cosine.

M0: with COCO_ROUTER_M0=1, each select() call writes one row to the local M0 sqlite
store (M0_DB, default ~/.local/share/coco-m0/thread.db): an HMAC-SHA256 of the prompt
keyed by a per-install salt (never the text), team keys, delegate. Off by default;
nothing leaves the machine. Outcome rows are append-only and point at a decision
(kept, overridden, rerouted, or bad) with no prompt and no HMAC. The same prompt
routed again within 600s records rerouted for the previous decision.

    python3 superintelligence/scripts/meta_select.py -- "should we ship an AI compliance product?"
    -> JSON {prompt, method, teams:[{team_id,short,score,weight,cells:[{cell,score}]}], delegate}

`--` ends options: what follows is always the prompt, even if it starts with --outcome.
Option errors (M0 off, unknown outcome, bad --days, no decision) print one line to
stderr and exit 2, leaving stdout empty. Run with no arguments for the full usage,
including the 500-row cap on --outcomes-summary.
"""
import errno, os, socket, sys, json, math, re, hashlib, hmac, urllib.request, urllib.error, pathlib
from datetime import datetime, timezone

from local_http import local_opener  # sibling module, shared with evals/skills/run.py

ROOT = pathlib.Path(__file__).resolve().parents[1]
# LM Studio first, then Ollama. Literal defaults stay greppable for tests/check-si-counts.py.
# COCO_EMBED_URL pins one endpoint. COCO_EMBED_ENDPOINTS=url|model,url|model replaces the
# pair list (tests). The first endpoint that answers is written back to EMBED_URL/EMBED_MODEL.
EMBED_URL = "http://127.0.0.1:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
_DEFAULT_EMBED_URL = EMBED_URL
_DEFAULT_EMBED_MODEL = EMBED_MODEL
_EMBED_ENDPOINTS = (
    (EMBED_URL, EMBED_MODEL),
    ("http://127.0.0.1:11434/v1/embeddings", "nomic-embed-text"),
)
EMBED_URL = os.environ.get("COCO_EMBED_URL", EMBED_URL)
EMBED_MODEL = os.environ.get("COCO_EMBED_MODEL", EMBED_MODEL)
_IMPORT_URL = EMBED_URL  # value at import, so a later patch of EMBED_URL is visible
_pinned = False  # set once an endpoint has answered; further calls skip the probe
_NO_EMBED = "router: no embedding server, using keyword matching"
_DOCTOR_PROBE = "ping"  # fixed word; --doctor never sends the user's prompt
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
_CONNECT_ERRNO = {
    errno.ECONNREFUSED, errno.ETIMEDOUT, errno.EHOSTUNREACH,
    errno.ENETUNREACH, errno.ENETDOWN, errno.EHOSTDOWN,
}


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


def _endpoint_list():
    """(url, model) pairs when COCO_EMBED_URL is not pinning a single endpoint."""
    model_over = os.environ.get("COCO_EMBED_MODEL")
    raw = os.environ.get("COCO_EMBED_ENDPOINTS")
    if raw:
        pairs = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            url, sep, model = part.partition("|")
            pairs.append((url.strip(), model_over or (model.strip() if sep else _DEFAULT_EMBED_MODEL)))
        return pairs
    return [(url, model_over or model) for url, model in _EMBED_ENDPOINTS]


def _is_connect_failure(exc):
    """Refused, unreachable, or timeout. HTTP and parse errors are not."""
    if isinstance(exc, urllib.error.HTTPError):
        return False
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (TimeoutError, ConnectionRefusedError, socket.gaierror)):
        return True
    return isinstance(reason, OSError) and getattr(reason, "errno", None) in _CONNECT_ERRNO


def _embed_at(url, model, texts):
    _check_embed_host(url)
    payload = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with local_opener().open(req, timeout=60) as r:
        data = json.loads(r.read())
    return [item["embedding"] for item in data["data"]]


def _walk(texts):
    """Try each candidate. Only a connection failure moves on; anything else propagates."""
    global EMBED_URL, EMBED_MODEL, _pinned
    last = None
    endpoints = _endpoint_list()
    if not endpoints:
        raise OSError("no embedding endpoint")
    for url, model in endpoints:
        try:
            vecs = _embed_at(url, model, texts)
        except Exception as exc:
            if _is_connect_failure(exc):
                last = exc
                continue
            raise
        EMBED_URL, EMBED_MODEL, _pinned = url, model, True
        return vecs
    raise last


def embed(texts):
    """Embed texts. COCO_EMBED_URL, when set, is the only endpoint tried.

    A patched EMBED_URL (the unit tests) is used as-is. Otherwise the built-in
    list is tried until one answers, and that winner sticks for the process.
    """
    global EMBED_URL, EMBED_MODEL, _pinned
    env_url = os.environ.get("COCO_EMBED_URL")
    patched = EMBED_URL != _IMPORT_URL and not _pinned
    if env_url and not patched:
        EMBED_URL = env_url
        env_model = os.environ.get("COCO_EMBED_MODEL")
        if env_model:
            EMBED_MODEL = env_model
        return _embed_at(EMBED_URL, EMBED_MODEL, texts)
    if _pinned or patched or _IMPORT_URL != _DEFAULT_EMBED_URL:
        return _embed_at(EMBED_URL, EMBED_MODEL, texts)
    return _walk(texts)


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
    print(_NO_EMBED, file=sys.stderr)
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
    """Count decisions and outcomes in the last `days` days. Read-only.

    Reads the newest SUMMARY_LIMIT rows. When that page is full, older rows are not
    counted and the result adds truncated=True and rows_read.
    """
    now = now or datetime.now(timezone.utc)
    window = days * 86400
    page = store.read(project=M0_PROJECT, limit=SUMMARY_LIMIT, kind="ambient_signal")
    rows = _entries(page)
    decisions = []
    counts = {name: 0 for name in M0_OUTCOMES}
    linked = set()
    for row in rows:
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
    out = {"days": days, "decisions": len(decisions), "outcomes": counts, "no_outcome_kept": implicit}
    if len(rows) >= SUMMARY_LIMIT:
        # ponytail: the store's read() has no offset or before cursor, so one page is all there is.
        out.update(truncated=True, rows_read=len(rows))
    return out


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


USAGE = """usage: meta_select.py [--] "<prompt>"
       meta_select.py --doctor
       meta_select.py --outcome kept|overridden|bad [--decision ID]
       meta_select.py --outcomes-summary [--days N]
`--` ends options: everything after it is the prompt, even if it starts with --outcome.
--doctor probes LM Studio then Ollama (or COCO_EMBED_URL) with a fixed word and prints
which endpoint answered. It does not route a prompt.
--outcome and --outcomes-summary need COCO_ROUTER_M0=1. Their errors go to stderr, exit 2.
--outcomes-summary reads the newest 500 router rows only (the store has no cursor). When
that page is full the JSON adds "truncated": true and "rows_read": 500, and older rows
are not counted."""


def _exit2(msg):
    print(msg, file=sys.stderr)
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


def _cli_doctor():
    """Probe the same endpoint order as embed(). One fixed word, never a user prompt."""
    try:
        embed([_DOCTOR_PROBE])
    except PermissionError:
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError,
            json.JSONDecodeError, KeyError, IndexError):
        print(_NO_EMBED, file=sys.stderr)
        raise SystemExit(1)
    print(f"router: embedding via {EMBED_URL} ({EMBED_MODEL})")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--"]:  # end of options: the rest is the prompt, whatever it starts with
        args = args[1:]
    elif args[:1] == ["--doctor"]:
        if len(args) != 1:
            _exit2("--doctor takes no arguments")
        _cli_doctor()
        return
    elif args[:1] == ["--outcome"]:
        _cli_outcome(args[1:])
        return
    elif args[:1] == ["--outcomes-summary"]:
        _cli_summary(args[1:])
        return
    if not args:
        sys.exit(USAGE)
    print(json.dumps(select(" ".join(args)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
