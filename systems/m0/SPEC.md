# M0 protocol specification

**Spec version:** `m0/1`
**Status:** stable
**License:** MIT

M0 is a minimal protocol for a shared *operational thread*: the running record of
what an agent did, what it verified, and what should happen next. Any number of
tools — different CLIs, editors, hooks, daemons — write to one store and read the
same thread back, so a session that starts cold can pick up where another left off.

This document is the contract. It is written so that a second implementation can
be built from it without reference to any particular codebase, in any language,
and remain wire-compatible. The reference implementation that ships with this
bundle (`skills/m0/scripts/m0_server.py`, Python standard library only) is one
conforming server, not the definition.

The keywords MUST, MUST NOT, SHOULD and MAY are used in the usual sense.

---

## 1. Data model

A conforming store holds exactly one logical relation, `operational_thread`, with
these fields. The order is normative because the content hash depends on it.

| # | Field | Type | Null | Meaning |
|---|-------|------|------|---------|
| 1 | `id` | text | no | Primary key. The content hash defined in §2. |
| 2 | `project` | text | no | Project key that scopes the thread. Any stable string; a repository or directory name is typical. |
| 3 | `session_id` | text | yes | Identifier of the writing session, when the writer knows one. |
| 4 | `source_tool` | text | yes | Which tool wrote the entry (`claude-code`, `cursor`, `mcp`, a hook name, …). Provenance for cross-tool reading. |
| 5 | `role` | text | yes | Who the entry speaks for. `assistant` by default; `user` or `system` are permitted. |
| 6 | `kind` | text | no | One of the values in §3. |
| 7 | `ts` | text | no | Write time, UTC ISO-8601 with a literal trailing `Z`, e.g. `2026-08-01T13:31:26.536Z`. Millisecond precision is RECOMMENDED. |
| 8 | `branch` | text | yes | Version-control branch at write time, when meaningful. |
| 9 | `head_sha` | text | yes | Version-control HEAD at write time, when meaningful. |
| 10 | `next_step` | text | yes | The single next action a fresh session should take. |
| 11 | `last_verified` | text | yes | What was actually verified, and how. Distinguishes a checked claim from an assumed one. |
| 12 | `text` | text | no | The entry itself, in prose. MUST be non-empty. |
| 13 | `meta_json` | text | yes | Structured metadata, stored as a canonical JSON string (§4). |
| 14 | `owner_user_id` | text | yes | Owner of the row. Defaults to a single local identity; present so a multi-tenant store can enforce ownership without a schema change. |
| 15 | `visibility` | text | yes | `private` (default), or any value a deployment defines. Present for the same reason as `owner_user_id`. |

A store SHOULD index `(project, ts DESC)` and `(project, kind, ts DESC)`.

Nothing else is required. There is no separate session table, no embedding, no
graph. That is the point: the thread is append-only prose plus a handful of
context columns, which is what makes the protocol implementable in an afternoon.

## 2. Identity: the content hash

`id` is the lowercase hex SHA-256 of the entry's content-bearing fields:

1. Take fields 2–15 above **in table order, skipping `ts`** — that is:
   `project`, `session_id`, `source_tool`, `role`, `kind`, `branch`, `head_sha`,
   `next_step`, `last_verified`, `text`, `meta_json`, `owner_user_id`,
   `visibility`.
   Note that the traversal order is the table order, so `kind` precedes `branch`.
2. Replace every null with the empty string. Apply the defaults from §5 *before*
   hashing, so a defaulted field and an explicitly supplied identical value hash
   the same.
3. Join with a single NUL byte (`U+0000`) as separator.
4. UTF-8 encode, SHA-256, lowercase hex, all 64 characters.

Reference implementation:

```python
HASHED = ("project", "session_id", "source_tool", "role", "kind", "branch",
          "head_sha", "next_step", "last_verified", "text", "meta_json",
          "owner_user_id", "visibility")

def content_id(row):
    joined = "\x00".join((row.get(f) or "") for f in HASHED)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
```

`ts` is excluded because it is a clock reading, not content. Two writes of the
same content at different times are the same entry; that is what makes a retry,
a re-fired hook, or a replayed log harmless.

## 3. `kind` values

Exactly six values are defined. A server MUST reject an unknown `kind` rather
than storing it, so that a typo fails loudly instead of creating a category no
reader knows to look for.

| `kind` | Use it for |
|--------|-----------|
| `step_done` | A completed step, a fact, or a decision. The default. |
| `compact_checkpoint` | A session handoff: enough state that a fresh session can continue. Written before context is dropped or a session ends. |
| `session_end` | A session closing. Typically written by a shutdown hook. |
| `lane_dispatched` | Work delegated to a subagent, worker or parallel lane. |
| `lane_result` | The outcome of delegated work. |
| `ambient_signal` | Context observed passively rather than reported by the agent. |

