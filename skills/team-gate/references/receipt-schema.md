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

## Optional Context Fields (Populated from Hook)

When `append_receipt` is called with `hook_payload`, these fields are copied if present:

- `session_id`: string. Claude Code session ID.
- `tool_use_id`: string. Tool invocation ID in the harness transcript.
- `agent_id`: string. Subagent ID (when called from a subagent).
- `agent_type`: string. Subagent type (e.g., "claude-code-guide").
- `permission_mode`: string. Permission mode in effect (e.g., "bypassPermissions").
- `cwd`: string. Working directory at the time of the call.

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

## Exit Contract

Validators using this schema exit with one of three codes:

- **0**: the claim is TRUE, verdict is PASS
- **1**: the claim is FALSE, verdict is BLOCK
- **2**: the claim is NOT DECIDED (validator could not run, dependency absent, claim is UNVERIFIED, NOT APPLICABLE, or DISABLED)

No other exit code is valid. This is the house contract, adopted from `validate_roles.py` and `arch_drift.py`.
