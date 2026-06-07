#!/usr/bin/env python3
"""
EXPERIMENT: generate a persona file from a LOCAL LM Studio model (no web).
Tests structure + prose quality + whether the model respects the
"verify or omit, never fabricate" gate when it has no browsing.

Usage:
    python3 gen_local_persona.py <slug> "<Real Name>" <cell> "<one-line anchor>"
Writes: superintelligence/finance/experiments/<slug>.local.md
Prints: timing + token usage + quick lint.
"""
import json, sys, time, urllib.request, pathlib, re

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen/qwen3.6-35b-a3b"
EXP_DIR = pathlib.Path(__file__).resolve().parents[1] / "experiments"
EXP_DIR.mkdir(exist_ok=True)

SYSTEM = """You write persona profiles for a structured decision-panel system. The subject is a REAL, named public figure.

Output ONLY one Markdown file and nothing else: no preamble, no commentary, no <think> blocks, no code fences around the whole file. Start at the first `---`.

STRUCTURE — YAML frontmatter between `---` delimiters with these keys, then narrative:
slug, real_name, archetype (one line "the X who Y"), teams (list), home_team, cell, cell_role (one of lead-driver/validator/specialist/swing), status (active or archetype), affiliations_2026 (list; SINGLE-QUOTE any value containing a colon), domains (list of keywords), signature_moves (list), canonical_works (list), key_publications (list), recent_signal_12mo (list of {title,date,url} — only if you are certain; else leave empty), public_stances (list of {stance, evidence_url}), mental_models (list), pairs_well_with (list of slugs), productive_conflict_with (list of slugs), blind_spots (list), voice_style (text), when_to_summon (list), confidence (0-1), last_verified (2026-06-01), sources (list of URLs).

Then narrative sections (markdown headers): "# {Real Name} — narrative profile", "## How they think" (3-5 paragraphs), "## What they would push back on", "## Signature moves in practice", "## Where they are weak", "## How to summon them".

VERIFICATION GATE — CRITICAL (these are real people):
- Verify or omit. NEVER fabricate to fill a field. You have NO web access, so for any field you are not genuinely confident about from training knowledge, LEAVE IT EMPTY rather than guess.
- Do NOT invent URLs. Only include a URL in `sources`/`evidence_url`/`recent_signal_12mo` if you are highly confident it is a real, stable URL (e.g. a known book page, the person's known blog/site). If unsure, leave the list empty. A fabricated URL is a defamation risk and a hard failure.
- No verbatim quotes unless you are certain they are real. Otherwise paraphrase with no quotation marks.
- Recent dated events: only include if confident; never invent dates. If you cannot supply 3 real recent signals, supply fewer (or none) — do not fabricate to hit a quota.
- Mark fields you could not verify by simply omitting them. It is correct and expected for a no-web model to leave recent_signal_12mo and most URLs sparse."""

def build_user(slug, name, cell, anchor):
    return f"""Subject: {name} — {anchor}
slug: {slug}
cell: {cell}
cell_role: lead-driver
teams: [finance-super-intelligence]
home_team: finance-super-intelligence
last_verified: 2026-06-01

Write the complete persona file now. Remember the verification gate: leave URLs/recent signals empty unless you are genuinely confident they are real. Output only the file."""

def main():
    slug, name, cell, anchor = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_user(slug, name, cell, anchor)},
        ],
        "temperature": 0.4,
        "max_tokens": 6000,
        "stream": False,
    }
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    dt = time.time() - t0
    content = data["choices"][0]["message"]["content"]
    # strip any stray <think> blocks
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
    # strip wrapping ``` fences if present
    content = re.sub(r"^```(?:markdown)?\n", "", content)
    content = re.sub(r"\n```$", "", content).strip()
    out = EXP_DIR / f"{slug}.local.md"
    out.write_text(content + "\n", encoding="utf-8")
    u = data.get("usage", {})
    print(f"model={MODEL}")
    print(f"wrote {out}  ({len(content)} chars)")
    print(f"time={dt:.1f}s  prompt_tok={u.get('prompt_tokens')} completion_tok={u.get('completion_tokens')} "
          f"tok/s={ (u.get('completion_tokens',0)/dt):.1f}")
    # quick lint
    fences = content.count("```")
    has_fm = content.startswith("---")
    urls = re.findall(r"https?://\S+", content)
    print(f"lint: starts_with_frontmatter={has_fm} stray_fences={fences} url_count={len(urls)}")

if __name__ == "__main__":
    main()