## 4. `meta_json` normalisation

`meta_json` is stored as a canonical JSON string: keys sorted, no insignificant
whitespace (`json.dumps(obj, sort_keys=True, separators=(",", ":"))`). Canonical
form is required so that logically identical metadata hashes identically.

A conforming server MUST accept all of the following for the write field, and
normalise before hashing:

| Input | Stored as |
|-------|-----------|
| JSON object or array | canonicalised form of that value |
| String that parses as a JSON object or array | canonicalised form of the parsed value |
| String that parses as a JSON scalar | `{"value": <scalar>}` |
| Number or boolean | `{"value": <scalar>}` |
| Any other string | `{"note": "<the string>"}` |
| `null`, absent, or empty string | null |

The last row is deliberate. A metadata parameter that rejects input it could
have stored is worse than a lenient one: callers stop using it, and the metadata
never gets written at all. **This rule exists because of a real defect.** In an
MCP tool, declaring this parameter as `{"type": "string"}` makes it unusable —
clients parse a JSON-looking string argument into an object before the tool is
invoked, so the value that arrives never matches the declared type and every
valid call is rejected. Declare it as `{"type": "object"}` and accept strings
defensively, as §7 requires.

Servers MUST accept `meta` as an alias for `meta_json` on write.

## 5. Write — `POST /api/brain/checkpoint`

Request body: a JSON object.

| Field | Required | Default |
|-------|----------|---------|
| `project` | yes | — (a server MAY substitute an environment default) |
| `text` | yes | — MUST be non-empty after trimming |
| `kind` | no | `step_done` |
| `next_step` | no | null |
| `last_verified` | no | null |
| `meta_json` (or `meta`) | no | null |
| `session_id` | no | environment default, else null |

A conforming server MUST also accept these optional passthrough fields, which map
onto the remaining columns: `source_tool`, `role`, `branch`, `head_sha`,
`owner_user_id`, `visibility`, `ts`. Clients that record version-control context
(the handoff flow does) need them, and a server that silently dropped them would
lose data it was handed.

Defaults applied before hashing: `role` → `assistant`, `owner_user_id` → a local
identity (`local` in the reference server), `visibility` → `private`,
`ts` → now. A server MAY source `session_id`, `source_tool`, `owner_user_id` and
`visibility` from its environment when absent from the body.

Response, HTTP 200:

```json
{"id": "<64 hex chars>", "ts": "<stored ts>", "ok": true, "deferred": false}
```

- `id` — the content hash (§2).
- `ts` — the timestamp **as stored**. On a repeat write this is the original
  timestamp, not the current time (§6.1).
- `ok` — `true` when the write is durable *or* spooled. A write that is neither
  MUST NOT report `ok: true`.
- `deferred` — `true` when the entry went to the sidecar spool instead of the
  store (§6.2).

Errors: HTTP 400 with `{"ok": false, "error": "<message>"}` for a missing
`project`, an empty `text`, an unknown `kind`, an unparseable body, or a
non-integer `limit`. HTTP 404 for an unknown route, 500 for an unexpected fault.
A server MUST NOT return HTTP 200 with `ok: false`.

## 6. Guarantees

### 6.1 Idempotent

The write is an upsert on `id`. Writing the same content twice MUST leave exactly
one row and MUST return the same `id`. First write wins: a repeat MUST NOT
overwrite the stored `ts` or any other stored field. Consequently two identical
writes return byte-identical responses, which is the cheapest way for a caller
to tell a retry from a new entry.

### 6.2 Never loses a write

Callers include shutdown and compaction hooks: paths that run once, at a bad
moment, and cannot retry. So a write that cannot reach the store MUST NOT be
dropped.

When the store rejects the insert because it is busy or locked, the server MUST:

1. Serialise the fully normalised entry (all 15 fields, `id` and `ts` included)
   to a sidecar file, written atomically — temporary file in the same directory,
   `fsync`, then rename over the target.
2. Return HTTP 200 with `deferred: true` and `ok: true`.

The sidecar file MUST be a single JSON object whose keys are the field names of
§1. The file name is unconstrained; `<ts>-<id prefix>.json` sorts usefully.

A conforming server MUST drain the spool on start: for each file, insert the
entry (idempotently, per §6.1) and delete the file on success. If the store is
still busy, the remaining files MUST stay spooled for a later attempt. A file
that is not valid JSON, or lacks an `id`, MUST be moved aside rather than
retried forever. A server MAY also expose an explicit drain (the reference
server has `POST /api/brain/sidecars/drain` and a `drain` CLI subcommand).

### 6.3 Bounded

Every store call MUST carry an explicit busy timeout, and it MUST be short
enough that a caller can tell "busy" from "hung". A default in the region of
10 seconds is RECOMMENDED and MUST be configurable. Long timeouts — a minute or
more — are non-conforming: from the caller's side, a two-minute wait inside a
shutdown hook is indistinguishable from a hang, and the deferred path in §6.2
exists precisely so that waiting is never necessary.

