#!/usr/bin/env python3
"""
Production local-first persona builder for the Finance SIT (and reusable for any team).
Pipeline per persona:  retrieve (deep, free) -> draft (local) -> repair/cite pass (local)
  -> write personas/<slug>.md + research/<slug>/notes.md -> validate -> verdict.

All generation is local (mlx-dspark speculative-decoding server) => ~$0. Validator enforces the verify-gate.

Usage:
  python3 build_local.py --all
  python3 build_local.py --only aswath-damodaran
  python3 build_local.py --cell macro-economics
  (model defaults to qwen/qwen3.6-35b-a3b; must be served by the mlx-dspark launchd service --
   see ~/.config/mlx-dspark/start.sh, or export MLX_DSPARK_API_KEY to override the key source)
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error, pathlib, yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retriever
from validate_persona import validate

FIN = pathlib.Path(__file__).resolve().parents[1]          # superintelligence/finance
ROSTER = json.loads((FIN / "roster.json").read_text())
PERSONAS = FIN / "personas"; PERSONAS.mkdir(exist_ok=True)
RESEARCH = FIN / "research"; RESEARCH.mkdir(exist_ok=True)
ENDPOINT = "http://127.0.0.1:8090/v1/completions"  # mlx-dspark server, raw prompt endpoint (see llm() below)
ADMIN_LOAD_ENDPOINT = "http://127.0.0.1:8090/admin/load"  # used to reload the model after an idle-unload (see llm() 503 handling)
POOL = [p["slug"] for p in ROSTER["personas"]]

FM = """slug, real_name, archetype (one line), teams (list), home_team, cell, cell_role, status (active|archetype), affiliations_2026 (list; single-quote values with a colon), domains (list), signature_moves (list), canonical_works (list), key_publications (list), recent_signal_12mo (list of {title,date,url}), public_stances (list of {stance,evidence_url}), mental_models (list), pairs_well_with (list of slugs), productive_conflict_with (list of slugs), blind_spots (list), voice_style (text), when_to_summon (list), confidence, last_verified, sources (list of URLs)"""
NARR = '"# {Real Name} — narrative profile", "## How they think" (3-5 para), "## What they would push back on", "## Signature moves in practice", "## Where they are weak", "## How to summon them"'

def sys_prompt(pool):
    return (f"You write persona profiles for a decision-panel system. Subject is a REAL public figure. "
            f"Output ONLY one Markdown file, no preamble/<think>, starting at the first `---`.\n"
            f"FRONTMATTER keys: {FM}\nThen narrative: {NARR}\n\n"
            "VERIFICATION GATE (real person): Verify or omit, NEVER fabricate. Use ONLY URLs that appear in the WEB CONTEXT. "
            "No invented URLs/dates. No unsourced verbatim quotes (paraphrase). "
            "`sources` MUST list ALL real URLs you used anywhere (every recent_signal_12mo url, every stance evidence_url, plus any other fetched source), de-duplicated — aim for >=8 if that many were fetched; if fewer were fetched, list what you have (do not invent). "
            "recent_signal_12mo: keep only items dated after 2025-06-01. "
            "CRITICAL YAML FORMAT: use BLOCK style for every list. For lists of objects (recent_signal_12mo, public_stances) put each item on its own line as `  - title: ...` then indented `    date: ...` / `    url: ...` / `    stance: ...` / `    evidence_url: ...`. NEVER use inline flow style [{...}, {...}]. Single-quote any scalar value that contains a colon, comma, or quote. "
            f"pairs_well_with / productive_conflict_with: choose ONLY from this slug list (omit if none fit): {pool}")

REASONING_TIMEOUT = 90  # safety-net: abort if literally nothing streams back for this long

def _raw_prompt(messages):
    # ChatML prompt with the assistant turn's <think> block pre-closed and EMPTY.
    # This is the "prefill trick": since reasoning is already closed, the model has
    # no room left to think and must go straight to the answer. Verified empirically
    # that LM Studio and mlx-dspark both do not honor reasoning_effort/enable_thinking
    # for this model via /v1/chat/completions (tried top-level, camelCase,
    # chat_template_kwargs, and baked into persisted per-model load config -- none
    # suppressed reasoning). Using the raw /v1/completions endpoint with a
    # forced-empty <think> block bypasses that gap entirely and gives the full
    # max_tokens budget to the real answer instead of burning it on unbounded
    # reasoning. Same trick works against mlx-dspark since it uses the identical
    # jinja chat-template mechanics.
    parts=[f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages]
    parts.append("<|im_start|>assistant\n<think>\n\n</think>\n\n")
    return "".join(parts)

def _dspark_api_key():
    # Never hardcode the key. Prefer the env var; fall back to the local,
    # non-repo key file the launchd service also reads (0600 perms, outside git).
    key = os.environ.get("MLX_DSPARK_API_KEY")
    if key:
        return key.strip()
    key_file = pathlib.Path.home() / ".config" / "mlx-dspark" / "api_key"
    if key_file.exists():
        return key_file.read_text().strip()
    raise RuntimeError(
        "mlx-dspark API key not found -- set MLX_DSPARK_API_KEY or ensure "
        f"{key_file} exists (see ~/.config/mlx-dspark/start.sh)"
    )

def _dspark_headers():
    # Build the auth header at call time from the key helper above -- never
    # store or format the header value as a literal anywhere in this file.
    auth_value = f"Bearer {_dspark_api_key()}"
    return {"Content-Type": "application/json", "Authorization": auth_value}

def _dspark_load(model):
    # Reload the model after an idle-unload (mlx-dspark's idle_watcher.py may
    # have called /admin/unload after 15min of no traffic). context_window is
    # sticky across loads server-side, so it does not need to be resent here.
    # /admin/load blocks until the swap finishes -- no polling loop needed.
    payload = json.dumps({"model": model, "mode": "auto"}).encode()
    req = urllib.request.Request(ADMIN_LOAD_ENDPOINT, data=payload, headers=_dspark_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def _dspark_request(payload):
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(), headers=_dspark_headers())
    return urllib.request.urlopen(req, timeout=900)

def llm(model, messages, max_tokens=11000, temp=0.4):
    prompt=_raw_prompt(messages)
    payload={"model":model,"prompt":prompt,"temperature":temp,"max_tokens":max_tokens,"stream":True,"stop":["<|im_end|>"]}
    t0=time.time()
    text_parts=[]
    try:
        response = _dspark_request(payload)
    except urllib.error.HTTPError as e:
        if e.code != 503:
            raise
        # Model was idle-unloaded -- reload once and retry the request once.
        _dspark_load(model)
        response = _dspark_request(payload)
    with response as r:
        for line in r:
            if not line.startswith(b"data: "): continue
            chunk=line[6:].strip()
            if chunk==b"[DONE]": break
            try: d=json.loads(chunk)
            except Exception: continue
            t=d["choices"][0].get("text","")
            if t: text_parts.append(t)
            if not text_parts and (time.time()-t0) > REASONING_TIMEOUT:
                raise RuntimeError(f"no content after {REASONING_TIMEOUT}s — aborting (prefill trick may not have suppressed reasoning)")
    if not text_parts:
        raise RuntimeError("LLM returned no answer content (empty response)")
    return "".join(text_parts), time.time()-t0

def clean(t):
    t=re.sub(r"<think>.*?</think>","",t,flags=re.S).strip()
    t=re.sub(r"^```(?:markdown)?\n","",t); t=re.sub(r"\n```$","",t).strip()
    if not t.startswith("---"):
        i=t.find("\n---\n")
        if i>=0: t=t[i+1:].strip()
    return t

def _parses(t):
    if not t.startswith("---"): return False
    end=t.find(chr(10)+"---"+chr(10),4)
    if end<0: end=t.find(chr(10)+"---",4)
    if end<0: return False
    try:
        return isinstance(yaml.safe_load(t[4:end]), dict)
    except Exception:
        return False

def pick_parseable(primary, fallback):
    if _parses(primary): return primary
    if _parses(fallback): return fallback
    return primary  # neither parses; validator will flag

def build_one(p, model):
    slug,name,cell,role,anchor = p["slug"],p["name"],p["cell"],p.get("role","specialist"),p["anchor"]
    pages,news = retriever.search(name, anchor, cell)
    wc, allow = retriever.context_block(pages, news)
    sysp = sys_prompt(POOL)
    user = (f"Subject: {name} — {anchor}\nslug: {slug}\ncell: {cell}\ncell_role: {role}\n"
            f"teams: [finance-super-intelligence]\nhome_team: finance-super-intelligence\nlast_verified: 2026-06-01\n\n"
            f"WEB CONTEXT:\n{wc}\n\nWrite the complete persona file. Output only the file.")
    draft,t1 = llm(model,[{"role":"system","content":sysp},{"role":"user","content":user}])
    draft=clean(draft)
    repair=("Repair this persona file WITHOUT fabricating: (1) every recent_signal_12mo url + stance evidence_url must be a REAL url from WEB CONTEXT (drop field if none); "
            "(2) `sources` must list ALL those real URLs deduped (>=8 if available); (3) pairs/conflict use only allowed slugs; (4) keep prose. Output only the file.\n\n"
            f"WEB CONTEXT:\n{wc}\n\nDRAFT:\n{draft}")
    fixed,t2 = llm(model,[{"role":"system","content":sysp},{"role":"user","content":repair}])
    fixed=clean(fixed)
    # write whichever output actually parses (prefer the repaired one)
    fixed = pick_parseable(fixed, draft)
    (PERSONAS/f"{slug}.md").write_text(fixed+"\n",encoding="utf-8")
    rd=RESEARCH/slug; rd.mkdir(exist_ok=True)
    dump=["# Research dump (auto, local pipeline)\n", f"name: {name}", f"generated_local: qwen via mlx-dspark\n", "## Fetched pages"]
    for u,txt in pages: dump.append(f"\n### {u}\n{txt}")
    dump.append("\n## Dated news")
    for n in news: dump.append(f"- {n['date']} :: {n['title']} :: {n['url']}")
    rd.joinpath("notes.md").write_text("\n".join(dump)+"\n",encoding="utf-8")
    v,reasons,nurls,okurls = validate(str(PERSONAS/f"{slug}.md"), POOL, "2025-06-01")
    return v,reasons,okurls,nurls,(t1+t2)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",default="qwen/qwen3.6-35b-a3b")
    ap.add_argument("--all",action="store_true"); ap.add_argument("--only",default=""); ap.add_argument("--cell",default="")
    ap.add_argument("--force",action="store_true",help="rebuild even if persona file already exists")
    a=ap.parse_args()
    todo=ROSTER["personas"]
    if a.only: todo=[p for p in todo if p["slug"]==a.only]
    elif a.cell: todo=[p for p in todo if p["cell"]==a.cell]
    elif not a.all: sys.exit("pass --all | --only <slug> | --cell <cell>")
    if not a.force:
        todo=[p for p in todo if not (PERSONAS/f"{p['slug']}.md").exists()]  # resume: skip built
    print(f"building {len(todo)} persona(s) with {a.model}")
    npass=0
    # 4 concurrent workers, matching the mlx-dspark server's `--max-batch 4` config
    # (measured ~1.71x aggregate throughput vs sequential on this server).
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(build_one,p,a.model):p for p in todo}
        for i,fut in enumerate(as_completed(futs),1):
            p=futs[fut]
            try:
                v,reasons,ok,n,dt=fut.result()
            except Exception as e:
                print(f"[{i}/{len(todo)}] {p['slug']:24} ERROR {type(e).__name__}: {str(e)[:80]}"); continue
            npass += v=="PASS"
            print(f"[{i}/{len(todo)}] {p['slug']:24} {v:11} urls {ok}/{n} {dt:.0f}s  {('; '.join(reasons))[:90]}")
    print(f"\nDONE: {npass}/{len(todo)} PASS")

if __name__=="__main__":
    main()
