---
name: m0
description: "Use when the user says 'm0', 'm0 status', 'start m0', 'cross-tool memory', 'operational thread', or 'where is my memory stored', or when the M0 daemon or MCP wiring needs attention."
---

# /m0 — Cross-Tool Agent Memory

M0 keeps one local *operational thread* per project: what was done, what was
verified, what is next. Any tool can write to it and read it back, so a session
that starts cold can continue work another tool began.

The live M0 is the Rust daemon `coco-m0d`, serving `127.0.0.1:8000` under the
launchd job `com.coco.m0-backend`. The write path is `/m0-remember`, the read
path is `/m0-recall`, and the session handoff flow is `/m0-handoff`.

The token is read from ~/.coco/m0-token on each call; never print it.

## Quick Reference

```bash
M0="${COCO_M0_URL:-http://127.0.0.1:8000}"     # daemon base URL

# Is it up? (health needs no token)
curl -s "$M0/api/health"

# Is the launchd job loaded?
launchctl list | grep com.coco.m0-backend

# Everything else needs the token, for example the recent thread:
curl -s -H "Authorization: Bearer $(cat ~/.coco/m0-token)" \
  "$M0/api/brain/thread?project=my-project&limit=5"
```

There is no offline path: if the daemon is down, say so and stop; do not write anywhere else.

## Sub-commands

### /m0 status — is memory working

```bash
M0="${COCO_M0_URL:-http://127.0.0.1:8000}"
curl -s "$M0/api/health"
launchctl list | grep com.coco.m0-backend
```

Report to the user, in this order:

1. **Daemon** — reachable at `$M0` or not.
2. **launchd** — whether the job `com.coco.m0-backend` is loaded and running.

If either is missing, tell the user and stop. Do not work around it.

### /m0 start — you do not start it

The daemon runs under launchd; if it is down, tell the user and stop (restarts
and deploys are the owner's).

### /m0 mcp — the MCP tool

The daemon's MCP binary `coco-platform-mcp` exposes one tool, `m0`, with modes
`recall`, `context`, `wip`, `handoff`, and `remember`. Call it directly — it is
the lowest-friction way to make memory habitual.

### /m0 verify — prove it works

```bash
curl -s "$M0/api/health"
```

A healthy response means the daemon is serving. Quote the output rather than
summarising it.

### /m0 privacy — what leaves the machine

Nothing. The daemon binds to loopback, there are no outbound calls in the
request path and no telemetry. Text fields are capped at 400 characters and
redacted by the daemon before storage.

## When to reach for this

- **Use `/m0-recall`** at the start of a session, or when picking up work started
  elsewhere, before asking the user to repeat context.
- **Use `/m0-remember`** after a step lands, a decision is made, or something is
  verified.
- **Use `/m0-handoff`** before context is compacted or a session ends.
- **Use `/m0` (this skill)** for the plumbing: daemon, token, wiring.

M0 answers "where were we and what is next". For deeper knowledge-graph
retrieval see the comparison with the cognee bundle in `systems/m0/README.md`
before choosing.
