# Session Handoff — 2026-04-19

> Stop point. Resume from this file. Companion: `SESSION-HANDOFF-2026-04-16.md` (prior session), `VERSION-CONTROL-PLAN.md` (reference).

---

## 0. TL;DR

Today = review pass + cleanup + 3 hot fixes shipped + VCP Phase 0. 9 commits across 2 repos.

**What shipped:**
1. **SEC-7 fix** — token-gate `/file/` route in wiki_server.py. Commit `48632db`.
2. **stakeholder_pulse timeout + circuit breaker** — stops 7h DB wedge. Commit `f7bb1d0`.
3. **Brain schema V2 migration** — codified `/tmp/migrate_brain_events_columns.py` as callable migration. Applied directly to `~/.claude/skills/brain/scripts/brain/schema.py` (not under git).
4. **parent_project backfill** — 2,091 rows unblocked from `source_hash+conf>=0.95` dedup poisoning.
5. **Session handoff 2026-04-16 surgery** — 12 edits (review fixes, SEC downgrades, §16 lift, Priority 1a, model lock). Absorbed into commit `713ac6f`.
6. **VCP Phase 0** — `~/.coco/.gitignore` safety net + tarball snapshot to iCloud. Commits `f16fc02`, `1cf257c`, `6fe21eb`, `0259192`.

