#!/usr/bin/env python3
"""
Production persona builder via Cursor headless agent (gemini-3.5-flash). Team-portable:
drop into superintelligence/<team>/scripts/. Reuses build_local retriever + verify-gate
prompt + validator. Parallel (separate node procs — keep workers modest). Archetype rule
+ both post-fixes (close '---', drop dead URLs) baked in. Writes to <team>/personas/.

    python3 build_cursor.py --all [--workers 6]
    python3 build_cursor.py --cell <cell> | --only <slug> [--force]

Resume: skips a persona whose file already validates PASS (unless --force).
"""
import sys, os, json, time, argparse, subprocess, re, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_local as bl
from validate_persona import validate, check_urls

TEAM_DIR = HERE.parents[0]
TEAM = TEAM_DIR.name
ROSTER = bl.ROSTER
TEAM_ID = ROSTER["team_id"]
POOL = bl.POOL
PERSONAS = TEAM_DIR / "personas"; PERSONAS.mkdir(exist_ok=True)
RESEARCH = TEAM_DIR / "research"; RESEARCH.mkdir(exist_ok=True)
CURSOR = "/Applications/Cursor.app/Contents/Resources/app/bin/cursor"
MODEL = os.environ.get("CURSOR_MODEL", "gemini-3.5-flash")
CUTOFF = "2025-06-01"

ARCHETYPE_RULE = (
    "\n\nARCHETYPE RULE: If the subject is DECEASED, or retired/emeritus with little public "
    "activity in the last 12 months, set `status: archetype` and provide >=3 `persistent_signals` "
    "(enduring dated positions/works, each with a real evidence_url from WEB CONTEXT) INSTEAD of "
    "recent_signal_12mo. Otherwise `status: active` with >=3 recent_signal_12mo dated after 2025-06-01.")


def cursor_llm(prompt, timeout=int(os.environ.get("CURSOR_TIMEOUT","420"))):
    env = dict(os.environ, TERM="xterm")
    r = subprocess.run(
        [CURSOR, "agent", "-p", "--output-format", "text", "--mode", "ask",
         "--trust", "--model", MODEL, prompt],
        capture_output=True, text=True, timeout=timeout, env=env, cwd=str(TEAM_DIR))
    return r.stdout, r.returncode, r.stderr[:160]


def close_frontmatter(t):
    if t.startswith("---") and t.find("\n---\n", 4) < 0:
        m = re.search(r"\n(#\s)", t)
        if m:
            t = t[:m.start() + 1] + "---\n\n" + t[m.start() + 1:]
    return t


def prune_dead_urls(t):
    urls = set(re.findall(r"https?://[^\s'\"]+", t))
    if not urls:
        return t
    st = check_urls(list(urls))
    dead = {u for u, s in st.items() if (isinstance(s, str) and s.startswith("ERR")) or s == 404}
    if not dead:
        return t
    return "\n".join(ln for ln in t.splitlines() if not any(d in ln for d in dead)) + "\n"


def build_one(p):
    slug, name, cell = p["slug"], p["name"], p["cell"]
    role, anchor = p.get("role", "specialist"), p["anchor"]
    pages, news = bl.retriever.search(name, anchor, cell)
    wc, allow = bl.retriever.context_block(pages, news)
    sysp = bl.sys_prompt(POOL) + ARCHETYPE_RULE
    prompt = (sysp + "\n\n=== TASK ===\n"
              f"Subject: {name} — {anchor}\nslug: {slug}\ncell: {cell}\ncell_role: {role}\n"
              f"teams: [{TEAM_ID}]\nhome_team: {TEAM_ID}\nlast_verified: 2026-06-01\n\n"
              f"WEB CONTEXT:\n{wc}\n\n"
              "Output ONLY the complete persona Markdown file (start at the first `---`). No commentary, no code fences.")
    t0 = time.time()
    out, rc, err = cursor_llm(prompt)
    fixed = bl.clean(out)
    fixed = close_frontmatter(fixed)
    fixed = prune_dead_urls(fixed)
    (PERSONAS / f"{slug}.md").write_text(fixed + "\n", encoding="utf-8")
    rd = RESEARCH / slug; rd.mkdir(exist_ok=True)
    dump = [f"# Research dump (gemini-3.5-flash via Cursor)\nname: {name}\n", "## Fetched pages"]
    for u, txt in pages:
        dump.append(f"\n### {u}\n{txt}")
    dump.append("\n## Dated news")
    for n in news:
        dump.append(f"- {n['date']} :: {n['title']} :: {n['url']}")
    rd.joinpath("notes.md").write_text("\n".join(dump) + "\n", encoding="utf-8")
    v, reasons, nurls, okurls = validate(str(PERSONAS / f"{slug}.md"), POOL, CUTOFF)
    return slug, v, reasons, okurls, nurls, time.time() - t0, rc, err


def needs_build(p, force):
    if force:
        return True
    f = PERSONAS / f"{p['slug']}.md"
    if not f.exists():
        return True
    try:
        v, *_ = validate(str(f), POOL, CUTOFF)
        return v != "PASS"
    except Exception:
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true"); ap.add_argument("--only", default="")
    ap.add_argument("--cell", default=""); ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("CURSOR_WORKERS", "6")))
    a = ap.parse_args()
    todo = ROSTER["personas"]
    if a.only:
        todo = [p for p in todo if p["slug"] == a.only]
    elif a.cell:
        todo = [p for p in todo if p["cell"] == a.cell]
    elif not a.all:
        sys.exit("pass --all | --only <slug> | --cell <cell>")
    todo = [p for p in todo if needs_build(p, a.force)]
    print(f"[{TEAM}] gemini build: {len(todo)} persona(s) via {MODEL}, {a.workers} parallel")
    npass = 0; done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(build_one, p): p for p in todo}
        for fut in as_completed(futs):
            p = futs[fut]; done += 1
            try:
                slug, v, reasons, ok, n, dt, rc, err = fut.result()
            except Exception as e:
                print(f"[{done}/{len(todo)}] {p['slug']:24} ERROR {type(e).__name__}: {str(e)[:60]}"); continue
            npass += v == "PASS"
            flag = "" if rc == 0 else f" rc={rc}"
            print(f"[{done}/{len(todo)}] {slug:24} {v:11} urls {ok}/{n} {dt:.0f}s{flag} {('; '.join(reasons))[:60]}")
    print(f"\n[{TEAM}] DONE: {npass}/{len(todo)} PASS")


if __name__ == "__main__":
    main()
