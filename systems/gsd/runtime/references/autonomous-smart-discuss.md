# Smart Discuss — Autonomous Mode

Smart discuss is the autonomous-optimized variant of `gsd-discuss-phase`. It proposes grey area answers in batch tables — the user accepts or overrides per area — then writes an identical CONTEXT.md to what discuss-phase produces.

**Inputs:** `PHASE_NUM` from execute_phase. Run init to get phase paths:

```bash
PHASE_STATE=$(gsd-sdk query init.phase-op ${PHASE_NUM})
```

Parse from JSON: `phase_dir`, `phase_slug`, `padded_phase`, `phase_name`.

---

## Sub-step 1: Load prior context

Read project-level and prior phase context to avoid re-asking decided questions.

**Read project files:**

```bash
cat .planning/PROJECT.md 2>/dev/null || true
cat .planning/REQUIREMENTS.md 2>/dev/null || true
cat .planning/STATE.md 2>/dev/null || true
```

Extract from these:
- **PROJECT.md** — Vision, principles, non-negotiables, user preferences
- **REQUIREMENTS.md** — Acceptance criteria, constraints, must-haves vs nice-to-haves
- **STATE.md** — Current progress, decisions logged so far

**Read all prior CONTEXT.md files:**

```bash
(find .planning/phases -name "*-CONTEXT.md" 2>/dev/null || true) | sort
```

For each CONTEXT.md where phase number < current phase:
- Read the `<decisions>` section — these are locked preferences
- Read `<specifics>` — particular references or "I want it like X" moments
- Note patterns (e.g., "user consistently prefers minimal UI", "user rejected verbose output")

**Build internal prior_decisions context** (do not write to file):

```
<prior_decisions>
## Project-Level
- [Key principle or constraint from PROJECT.md]
- [Requirement affecting this phase from REQUIREMENTS.md]

## From Prior Phases
### Phase N: [Name]
- [Decision relevant to current phase]
- [Preference that establishes a pattern]
</prior_decisions>
```

