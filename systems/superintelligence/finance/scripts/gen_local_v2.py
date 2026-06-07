#!/usr/bin/env python3
"""
EXPERIMENT harness v2 for local-LLM persona generation.

Modes / knobs:
  --model <id>         LM Studio model id (must be loaded)
  --web                ground citations in real DuckDuckGo results (text + news)
  --twopass            draft pass, then a citation/repair pass (implied by --web)
  --slugs "a,b,c"      real roster slugs the model may use for pairs/conflicts
  --refresh <path>     refresh an existing persona file's recent_signal_12mo + affiliations
  positional: <slug> "<name>" <cell> "<anchor>"

Writes superintelligence/finance/experiments/<slug>.<tag>.md  where tag encodes the run.
Prints timing, tokens, and a lint (frontmatter ok? url count? real-url count? roster-slug validity?).
All generation is local => $0.
"""
import argparse, json, re, sys, time, urllib.request, pathlib

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
EXP = pathlib.Path(__file__).resolve().parents[1] / "experiments"
EXP.mkdir(exist_ok=True)

FRONTMATTER_SPEC = """slug, real_name, archetype (one line), teams (list), home_team, cell, cell_role (lead-driver/validator/specialist/swing), status (active|archetype), affiliations_2026 (list; single-quote values with a colon), domains (list), signature_moves (list), canonical_works (list), key_publications (list), recent_signal_12mo (list of {title,date,url}), public_stances (list of {stance,evidence_url}), mental_models (list), pairs_well_with (list of slugs), productive_conflict_with (list of slugs), blind_spots (list), voice_style (text), when_to_summon (list), confidence (0-1), last_verified, sources (list of URLs)"""

NARRATIVE = '"# {Real Name} — narrative profile", "## How they think" (3-5 para), "## What they would push back on", "## Signature moves in practice", "## Where they are weak", "## How to summon them"'

GATE = """VERIFICATION GATE (real person):
- Verify or omit. NEVER fabricate. Only include a URL/date you are confident is real, or that appears in the WEB CONTEXT provided below. No invented URLs. No unsourced verbatim quotes (paraphrase instead).
- If WEB CONTEXT is provided, draw sources, recent_signal_12mo (use the dated news items), and stance evidence_urls ONLY from those real URLs. Do not exceed what the evidence supports.
- If no WEB CONTEXT, leave recent_signal_12mo empty and sources to only URLs you are certain are real (e.g. the person's official site). Quotas are ceilings not floors."""

def llm(model, messages, max_tokens=6000, temp=0.4):
    payload = {"model": model, "messages": messages, "temperature": temp,
               "max_tokens": max_tokens, "stream": False}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"], d.get("usage", {}), time.time() - t0

def clean(txt):
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()
    txt = re.sub(r"^```(?:markdown)?\n", "", txt)
    txt = re.sub(r"\n```$", "", txt).strip()
    return txt

def web_context(name, cell, anchor):
    """Deep retriever: multi-query ddgs + page fetch + trafilatura extract."""
    import retriever
    try:
        pages, news = retriever.search(name, anchor, cell)
    except Exception as e:
        return f"(web search failed: {e})", []
    return retriever.context_block(pages, news)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("name"); ap.add_argument("cell"); ap.add_argument("anchor")
    ap.add_argument("--model", required=True)
    ap.add_argument("--web", action="store_true")
    ap.add_argument("--twopass", action="store_true")
    ap.add_argument("--slugs", default="")
    ap.add_argument("--tag", default="run")
    a = ap.parse_args()

    pool = [s.strip() for s in a.slugs.split(",") if s.strip()]
    pool_txt = ("\nROSTER SLUGS — for pairs_well_with / productive_conflict_with, choose ONLY from this list "
                f"(omit if none fit): {pool}\n" if pool else "")

    system = (f"You write persona profiles for a decision-panel system. Subject is a REAL public figure. "
              f"Output ONLY one Markdown file, no preamble/commentary/<think>, starting at the first `---`.\n\n"
              f"FRONTMATTER keys: {FRONTMATTER_SPEC}\nThen narrative sections: {NARRATIVE}\n\n{GATE}{pool_txt}")

    wc, urls = ("", [])
    if a.web:
        wc, urls = web_context(a.name, a.cell, a.anchor)

    user = (f"Subject: {a.name} — {a.anchor}\nslug: {a.slug}\ncell: {a.cell}\ncell_role: lead-driver\n"
            f"teams: [finance-super-intelligence]\nhome_team: finance-super-intelligence\nlast_verified: 2026-06-01\n\n"
            + (f"WEB CONTEXT:\n{wc}\n\n" if a.web else "")
            + "Write the complete persona file now. Output only the file.")

    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    content, usage, dt = llm(a.model, msgs)
    content = clean(content)
    total_dt, total_ct = dt, usage.get("completion_tokens", 0)

    if a.twopass:
        repair = ("Here is a draft persona file. Repair it WITHOUT fabricating: (1) ensure every public_stance "
                  "evidence_url and every recent_signal_12mo url is a REAL url from the WEB CONTEXT (drop the field if none); "
                  "(2) ensure pairs_well_with/productive_conflict_with use only allowed roster slugs; "
                  "(3) keep prose. Output only the corrected file.\n\n"
                  f"WEB CONTEXT:\n{wc}\n\nDRAFT:\n{content}")
        content2, usage2, dt2 = llm(a.model, [{"role": "system", "content": system},
                                              {"role": "user", "content": repair}])
        content = clean(content2)
        total_dt += dt2; total_ct += usage2.get("completion_tokens", 0)

    tag = a.tag
    out = EXP / f"{a.slug}.{tag}.md"
    out.write_text(content + "\n", encoding="utf-8")

    found = re.findall(r"https?://[^\s\)\]'\"]+", content)
    real = [u for u in found if u in set(urls)] if urls else []
    used_slugs = re.findall(r"productive_conflict_with: \[([^\]]*)\]", content)
    print(f"[{tag}] model={a.model} web={a.web} twopass={a.twopass}")
    print(f"  wrote {out.name} ({len(content)}c)  time={total_dt:.1f}s completion_tok={total_ct} tok/s={total_ct/total_dt:.1f}")
    print(f"  lint: frontmatter={content.startswith('---')} url_count={len(found)} real_urls_from_web={len(real)}")
    print(f"  conflict_slugs={used_slugs}")

if __name__ == "__main__":
    main()