**Big finding:** `~/projects/coco-dotfiles/` is already a proper dotfiles repo (user's prior Apr 17 migration). 80 of 120 files in `~/.coco/knowledge/` = symlinks to coco-dotfiles. All today's fixes are live via symlink. `~/.coco/` repo = historical / safety-net only going forward.

**Disarmed rogue scripts:** `/tmp/conftest/*.sh` `chmod -x`. Same root cause as 12:00 master-cron mystery (plist only schedules 01:00 + 14:00).

**Wiki restarted** (new PIDs 3429, 3430) so SEC-7 token gate loads. Token at `~/.coco/.wiki-token` (chmod 600). Session-auth wall via `wiki_auth.py` already redirects `/file/` to `/login` — token gate = defense-in-depth.

**Resume order:** Phase 0 sanity check (~20 min) → if green, Phase 2 Option B (decision extraction PRD) or C (dashboard HTTP fix).

---

## 1. Today's session — what we did

### 1.1 /team review on SESSION-HANDOFF-2026-04-16.md
4 parallel agents (technical-accuracy, security-claims, PM-completeness, doc-quality). Synthesized as principal.

**Critical findings:**
- PID 57376 (pykeen) was dead — doc had hardcoded stale PID. Fix: use `pgrep`.
- 4 of 5 SEC findings (1/2/3/5) already mitigated in wiki_server.py since the 2026-04-13 security review. Only SEC-7 was live.
- §14.8 hypotheses all wrong — superseded by §16 (dedup was the actual cause).
- §13.15 #6 (article generator `model=claude-sonnet-4-6` label) already fixed in §14.6.
- Model choice was ambiguous (`gpt-5-nano` vs `gpt-5.4-nano-2026-03-17`) — locked to the latter.
- 9 broken `example.invalid` URL placeholders in §14.

**Net verdict:** doc was solid but amended faster than refreshed; TL;DR had fallen out of sync with §14/§16. 6/10 resume-readiness → ~9/10 after surgery.

### 1.2 /team develop — 3 parallel agents
Wiki SEC-7, brain schema migration, stakeholder_pulse timeout. Plus handoff doc surgery inline.

**SEC-7 (agent 1):** Token gate added. `~/.coco/.wiki-token` auto-generated chmod 600. `?t=<token>` or `X-Wiki-Token` header. `hmac.compare_digest`. 403 + stderr log on mismatch. `Cache-Control: no-store` + `X-Content-Type-Options: nosniff` on `/file/` responses. File-browser UI link updated to include token.

**Brain schema V2 (agent 2):** Blocked by sandbox. Applied manually in later step. Widened `MIGRATIONS: dict[int, str | Callable]`. Added `_migrate_events_columns_v2(conn)` — idempotent `PRAGMA table_info` gate. Bumped `SCHEMA_VERSION` to 2. 3 smoke tests pass (fresh / legacy / idempotent).

**stakeholder_pulse (agent 3):** Wrapped `update_pulse()` with wall-clock budget (`STAKEHOLDER_PULSE_TIMEOUT_SEC=600`), circuit breaker (`STAKEHOLDER_PULSE_MAX_CONTRADICTIONS=10000`), progress logging every 1K upserts or 30s. Analysis logic untouched. Deeper fix flagged: `_gather_email_dates_for_person` O(persons × bundles) I/O — future work.

**Handoff doc surgery (inline):** Absorbed into commit `713ac6f` by the user concurrently. All edits landed.

### 1.3 Hot-item execution — #1, #2, #3
- **#1 Wiki restart:** PIDs 51149, 51184 killed → 3429, 3430 fresh. Token gate code loaded. Session auth (`wiki_auth.py`) already redirects to `/login` — SEC-7 effectively double-walled.
- **#2 Brain schema applied:** Files `schema.py` + `__init__.py` edited. Backup at `.bak-20260417-170147`. Smoke tests green.
- **#3 parent_project backfill:** Killed stuck email_watcher PID 68845 (7h 15m, 66% CPU — same hang pattern stakeholder_pulse fix targets). launchd respawned as PID 10972 with new code. Ran UPDATE via `schema.knowledge_db_lock()`. **2,091 rows backfilled** (53 legit orphans remain — no PEL mapping).

### 1.4 Quick cleanup — #4, #5
- **#4 disarmed `/tmp/conftest/*.sh`:** 3 scripts `chmod -x` (run-gemma-test, run-gpt5-test, run-verify).
- **#5 12:00 master-cron mystery:** plist has only 01:00 + 14:00. The 12:00 fire was almost certainly one of the /tmp/conftest scripts — same root cause as #4.

### 1.5 Scale-verify attempt — #1 (Near-term list)
Discovered `master_cron.py --all --force` (PID 15217) was already running serially through 36 projects (kicked off 17:50 EDT). audit-board is in the queue. Did NOT launch a separate job — would have caused DB lock contention. Articles landing live: 5 new rows for 3pi-v2 in the 2 min window right before handoff write.

### 1.6 Dashboard label check — #2 (Near-term list)
**Blocked.** Dashboard process up (PID 49161 → 71659 after restarts) but port 9876 refuses connections. Log shows prior `KeyError: 'cancelled'` + `BrokenPipeError` cascade — HTTPServer daemon thread likely dies silently. Process stays alive in `write_html` loop. Two SIGKILL + kickstart cycles didn't fix. Articles don't store `model_used` in DB — no workaround.

### 1.7 VCP Phase 0
Per `VERSION-CONTROL-PLAN.md`. Tarball: 150 files, 229K, iCloud at `coco-snapshots/coco-code-20260419-1545.tar.gz`.

**Then discovered:** `~/projects/coco-dotfiles/` already exists as the proper dotfiles repo (initial snapshot commit `5558ef7` from Apr 17 17:37). 80 files in `~/.coco/knowledge/` are symlinks to it. `wiki_server.py` + `stakeholder_pulse.py` included. Our Apr 17-19 edits via the symlinks wrote to coco-dotfiles files on disk — already in the initial snapshot commit.

**Pivot:** Instead of duplicating work in `~/.coco/`, just added `.gitignore` safety net + committed the type-changes (8 files: regular → symlink) to accurately reflect disk state.

---

## 2. Commits made today

### `~/projects/coco-platform` (main branch)
```
713ac6f docs: add Section 16 — articles-not-landing RCA + fix shipped
        (also absorbed the review-derived surgery edits to §0/§6/§9/§13/§14)
```

### `~/.coco` (main branch, largely historical/safety-net now)
```
0259192 chore: untrack public/index.html (now under symlinked public/ -> coco-platform)
6fe21eb chore: reflect coco-platform migration (remaining symlinks)
1cf257c chore: reflect coco-dotfiles migration (symlink type-changes)
f16fc02 chore: add .gitignore safety net
f7bb1d0 fix(stakeholder_pulse): add timeout budget + circuit breaker to prevent DB wedge
48632db fix(wiki): SEC-7 — token-gate /file/ route to stop personal-doc exposure
```

### `~/.claude/skills/brain/` (no git)
- `schema.py` — V2 migration added (callable-based MIGRATIONS dict)
- `__init__.py` — SCHEMA_VERSION 1 → 2
- Backups at `.bak-20260417-170147` alongside

---

## 3. Current live state (session end)

### Processes
| Name | PID | Notes |
|---|---|---|
| wiki :8888 | 3429 | new — SEC-7 token gate active |
| wiki :8889 | 3430 | new — personal wiki, same |
| email_watcher | 10972 | new — runs new stakeholder_pulse.py with timeout+breaker |
| knowledge-dashboard | 71659 | **BROKEN** — port 9876 not accepting |
| master_cron --all --force | 15217 | serial through 36 projects, started 17:50 EDT |
| cron.py --run (subprocess) | 14675 | current project being processed by master-cron |
| pykeen_bridge | (pgrep) | alive, Adam checkpoint active |
| mlx-vlm-server | (launchctl) | warm-pool for Gemma4-26B |

### DBs + state
- `~/.coco/.wiki-token` — exists (chmod 600, 65 bytes)
- `~/.coco/knowledge/knowledge.db` — WAL active, backfill applied
- `~/.coco/knowledge/pykeen-model/pykeen_training_checkpoint.pt` — needs verification (§4)
- `~/.coco/events.jsonl` — 2.4 MB, growing
- Litestream replicating

### Articles status
- Pre-session: dedup shadowed 3,976 entities across 10+ projects
- Post-backfill: 2,091 rows unblocked
- Live at session end: master-cron `--all --force` producing articles for 3pi-v2, ab1
- 53 legitimate `parent_project`-blank orphans remain (no PEL mapping)

---

## 4. Pending items — refreshed backlog

Ordered by priority. Each has enough context to resume cold.

### P1 — Hot (next session)

1. **Dashboard HTTPServer crash** (new)
   - File: `~/.coco/knowledge/knowledge-dashboard.py`
   - Root cause: `KeyError: 'cancelled'` on `_STATUS_EMOJI[status]` line 818 (status value unknown in log) + `BrokenPipeError` cascade → HTTPServer daemon thread dies silently
   - Fix (30 min):
     - Line 818: `_STATUS_EMOJI[status]` → `_STATUS_EMOJI.get(status, "❓")`
     - Wrap `RerunHandler.do_GET`/`do_POST` in try/except
     - Optional: restart wrapper around `server.serve_forever()` in case it exits
   - Unblocks: #2 (label check), queue visibility, job stop buttons

2. **Watch master-cron finish audit-board** (carryover)
   - PID 15217 grinding since 17:50 EDT. Check status:
     ```bash
     ps -p 15217 2>&1
     sqlite3 ~/.coco/knowledge/knowledge.db "SELECT parent_project, COUNT(*) FROM articles WHERE updated_at > datetime('now','-24 hours') GROUP BY parent_project ORDER BY 2 DESC LIMIT 10"
     ```
   - Expected: audit-board eventually hits ~300-500 articles (2,726 entities × ~15-20% landing rate with 0.90 floor)

3. **Watch stakeholder_pulse first natural cycle**
   - Grep log:
     ```bash
     grep -E 'C2: update_pulse (START|progress|END|TIMEOUT|CIRCUIT)' ~/.coco/logs/email-watcher.log | tail -20
     ```
   - Expected: `START` → `progress` (every 1K or 30s) → `END` with total time + count. OR `CIRCUIT BREAKER TRIPPED` if est_work > 10K.
   - Escalate to deeper fix if still wedges past the 10-min budget.

### P2 — Medium-term forward motion

4. **Decision extraction pipeline** (§15.8 #1 of Apr 16 handoff)
   - Problem: `brain.decisions` empty across most projects → Phase 8 `decision_log_generator` returns None → driver marks as FAILURE (§15.8 #3)
   - Deliverable: 1-page PRD
     - Read `~/.coco/knowledge/decision_detector.py` (may already do 80%)
     - Inventory signal sources (emails, docs, meeting notes)
     - LLM prompt + confidence floor
     - Integration shape (new phase vs extend email_watcher C5)
     - Success metric (N decisions/week per active project)
   - Estimate: 2h scoping, implementation next session

5. **Phase 8 skip-by-guard sentinel** (§15.8 #3)
   - `decision_log_generator` returns None for "not enough data" → driver treats as failure
   - Fix: return `{"skipped": True, "reason": "insufficient_data"}` OR raise `PhaseSkipped` typed exception, adjust driver
   - Often paired with #4 above

6. **Pykeen Adam checkpoint verify**
   - `ls -la ~/.coco/knowledge/pykeen-model/pykeen_training_checkpoint.pt`
   - Should exist since Apr 16 20:44 pykeen restart (Adam kwargs activation)
   - If missing → restart didn't pick up new kwargs → fix

### P3 — Backlog (medium-term, no deadline)

7. **Group C2 plist treatment** — 5 plists still un-treated: `backup`, `morning-briefing`, `weekly-report`, `litestream`, `mempalace`. All currently booted-out. Re-enabling any without Group C pattern brings back boot-storm risk. Template proven on first 5.

8. **Re-enable stopped agents** (suggested order, lowest-memory first):
   - `mempalace` — vector search currently unavailable
   - `morning-briefing` — needed for 06:00 summary
   - `meeting-prep` — upcoming meeting briefings
   - `weekly-report` — Friday afternoon
   - `backup` — Sunday snapshot (litestream may suffice)

9. **`_LOCAL_MODEL_REGISTRY` framework `mlx_vlm` → `mlx_lm`** (§11.4, §7 #9 of Apr 16 handoff)
   - 2-3× speedup + lower RAM for text-only tasks
   - Warm-pool already shipped on `mlx_vlm` — coordinate swap carefully
   - Nice-to-have, not blocker

10. **stakeholder_pulse deeper fix** (flagged in commit `f7bb1d0`)
    - `_gather_email_dates_for_person` runs `EVIDENCE_DIR.glob("*.json")` per (person, project) = O(persons × bundles) I/O
    - Options: force `full_scan=True` always, OR cache global email-date index across calls
    - Only needed if current timeout+breaker proves insufficient

11. **DEV-1 wiki_server.py monolith split** (~2,100 lines)
    - Nice-to-have. Not a fire. Skip indefinitely unless SEC re-surfaces.

### P4 — Housekeeping

12. **Delete `.bak-20260417-*` files** — wiki_server, stakeholder_pulse, schema.py, __init__.py, SESSION-HANDOFF. Do once code is stable (a few clean days).

13. **Untrack existing symlinks in `~/.coco/`** — repo still tracks ~110 symlinked knowledge files. Either `git rm --cached` them all (cleanest) or accept the duplication (harmless). `~/.coco/` is the source-of-record fallback, coco-dotfiles is primary.

14. **Tombstone `~/.coco/.git`** — at some future point, when confident everything flows via coco-dotfiles. Not yet.

### Open decisions (unresolved)

- **§7 #5 (Apr 16)** Reboot timing — Adam checkpoint active since Apr 16 20:44. Safe to reboot past 48h clean. Default OK.
- **§7 #9 (Apr 16)** `mlx_vlm` → `mlx_lm` swap — per #9 above.

---

## 5. April 20 plan

Reality-first. 2-day gap between Apr 17 handoff and today — don't assume pending list reflects current state.

### Phase 0 — Sanity check (20 min, do FIRST)

```bash
# master-cron state
ps -p 15217 2>&1
tail -20 ~/.coco/knowledge/cron.log
grep -c "Master Cron starting" ~/.coco/knowledge/master-cron.log

# articles landed last 48h (dedup fix + backfill validation)
sqlite3 ~/.coco/knowledge/knowledge.db "SELECT parent_project, COUNT(*) AS n, datetime(MAX(updated_at)) AS latest FROM articles WHERE updated_at > datetime('now','-48 hours') GROUP BY parent_project ORDER BY n DESC LIMIT 15"

# stakeholder_pulse fires (fix validation)
grep -E 'C2: update_pulse (START|END|TIMEOUT|CIRCUIT)' ~/.coco/logs/email-watcher.log | tail -20

# jetsam since Fri (flock + warm-pool validation)
find /Library/Logs/DiagnosticReports -name 'JetsamEvent-*' -newermt '2026-04-17'

# pykeen checkpoint
ls -la ~/.coco/knowledge/pykeen-model/pykeen_training_checkpoint.pt

# SEC-7 smoke
TOKEN=$(cat ~/.coco/.wiki-token)
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8888/file/personal-immigration/1
curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8888/file/personal-immigration/1?t=$TOKEN"

# crashes/exceptions last 48h
grep -iE 'traceback|exception|error' ~/.coco/knowledge/cron.log | tail -20
```

**Decision tree:**
- All green → skip to Phase 2
- master-cron stuck → Phase 1 triage (kill + diagnose + restart)
- stakeholder_pulse wedged despite fix → Phase 1 deeper fix (P3 #10)
- New crashes → debug before new work

### Phase 1 — Hardening (only if needed, ≤1h)

Branch on Phase 0 findings. Default: nothing.

### Phase 2 — Forward motion (pick ONE)

**Option A — Already done.** VCP Phase 0 shipped today.

**Option B — Scope decision extraction pipeline** (2h, no code)
- Deliverable: 1-page PRD per P2 #4 above
- High value: unblocks Phase 8 composites across 10+ projects
- Risk: discovery may reveal `decision_detector.py` already does 80% → pivot to wiring

**Option C — Fix dashboard HTTPServer** (30 min)
- Per P1 #1 above
- Unblocks: label verification, queue visibility, stop buttons
- Low risk, reversible, small surface

**Recommendation:** **C first** (30 min, high leverage) then **B** (2h focused discovery). Both fit in one morning if Phase 0 is clean.

### Phase 3 — Housekeeping (end of day, 15 min)
- Clean `.bak-20260417-*` if stable → P4 #12
- Commit any Phase 2 work
- Update this handoff with next-day reality

---

## 6. Key paths reference card

```
# Source-of-record (dotfiles repo)
~/projects/coco-dotfiles/
├── coco/knowledge/          # 80+ .py files — LIVE CODE
├── launchagents/            # plists
├── .gitignore
├── README.md
└── install.sh

# Live runtime (largely symlinks to above)
~/.coco/
├── .gitignore               # NEW — safety net (f16fc02)
├── .wiki-token              # NEW — SEC-7 token (chmod 600)
├── .qb-gateway-key          # secret — gitignored
├── knowledge/               # 80% symlinks to coco-dotfiles
│   ├── wiki_server.py → coco-dotfiles (SEC-7 live)
│   ├── stakeholder_pulse.py → coco-dotfiles (timeout live)
│   ├── article_writer.py → coco-dotfiles (force-bypass live)
│   └── ...
├── knowledge.db             # gitignored — WAL + backfilled
├── events.jsonl             # gitignored — 2.4 MB
└── brain.json               # gitignored — people graph

# Platform code repo
~/projects/coco-platform/
├── SESSION-HANDOFF-2026-04-16.md       # prior session
├── SESSION-HANDOFF-2026-04-19.md       # THIS FILE
├── VERSION-CONTROL-PLAN.md             # VCP reference
├── STABILITY-PLAN.md                   # crash-fix plan
├── CRON-ECOSYSTEM-MAP.html             # visual map
└── .planning/                          # ROADMAP, UI_SPEC, FEATURES, etc.

# Brain skill (not under git)
~/.claude/skills/brain/scripts/brain/
├── schema.py                # V2 migration added today
├── __init__.py              # SCHEMA_VERSION 2
└── *.bak-20260417-170147    # backups

# Tarball snapshot
~/Library/Mobile Documents/com~apple~CloudDocs/coco-snapshots/
└── coco-code-20260419-1545.tar.gz   # 150 files, 229K
```

---

## 7. Resume tomorrow — first 10 minutes

1. `cat SESSION-HANDOFF-2026-04-19.md | head -60`
2. Run Phase 0 sanity check block (§5)
3. Decide Phase 2 path based on output (recommend C → B)

If you skip everything else, the one command that matters:
```bash
sqlite3 ~/.coco/knowledge/knowledge.db "SELECT COUNT(*) FROM articles WHERE updated_at > datetime('now','-24 hours')"
```
If that number is >500 = ecosystem healthy, pick forward work. If 0 = something's broken, triage.

---

## 8. Verification checklist

- [x] `~/.coco/` 6 commits today, clean except intentional untracked
- [x] `~/.coco/.wiki-token` exists, chmod 600
- [x] `~/.coco/.gitignore` present with DBs/secrets/caches blocked
- [x] wiki PIDs 3429 + 3430 (fresh, SEC-7 loaded)
- [x] email_watcher PID 10972 (runs new stakeholder_pulse.py)
- [x] `~/.claude/skills/brain/scripts/brain/__init__.py` SCHEMA_VERSION = 2
- [x] coco-dotfiles git status clean — all today's fixes live via symlink
- [x] `/tmp/conftest/*.sh` disarmed (chmod 644)
- [x] 2,091 articles backfilled for parent_project
- [x] 53 legitimate orphans remain (no PEL)
- [x] Tarball `coco-code-20260419-1545.tar.gz` in iCloud
- [ ] ⏰ Dashboard HTTPServer fix — deferred to Apr 20
- [ ] ⏰ Phase 0 sanity run — Apr 20 morning
- [ ] ⏰ audit-board scale verification — via live master-cron
- [ ] ⏰ stakeholder_pulse first natural fire — grep log when available

---

**End of handoff. Good luck tomorrow.**

---

## 9. Post-handoff updates (added later 2026-04-19)

Since §2 was written, 4 more commits landed across 2 repos plus the 04-16 doc got a Section 18 reconciliation.

### 9.1 New commits

**`~/projects/coco-platform`:**
```
cb108b7 docs: Section 18 — reanalysis snapshot as of 2026-04-19
        Reconciles §0-17 of 04-16 doc vs current state. 14-claim delta table.
```

**`~/projects/coco-dotfiles`:**
```
0f342e9 2026-04-19 09:10 — Rip Anthropic SDK + claude CLI fallback paths — gpt-5-nano only
33b7c32 2026-04-17 18:47 — cron.py + wiki_improver.py: bump max_workers 8 → 20
3420bde 2026-04-17 18:20 — cron.py + wiki_improver.py: bump max_workers 3 → 8
```

### 9.2 Architecture pivot (per Section 18 of 04-16 doc + `0f342e9`)

- **Anthropic SDK + `claude -p` CLI fallback paths removed.** gpt-5-nano is the only LLM path now.
- **Warm MLX server retired.** No longer in process list. PID 55642 from earlier handoff is dead.
- **max_workers bumped 3 → 20** in `cron.py` + `wiki_improver.py`. QB gateway absorbed the parallelism without rate-limit issues.
- Several §14.8 / §14.11 / §15.8 / §16.6 / §17.8 "pending" items in 04-16 doc now resolved, obsolete, or moot per Section 18 delta table.

### 9.3 What this means for the P1-P4 lists above

- **P2 #9 (`mlx_vlm → mlx_lm` swap)** — obsolete. Warm MLX retired entirely.
- **P2 #6 (pykeen Adam checkpoint verify)** — still valid, independent of LLM path.
- **P1 #1 (dashboard HTTPServer crash)** — still valid, independent.
- **P1 #2 (audit-board scale verification)** — invalidated if `master_cron --all --force` already completed. Check via Phase 0 sanity block.
- **P2 #4 (decision extraction PRD)** — still the highest-leverage forward item.

### 9.4 Current uncommitted state

`~/projects/coco-platform`:
- `SESSION-HANDOFF-2026-04-19.md` — this file, not yet committed (will be after this update)
- `frontend/src/bones/home-dashboard.bones.json` — pre-existing modification from prior session, unrelated

Everything else across the 3 repos = clean.

### 9.5 Verification checklist updates

- [x] Section 18 of 04-16 doc reconciles prior "pending" claims against reality
- [x] gpt-5-nano-only routing in coco-dotfiles (`0f342e9`)
- [x] max_workers=20 active
- [ ] ⏰ audit-board completion check — query articles table for last 48h row counts
- [ ] ⏰ Phase 0 sanity run — deferred to Apr 20

### 9.6 Recommended resume order (updated)

1. Phase 0 sanity block from §5 — confirms ecosystem state
2. **C → Dashboard fix (30 min)** — unblocks label/queue visibility
3. **B → Decision extraction PRD (2h)** — forward motion on the one remaining data gap
4. Housekeeping at end of day (cleanup .bak-20260417 files, update this doc with Apr 20 reality)

End of §9 update.
