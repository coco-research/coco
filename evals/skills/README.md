# Skill evals

This harness scores a skill file (`SKILL.md`) on a fixed set of items. Each item is `dev` or `heldout`. One run scores one split and writes a JSON record.

The executor talks to a local model server on a loopback address only (`127.0.0.1`, `localhost`, or `::1`). Any other host is refused. Proxy environment variables are ignored and HTTP redirects are refused, so a prompt cannot leave the machine that way. The default server is `http://127.0.0.1:11434` (`COCO_SKILL_EXEC_URL`) and the default model is `qwen3:4b-instruct-2507-q4_K_M` (`COCO_SKILL_EXEC_MODEL`). Calls use temperature 0, a fixed seed, and a 16384-token context. Dev replies are cached under `evals/skills/.cache/`, which is not committed. Held-out replies are not written to disk. `--executor stub` scores without a server.

## Dev and held-out

Held-out records carry numbers only (ids and scores, plus run metadata such as the commit and the file hashes). They omit model outputs and grader notes.

A proposer may read dev rows and dev records. A proposer may not read held-out rows or held-out records.

## Run

Items and the grader live in `evals/skills/<NAME>/` (`items.jsonl`, `grader.py`). `grader.py` exposes `grade(item, output)` and returns `{"score": float, "notes": [str]}` with `score` in `[0, 1]`. The skill text defaults to `skills/<NAME>/SKILL.md`. `--skill-md` scores a candidate file instead.

```bash
python3 evals/skills/score.py --skill NAME --split dev
python3 evals/skills/score.py --skill NAME --split heldout --out run.json
python3 evals/skills/score.py --skill NAME --split dev --executor stub
python3 evals/skills/score.py --skill NAME --split dev --skill-md path/to/SKILL.md
python3 evals/skills/score.py --self-test
```

Directory names starting with `_` are fixtures, not pilots.

## Pilot skills

- **generate-tests.** The grader takes the first Python or unlabeled code fence that contains `unittest`, runs it on the correct function, then on three buggy mutants. The score is the fraction of mutants killed. Tests that fail on the correct function score 0. Model-written test code runs only when `COCO_SKILL_EXEC_UNTRUSTED=1` is set, and then inside macOS `sandbox-exec` (no network, writes confined to a temp directory); on other systems it is not run and scores 0; without a sandbox the score is 0.
- **humanizer.** The grader counts a fixed list of AI-tell phrases before and after the rewrite, and the fraction of required facts still present. The score is half tell-removal and half facts kept, and is halved when the rewrite is under 40% or over 160% of the original word count.
