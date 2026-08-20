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
- mlx-dspark `dflash` (speculative decoding): highly variable, because the
  gain depends entirely on how predictable the output is. Measured on this
  machine at 111 tok/s on trivially predictable output and 10.1 tok/s on
  open-ended prose, against a server-reported mean of about 14 tok/s across
  mixed real requests. Speculative decoding amortizes one expensive
  full-weight read over several accepted draft tokens, so it can exceed the
  naive per-token ceiling when the drafter is usually right and falls back
  toward the base rate when it is not. See "Timing expectations" below for
  the measurements and the method.

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

## What this model is good at, and what it is not

The local model runs entirely on the local machine, which ensures that no data leaves the device and that there is no per-token cost associated with usage. The measured decode speed ranges from 20 to 35 tokens per second, and the context window supports 65,536 tokens. The model performs well at summarizing many small-to-medium diffs, at bulk classification of files into categories, and at mechanical text transformation, which represent its strongest use cases. It has no network access at all, so it cannot perform web research, cannot resolve a URL, and cannot look up a current fact beyond its training data. The model is weak in scenarios where a silently wrong answer is expensive, such as merge conflict resolution, security judgements, and attribution or licensing decisions. In those cases, the model should gather and summarize evidence, then a human or a stronger model should make the actual decision. Because the model is slow relative to a hosted model, it is preferable for work that is bulky and mechanical rather than short and latency sensitive.

## Known failure modes

Diff polarity inversion occurs when the model is asked to summarize a unified diff and reports a text change in the wrong direction. Specifically, the model may state that a value changed from A to B when the diff actually shows it changing from B to A. This was observed on a real diff and matters because the two directions can have opposite consequences. The mitigation is to state the polarity explicitly and twice in the prompt, specifying which side the minus lines come from and which side the plus lines come from. The prompt must also require the model to quote the raw diff line verbatim, including its leading plus or minus character, as evidence for every claim. The quoted line makes each claim cheap to verify with a single search, and any claim without evidence should be discarded.

Silent truncation happens if the returned `completion_tokens` value is equal to the `max_tokens` that was requested. In this case, the answer was cut off mid-thought rather than completed, even though the output can still look superficially finished. The mitigation is to compare those two numbers on every call and treat equality as a failure. The system should then raise `max_tokens` and run the request again rather than using the partial answer.

Reasoning suppression being ignored is a failure mode where every documented flag for suppressing reasoning is ignored by the model on the chat completions endpoint. This causes the model to exhaust its whole output budget before answering. The mitigation is the prefill technique described elsewhere in this document, and it is not optional.

During a test where the caller requested the local LLM to reproduce a code block verbatim, the model emitted the end-of-turn token string as part of the requested content because that specific string was present in the source code. Since the server had configured this same string as the stop sequence, it interpreted the emitted token as a termination signal and halted generation prematurely, resulting in a response that ended mid-sentence after only 112 tokens. This behavior is indistinguishable from unrelated truncation errors, which creates a significant risk of misdiagnosis during troubleshooting. To mitigate this issue, callers must either unset the stop sequence for requests where the output may legitimately contain the stop string and trim any trailing content afterwards, or substitute a placeholder token in the prompt and swap the real value back in after generation. A general rule to prevent this failure mode is to never ask the model to echo its own control tokens.

## Giving the model web access

The mlx-dspark server is only an inference endpoint. It has no browser, no tool calling loop, and no network egress of its own, so the model genuinely cannot fetch anything. The practical pattern is therefore to keep the network on the caller's side. The orchestrating agent performs the fetch or the search itself, then passes the retrieved text into the prompt as context. The local model still does all of the reasoning, and the caller acts only as its input and output layer. This approach needs no additional infrastructure.

A second option is to build a genuine tool calling loop, since the server exposes an OpenAI compatible API and could therefore emit a structured request that the caller executes and feeds back. Tool calling reliability on a 27B four-bit model is mediocre, so this is worth building only when the extra autonomy is actually needed. Whichever pattern is used, remember the context window is 65,536 tokens, so fetched pages should be trimmed or summarized before they are pasted in.

## Calling it from your own script

