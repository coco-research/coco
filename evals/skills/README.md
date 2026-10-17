# Skill evals

This harness scores a skill file (`SKILL.md`) on a fixed set of items. Each item is `dev` or `heldout`. One run scores one split and writes a JSON record.

The executor talks to a local model server on a loopback address only (`127.0.0.1`, `localhost`, or `::1`). Any other host is refused. The default server is `http://127.0.0.1:11434` (`COCO_SKILL_EXEC_URL`) and the default model is `qwen3:4b-instruct-2507-q4_K_M` (`COCO_SKILL_EXEC_MODEL`). Calls use temperature 0, a fixed seed, and a 16384-token context. Replies are cached under `evals/skills/.cache/`, which is not committed. `--executor stub` scores without a server.

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
