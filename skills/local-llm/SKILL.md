---
name: local-llm
description: Use when working with this machine's local LLM setup (LM Studio + mlx-dspark) -- checking status, changing context window, diagnosing a reasoning hang or dead request, understanding RAM/speed tradeoffs, or wiring a new script to the local inference endpoint.
domain: ops
---

# Local LLM Setup (LM Studio + mlx-dspark)

## Announce at start
"I'm using the local-llm skill to work with the local inference setup."

## Architecture

Two local LLM backends exist on this machine, serving the same underlying model
family (`Qwen3.8-27B`, 4-bit, hybrid attention -- see RAM cheatsheet below):

| Backend | Port | Role | Managed by |
|---|---|---|---|
| **LM Studio** | 1234 | Interactive chat UI use only | LM Studio app itself (own TTL-based auto-unload) |
| **mlx-dspark** | 8090 | Production -- everything `build_local.py` and any script under `systems/superintelligence/*` talks to | `launchd` (`~/Library/LaunchAgents/com.local.mlx-dspark.plist`) |

`build_local.py` (all 6 copies under `systems/superintelligence/{data-analytics,
finance,gtm,risk-compliance,strategy,trading}/scripts/`) talks **only** to
mlx-dspark. LM Studio is not in that pipeline's path at all -- it exists purely
for manual/interactive use. Do not assume both are always loaded; see
"Idle-unload" below.

Config lives outside the repo (never committed, never touched by git):
- `~/.config/mlx-dspark/start.sh` -- the server launch command (model, mode,
  context window, batch size, host/port, API key).
- `~/.config/mlx-dspark/api_key` -- 0600-perms API key file. `build_local.py`
  reads `MLX_DSPARK_API_KEY` env var first, falls back to this file.
- `~/.config/mlx-dspark/idle_watcher.py` -- the idle-unload poller (see below).
- `~/Library/LaunchAgents/com.local.mlx-dspark.plist` -- the server's LaunchAgent
  (`RunAtLoad` + `KeepAlive(Crashed)` -- verified to auto-restart on a crash).
- `~/Library/LaunchAgents/com.local.mlx-dspark-idle-watcher.plist` -- the
  watcher's own LaunchAgent (same pattern, negligible RAM, just a polling loop).

## The prefill trick (why this matters)

Both LM Studio and mlx-dspark, when hit via `/v1/chat/completions`, silently
ignore every attempt to suppress reasoning for this model (`reasoning.effort`,
top-level `reasoning`, camelCase variants, `chat_template_kwargs`, and even a
persisted per-model load config -- all tried, none worked). The model just
burns its entire `max_tokens` budget "thinking" and the caller sees total
silence until a timeout fires. This was the original "thinks then dies after 5
minutes" bug report.

**Fix:** use the raw `/v1/completions` endpoint (not chat/completions) and
hand-build a ChatML prompt with the assistant turn's `<think>` block
**pre-closed and empty**:

```
<|im_start|>user
...<|im_end|>
<|im_start|>assistant
<think>

</think>

```

Since reasoning is already "closed" in the prompt itself, the model has no
room left to think and goes straight to the real answer, giving the full
token budget to the answer instead of unbounded reasoning. This is exactly
what `_raw_prompt()` in every `build_local.py` does -- see that function's
docstring for the full investigation trail. Works identically against both
backends since they share the same jinja chat-template mechanics.

If you're wiring a **new** script to either backend, reuse this pattern --
don't call `/v1/chat/completions` and hope reasoning-suppression flags work.

## Idle-unload (don't keep the model hot-loaded when nothing is working)

Neither backend should sit fully loaded in RAM 24/7 if nothing is using it.

- **LM Studio**: has its own TTL (currently 60m/1h) that auto-unloads an idle
  model loaded via the chat UI. No extra config needed -- just don't rely on
  it staying loaded indefinitely.
- **mlx-dspark**: `idle_watcher.py` polls `/metrics`'s `requests` counter every
  60s; if it hasn't changed for 15 minutes (env var `DSPARK_IDLE_TIMEOUT_SEC`,
  default 900) **and** `/health` shows a model loaded, it calls
  `POST /admin/unload`. This frees the full target+drafter footprint (~20GB).

**What happens to a request that lands while unloaded:** `build_local.py`'s
`llm()` catches the resulting `HTTP 503` (`"no model is loaded"`), calls
`POST /admin/load` once (re-supplying only `model`+`mode` -- `context_window`
is **sticky across loads** server-side, no need to resend it), and retries the
request once. This is invisible to callers except for one cold-load delay.
Measured empirically on this machine (weights warm in OS page cache): a
reload-and-retry completed in ~7s total. A truly cold boot (fresh page cache,
e.g. right after a machine restart) would be slower -- budget more like
20-40s the first time until you've measured it fresh.

If you're calling mlx-dspark from something that ISN'T `build_local.py`
(a one-off script, a curl command, etc.), you don't get this retry for free --
either reuse `_dspark_request`/`_dspark_load` from `build_local.py`, or catch
503 yourself and POST `/admin/load` before retrying.

## RAM cheatsheet

The loaded model (`mlx-community/Qwen3.8-27B-4bit`, HF architecture
`Qwen3_5ForConditionalGeneration`) is a **hybrid attention** model: only 16 of
64 layers use full (quadratic-KV-cost) attention; the other 48 use linear
attention with ~constant memory cost. That makes its KV cache scale far
better with context length than a plain transformer, and is why 64k context is
cheap here when it wouldn't be on an all-full-attention model of this size.
`max_position_embeddings: 262144`, so 64k (and even 128k) are both well within
the model's trained range, not extrapolation.

