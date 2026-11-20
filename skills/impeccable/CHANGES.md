# Changes to impeccable

Modified from pbakaus/impeccable at e103efe779e2dd01274dabae83531fef00bf2563 for coco.

- `scripts/` is not included. The upstream launcher downloads and runs a binary on first use, which coco does not ship, so the skill is guidance only.
- Setup now reads the user's PRODUCT.md, DESIGN.md and surface brief directly, and does not invent missing context. The upstream launcher-unavailable fallback became the normal path.
- Every line that ran `scripts/impeccable` (context, detect, pin, doctor, concept-seed, build-phase, comp-spec, font-match, serve-question, critique-storage, embed-prompt, comp-diff, surface-brief, live-*) was rewritten to the same check done by reading files or inspecting the page, or removed where no manual equivalent exists. The commands table marks `live` and `generate` upstream only.
- Reference files rewritten for the tool removal: `SKILL.md`, `new-work.md`, `visualize.md`, `region-map.md`, `component-review.md`, `routing.md`, `init.md`, `polish.md`, `critique.md`, `layout.md`, `typeset.md`, `audit.md`, `audit.native.md`, `mode-operate.md`, `mode-persuade.md`, `mode-read.md`, `degraded/finish-reviewer.md`.
- `live`, `live-setup`, `hooks`, `generate`, `doctor`, `degraded/asset-producer` and `degraded/manual-edit-applier` now point to upstream, because those modes need the engine.
- `LICENSE` and `NOTICE.md` are unchanged.
