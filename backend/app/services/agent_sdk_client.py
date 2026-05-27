"""Thin wrapper around the Anthropic Python SDK for chat, commands, and agent spawning.

Includes: rate-limit retry with exponential backoff, budget pre-check,
model fallback (opus -> sonnet), and dual token recording
(cost_ledger + agent_sessions).
"""

import asyncio
import os
import time
import uuid
import structlog
from anthropic import Anthropic, AsyncAnthropic, RateLimitError, APIStatusError
from sqlalchemy import insert
from typing import AsyncIterator

from app.config import LOCAL_LLM_ENABLED, LOCAL_LLM_FALLBACK_TO_CLOUD
from app.db.session import get_db
from app.db.tables import budgets, cost_ledger

log = structlog.get_logger()

# Model mapping: our friendly names -> Anthropic model IDs
MODEL_MAP = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

# Fallback chain: if a model fails repeatedly, try the next one
MODEL_FALLBACK = {
    "claude-opus-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4-6": "claude-haiku-4-5-20251001",
}

# Pricing per 1M tokens (input, output) in USD
PRICING = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
}

# Retry config
MAX_RETRIES = 3
INITIAL_BACKOFF_S = 1.0
MAX_FALLBACK_ATTEMPTS = 2  # How many model fallbacks before giving up


