"""LocalLLMClient — routes tasks to local MLX models via subprocess.

Task types and their model routing:
  classification   → Qwen3-4B       (fastest, short output)
  extraction       → Gemma4-26B MoE (structured JSON, quality matters)
  summarization    → Gemma4-26B MoE
  briefing         → Gemma4-26B MoE
  rag-lightning    → Qwen3-4B       (speed critical, short output)
  meeting-notes    → Gemma4-E4B     (native multimodal, audio capable)
  article-stub     → Gemma4-26B MoE
  article-standard → Gemma4-26B MoE
  article-rich     → Gemma4-31B     (highest quality, batch only)
  default          → Gemma4-26B MoE
"""

import subprocess
import sys
import structlog

from app.config import LOCAL_LLM_ENABLED, LOCAL_LLM_TIMEOUT, LOCAL_LLM_FALLBACK_TO_CLOUD

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

# (model_id, framework)  framework is "lm" or "vlm"
_MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    "qwen3-4b": (
        "mlx-community/Qwen3-4B-Instruct-2507-4bit",
        "lm",
    ),
    "qwen2.5-7b": (
        "mlx-community/Qwen2.5-7B-Instruct-4bit",
        "lm",
    ),
    "gemma4-e4b": (
        "mlx-community/gemma-4-e4b-it-4bit",
        "vlm",
    ),
    "gemma4-26b": (
        "mlx-community/gemma-4-26b-a4b-it-4bit",
        "vlm",
    ),
    "gemma4-31b": (
        "mlx-community/gemma-4-31b-it-4bit",
        "vlm",
    ),
}

# Task-type → registry key
#
# Routing rationale (benchmark-informed):
#   classification   → Qwen3-4B:    IFEval 89.8%, 2.3GB, clean text output, fast prefill.
#                                   E4B's multimodal overhead wasted on text-only emails.
#   rag-lightning    → Qwen2.5-7B:  63 tok/s prefill vs 6 tok/s for 26B MoE — 10× faster
#                                   context processing for 2KB RAG inputs. Also strong JSON.
#   extraction       → Qwen2.5-7B:  Built for structured output / JSON schema adherence.
#                                   No prompt-echo stripping needed (clean text output).
#   summarization    → Gemma4 26B:  Quality matters more than speed for synthesis.
#   briefing         → Gemma4 26B:  Same — narrative quality over raw speed.
#   meeting-notes    → Gemma4 E4B:  ONLY model with native audio input. Keeps this.
#   article-stub     → Gemma4 26B:  26B quality for article body generation.
#   article-standard → Gemma4 26B:  Same.
#   article-rich     → Gemma4 31B:  Top quality, batch-only job.
_TASK_ROUTING: dict[str, str] = {
    "classification": "qwen3-4b",     # faster prefill, cleaner output, higher IFEval
    "rag-lightning":  "qwen2.5-7b",   # 10× faster prefill than 26B MoE for long contexts
    "extraction":     "qwen2.5-7b",   # purpose-built for structured JSON output
    "summarization":  "gemma4-26b",   # quality synthesis
    "briefing":       "gemma4-26b",   # quality narrative
    "meeting-notes":  "gemma4-e4b",   # native audio input
    "article-stub":   "gemma4-26b",
    "article-standard":"gemma4-26b",
    "article-rich":   "gemma4-31b",
    "default":        "gemma4-26b",
}

