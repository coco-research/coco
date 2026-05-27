# Prototypes

Static HTML exploration of three competing design directions for the CoCo Platform redesign (2026-04).

## Decision

**Path A (light theme, patch-existing-UI approach) was selected.**

Rationale (from project memory):

> Path A Light selected: patch existing UI, light theme, happy path focus, 23s triage target.

Path A was chosen over higher-scoring Path C (9/10 in QA) because it preserves the current
information architecture and ships faster — the goal of the redesign was to polish the
existing experience around the happy-path triage flow, not to rebuild around a command-bar
paradigm.

## Layout

```
prototypes/
├── README.md            ← this file
├── QA-REPORT.md         ← 2026-04-06 QA pass across all 24 originals
├── selected/            ← Path A — the chosen direction
│   ├── PATH-A.html              (master spec / index)
│   ├── path-a-home.html
│   ├── path-a-main.html
│   ├── path-a-agents.html
│   ├── path-a-chat.html
│   ├── path-a-costs.html
│   ├── path-a-flow.html
│   ├── path-a-happy-path.html
│   ├── path-a-inbox.html
│   ├── path-a-light.html         (light-theme variant — the locked-in look)
│   ├── path-a-project.html
│   └── path-a-real.html
└── archive/             ← Explorations not pursued (kept for reference)
    ├── PATH-B.html / path-b-*.html   (8 files — green-accent, slide-over panel system)
    ├── PATH-C.html / path-c-*.html   (9 files — command-bar / keyboard-first, highest QA score)
    ├── comparison.html               (side-by-side overview of A/B/C)
    └── inbox-redesign.html           (earlier smart-triage exploration)
```

## Why archive rather than delete

Path B and Path C contain ideas worth revisiting:

- **Path B panel system** — slide-over inspectors could land in a later phase.
- **Path C command bar (`Cmd+K`)** — already noted as a follow-on enhancement to Path A.
- **inbox-redesign.html** — the smart-triage concept that seeded path-a-inbox.html.

See `QA-REPORT.md` for per-file quality notes from the 2026-04-06 review.
