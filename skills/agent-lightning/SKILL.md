---
name: agent-lightning
description: Train and optimize AI agents using Microsoft's Agent Lightning framework with reinforcement learning. Use when setting up agent training, instrumenting agents with tracing, configuring LightningStore, implementing reward functions, or optimizing prompts with RL/APO algorithms.
---

# Agent Lightning

Microsoft's framework for training AI agents with reinforcement learning, automatic prompt optimization, and supervised fine-tuning.

## Quick Start

### Installation

```bash
pip install agentlightning
```

For nightly builds:
```bash
pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --pre agentlightning
```

### Minimal Integration (Zero Code Change)

Add `agl.emit_xxx()` helpers to your existing agent:

```python
import agentlightning as agl

# Your existing agent code
def my_agent(task):
    agl.emit_input(task)  # Track input
    
    response = llm.generate(task)
    agl.emit_output(response)  # Track output
    
    reward = evaluate(response)
    agl.emit_reward(reward)  # Track reward
    
    return response
```

## Core Concepts

### Architecture Flow

```
Agent (your code) → agl.emit_xxx() → Spans → LightningStore → Algorithm → Updated Resources
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `LightningStore` | Central hub for traces, tasks, and resources |
| `Tracer` | Collects spans from agent execution |
| `Algorithm` | Consumes traces, produces improvements |
| `Trainer` | Orchestrates training loop |

## Instrumentation

### Emit Functions

```python
import agentlightning as agl

# Basic emissions
agl.emit_input(prompt)           # Track input to agent
agl.emit_output(response)        # Track agent output
agl.emit_reward(score)           # Track reward signal
agl.emit_tool_call(name, args)   # Track tool usage
agl.emit_tool_result(result)     # Track tool results
```

### Tracer Context

```python
from agentlightning import Tracer

tracer = Tracer(store=store)

with tracer.trace_context(task_id="task-123"):
    # All emissions within this context are grouped
    result = agent.run(task)
    
# Retrieve trace after execution
trace = tracer.get_last_trace()
```

### OpenTelemetry Integration

Agent Lightning integrates with OpenTelemetry:

```python
from agentlightning.utils.otel import get_tracer

tracer = get_tracer()  # Returns OTel tracer for "agentlightning"
```

## LightningStore

### In-Memory Store (Development)

```python
from agentlightning.store.memory import InMemoryLightningStore

store = InMemoryLightningStore()
```

### Client-Server Store (Production)

```python
from agentlightning.store.client_server import (
    LightningStoreServer,
    LightningStoreClient
)

# Server side
server = LightningStoreServer(store, host="0.0.0.0", port=8080)
await server.start()

# Client side
client = LightningStoreClient("http://localhost:8080")
```

### Store Operations

```python
# Add rollouts (tasks for the agent)
await store.enqueue_rollout(task=task, config=RolloutConfig())

# Query rollouts
rollouts = await store.query_rollouts(status_in=["completed"])

# Add resources (updated prompts, weights)
await store.add_resources(resources)

# Get latest resources
resources = await store.get_latest_resources()
```

## Training

### Basic Trainer Setup

```python
import agentlightning as agl

trainer = agl.Trainer(
    n_runners=8,           # Parallel rollout workers
    algorithm=algorithm,   # Your chosen algorithm
    store=store           # Optional, creates InMemory if not provided
)

trainer.run()
```

### Custom Algorithm

```python
from agentlightning import LightningStore
from agentlightning.types import ExecutionEvent

async def my_algorithm(store: LightningStore, event: ExecutionEvent):
    # Fetch completed rollouts
    rollouts = await store.query_rollouts(status_in=["completed"])
    
    # Process traces, compute gradients, etc.
    new_resources = optimize(rollouts)
    
    # Push updated resources
    await store.add_resources(new_resources)
```

### Runner Function

```python
async def my_runner(store: LightningStore, worker_id: int, event: ExecutionEvent):
    while not event.is_set():
        rollout = await store.dequeue_rollout()
        if rollout:
            result = execute_task(rollout.task)
            await store.update_rollout(
                rollout_id=rollout.id,
                status="completed",
                result=result
            )
```

## Algorithms

### Reinforcement Learning (GRPO/PPO)

For RL training with vLLM backend:

```python
from agentlightning.algorithm.verl import VeRLAlgorithm

algorithm = VeRLAlgorithm(
    model="your-model",
    learning_rate=1e-5,
    batch_size=32
)
```

### Automatic Prompt Optimization (APO)

```python
from agentlightning.algorithm.apo import APOAlgorithm

algorithm = APOAlgorithm(
    optimizer_model="gpt-4",
    target_model="gpt-3.5-turbo"
)
```

## Framework Adapters

### LangChain

```python
from agentlightning.instrumentation.langchain import instrument_langchain

instrument_langchain()  # Auto-traces all LangChain calls
```

### OpenAI SDK

```python
from agentlightning.instrumentation.openai import instrument_openai

instrument_openai()  # Auto-traces OpenAI API calls
```

### vLLM

```python
from agentlightning.instrumentation.vllm import instrument_vllm

instrument_vllm()  # Instrument vLLM for token-level tracing
```

## Logging & Debugging

### Configure Logging

```python
from agentlightning import setup_logging

setup_logging(
    level="DEBUG",
    submodule_levels={
        "agentlightning.store": "INFO",
        "agentlightning.tracer": "DEBUG"
    }
)
```

### Metrics

Agent Lightning emits Prometheus-compatible metrics:

- `agl.store.total` - Store operation counts
- `agl.store.latency` - Store operation latencies
- `agl.rollouts.total` - Rollout counts by status
- `agl.rollouts.duration` - Rollout execution times

## Common Patterns

### Reward Function Design

```python
def compute_reward(task, response):
    """Good rewards are: normalized, dense when possible, aligned with goals."""
    
    correctness = check_correctness(task, response)  # 0-1
    efficiency = measure_efficiency(response)         # 0-1
    
    return 0.7 * correctness + 0.3 * efficiency
```

### Multi-Agent Training

Train specific agents in a multi-agent system:

```python
with tracer.trace_context(agent_id="planner"):
    plan = planner.run(task)

with tracer.trace_context(agent_id="executor"):
    result = executor.run(plan)
    
# Only the executor's traces are used for training
```

### Checkpoint & Resume

```python
# Save checkpoint
await store.add_resources(
    checkpoint=True,
    resources=current_resources
)

# Load latest
resources = await store.get_latest_resources()
```

## Integration with JavaScript Agents

For JavaScript/TypeScript agents (like Claude-based apps), you have two options:

### Option 1: Python Training Service

Create a Python microservice that:
1. Receives trace events from your JS app via HTTP
2. Stores them in LightningStore
3. Runs training algorithms
4. Returns optimized prompts

### Option 2: REST API Integration

Use `LightningStoreServer` as a REST backend:

```javascript
// JavaScript client
const response = await fetch('http://localhost:8080/rollouts', {
    method: 'POST',
    body: JSON.stringify({
        task: { prompt: userMessage },
        config: { max_retries: 3 }
    })
});
```

## Resources

- [Documentation](https://microsoft.github.io/agent-lightning/)
- [GitHub](https://github.com/microsoft/agent-lightning)
- [arXiv Paper](https://arxiv.org/abs/2508.03680)
- [Discord Community](https://discord.gg/RYk7CdvDR7)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Ensure `pip install agentlightning` succeeded |
| Store connection failed | Check server is running, verify endpoint URL |
| No traces collected | Verify `emit_xxx()` calls are within trace context |
| Training not converging | Check reward function normalization, increase rollouts |
