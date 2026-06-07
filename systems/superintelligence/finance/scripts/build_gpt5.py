#!/usr/bin/env python3
"""
EXPERIMENT: build personas via QB AI Gateway gpt-5.4-nano (same model CoCo uses),
reusing the EXACT retriever + prompts + validator from build_local — only the LLM
backend changes. Writes to finance/personas_gpt5/ (sandbox, side-by-side with the
local qwen output in finance/personas/) so we can compare quality head-to-head.

    python3 build_gpt5.py                         # default 3-slug test set
    python3 build_gpt5.py --only warren-buffett
"""
import sys, pathlib, json, time, argparse, urllib.request, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_local as bl                       # reuse sys_prompt, clean, pick_parseable, retriever, POOL, ROSTER
from validate_persona import validate, check_urls


def close_frontmatter(t):
    """If the model omitted the closing '---' before the narrative, insert it."""
    if t.startswith("---") and t.find("\n---\n", 4) < 0:
        m = re.search(r"\n(#\s)", t)            # first markdown heading = narrative start
        if m:
            t = t[:m.start() + 1] + "---\n\n" + t[m.start() + 1:]
    return t


def prune_dead_urls(t):
    """Drop any line carrying a URL that 404s / is unresolvable (keeps soft-ok 403/405/429)."""
    urls = set(re.findall(r"https?://[^\s'\"]+", t))
    if not urls:
        return t
    st = check_urls(list(urls))
    dead = {u for u, s in st.items()
            if (isinstance(s, str) and s.startswith("ERR")) or s == 404}
    if not dead:
        return t
    keep = [ln for ln in t.splitlines()
            if not any(d in ln for d in dead)]
    return "\n".join(keep) + "\n"

FIN = HERE.parents[0]
OUT = FIN / "personas_gpt5"; OUT.mkdir(exist_ok=True)
RES = FIN / "research_gpt5"; RES.mkdir(exist_ok=True)

KEY = (pathlib.Path.home() / ".coco" / ".qb-gateway-key").read_text().strip()
PROJECT = "39867e95-6e22-4c1b-b20d-aba44c739c72"
URL = f"https://openai.prod.ai-gateway.quantumblack.com/{PROJECT}/v1/chat/completions"
MODEL = "gpt-5.4-nano-2026-03-17"
# pricing (per CoCo base_generator): $0.05/MTok in, $0.40/MTok out
PIN, POUT = 0.05 / 1e6, 0.40 / 1e6

DEFAULT_SET = ["warren-buffett", "charlie-munger", "alfred-rappaport"]  # 2 truncated + 1 quota-short under qwen


def gpt5(messages, max_completion_tokens=16000, timeout=240):
    payload = json.dumps({"model": MODEL, "messages": messages,
                          "max_completion_tokens": max_completion_tokens}).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    content = d["choices"][0]["message"]["content"]
    return content, time.time() - t0, d.get("usage", {}) or {}


def build_one_gpt5(p):
    slug, name, cell = p["slug"], p["name"], p["cell"]
    role, anchor = p.get("role", "specialist"), p["anchor"]
    pages, news = bl.retriever.search(name, anchor, cell)
    wc, allow = bl.retriever.context_block(pages, news)
    sysp = bl.sys_prompt(bl.POOL)
    user = (f"Subject: {name} — {anchor}\nslug: {slug}\ncell: {cell}\ncell_role: {role}\n"
            f"teams: [finance-super-intelligence]\nhome_team: finance-super-intelligence\nlast_verified: 2026-06-01\n\n"
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
    fixed = close_frontmatter(fixed)           # fix 1: insert missing closing '---'
    fixed = prune_dead_urls(fixed)             # fix 2: drop 404/dead URLs
    (OUT / f"{slug}.md").write_text(fixed + "\n", encoding="utf-8")
    rd = RES / slug; rd.mkdir(exist_ok=True)
    rd.joinpath("notes.md").write_text(f"# gpt-5.4-nano research dump\nname: {name}\n", encoding="utf-8")
    v, reasons, nurls, okurls = validate(str(OUT / f"{slug}.md"), bl.POOL, "2025-06-01")
    pin = u1.get("prompt_tokens", 0) + u2.get("prompt_tokens", 0)
    pout = u1.get("completion_tokens", 0) + u2.get("completion_tokens", 0)
    cost = pin * PIN + pout * POUT
    return v, reasons, okurls, nurls, t1 + t2, cost, pout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    slugs = [a.only] if a.only else DEFAULT_SET
    todo = [p for p in bl.ROSTER["personas"] if p["slug"] in slugs]
    print(f"GPT-5.4-nano experiment: {len(todo)} persona(s) -> {OUT}")
    tot_cost = 0.0; npass = 0
    for i, p in enumerate(todo, 1):
        try:
            v, reasons, ok, n, dt, cost, pout = build_one_gpt5(p)
        except Exception as e:
            print(f"[{i}/{len(todo)}] {p['slug']:20} ERROR {type(e).__name__}: {str(e)[:90]}"); continue
        tot_cost += cost; npass += v == "PASS"
        print(f"[{i}/{len(todo)}] {p['slug']:20} {v:11} urls {ok}/{n}  {dt:.0f}s  ${cost:.4f}  {pout}tok  {('; '.join(reasons))[:80]}")
    print(f"\nGPT-5.4-nano: {npass}/{len(todo)} PASS  total ${tot_cost:.4f}")


if __name__ == "__main__":
    main()
