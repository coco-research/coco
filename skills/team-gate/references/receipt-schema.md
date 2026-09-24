# Receipt Schema, version 1.0

Each record in `receipts.jsonl` represents one event in a gate run. The schema enforces structure; the chain (prev_hash / hash) enforces integrity.

## Closed Receipt Kinds

Receipt kind must be one of: `run-started`, `stage-opened`, `artifact-written`, `agent-spawned`, `agent-returned`, `gate-result`, `worktree-registered`, `approval`, `block`, `override`, `pr-opened`, `stop-checked`, `certified`, `gate-timeout`.

Any other kind is rejected and causes the receiver to raise InvalidReceiptKind, causing exit code 2 (unrunnable: malformed request).

## Top-Level Fields

Every receipt record contains these fields:

- `seq`: integer. Sequence number starting at 1. Must be contiguous; a gap indicates truncation.
- `timestamp`: ISO-8601 string in UTC (e.g., "2026-09-17T14:22:03Z"). Sortable by creation time.
- `kind`: string from the closed set above. Identifies the event type.
- `detail`: object. Event-specific data. Structure depends on kind.
- `prev_hash`: string or null. SHA-256 hex digest of the previous record (without its hash field), or null for seq=1. Detects insertion.
- `hash`: string. SHA-256 hex digest of this record with all fields except `hash` itself, using canonical JSON (sorted keys, no spaces). Detects modification of this record.

## Gate Result Receipts

When `kind` is `gate-result`, the `detail` object contains:

- `gate`: string. Gate identifier (e.g., "preconditions", "tdd-redgreen").
- `gate_file`: string (optional). Relative path to the gate report (e.g., `gates/8.json`). Used for orphan detection. Orphan detection compares on basename; a receipt naming `gates/8.json` is matched against file `gates/8.json` by comparing only the filename `8.json`.
- `gate_sha256`: string (optional). SHA-256 hex digest of the gate file's bytes at the time the receipt was written. Used to detect if the gate file was altered after the receipt was created.

**Note**: The `gates/` directory is flat (no subdirectories). `detail.gate_file` is always of the form `gates/<n>.json` where `<n>` is a filename. Verifiers inspect only one level deep; nested gates are out of contract and will not be detected.

## Artifact Written Receipts

When `kind` is `artifact-written`, the `detail` object contains:

- `path`: string (optional). Relative path to the artifact within the repository, relative to the repository root specified in `run.json`. Paths must be relative (no absolute paths or `..` segments), and must not be symlinks. Used for two-way verification.
- `sha256`: string (optional). SHA-256 hex digest of the artifact file at the time the receipt was written. Used to detect if the artifact was altered after the receipt was created.
- `lines`: integer (optional). Line count of the artifact if it is text-based.

**Two-way verification**: When `verify-chain` executes, it validates receipt chain integrity (hashes, seq contiguity, prev_hash links) and also resolves gate-result and artifact-written receipts in the forward direction. For each receipt with `kind` = `gate-result`, `verify-chain` checks that the file named in `detail.gate_file` exists under `run_dir` and its SHA-256 matches `detail.gate_sha256`. For each receipt with `kind` = `artifact-written` that specifies a path and sha256, `verify-chain` requires `run.json` to be readable and contain a `repo_root` field; if any such receipt exists and `run.json` is missing, unparseable, or lacks `repo_root`, the chain is reported broken with details on what failed. Otherwise, `verify-chain` checks that the file named in `detail.path` exists under the repository root from `run.json` and its SHA-256 matches `detail.sha256`. Gate files and artifacts are refused when they are symlinks or when their resolved paths fall outside their base directory. If a gate file or artifact is moved, altered, deleted, or becomes a symlink after the receipt is written, `verify-chain` detects the discrepancy and reports the chain as broken.

