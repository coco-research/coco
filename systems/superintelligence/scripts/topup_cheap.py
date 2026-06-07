#!/usr/bin/env python3
"""
Cheap deterministic top-up: for every NEEDS-TOPUP-prone persona file, (1) if YAML
unparseable -> nano re-emit valid YAML (content preserved); (2) prune dead/404 URL
lines (recovers the dead_url failures, incl false-positives from validate HTTP storms).
Re-checks URLs once, serially-per-file, to avoid the parallel-storm false-deads.
20-parallel across files. Then re-validate separately.

    python3 superintelligence/scripts/topup_cheap.py
"""
import sys, os, json, re, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import yaml
except ImportError:
    sys.exit("pip install --break-system-packages pyyaml")

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "finance" / "scripts"))
from validate_persona import check_urls
KEY = (pathlib.Path.home() / ".coco" / ".ai-gateway-key").read_text().strip()
URL = "https://YOUR_AI_GATEWAY_HOST/YOUR_PROJECT_ID/v1/chat/completions"
MODEL = "gpt-5.4-nano-2026-03-17"
TEAMS = ["finance", "trading", "risk-compliance", "strategy", "data-analytics", "gtm"]
MAXW = int(os.environ.get("TOPUP_WORKERS", "20"))

SYS = ("FIX YAML SYNTAX ONLY in this persona file. Preserve every key, value, URL, date, list item "
       "and the entire narrative EXACTLY. Single-quote scalars with colon/comma/quote; correct list "
       "indentation; block style. Output ONLY the corrected file from the first `---`. No fences/commentary.")


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


def nano(t):
    payload = json.dumps({"model": MODEL, "messages": [
        {"role": "system", "content": SYS}, {"role": "user", "content": t}],
        "max_completion_tokens": 16000}).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read())["choices"][0]["message"]["content"]
    out = re.sub(r"^```(?:markdown)?\n", "", out.strip())
    return re.sub(r"\n```$", "", out).strip()


def prune_dead(t):
    urls = set(re.findall(r"https?://[^\s'\"]+", t))
    if not urls:
        return t, 0
    st = check_urls(list(urls))
    dead = {u for u, s in st.items() if (isinstance(s, str) and s.startswith("ERR")) or s == 404}
    if not dead:
        return t, 0
    kept = [ln for ln in t.splitlines() if not any(d in ln for d in dead)]
    return "\n".join(kept) + "\n", len(dead)


def fix(f):
    t = f.read_text()
    changed = False
    if not parses(t):
        try:
            n = nano(t)
            if parses(n):
                t = n; changed = True
        except Exception as e:
            return f.stem, f"repair-err:{type(e).__name__}"
    t2, ndead = prune_dead(t)
    if ndead:
        t = t2; changed = True
    if changed:
        f.write_text(t if t.endswith("\n") else t + "\n", encoding="utf-8")
        return f.stem, f"fixed(parse={'y' if parses(t) else 'n'},pruned={ndead})"
    return f.stem, "nochange"


def main():
    files = []
    for tm in TEAMS:
        files += sorted((ROOT / tm / "personas").glob("*.md"))
    print(f"cheap top-up over {len(files)} files ({MAXW} parallel)")
    fixed = 0
    with ThreadPoolExecutor(max_workers=MAXW) as ex:
        futs = {ex.submit(fix, f): f for f in files}
        for fut in as_completed(futs):
            slug, st = fut.result()
            if st.startswith("fixed"):
                fixed += 1
            elif "err" in st:
                print(f"  {slug}: {st}")
    print(f"changed {fixed} files")


if __name__ == "__main__":
    main()
