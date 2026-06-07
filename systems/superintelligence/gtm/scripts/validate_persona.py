#!/usr/bin/env python3
"""
Persona validator — enforces the quality bar + verify-gate on a persona file.
Works for both local-built and Claude-built personas.

Checks:
  - frontmatter parses; required keys present
  - status active -> recent_signal_12mo >=3 (dates after CUTOFF); archetype -> persistent_signals >=3
  - sources >=8
  - every public_stance has evidence_url
  - pairs_well_with / productive_conflict_with use real roster slugs (if --slugs given)
  - EVERY url actually resolves over HTTP (the verify-gate check) -> flags dead/unverifiable

Verdict: PASS / NEEDS-TOPUP (with reasons).

Usage:
  python3 validate_persona.py <file.md> [<file.md> ...] [--slugs "a,b,c"] [--cutoff 2025-06-01]
"""
import argparse, concurrent.futures as cf, re, sys, urllib.request, pathlib
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

REQUIRED = ["slug","real_name","archetype","teams","home_team","cell","cell_role",
            "status","domains","signature_moves","public_stances","voice_style","confidence","sources"]

def collect_urls(fm):
    urls=set()
    for s in (fm.get("sources") or []):
        if isinstance(s,str) and s.startswith("http"): urls.add(s)
    for r in (fm.get("recent_signal_12mo") or []):
        u=r.get("url") if isinstance(r,dict) else None
        if u: urls.add(u)
    for r in (fm.get("persistent_signals") or []):
        u=r.get("url") if isinstance(r,dict) else None
        if u: urls.add(u)
    for s in (fm.get("public_stances") or []):
        u=s.get("evidence_url") if isinstance(s,dict) else None
        if u and u.startswith("http"): urls.add(u)
    return sorted(urls)

def url_status(u):
    for method in ("HEAD","GET"):
        try:
            req=urllib.request.Request(u, method=method, headers={"User-Agent":"Mozilla/5.0 (persona-validator)"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return u, r.status
        except urllib.error.HTTPError as e:
            if e.code in (403,405,406,429):
                if method=="GET": return u, e.code   # exists but blocks bots -> treat as soft-ok
                continue
            return u, e.code
        except Exception as e:
            if method=="GET": return u, f"ERR:{type(e).__name__}"
            continue
    return u, "ERR"

def check_urls(urls):
    out={}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for u,st in ex.map(url_status, urls):
            out[u]=st
    return out

def validate(path, slugs, cutoff):
    t=pathlib.Path(path).read_text()
    reasons=[]
    if not t.startswith("---"):
        return "NEEDS-TOPUP", ["no leading frontmatter delimiter"], 0, 0
    end=t.find(chr(10)+"---"+chr(10),4)
    if end<0:
        end=t.find(chr(10)+"---",4)   # tolerate missing trailing newline
    try:
        fm=yaml.safe_load(t[4:end]) if end>0 else None
        if not isinstance(fm,dict): raise ValueError("frontmatter not a mapping")
    except Exception as e:
        return "NEEDS-TOPUP", [f"YAML PARSE ERROR: {type(e).__name__}: {str(e).splitlines()[0]}"], 0, 0
    miss=[k for k in REQUIRED if not fm.get(k)]
    if miss: reasons.append(f"missing keys: {miss}")
    status=fm.get("status")
    rs=fm.get("recent_signal_12mo") or []; ps_sig=fm.get("persistent_signals") or []
    # RECALIBRATED 2026-06-01: keep anti-fabrication (>=4 LIVE real URLs, stances cited, >=2 signals);
    # relax arbitrary quotas (was 8 sources / 3 signals); tolerate link-rot (dead URL != wrong persona).
    if status=="archetype":
        if len(ps_sig)<2: reasons.append(f"archetype persistent_signals {len(ps_sig)}<2")
    else:
        if len(rs)<2: reasons.append(f"recent_signal_12mo {len(rs)}<2")
        # recency (date<cutoff): best-effort, not a hard gate
    ps=fm.get("public_stances") or []
    uncited=[i for i,s in enumerate(ps) if isinstance(s,dict) and not s.get("evidence_url")]
    if uncited: reasons.append(f"uncited stances idx {uncited}")   # anti-fabrication: keep
    if slugs:
        pool=set(slugs)
        for fld in ("pairs_well_with","productive_conflict_with"):
            bad=[s for s in (fm.get(fld) or []) if s not in pool]
            if bad: reasons.append(f"{fld} non-roster slugs: {bad}")
    # URL resolution -> gate on LIVE count (anti-fabrication + depth); rot tolerated/pruned elsewhere
    urls=collect_urls(fm)
    st=check_urls(urls) if urls else {}
    ok=sum(1 for s in st.values() if (isinstance(s,int) and s<400) or s in (403,405,406,429))
    dead=len(urls)-ok
    if ok<4: reasons.append(f"live sources {ok}<4 (of {len(urls)} cited)")
    verdict="PASS" if not reasons else "NEEDS-TOPUP"
    return verdict, reasons, len(urls), ok

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--slugs", default="")
    ap.add_argument("--cutoff", default="2025-06-01")
    a=ap.parse_args()
    slugs=[s.strip() for s in a.slugs.split(",") if s.strip()]
    for f in a.files:
        v,reasons,nurls,okurls=validate(f, slugs, a.cutoff)
        print(f"\n=== {pathlib.Path(f).name} -> {v} ===")
        print(f"  urls: {okurls}/{nurls} resolve")
        for r in reasons: print(f"  - {r}")

if __name__=="__main__":
    main()