### 6.4 Local-only by default

A conforming server MUST default to a loopback bind, MUST NOT make outbound
network calls in the course of serving these endpoints, and MUST NOT emit
telemetry. A non-loopback bind SHOULD warn, since the protocol defines no
authentication.

### 6.5 Resilient read

A read MUST still succeed while the store is busy. A server SHOULD return the
union of the stored rows and the pending sidecar entries, marking the pending
ones (the reference server sets `"pending": true`), so that a deferred write is
readable immediately rather than after the next drain. If the stored rows cannot
be read at all, the server SHOULD return what it has and report the reason in
`degraded`.

## 7. Read — `GET /api/brain/thread`

Query parameters:

| Parameter | Required | Default | Meaning |
|-----------|----------|---------|---------|
| `project` | no | all projects | Scope to one project. |
| `limit` | no | 20 | Maximum entries. A server SHOULD cap this (500 in the reference server). |
| `kind` | no | all kinds | Filter to one `kind`. An unknown value MUST be rejected. |

Response, HTTP 200: entries ordered by `ts` descending — **newest first** — with
`id` descending as a tiebreak.

```json
{
  "project": "acme-web",
  "kind": null,
  "limit": 20,
  "count": 1,
  "pending_sidecars": 0,
  "degraded": null,
  "entries": [
    {
      "id": "9a71de71…",
      "project": "acme-web",
      "session_id": "sess-001",
      "source_tool": "claude-code",
      "role": "assistant",
      "kind": "compact_checkpoint",
      "ts": "2026-08-01T13:31:26.536Z",
      "branch": "feat/auth",
      "head_sha": "deadbee",
      "next_step": "Wire the new middleware into the admin router.",
      "last_verified": "pytest tests/ -q: 214 passed",
      "text": "Refactored the auth middleware and got the full suite green.",
      "meta_json": "{\"pr\":42,\"tests\":\"green\"}",
      "owner_user_id": "local",
      "visibility": "private"
    }
  ]
}
```

Every entry MUST carry all 15 fields of §1. `count`, `entries` and newest-first
ordering are required; `pending_sidecars` and `degraded` are RECOMMENDED.
Additional keys are permitted, so clients MUST ignore fields they do not know.

## 8. MCP surface

A conforming MCP server exposes at least two tools over JSON-RPC 2.0 on stdio:

- **`m0_remember`** — wraps §5. Required input: `text`. Optional: `project`,
  `kind` (enumerated), `next_step`, `last_verified`, `session_id`, `branch`,
  `head_sha`, and `meta`.
- **`m0_recall`** — wraps §7. Optional input: `project`, `limit`, `kind`.

`meta` MUST be declared as `{"type": "object"}`, for the reason given in §4.
Tool-execution failures MUST be returned as a result with `isError: true`, not
as a JSON-RPC protocol error, so the client can show the agent what went wrong.

## 9. Optional endpoints

A server MAY implement these. Clients MUST NOT depend on them.

- `GET /api/health` → `{"ok", "version", "spec", "db", "rows", "pending_sidecars", "degraded", "local_only", …}`
- `POST /api/brain/sidecars/drain` → `{"drained", "skipped", "quarantined"}`

## 10. Conformance checklist

An implementation conforms to `m0/1` when all of the following hold:

- [ ] `operational_thread` carries all 15 fields of §1 with the stated nullability.
- [ ] `id` matches the §2 hash for the same input, byte for byte.
- [ ] The six `kind` values of §3 are accepted; anything else is rejected.
- [ ] `meta_json` normalises per §4, including the object/string/free-text cases.
- [ ] `POST /api/brain/checkpoint` accepts §5's required, optional and passthrough fields and returns the four documented response keys.
- [ ] A repeat write returns the same `id` and `ts` and leaves one row (§6.1).
- [ ] A busy store yields `deferred: true` plus an atomically written sidecar, and the spool drains on start (§6.2).
- [ ] Every store call has a configurable, short busy timeout (§6.3).
- [ ] Loopback bind by default, no outbound calls, no telemetry (§6.4).
- [ ] Reads succeed while the store is busy (§6.5).
- [ ] `GET /api/brain/thread` returns newest-first entries with all 15 fields (§7).
- [ ] The MCP `meta` parameter is typed `object` (§8).

`systems/m0/tests/m0-smoke.sh` exercises every item on that list against a live
server, in a throwaway directory. Run it against your own implementation by
pointing `M0_BASE_URL` at it.

## 11. Versioning

The spec version is `m0/1`. Additive fields and additional endpoints are minor
changes and do not bump it. Anything that changes the hash input, the meaning of
a `kind`, or a response key that clients read bumps it to `m0/2`. A server
SHOULD report its spec version from `GET /api/health`.
