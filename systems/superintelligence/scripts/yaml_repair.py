#!/usr/bin/env python3
"""
Cheap YAML-repair pass via gpt-5.4-nano (gateway). Salvages persona files whose
frontmatter has a YAML syntax error (rich content intact, only YAML broken) WITHOUT
re-researching. Preserves every field/URL/word — only fixes YAML syntax. Idempotent:
parseable files are skipped. 20-parallel, ~$0.003/file.

    python3 superintelligence/scripts/yaml_repair.py                 # all teams
    python3 superintelligence/scripts/yaml_repair.py finance trading # subset
"""
import sys, os, json, re, urllib.request, pathlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import yaml
except ImportError:
    sys.exit("pip install --break-system-packages pyyaml")

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = (pathlib.Path.home() / ".coco" / ".ai-gateway-key").read_text().strip()
PROJECT = "YOUR_PROJECT_ID"
URL = f"https://YOUR_AI_GATEWAY_HOST/{PROJECT}/v1/chat/completions"
MODEL = "gpt-5.4-nano-2026-03-17"
TEAMS = sys.argv[1:] or ["finance", "trading", "risk-compliance", "strategy", "data-analytics", "gtm"]
MAXW = int(os.environ.get("REPAIR_WORKERS", "20"))

SYS = ("You FIX YAML SYNTAX in a persona Markdown file. The file has valid content but its YAML "
       "frontmatter fails to parse. Re-emit the COMPLETE file UNCHANGED except for YAML syntax fixes. "
       "RULES: preserve every key, value, URL, date, list item, and the ENTIRE narrative body EXACTLY "
       "(do not drop, add, summarize, or invent anything — especially keep all URLs verbatim). "
       "Fix ONLY: single-quote any scalar value containing a colon/comma/quote/'#'; correct list indentation; "
       "use block style for lists of objects (each item `  - key: val` with nested keys indented). "
       "Output ONLY the corrected file starting at the first `---`. No commentary, no code fences.")


def parses(t):
    if not t.startswith("---"):
        return False
    e = t.find("\n---\n", 4)
    if e < 0:
        return False
    try:
        return isinstance(yaml.safe_load(t[4:e]), dict)
    except Exception:
        return False


def nano(messages, max_completion_tokens=16000, timeout=180):
    payload = json.dumps({"model": MODEL, "messages": messages,
                          "max_completion_tokens": max_completion_tokens}).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def clean(t):
    t = re.sub(r"^```(?:markdown)?\n", "", t.strip())
    t = re.sub(r"\n```$", "", t).strip()
    return t


def repair_one(f):
    t = f.read_text()
    if parses(t):
        return f.stem, "ok-skip"
    try:
        fixed = clean(nano([{"role": "system", "content": SYS},
                            {"role": "user", "content": t}]))
    except Exception as e:
        return f.stem, f"ERR {type(e).__name__}"
    if parses(fixed):
        f.write_text(fixed + ("\n" if not fixed.endswith("\n") else ""), encoding="utf-8")
        return f.stem, "REPAIRED"
    return f.stem, "still-broken"


def main():
    files = []
    for t in TEAMS:
        files += sorted((ROOT / t / "personas").glob("*.md"))
    broken = [f for f in files if not parses(f.read_text())]
    print(f"scanning {len(files)} files; {len(broken)} unparseable -> repairing ({MAXW} parallel)")
    rep = skip = fail = 0
    with ThreadPoolExecutor(max_workers=MAXW) as ex:
        futs = {ex.submit(repair_one, f): f for f in broken}
        for fut in as_completed(futs):
            slug, st = fut.result()
            if st == "REPAIRED":
                rep += 1
            elif st.startswith(("ERR", "still")):
                fail += 1; print(f"  {slug}: {st}")
            else:
                skip += 1
    print(f"\nREPAIRED {rep} | failed {fail} | (parseable now: {sum(1 for f in files if parses(f.read_text()))}/{len(files)})")


if __name__ == "__main__":
    main()
