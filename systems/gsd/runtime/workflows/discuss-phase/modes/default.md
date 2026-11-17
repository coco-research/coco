# Default mode — interactive discuss-phase

> **Lazy-loaded.** Read this file from `workflows/discuss-phase.md` when no
> mode flag is present (the baseline interactive flow). When `--text`,
> `--batch`, or `--analyze` is also present, layer the corresponding overlay
> file from this directory on top of the rules below.

This document defines `discuss_areas` for the default flow. The shared steps
that come before (`initialize`, `check_blocking_antipatterns`, `check_spec`,
`check_existing`, `load_prior_context`, `cross_reference_todos`,
`scout_codebase`, `analyze_phase`, `present_gray_areas`) live in the parent
file and run for every mode.

## discuss_areas (default, interactive)

For each selected area, conduct a focused discussion loop.

**Research-before-questions mode:** Check if `workflow.research_before_questions` is enabled in config (from init context or `.planning/config.json`). When enabled, before presenting questions for each area:
1. Do a brief web search for best practices related to the area topic