# Haiku pricing used for cost-savings estimate (USD per 1M tokens)
_HAIKU_OUTPUT_PRICE_PER_M = 4.0  # $4.00 / 1M output tokens


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class LocalLLMError(Exception):
    """Raised when local MLX inference fails."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class LocalLLMClient:
    """Stateless wrapper — create one instance per app lifetime.

    All calls are synchronous and run the MLX CLI via subprocess so they are
    safe to call from FastAPI background tasks or sync endpoints.
    """

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    @staticmethod
    def is_available() -> bool:
        """Return True if the mlx_lm CLI is available on PATH.

        Uses CLI check (not Python import) because MLX may be installed in the
        system Python while the backend runs in a venv.
        """
        import shutil
        # Check for mlx_lm CLI or fallback to checking via python3 -c import
        if shutil.which("mlx_lm.generate"):
            return True
        try:
            result = subprocess.run(
                ["python3", "-c", "import mlx_lm"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    @staticmethod
    def get_model_for_task(task_type: str) -> tuple[str, str]:
        """Return (model_id, framework) for the given task_type.

        Falls back to the "default" route for unknown task types.
        Framework is either "lm" (mlx_lm) or "vlm" (mlx_vlm).
        """
        key = _TASK_ROUTING.get(task_type, _TASK_ROUTING["default"])
        model_id, framework = _MODEL_REGISTRY[key]
        return model_id, framework

    # ------------------------------------------------------------------
    # Core call
    # ------------------------------------------------------------------

    def quick_command(
        self,
        prompt: str,
        task_type: str = "default",
        max_tokens: int = 1024,
        system: str | None = None,
    ) -> dict:
        """Run a single-turn inference via the MLX CLI.

        Returns the same shape as ``AgentSDKClient.quick_command()``:
        ``{"content": str, "input_tokens": int, "output_tokens": int,
           "model": str, "local": True}``

        ``input_tokens`` is always 0 — the MLX CLI does not report it easily.

        Raises ``LocalLLMError`` on any failure.
        """
        if not LOCAL_LLM_ENABLED:
            raise LocalLLMError("Local LLM is disabled via LOCAL_LLM_ENABLED=False")

        model_id, framework = self.get_model_for_task(task_type)
        timeout: int = LOCAL_LLM_TIMEOUT

        # Build prompt text — prepend system message as a plain prefix when
        # the CLI has no dedicated --system flag (both mlx_lm and mlx_vlm
        # accept a single --prompt string).
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        # Build subprocess command.
        # Use absolute path to system python3 — MLX is installed there,
        # not in the FastAPI venv. Bare "python3" resolves to venv python.
        _python = "/opt/homebrew/bin/python3"
        if framework == "lm":
            cmd = [
                _python, "-m", "mlx_lm", "generate",
                "--model", model_id,
                "--prompt", full_prompt,
                "--max-tokens", str(max_tokens),
            ]
        else:
            # vlm path (Gemma 4 family) — use "mlx_vlm generate" (non-deprecated form)
            cmd = [
                _python, "-m", "mlx_vlm", "generate",
                "--model", model_id,
                "--prompt", full_prompt,
                "--max-tokens", str(max_tokens),
            ]

        log.info(
            "local_llm_call",
            task_type=task_type,
            model=model_id,
            framework=framework,
            max_tokens=max_tokens,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise LocalLLMError(
                f"Local LLM timed out after {timeout}s (model={model_id})",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise LocalLLMError(
                f"Failed to launch local LLM subprocess: {exc}",
                cause=exc,
            ) from exc

        if result.returncode != 0:
            stderr_snippet = (result.stderr or "")[:400]
            raise LocalLLMError(
                f"Local LLM exited with code {result.returncode}: {stderr_snippet}",
            )

        # ------------------------------------------------------------------
        # Parse output
        # The CLI prints:
        #   <generated text>
        #   (blank line)
        #   ==========
        #   Prompt: N tokens, X tok/s
        #   Generation: M tokens, Y tok/s
        #   Peak memory: Z GB
        # ------------------------------------------------------------------
        raw_output = result.stdout or ""
        content, output_tokens = _parse_mlx_output(raw_output, model_id)

        log.info(
            "local_llm_done",
            task_type=task_type,
            model=model_id,
            output_tokens=output_tokens,
        )

        return {
            "content": content,
            "input_tokens": 0,
            "output_tokens": output_tokens,
            "model": model_id,
            "local": True,
        }

    # ------------------------------------------------------------------
    # Cost savings estimate
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_cost_saved(
        output_tokens: int,
        cloud_model: str = "haiku",
    ) -> float:
        """Estimate USD saved vs running the same output on Claude Haiku.

        Uses Haiku output pricing: $4.00 / 1M output tokens.
        Input tokens are not counted (MLX CLI doesn't report them and they
        are typically cheaper anyway).
        """
        if cloud_model == "haiku":
            price_per_token = _HAIKU_OUTPUT_PRICE_PER_M / 1_000_000
        else:
            # Default to Haiku pricing for any unknown cloud model
            price_per_token = _HAIKU_OUTPUT_PRICE_PER_M / 1_000_000

        return round(output_tokens * price_per_token, 8)


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------

def _parse_mlx_output(raw: str, model_id: str) -> tuple[str, int]:
    """Split on ``==========`` and extract generated text + token count.

    Actual mlx_lm output format:
        ==========
        <generated text>
        ==========
        Prompt: N tokens, X tok/s
        Generation: M tokens, Y tok/s
        Peak memory: Z GB

    Returns ``(content, output_tokens)``.
    """
    separator = "=========="
    parts = raw.split(separator)

    # Format: parts[0]=empty, parts[1]=content_block, parts[2]=stats
    # Fall back gracefully if format differs
    if len(parts) >= 3:
        content_block = parts[1]
    elif len(parts) == 2:
        content_block = parts[1]
    else:
        content_block = raw

    # mlx_vlm (Gemma4) echoes the prompt inside the content block:
    #   Files: []\n\nPrompt: <bos><|turn>user\n...<|turn>model\n<|channel>thought\n<channel|>\n<actual response>
    # Extract only the text after the last chat/channel marker.
    content = content_block.strip()
    for marker in ("<channel|>", "<|turn>model", "<|im_start|>assistant", "[/INST]"):
        if marker in content:
            content = content.split(marker)[-1].strip()
            break

    # Parse token count from the stats block (last segment after separators)
    output_tokens = 0
    if len(parts) > 1:
        stats_block = parts[-1]  # Always the last segment
        for line in stats_block.splitlines():
            line_lower = line.strip().lower()
            # "Generation: 123 tokens, 45.6 tok/s"
            if line_lower.startswith("generation:"):
                try:
                    # e.g. "Generation: 123 tokens, 45.6 tok/s"
                    token_part = line.split(":")[1].strip()          # "123 tokens, 45.6 tok/s"
                    output_tokens = int(token_part.split()[0])       # 123
                except (IndexError, ValueError):
                    pass
                break

    return content, output_tokens


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

local_llm = LocalLLMClient()