**Latest wins for re-written gate files and re-rendered artifacts**: Receipts are an append-only log. When a stage reruns (e.g., stage 8 fails, is fixed, and reruns), the gate file is rewritten and a new gate-result receipt is appended with a new seq number and updated hash. For each distinct `detail.gate_file` among all gate-result receipts, only the receipt with the highest seq is compared against the file on disk. Earlier receipts for the same gate file are recorded as superseded; their hashes remain part of the chain and are validated as chain links, but the file-existence and SHA-256 checks are skipped. The same rule applies to artifact-written receipts: for each distinct `detail.path`, only the receipt with the highest seq is verified against disk. Gate files must be rewritten atomically, using a temporary name and then `os.replace()`, so that a reader never observes a half-written file.

## Optional Context Fields (Populated from Hook)

When `append_receipt` is called with `hook_payload`, these fields are copied if present:

- `session_id`: string. Claude Code session ID.
- `tool_use_id`: string. Tool invocation ID in the harness transcript.
- `agent_id`: string. Subagent ID (when called from a subagent).
- `agent_type`: string. Subagent type (e.g., "claude-code-guide").
- `permission_mode`: string. Permission mode in effect (e.g., "bypassPermissions").
- `cwd`: string. Working directory at the time of the call.

## Run Details (run.json)

The `run.json` file in each run directory contains:

- `run_id`: string. Unique identifier for this run (generated by start_run).
- `repo_root`: string. Path to the repository root. Absolute paths are resolved directly; relative paths are resolved against the run directory and used by test fixtures for portability across machines.
- `command`: string. The command being run (e.g., "ship").
- `flags`: array. Command-line flags passed to the run.
- `started_at`: string. ISO-8601 timestamp when the run started.

## Example Record

```json
{
  "seq": 1,
  "timestamp": "2026-09-17T14:22:03Z",
  "kind": "run-started",
  "detail": {
    "command": "ship",
    "repo_root": "/Users/x/proj"
  },
  "prev_hash": null,
  "hash": "sha256:a1b2c3d4…"
}
```

## Chain Integrity (Corruption vs Forgery)

The chain detects accidental corruption and truncation:

- **Truncation**: the last record is removed or corrupted. Detected by `head.json`, which stores seq and hash of the last record. If the last record's seq and hash do not match `head.json`, or if `head.json` is missing when receipts.jsonl exists, truncation is detected. Additional detection: orphan `gates/*.json` files (those not named by any gate-result receipt) indicate dropped receipts.
- **Insertion**: a record is spliced into the middle. The following record's `prev_hash` no longer matches the previous record's `hash`. Detected by pairwise comparison.
- **Modification**: a field in a record is changed. The record's `hash` no longer matches the canonical JSON of its fields. Detected by recomputation.

The chain is **not claimed as integrity against the model**, because the model runs at the same uid and can rewrite the entire file. Integrity against the model rests on re-derivation: a hook re-reads HEAD, recomputes the tree digest, and re-parses the stored raw output, so a forged receipt must also forge the repository state it describes. Receipt integrity is sufficient against carelessness and insufficient against an adversary. At the same uid, no software mechanism closes that gap.

The hardening that does close it uses a root-owned receipt directory (phase two), where receipts are written by a privilege-separated daemon and the agent can read but never write.

**Corrupt tail prevention**: The `append_receipt` function validates the tail of receipts.jsonl before writing. If the file has a final line that does not end with a newline, or if the last line is not a valid JSON object containing an integer `seq` field, `append_receipt` raises ReceiptFileCorrupt rather than writing the new record. The CLI reports this as exit code 2 with the message "receipts.jsonl corrupt tail: <reason>". The file is left byte-for-byte unchanged by the validation and refusal to write, so verification can recover the corruption reason and retry after correction.

## Exit Contract

Validators using this schema exit with one of three codes:

- **0**: the claim is TRUE, verdict is PASS
- **1**: the claim is FALSE, verdict is BLOCK
- **2**: the claim is NOT DECIDED (validator could not run, dependency absent, claim is UNVERIFIED, NOT APPLICABLE, or DISABLED)

No other exit code is valid. This is the house contract, adopted from `validate_roles.py` and `arch_drift.py`.