| Context window | KV cache / request | x4 concurrent (`--max-batch 4`) |
|---|---|---|
| 32,768 | 2.0 GB | 8 GB |
| **65,536 (current default)** | **4.0 GB** | **16 GB** |
| 131,072 (128k, considered, not adopted) | 8.0 GB | 32 GB |

Base model weights: ~16GB (target) + ~4GB (drafter, `dflash` mode) = ~20GB,
before any KV cache. Add LM Studio's own separate ~16GB if it's also loaded
(chat UI use) -- this is exactly why idle-unload matters: without it, both
backends can be loaded simultaneously and there's no config-time guard against
that (each one only knows about its own footprint).

## Speed cheatsheet

LLM autoregressive decoding is **memory-bandwidth-bound**, not compute-bound:
each output token requires reading the entire model's weights once. The
theoretical per-token ceiling for single-stream (batch=1) decoding is:

```
tokens/sec ceiling = GPU memory bandwidth / model size in bytes
```

On this machine (Apple M4 Max, 40-core GPU, 546 GB/s) with this model
(~16.08GB at 4-bit): `546 / 16.08 ~= 34 tok/s` ceiling.

Measured against that ceiling:
- LM Studio: 25-27.5 tok/s (74-81% of ceiling -- well-optimized).
- mlx-dspark baseline (non-speculative): 15.2-19 tok/s (45-56% -- less
  optimized kernels than LM Studio's llama.cpp-derived backend).
- mlx-dspark `dflash` (speculative decoding): 20-35.9 tok/s (59-106% --
  *can exceed* the naive per-token ceiling, because speculative decoding
  amortizes one expensive full-weight read over `accept_len` ~2.7 accepted
  tokens per verification round instead of one token per read).

**Untapped levers, if more speed is ever needed** (ranked by expected impact):
1. **`kv_bits` (KV-cache quantization)** -- currently `0`/unused. Helps most at
   long context, since it shrinks the growing KV cache instead of the fixed
   model weights. Directly relevant now that context is 64k.
2. **`--lookup-drafts`** -- currently `false`. A cheap draft-generation mode
   worth trying if `dflash`'s drafter model ever becomes a bottleneck.
3. Lower weight quantization below 4-bit -- diminishing returns, not
   recommended without re-benchmarking accuracy.
4. **`--max-batch`** -- already at 4, matching `build_local.py`'s worker pool;
   this raises aggregate throughput across concurrent requests, not
   single-request speed.
5. Hardware upgrade (M4 Ultra ~= 2x memory bandwidth) -- out of scope, just
   noted for completeness.

## Troubleshooting playbook

**Symptom: request hangs / "thinks" forever, dies after a client timeout.**
- Confirm the request is going through the prefill trick (raw
  `/v1/completions` with a pre-closed `<think>` block), not
  `/v1/chat/completions`. Chat/completions ignores every reasoning-suppression
  flag for this model on both backends.

**Symptom: build_local.py raises "no content after 90s".**
- `REASONING_TIMEOUT` safety-net fired -- the prefill trick didn't suppress
  reasoning for some reason (unusual). Check the server is actually serving
  the expected model (`/health`'s `model` field) and that the request really
  used the raw-completions + pre-closed-think shape.

**Symptom: YAML/formatting slip in the model's own output.**
- This is a stochastic LLM output issue, not a pipeline bug. The existing
  validator (`validate_persona.py`, `pick_parseable`) is designed to catch
  this -- retry the same command; it usually self-resolves and the
  verify-gate will flag it rather than silently writing bad output if it
  doesn't.

**Symptom: request against mlx-dspark returns 503.**
- Expected if idle-unload just fired. `build_local.py`'s `llm()` already
  retries automatically once. If calling the endpoint directly (curl, a
  one-off script), POST `/admin/load` with `{"model": "mlx-community/
  Qwen3.8-27B-4bit", "mode": "auto"}` first.

**Symptom: context length errors / truncated output on long prompts.**
- Check `/health`'s `context_window` field matches what you expect (currently
  65536). If you need to raise it, see "Changing the context window" below --
  don't just increase `max_tokens` in the request, that's the output budget,
  not the context window.

**Symptom: server not responding at all.**
- `launchctl list | grep dspark` -- confirm both
  `com.local.mlx-dspark` and `com.local.mlx-dspark-idle-watcher` are listed.
  `KeepAlive(Crashed)` means a crashed server process auto-restarts within
  seconds; if it's genuinely down, `launchctl kickstart -k
  gui/$(id -u)/com.local.mlx-dspark`.

## Changing the context window

1. Edit `~/.config/mlx-dspark/start.sh`: change the `--context-window <n>`
   flag value.
2. Find and kill the running server process (`ps aux | grep mlx_dspark`) --
   `launchd`'s `KeepAlive` will restart it immediately with the new flags.
3. Poll `curl -s http://127.0.0.1:8090/health` until `status` is `"ok"` and
   confirm `context_window` matches the new value.
4. Recompute the RAM cheatsheet table above for the new value before deciding
   to go higher -- KV cache scales linearly with context and multiplies by
   `--max-batch`.

## Forward-looking note: `m0`

A **different, not-checked-out branch/worktree** of the `m0` project (this
system's operational-memory store) reportedly has an LLM-enrich step that also
talks to LM Studio. This repo's checked-out `systems/m0/` is explicitly
LLM-free by design (its own README/SPEC state "Python standard library only,
no network calls... no embedding") -- so there's nothing to reconcile here yet.
Whoever picks up that other branch should be aware of this skill and the
mlx-dspark production endpoint before wiring anything new to LM Studio, given
LM Studio is meant to stay interactive-only per this setup.
