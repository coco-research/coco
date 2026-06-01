# Ship Evidence — Track 0 Wave 0.1 (Cost / Classification Spine)

**Date:** 2026-06-01
**Branch:** `phase/0.1-cost-classification-spine`
**Scope:** Audit fixes #1 (cost recording), #2 (auto-classifier + content classify), #3 (content-to-action), #11 (chat double cost-record). Plus two latent schema-drift bugs surfaced by TDD.

> Evidence protocol: every claim below has a captured command + output. No claim without evidence.

---

## Stage 9 — TDD Red → Green

New test file `backend/tests/test_wave01_persistence.py` (16 tests) asserts rows actually land.

**RED (before fixes):**
```
$ uv run pytest tests/test_wave01_persistence.py -q
16 failed in 2.57s
```
Failures for the right reasons: `TypeError` (upsert kwargs), `CompileError` (phantom columns), `IntegrityError` (wrong conflict target), 2× cost-record assertion, CHECK-not-enforced.

**GREEN (after fixes):**
```
$ uv run pytest tests/test_wave01_persistence.py -q
16 passed in 1.74s
```

## Stage 8 — Full Suite

```
$ uv run pytest -q
378 passed, 9 skipped in 7.57s
```
- 0 failures.
- 9 skipped are PRE-EXISTING integration tests gated on unprovisioned deps (not introduced here). Per protocol they are UNVERIFIED, not "passed". None relate to Wave 0.1.

## Live DB migration (#1) — applied + verified

```
$ uv run alembic stamp 008_audit_log     # live DB was stamped 005; 006-008 tables already exist via create_all
$ uv run alembic upgrade head            # runs ONLY 009
Running upgrade 008_audit_log -> 009_widen_cost_ledger_source

$ sqlite3 ~/.coco/platform.db '.schema cost_ledger' | grep CHECK
  source TEXT NOT NULL DEFAULT 'agent' CHECK(source IN
    ('station','chat','think','kh_pipeline','agent','classifier','brain','api_token'))

$ # source='agent' (a real writer the old CHECK rejected):
INSERT ... source='agent';   -> agent OK
$ # bogus source still rejected:
INSERT ... source='bogus';   -> CHECK constraint failed
```
Backup taken before migration: `~/.coco/platform.db.pre009.<ts>`.

## Stage 7/13 — Lint (CI mirror, degraded honestly)

- CI gate = `uv run ruff check .` (from `.github/workflows/pr-tests.yml`). `ruff` is not in the synced venv (`uv run ruff` fails to spawn), so mirrored via `uvx ruff@latest check` on the changed files.
- **My diff is lint-clean:** all 11 reported `B904`/`RUF010` findings are at lines OUTSIDE this change's diff hunks (pre-existing repo debt), and `ruff@latest` may enforce rules not in the repo's pinned `[tool.ruff.lint]` select set. No new lint introduced. Pre-existing repo-wide lint debt is explicitly out of Wave 0.1 scope.

## Bugs fixed (claim ↔ change)

| # | Claim | Change |
|---|---|---|
| 1 | cost_ledger accepts real sources; failures are loud | `tables.py` widened `CHECK` + `created_at` server_default; migration 009 rebuilds live table; `record_sdk_cost` swallow → `log.error` |
| 2 | classifier persistence works + idempotent | `auto_classifier.py` `conflict_cols`→`conflict_columns`, `update_cols`→`update_columns`; `content_classifications.hub_content_id` made `unique=True` (parity) |
| 2b | content classify/dismiss idempotent | `content.py` conflict target `['id']`→`['hub_content_id']` |
| 3 | content→action staging + approve works | `action_pipeline.py` dropped phantom cols (`extraction_mode`/`updated_at`/`result_id`→`created_todo_id`); fixed `body`/`raw_text` key read (latent bug: extraction always empty) |
| 11 | chat SDK cost recorded once | `chat.py` removed redundant `record_sdk_cost` (stream_chat owns it) |

## Latent bugs surfaced by TDD (not in original audit)

1. `content_classifications.hub_content_id` lacked `UNIQUE` in `tables.py` → `ON CONFLICT` failed on fresh DBs (live had it). Fixed (parity).
2. `process_content` read `.get("body")` but `row._mapping` is keyed `raw_text`/`processed_text` → extraction always empty → zero actions, ever. Fixed.

---

# Wave 0.2 — Schema Reconcile (#4 insights, #5 verification, #10 tasks)

## Tests
```
$ uv run pytest tests/test_wave02_schema.py -q
8 passed
$ uv run pytest -q          # full suite
386 passed, 9 skipped
```
- #4 is red→green (insights insert with metadata_json/updated_at: CompileError before tables.py gained the columns).
- #5 and #10 are live-migration fixes (fresh create_all DBs already match tables.py); tests guard the canonical schema + the get_history JOIN.

## Live migration 010 (applied, backup `platform.db.pre010.<ts>`)
```
$ uv run alembic upgrade head   # 009 -> 010
$ PRAGMA table_info(insights) | grep         -> metadata_json, updated_at   (#4)
$ .schema verification_results | grep        -> gate TEXT NOT NULL          (#5, was gate_name/passed/score)
$ .schema tasks | grep status                -> status TEXT NOT NULL DEFAULT 'open'   (no CHECK)  (#10)
$ INSERT tasks ... status='backlog'          -> backlog OK                 (#10, old CHECK rejected it)
$ SELECT status,COUNT(*) FROM tasks          -> done|17 (rows preserved)
```
