# Task 23 brief: the brownfield map as a Stage 1 artifact

The owner's thesis, stated on 2026-09-17: most projects are brownfield, so a machine-made map of the code that exists should be the first step of any ship pipeline, before the model reads anything. ripwire (redhat-et/ripwire, Apache 2.0, C++23, zero runtime dependencies, tree-sitter for twenty-four languages, offline) produces that map: ranked call graphs, impact and blast radius for a described change, and the tests that touch it. This task makes the map a measured Stage 1 artifact with a receipt, in the same shape as every other gate script, and leaves the judgement about what the map means to the model.

## Installation and audit, done by the brain

Source cloned shallowly to ~/projects/ripwire and built with cmake in Release mode (no Homebrew, which broke node earlier in this project). The binary is installed to ~/.local/bin/ripwire. Before any use on a work repository the brain audits: the source has no socket, curl or URL-fetching code outside the optional MCP server (which binds 127.0.0.1 only) and the SARIF schema URL string; CMake FetchContent blocks are provenance only with FETCHCONTENT_SOURCE_DIR pointing at vendored trees, so the build is offline; one run against the coco repository is observed with `lsof -i -p <pid>` sampled every 200 ms and must show no network sockets. The result of the audit is recorded in HANDOFF-BRAIN.md and in the wrapper's README.

## The wrapper: skills/team-gate/scripts/brownfield_map.py

Owner: Sonnet builder. Verifier: Sonnet.

Contract, the same as every gate script: stdlib only; `sys.path.insert` then `import gate_state`; the run from gate_state.find_run, absence exit 2; exit 0 when the map was written, 1 never (a map is not a pass or fail judgement), 2 when the binary is absent, the repository is unreadable, or ripwire exits non-zero. It writes `.team-ship/BROWNFIELD-MAP.md` and `.team-ship/brownfield-map.json` under the repository root taken from run.json, atomically, and appends an artifact-written receipt for each with path and sha256; it writes `gates/handoff-1-map.json` under the run directory with argv, cwd, head, exit, summary, `ripwire_version`, `binary` (the resolved path), `elapsed_seconds`, `languages` and `symbols` counts, followed by a gate-result receipt.

Invocation: `brownfield_map.py --repo-root <dir> [--for "<task in words>"] [--binary <path>]`. The binary is resolved from `--binary`, else the environment variable RIPWIRE_BIN, else `ripwire` on PATH, else `~/.local/bin/ripwire`; the resolution is recorded. The wrapper runs `ripwire <repo> --for=<task>` when a task is given, else `ripwire <repo>`, with the machine-readable output requested in JSON (read `ripwire --help` for the exact flag; record it in the README), a 300-second timeout, no shell, cwd at the repository root, and the environment stripped of proxy variables so nothing can leave the machine even by accident. It parses the JSON into `brownfield-map.json` unchanged plus a `meta` block, and renders `BROWNFIELD-MAP.md` deterministically from the JSON with these headings exactly: `## Summary` (languages, file and symbol counts, the task if given), `## Entry points` (the top-ranked symbols with file and line), `## Impact` (for a task, the symbols and files ripwire ranks as affected; without a task, the highest-churn files), `## Tests` (the test files ripwire associates with the impacted symbols, or "none identified"), `## Limits` (ripwire's own stated limits copied from its README: multi-file retrieval accuracy, pointer aliasing untracked, churn needs full history). No wall-clock anywhere in the rendered file; the run id and HEAD identify it.

Greenfield: a repository with a single commit and fewer than three source files still gets a map whose Summary says so; the artifact is always present, so the manifest can require it unconditionally.

## Manifest and check_artifacts changes (scoped edits to committed task 7 files)

ship-manifest.json stage 1 outputs gain `.team-ship/BROWNFIELD-MAP.md` with minLines 12, requiredHeadings ["Summary", "Impact", "Tests", "Limits"], forbidTokens as the other artifacts; stage 2 inputs gain the same entry, so Think cannot open without the map. The check_artifacts fixtures that model complete stages gain the map, and one new fixture, map-missing (stage-inputs 2 with the brief present and the map absent; exit 1 naming the map). This is a change to a committed, verified script and its fixtures and gets a scoped Sonnet round: the full check_artifacts self-test, the manifest against ship.md (the map is an addition, not a rename), and the new fixture.

## Fixtures for the wrapper

A stub ripwire: `fixtures/brownfield_map/stub-ripwire` is a small Python script named `ripwire` that prints a fixed JSON document shaped like the real output (copy the shape from a real run's JSON, redacted to a tiny repository) and honours `--version`; the self-test puts it first on PATH so the wrapper's self-test runs on CI without the binary. Fixtures: map-written (exit 0, both artifacts present, receipts appended, headings present, verify-chain 0), map-with-task (exit 0, the task appears in Summary and Impact is non-empty), binary-absent (PATH without ripwire and no RIPWIRE_BIN; exit 2 naming what was searched), ripwire-fails (stub exits 3; exit 2 with the stub's stderr line), no-run (exit 2), greenfield (single-commit repository; exit 0, Summary says greenfield). The self-test runs every case on a temporary copy through subprocess.run([sys.executable, __file__, ...]) and the generator follows the wave-2 rules (anchored, --out, pinned dates). One additional self-test case, real-binary, runs only when a real ripwire is found and is reported as "real-binary: skipped, no binary" otherwise; that is the one permitted skip in the suite, because CI has no binary, and it is stated in the README.

## Cross-check with prove_red (task 23b, later)

ripwire's `--test-gate` names the tests that touch a change. prove_red enumerates the tests a change added or modified. A later task compares the two on the pilot repository and records agreements and disagreements in gates/9.json under `attribution_hint`; nothing blocks on it until the comparison has been observed on real changes.

## Order

1. Brain: build, install, audit, one observed run on coco, record.
2. Sonnet builder: brownfield_map.py, fixtures, README; Sonnet verify.
3. Sonnet builder (scoped): manifest and check_artifacts fixtures; scoped Sonnet verify.
4. run_fixtures.sh gains brownfield_map.py after both land.
