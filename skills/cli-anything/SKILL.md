---
name: cli-anything
description: Wrap any command-line tool into a JSON-emitting agent skill. Use when you want to make a CLI reliably callable and parseable by an AI agent — introspect its --help, define a structured-output (--json) contract and a stable error contract, then generate a SKILL.md wrapper with verified examples. Triggers on "wrap this CLI", "make X agent-usable", "generate a skill for this command", "turn a tool into an agent skill".
---

<!-- Methodology adapted from HKUDS/CLI-Anything (https://github.com/HKUDS/CLI-Anything) — Apache-2.0. -->

# cli-anything: wrap any CLI into an agent skill

Turn any command-line tool into something an AI agent can call reliably and parse. The output is a thin, well-documented wrapper contract — never a reimplementation of the tool. Use the real tool; document how to drive it.

## When to use

You have a CLI (your own, or a third-party binary) and you want an agent to invoke it predictably, read structured results, and recover from errors. This skill produces a `SKILL.md` wrapper that encodes that contract.

## Step 1 — Introspect the CLI (do not guess)

Enumerate the real surface before writing anything:

- Run `<tool> --help` and `<tool> <subcommand> --help` for each subcommand.
- Capture: subcommands, flags (required vs optional), positional args, exit codes, and the output format (human text vs structured).
- If `--help` is thin, read the source or man page. Every claim in the wrapper must trace to observed behavior.

## Step 2 — Define the output contract

- Prefer a `--json` machine-readable mode for every command an agent will call. Document the exact JSON keys the agent should read (one shape per command).
- If the tool has no JSON mode, say so honestly and document what to parse from stdout (and which token carries the answer). Do not pretend output is structured when it is not.
- Human output stays the default; structured output is the agent path.

## Step 3 — Define the error contract

- Map exit codes to meaning (0 = success; document each non-zero class).
- On failure, surface a parseable signal (`{"error": "...", "code": N}` if the tool supports it, otherwise the captured stderr) — never a bare stack trace.
- Fail loud and parseable. Never half-succeed silently.

## Step 4 — Write the SKILL.md wrapper

Standard structure so an agent can discover and drive the tool:

- Frontmatter: `name`, `description` (include natural trigger phrases).
- `Commands` — each command: purpose, exact invocation, args, and the result shape it returns.
- `Examples` — 2-4 real invocations with expected output.
- `Errors` — the exit-code/error contract from Step 3.
- `Notes` — auth, side effects, idempotency, network egress, prerequisites.

## Step 5 — Verify against reality

- Run each documented command once; confirm the real output matches what the wrapper claims.
- Confirm any `--json` shape parses.
- A wrapper that drifts from reality is worse than none — re-introspect and fix.

## Principles

- Use the real tool; never reimplement its logic in the wrapper.
- Deterministic and structured beats clever.
- The wrapper is a contract: introspect, structure, document, verify.

## Worked example

`skills/coco-cli/SKILL.md` is a wrapper produced with this pattern over the `@coco-research/coco-cli` command — note how it documents the (human-only) output contract honestly rather than inventing a JSON mode the tool lacks.
