# Quickstart cookbook

Four end-to-end scenarios. Each takes 5–60 minutes. Pick the one closest to what you want to do.

---

## 1. Ship a side project this weekend

You have an idea. You want a working prototype by Monday. Coco runs the team for you.

```bash
# Install with the orchestration bundle
git clone https://github.com/rkz91/coco.git
cd coco
bash install.sh --systems gsd,team
```

In your AI tool, type:

```
/team:ship build a habit tracker iOS app with HealthKit integration
```

What happens:

```
Stage 1  Researcher           competitive landscape, technical feasibility (5 min)
Stage 2  Architect            evaluates stack options, picks one (3 min)
Stage 3  Planner              breaks work into 5 phases, dependencies, owners (5 min)
Stage 4  Reviewer             audits the plan before any code is written (3 min)
         ─── you approve once ───
Stage 5  Fixer                addresses review findings (2 min)
Stage 6  Build agents (4×)    parallel waves, each on its own phase (varies)
Stage 7  Verifier             requirements traceability, pass/fail verdict (5 min)
         ─── shipped ───
```

The plan + code live in your project folder. Commit history is atomic per step. If you don't like a phase, `git revert` and restart from there.

**For overnight builds:** add `/coco yolo` after step 4 — autonomy mode skips approval gates after planning. Walk away. Come back to a shipped product.

---

## 2. Audit your codebase for AI-introduced bugs

Your AI tool just generated a thousand lines of code. You're about to ship. You want to know what's broken before users find out.

```bash
# Standard install (no extra bundles needed)
bash install.sh
```

In your AI tool:

```
/code-verification
```

Coco runs a 7-category audit on your changes:

| Category | What it catches |
|----------|-----------------|
| Variable hoisting (TDZ) | `const x = ...; ... f(x)` where `x` is referenced before declaration |
| Import/export integrity | named/default mismatch, missing exports, circular deps |
| Reference integrity | identifiers renamed in some files but not others |
| Dead code | functions called from nowhere, imports never used |
| React anti-patterns | `useEffect` missing deps, ref in render, state derived without `key` |
| Mock leakage | `jest.fn()` calls leaking across `describe` blocks |
| CSS class breakage | classes referenced in JSX that no longer exist in CSS |

Output:

```
PASS  variable hoisting          (0 issues)
FAIL  import/export integrity    (2 issues)
        - components/Sidebar.tsx imports `Header` as default; Header.tsx exports as named
        - utils/format.ts uses `parseDate` but parseDate.ts was deleted
WARN  react anti-patterns        (1 issue)
        - Page.tsx:42 useEffect missing dependency `userId`
PASS  ...
```

Each issue is actionable. Saves 30+ minutes of debugging per session.

---

## 3. Reverse-engineer a competitor's UI

You see a beautiful site. You want to understand how it's built. You want a prototype to riff on.

```bash
bash install.sh
```

In your AI tool:

```
/clone-website https://stripe.com
```

Coco's clone-website skill:

1. Fires up Playwright
2. Captures full-page + viewport + mobile screenshots
3. Extracts design tokens — top 30 colors, 20 type styles, all spacing values, all shadows, all border-radii
4. Walks the DOM and extracts computed styles for major sections
5. Runs interaction sweeps (scroll, hover, click) to discover behaviors
6. Builds a single-file HTML reproduction with inline CSS, inline JS, base64-encoded images
7. Compares the clone against the original via Playwright; reports visual diffs

Output: `clone.html` — a single file you can open in any browser. No build system. No CDN. No external dependencies.

Use it as inspiration, learning material, or a starting template for your own product.

---

## 4. Run a multi-phase project autonomously

You're building something real. Multiple weeks of work. You don't want to micromanage every step. You want git-tracked state, atomic commits, and verification gates.

```bash
bash install.sh --systems gsd
```

In your AI tool:

```
/gsd-new-project
```

Answers questions about your project. Creates `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json`.

```
/gsd-plan-phase
```

Researches how to implement Phase 1, writes `RESEARCH.md`, then breaks it into multi-wave plans with dependencies. Each plan has independent verification gates.

```
/gsd-execute-phase
```

Spawns agents in parallel waves. Each wave commits atomically. Built-in verification before claiming "done."

```
/gsd-progress
```

Anytime, in any session — even after `/clear` — shows current phase, completed plans, blockers, and next action. State persists on disk in `.planning/`.

```
/gsd-ship
```

When the milestone is done, creates a clean PR branch (filtered to exclude `.planning/`), runs final review, prepares for merge.

```
/gsd-undo
```

Roll back any phase or plan via the manifest, with dependency checks. Atomic commits make every action reversible.

**For autonomous mode:** `bash install.sh --systems gsd && /coco yolo` then `/gsd-autonomous` runs all remaining phases without per-step approval. Atomic commits give you a paper trail.

---

## What's next

- More scenarios in [`docs/guides/`](.) (run-an-incident-response, build-a-design-system, set-up-personal-brain — coming in v0.2)
- Per-domain skill listing in [`docs/by-domain/`](../by-domain/)
- Architecture deep-dive in [`docs/architecture.md`](../architecture.md)
- Full skill catalog in [`skills/INDEX.md`](../../skills/INDEX.md)

Open an issue if there's a scenario you'd like covered next.
