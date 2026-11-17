<purpose>
Orchestrate the full developer profiling flow: consent, session analysis (or questionnaire fallback), profile generation, result display, and artifact creation.

This workflow wires Phase 1 (session pipeline) and Phase 2 (profiling engine) into a cohesive user-facing experience. All heavy lifting is done by existing `gsd-sdk query` handlers (with legacy `gsd-tools.cjs` parity where needed) and the gsd-user-profiler agent -- this workflow orchestrates the sequence, handles branching, and provides the UX.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
