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

    python3 superintelligence/scripts/meta_select.py "should we ship an AI compliance product?"
    -> JSON {prompt, method, teams:[{team_id,short,score,weight,cells:[{cell,score}]}], delegate}
"""
import sys, json, math, re, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EMBED_URL = "http://127.0.0.1:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
META = json.loads((ROOT / "registry.json").read_text())
FLOOR = 0.55          # cosine relevance floor for a team to be considered (embed only)
DELEGATE_MARGIN = 0.12  # if top team beats 2nd by this much -> single-domain delegate (embed only)
MAX_TEAMS = 4
# Keyword scores are Jaccard-ish on a different scale than cosine — never reuse FLOOR.
KEYWORD_MAX_TEAMS = 4


def embed(texts):
    payload = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(EMBED_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
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


def select(prompt):
    profs = team_profiles()
    try:
        return select_embed(prompt, profs)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, json.JSONDecodeError, KeyError, IndexError) as e:
        out = select_keyword(prompt, profs)
        out["fallback_reason"] = f"{type(e).__name__}: {e}"
        return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: meta_select.py "<prompt>"')
    print(json.dumps(select(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
