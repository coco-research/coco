#!/usr/bin/env python3
"""
Production persona builder via QB AI Gateway gpt-5.4-nano. Team-portable: drop into
superintelligence/<team>/scripts/ and run. Reuses the SAME retriever + prompts +
validator as the local pipeline (imports build_local), swapping only the LLM backend.
Parallel (API is I/O-bound, not GPU-bound). Post-processes fix the two nano quirks
(missing closing '---', dead URLs). ~$0.003/persona, ~35s each, ~85-90% clean yield.

    python3 build_nano.py --all                 # whole team, parallel
    python3 build_nano.py --cell <cell>
    python3 build_nano.py --only <slug> [--force]

Resume: skips a persona whose file already exists AND validates PASS (unless --force).
"""
import sys, os, json, time, argparse, urllib.request, re, pathlib
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

KEY = (pathlib.Path.home() / ".coco" / ".qb-gateway-key").read_text().strip()
PROJECT = os.environ.get("QB_OPENAI_PROJECT", "39867e95-6e22-4c1b-b20d-aba44c739c72")
URL = f"https://openai.prod.ai-gateway.quantumblack.com/{PROJECT}/v1/chat/completions"
MODEL = os.environ.get("COCO_GPT5_NANO_MODEL", "gpt-5.4-nano-2026-03-17")
PIN, POUT = 0.05 / 1e6, 0.40 / 1e6
MAXW = int(os.environ.get("NANO_WORKERS", "5"))
CUTOFF = "2025-06-01"


def gpt5(messages, max_completion_tokens=16000, timeout=240):
    payload = json.dumps({"model": MODEL, "messages": messages,
                          "max_completion_tokens": max_completion_tokens}).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"], time.time() - t0, d.get("usage", {}) or {}


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
    sysp = bl.sys_prompt(POOL)
    user = (f"Subject: {name} — {anchor}\nslug: {slug}\ncell: {cell}\ncell_role: {role}\n"
            f"teams: [{TEAM_ID}]\nhome_team: {TEAM_ID}\nlast_verified: 2026-06-01\n\n"
            f"WEB CONTEXT:\n{wc}\n\nWrite the complete persona file. Output only the file.")
    draft, t1, u1 = gpt5([{"role": "system", "content": sysp}, {"role": "user", "content": user}])
    draft = bl.clean(draft)
    repair = ("Repair this persona file WITHOUT fabricating: (1) every recent_signal_12mo url + stance evidence_url "
              "must be a REAL url from WEB CONTEXT (drop field if none); (2) `sources` must list ALL those real URLs "
              "deduped (>=8 if available); (3) pairs/conflict use only allowed slugs; (4) keep prose. Output only the file.\n\n"
              f"WEB CONTEXT:\n{wc}\n\nDRAFT:\n{draft}")
    fixed, t2, u2 = gpt5([{"role": "system", "content": sysp}, {"role": "user", "content": repair}])
    fixed = bl.clean(fixed)
    fixed = bl.pick_parseable(fixed, draft)
    fixed = close_frontmatter(fixed)
    fixed = prune_dead_urls(fixed)
    (PERSONAS / f"{slug}.md").write_text(fixed + "\n", encoding="utf-8")
    rd = RESEARCH / slug; rd.mkdir(exist_ok=True)
    dump = [f"# Research dump (gpt-5.4-nano)\nname: {name}\n", "## Fetched pages"]
    for u, txt in pages:
        dump.append(f"\n### {u}\n{txt}")
    dump.append("\n## Dated news")
    for n in news:
        dump.append(f"- {n['date']} :: {n['title']} :: {n['url']}")
    rd.joinpath("notes.md").write_text("\n".join(dump) + "\n", encoding="utf-8")
    v, reasons, nurls, okurls = validate(str(PERSONAS / f"{slug}.md"), POOL, CUTOFF)
    cost = (u1.get("prompt_tokens", 0) + u2.get("prompt_tokens", 0)) * PIN + \
           (u1.get("completion_tokens", 0) + u2.get("completion_tokens", 0)) * POUT
    return slug, v, reasons, okurls, nurls, t1 + t2, cost


def needs_build(p, force):
    if force:
        return True
    f = PERSONAS / f"{p['slug']}.md"
    if not f.exists():
        return True
    try:
        v, *_ = validate(str(f), POOL, CUTOFF)
        return v != "PASS"          # rebuild anything not already PASS
    except Exception:
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true"); ap.add_argument("--only", default="")
    ap.add_argument("--cell", default=""); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    todo = ROSTER["personas"]
    if a.only:
        todo = [p for p in todo if p["slug"] == a.only]
    elif a.cell:
        todo = [p for p in todo if p["cell"] == a.cell]
    elif not a.all:
        sys.exit("pass --all | --only <slug> | --cell <cell>")
    todo = [p for p in todo if needs_build(p, a.force)]
    print(f"[{TEAM}] building {len(todo)} persona(s) via {MODEL}, {MAXW} parallel")
    npass = 0; tot = 0.0; done = 0
    with ThreadPoolExecutor(max_workers=MAXW) as ex:
        futs = {ex.submit(build_one, p): p for p in todo}
        for fut in as_completed(futs):
            p = futs[fut]; done += 1
            try:
                slug, v, reasons, ok, n, dt, cost = fut.result()
            except Exception as e:
                print(f"[{done}/{len(todo)}] {p['slug']:24} ERROR {type(e).__name__}: {str(e)[:70]}"); continue
            npass += v == "PASS"; tot += cost
            print(f"[{done}/{len(todo)}] {slug:24} {v:11} urls {ok}/{n} {dt:.0f}s ${cost:.4f} {('; '.join(reasons))[:70]}")
    print(f"\n[{TEAM}] DONE: {npass}/{len(todo)} PASS  total ${tot:.4f}")


if __name__ == "__main__":
    main()