The preceding sections of this document describe the prefill technique conceptually, but they do not provide a ready-made implementation. This section supplies a working client so that a new caller does not have to reconstruct the specific request structure from scratch. The existing `build_local.py` script is designed as a persona pipeline rather than a general purpose client, which is why a standalone version is useful for other use cases.

### The four things that are easy to get wrong

- The endpoint must be `/v1/completions` and not `/v1/chat/completions`.
- The assistant turn's `<think>` block must be present and already closed and empty, otherwise the model spends its entire budget reasoning.
- The stop sequence must be set to `["<|im_end|>"]`, because without it the model can continue past the end of its turn and emit further dialogue.
- A returned `completion_tokens` equal to the requested `max_tokens` means the answer was truncated and must not be used as though it were complete.

### Timing expectations

The primary finding from this setup is that decode throughput is not a single fixed value; it varies by more than a factor of ten depending on how predictable the output text is. Consequently, citing a single "tokens per second" figure is misleading for this specific configuration.

The server operates in speculative decoding mode, where a smaller drafter model proposes several tokens and the large model verifies them in a single pass. When the output is highly predictable, the drafter is usually correct, allowing many tokens to be committed per expensive weight read. This raises throughput far above the naive memory-bandwidth ceiling. Conversely, when the output is open-ended prose, the drafter is often incorrect, few tokens survive each verification round, and throughput falls back toward or below the base rate.

The following table presents measured decode figures for single-stream requests on this machine. The request counter was verified to advance by exactly one per call to ensure no other traffic interfered with the measurements.

| Output kind | Tokens produced | Wall clock | Decode rate |
| :--- | :--- | :--- | :--- |
| Highly predictable output (counting from 1 to 400) | 401 | 3.6 s | 111 tokens per second |
| Open ended technical prose | 481 | 47.6 s | 10.1 tokens per second |

The mechanism behind that spread is measurable rather than theoretical. The throughput of a server using speculative decoding is determined by the ratio of tokens accepted per verification round to the duration of that round, where each round incurs a fixed cost for a single pass through the large model regardless of the draft length. In a controlled test on a single stream, the server drafts up to eight tokens per round, and the measured performance varied significantly based on output predictability. For trivially predictable output such as counting, the system accepted the full eight tokens per round with a round time of 78 milliseconds, yielding a rate of 103 tokens per second. In contrast, open ended prose accepted only 2.55 tokens per round with a round time of 133 milliseconds, resulting in a rate of 19.3 tokens per second. These two effects compound, as the reduction in accepted tokens is roughly three times greater and the round time is about 1.7 times slower, which together account for the observed five fold difference in throughput. Consequently, the planning figure for performance is set by the nature of the output rather than by the hardware, and analytical prose work should be planned at the low end.

| Output kind | Tokens accepted per round | Time per round | Resulting rate |
| :--- | :--- | :--- | :--- |
| Trivially predictable (counting) | 8.00 | 78 ms | 103 tokens/s |
| Open ended prose | 2.55 | 133 ms | 19.3 tokens/s |

The server's own /metrics endpoint reported a mean of about 14 tokens per second across 30 mixed real requests. This average is the appropriate figure to use when planning for ordinary work.

Prompt processing, or prefill, is a distinct cost from decode and dominates latency on long inputs. This cost was measured by issuing two requests that requested the same output length but differed by 5,995 prompt tokens. The request with the longer prompt took 32.7 seconds more to complete, yielding a prefill rate of roughly 183 tokens per second. The practical consequence is that a prompt of 13,000 tokens costs approximately 70 seconds before generation even begins.

The server is configured with a maximum batch size of four. Therefore, several callers sharing the server simultaneously will each observe lower throughput than the single-stream figures listed above. Anyone performing benchmarks should check the "requests" counter in the /metrics endpoint before and after a call. They must confirm that the counter advanced by exactly one; otherwise, the measurement includes traffic from other users.

Callers should set client timeouts in minutes rather than seconds. They should expect roughly 14 tokens per second when planning ordinary analytical work and treat any faster performance as a bonus that depends on the predictability of the output. Finally, callers should prefer fewer large requests over many small ones because each request incurs its own prefill cost.

### A working client

The client below is a standalone Python function.