def _resolve_model(model: str) -> str:
    return MODEL_MAP.get(model, model)


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate approximate cost in USD."""
    resolved = _resolve_model(model) if model in MODEL_MAP else model
    input_rate, output_rate = PRICING.get(resolved, (3.0, 15.0))
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


def _check_budget_before_spawn(
    node_id: str | None,
    project_id: str | None,
) -> None:
    """Raise RuntimeError if daily budget is already exceeded."""
    if not node_id and not project_id:
        return
    try:

        with get_db() as conn:
            budget_row = conn.exec_driver_sql(
                "SELECT daily_cap_usd FROM budgets "
                "WHERE node_id = ? OR project_id = ? LIMIT 1",
                (node_id, project_id),
            ).fetchone()
            if not budget_row or not budget_row._mapping.get("daily_cap_usd"):
                return

            daily_cap = budget_row._mapping["daily_cap_usd"]
            spent_row = conn.exec_driver_sql(
                "SELECT COALESCE(SUM(cost_usd), 0) as total "
                "FROM cost_ledger "
                "WHERE (node_id = ? OR project_id = ?) "
                "AND created_at >= datetime('now', '-1 day')",
                (node_id, project_id),
            ).fetchone()
            spent = spent_row._mapping["total"] if spent_row else 0.0

            if spent >= daily_cap:
                raise RuntimeError(
                    f"Daily budget exceeded: ${spent:.2f} of ${daily_cap:.2f}"
                )
    except RuntimeError:
        raise
    except Exception as e:
        log.warning("budget_check_failed", error=str(e))


class AgentSDKClient:
    """Stateless wrapper -- create one instance per app lifetime."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            log.warning("no_anthropic_api_key", msg="ANTHROPIC_API_KEY not set, SDK client will fail")
        self._sync = Anthropic(api_key=api_key) if api_key else None
        self._async = AsyncAnthropic(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        return self._sync is not None

    def quick_command(
        self,
        prompt: str,
        model: str = "haiku",
        system: str | None = None,
        max_tokens: int = 4096,
        task_type: str | None = None,  # if set + local eligible, route to local LLM
    ) -> dict:
        """Synchronous single-turn call with retry and fallback.

        Returns {"content": str, "input_tokens": int, "output_tokens": int, "model": str}.
        """
        # Route to local LLM if task_type is local-eligible
        LOCAL_ELIGIBLE_TASKS = {
            "classification", "extraction", "summarization", "briefing",
            "rag-lightning", "meeting-notes", "article-stub", "article-standard",
        }

        if task_type and task_type in LOCAL_ELIGIBLE_TASKS and LOCAL_LLM_ENABLED:
            from .local_llm_client import LocalLLMClient, LocalLLMError  # noqa: lazy import (optional dep)
            local = LocalLLMClient()
            if local.is_available():
                try:
                    result = local.quick_command(prompt, task_type=task_type, max_tokens=max_tokens)
                    log.info("local_llm_used", task_type=task_type, model=result["model"],
                             output_tokens=result["output_tokens"])
                    return result
                except LocalLLMError as e:
                    if LOCAL_LLM_FALLBACK_TO_CLOUD:
                        log.warning("local_llm_failed_falling_back", task_type=task_type, error=str(e))
                        # Fall through to cloud
                    else:
                        raise

        if not self._sync:
            raise RuntimeError("Anthropic API key not configured")

        messages = [{"role": "user", "content": prompt}]
        resolved_model = _resolve_model(model)
        fallback_attempts = 0

        while True:
            kwargs = {
                "model": resolved_model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = self._sync.messages.create(**kwargs)
                    content = ""
                    for block in response.content:
                        if block.type == "text":
                            content += block.text
                    return {
                        "content": content,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "model": response.model,
                    }
                except RateLimitError as e:
                    last_error = e
                    backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                    log.warning(
                        "rate_limited",
                        model=resolved_model,
                        attempt=attempt + 1,
                        backoff_s=backoff,
                    )
                    time.sleep(backoff)
                except APIStatusError as e:
                    if e.status_code == 529:  # Overloaded
                        last_error = e
                        backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                        log.warning("api_overloaded", model=resolved_model, attempt=attempt + 1)
                        time.sleep(backoff)
                    else:
                        raise

            # All retries exhausted -- try fallback model
            fallback = MODEL_FALLBACK.get(resolved_model)
            if fallback and fallback_attempts < MAX_FALLBACK_ATTEMPTS:
                fallback_attempts += 1
                log.warning(
                    "model_fallback",
                    from_model=resolved_model,
                    to_model=fallback,
                )
                resolved_model = fallback
                continue

            raise last_error or RuntimeError(f"All retries and fallbacks exhausted for {model}")

    async def stream_chat(
        self,
        prompt: str,
        model: str = "sonnet",
        system: str | None = None,
        max_tokens: int = 8192,
        agent_id: str | None = None,
        node_id: str | None = None,
        project_id: str | None = None,
    ) -> AsyncIterator[dict]:
        """Async streaming chat with retry. Yields {"type": "token"|"usage"|"done", ...} dicts."""
        if not self._async:
            raise RuntimeError("Anthropic API key not configured")

        _check_budget_before_spawn(node_id, project_id)

        messages = [{"role": "user", "content": prompt}]
        resolved_model = _resolve_model(model)
        fallback_attempts = 0

        while True:
            kwargs = {
                "model": resolved_model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    async with self._async.messages.stream(**kwargs) as stream:
                        async for text in stream.text_stream:
                            yield {"type": "token", "content": text}

                        final = await stream.get_final_message()

                        # Record tokens to both tables
                        _record_dual(
                            model=final.model,
                            input_tokens=final.usage.input_tokens,
                            output_tokens=final.usage.output_tokens,
                            source="chat",
                            agent_id=agent_id,
                            node_id=node_id,
                            project_id=project_id,
                        )

                        yield {
                            "type": "usage",
                            "input_tokens": final.usage.input_tokens,
                            "output_tokens": final.usage.output_tokens,
                            "model": final.model,
                        }
                        yield {
                            "type": "done",
                            "content": "".join(
                                b.text for b in final.content if b.type == "text"
                            ),
                        }
                        return  # Success
                except RateLimitError as e:
                    last_error = e
                    backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                    log.warning("rate_limited_stream", model=resolved_model, attempt=attempt + 1)
                    await asyncio.sleep(backoff)
                except APIStatusError as e:
                    if e.status_code == 529:
                        last_error = e
                        backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                        await asyncio.sleep(backoff)
                    else:
                        raise

            # Fallback
            fallback = MODEL_FALLBACK.get(resolved_model)
            if fallback and fallback_attempts < MAX_FALLBACK_ATTEMPTS:
                fallback_attempts += 1
                log.warning("model_fallback_stream", from_model=resolved_model, to_model=fallback)
                resolved_model = fallback
                continue

            raise last_error or RuntimeError(f"All retries and fallbacks exhausted for {model}")

    async def spawn_agent(
        self,
        task: str,
        model: str = "sonnet",
        system: str | None = None,
        max_tokens: int = 16384,
        agent_id: str | None = None,
        node_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Non-streaming agent call with retry, fallback, budget check, and token recording."""
        if not self._async:
            raise RuntimeError("Anthropic API key not configured")

        _check_budget_before_spawn(node_id, project_id)

        messages = [{"role": "user", "content": task}]
        resolved_model = _resolve_model(model)
        fallback_attempts = 0

        while True:
            kwargs = {
                "model": resolved_model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = await self._async.messages.create(**kwargs)

                    content = ""
                    for block in response.content:
                        if block.type == "text":
                            content += block.text

                    # Record tokens to both tables
                    _record_dual(
                        model=response.model,
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                        source="agent",
                        agent_id=agent_id,
                        node_id=node_id,
                        project_id=project_id,
                    )

                    return {
                        "content": content,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "model": response.model,
                        "stop_reason": response.stop_reason,
                    }
                except RateLimitError as e:
                    last_error = e
                    backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                    log.warning("rate_limited_spawn", model=resolved_model, attempt=attempt + 1)
                    await asyncio.sleep(backoff)
                except APIStatusError as e:
                    if e.status_code == 529:
                        last_error = e
                        backoff = INITIAL_BACKOFF_S * (2 ** attempt)
                        await asyncio.sleep(backoff)
                    else:
                        raise

            # Fallback
            fallback = MODEL_FALLBACK.get(resolved_model)
            if fallback and fallback_attempts < MAX_FALLBACK_ATTEMPTS:
                fallback_attempts += 1
                log.warning("model_fallback_spawn", from_model=resolved_model, to_model=fallback)
                resolved_model = fallback
                continue

            raise last_error or RuntimeError(f"All retries and fallbacks exhausted for {model}")


def _record_dual(
    model: str,
    input_tokens: int,
    output_tokens: int,
    source: str = "agent",
    agent_id: str | None = None,
    node_id: str | None = None,
    project_id: str | None = None,
) -> None:
    """Write token usage to cost_ledger AND agent_sessions (if agent_id present)."""
    # 1. cost_ledger
    record_sdk_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        source=source,
        agent_id=agent_id,
        node_id=node_id,
        project_id=project_id,
    )

    # 2. agent_sessions
    if agent_id:
        try:
            from app.services.agent_session_store import increment_tokens  # noqa: lazy import (cycle)
            increment_tokens(agent_id, input_tokens, output_tokens)
        except Exception as e:
            log.warning("session_token_update_failed", agent_id=agent_id, error=str(e))


def record_sdk_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float | None = None,
    source: str = "chat",
    agent_id: str | None = None,
    node_id: str | None = None,
    project_id: str | None = None,
) -> None:
    """Write a row to cost_ledger with real token counts from the SDK."""
    if cost_usd is None:
        cost_usd = calculate_cost(model, input_tokens, output_tokens)
    try:
        with get_db() as conn:
            conn.execute(
                insert(cost_ledger).values(
                    id=uuid.uuid4().hex,
                    agent_id=agent_id,
                    node_id=node_id,
                    project_id=project_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    source=source,
                )
            )
    except Exception as e:
        log.warning("record_sdk_cost_failed", error=str(e))


# Singleton
agent_sdk = AgentSDKClient()


def create_message(
    model: str = "haiku",
    system: str | None = None,
    messages: list | None = None,
    max_tokens: int = 1024,
    purpose: str = "briefing",
    **_kwargs,
) -> dict:
    """Compatibility shim used by podcast.py.

    Routes through quick_command with task_type=purpose so eligible tasks
    (briefing, summarization) are handled by the local LLM.
    """
    prompt = ""
    if messages:
        for m in messages:
            if m.get("role") == "user":
                prompt += m.get("content", "")
    return agent_sdk.quick_command(
        prompt=prompt,
        model=model,
        system=system,
        max_tokens=max_tokens,
        task_type=purpose,
    )