```python
import json, os, pathlib, urllib.error, urllib.request

BASE = "http://127.0.0.1:8090"
MODEL = "mlx-community/Qwen3.8-27B-4bit"
STOP = "<|im_end|>"


def _key():
    k = os.environ.get("MLX_DSPARK_API_KEY")
    if k:
        return k
    p = pathlib.Path.home() / ".config/mlx-dspark/api_key"
    if not p.exists():
        raise RuntimeError(f"no API key: set MLX_DSPARK_API_KEY or create {p}")
    return p.read_text().strip()


def _post(path, payload, timeout=900):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + _key()},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ask(question, max_tokens=1600, temperature=0.3, stop=(STOP,)):
    """Return (text, usage) from the local model.

    Raises RuntimeError if the reply was cut short, so a partial answer can
    never be mistaken for a complete one. Pass stop=() when the desired output
    may legitimately contain the stop string.
    """
    payload = {
        "model": MODEL,
        "prompt": ("<|im_start|>user\n" + question + STOP + "\n"
                   "<|im_start|>assistant\n<think>\n\n</think>\n\n"),
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if stop:
        payload["stop"] = list(stop)
    try:
        out = _post("/v1/completions", payload)
    except urllib.error.HTTPError as e:
        if e.code != 503:
            raise
        # Idle-unloaded. Reload once, then retry exactly once.
        _post("/admin/load", {"model": MODEL, "mode": "auto"})
        out = _post("/v1/completions", payload)

    text = out["choices"][0]["text"].strip()
    usage = out.get("usage") or {}
    produced = usage.get("completion_tokens")

    # Truncation is detected two ways, because the token count alone is not
    # enough: the server may omit usage entirely, and a stop-string collision
    # halts generation well below max_tokens.
    if produced is None:
        raise RuntimeError("no usage in response; cannot confirm completeness")
    if produced >= max_tokens:
        raise RuntimeError(
            f"truncated at max_tokens={max_tokens}; raise it and retry")
    finish = (out["choices"][0].get("finish_reason") or "").lower()
    if finish and finish not in ("stop", "eos", "length_stop", ""):
        raise RuntimeError(f"unexpected finish_reason {finish!r}; treat as partial")
    return text, usage
```

The 503 branch handles the idle unload described elsewhere in this document. The truncation check is deliberately an exception rather than a warning so that a partial answer cannot be used by accident. The imports required are `json`, `os`, `pathlib`, `urllib.request` and `urllib.error`.

## Concurrency does not help on this setup

The `--max-batch 4` flag sets a ceiling on how many requests may be in flight at once, it does not force a batch size, so a single request is not penalised by it. This distinction is important because the flag is easy to misread as a fixed batch size that would artificially constrain single-user performance.

On this server, running requests concurrently reduces total throughput rather than increasing it. Normally batching raises aggregate tokens per second while lowering per-request speed. Here both fall. The measurements below were taken with open-ended prose of the same length, issued together.

| Concurrent requests | Aggregate tokens per second | Mean per request | Slowest request |
| :--- | :--- | :--- | :--- |
| 1 | 12.7 | 12.7 | 12.7 |
| 2 | 12.4 | 9.6 | 6.1 |
| 4 | 11.3 | 6.1 | 2.2 |

There is a significant fairness problem at four concurrent requests. The individual rates were 12.4, 6.1, 2.2, and 3.6 tokens per second, so the first caller ran roughly five and a half times faster than the slowest one. Work queued behind other work starves rather than degrading evenly.

The likely mechanism is that speculative decoding already converts spare compute into speed by having a drafter propose tokens that the large model verifies in one pass, so the memory bandwidth is already well used at a single stream. Adding concurrent streams therefore competes for bandwidth that was not idle, while also multiplying the key-value cache footprint. This is the most probable explanation given the numbers rather than a proven cause.

Callers should serialise work through this server and queue requests rather than fanning them out. Parallelism buys no aggregate throughput here and costs latency and predictability.

### A memory consequence worth acting on

The key-value cache is reserved per batch slot, so at a 65,536 token context each slot costs about 4 GB and four slots reserve about 16 GB, on top of roughly 20 GB for the target and drafter weights. Since concurrency is not earning anything, lowering `--max-batch` in `~/.config/mlx-dspark/start.sh` would free roughly 12 GB, which could instead fund a larger context window or leave room for LM Studio to be loaded at the same time. This is a recommendation about a file outside the repository and it has not been applied.

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
