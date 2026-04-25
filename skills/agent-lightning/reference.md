# Agent Lightning API Reference

## Types

### Rollout Types

```python
from agentlightning.types import (
    Rollout,           # Full rollout with attempts
    RolloutConfig,     # Retry/timeout policy
    RolloutStatus,     # queuing, running, completed, failed
    AttemptedRollout,  # Rollout with current attempt info
    Attempt,           # Single execution attempt
    AttemptStatus,     # running, succeeded, failed, timeout
)
```

### Resource Types

```python
from agentlightning.types import (
    Resource,          # Base resource type
    LLM,               # LLM configuration
    ProxyLLM,          # Proxied LLM
    PromptTemplate,    # Optimizable prompt
    NamedResources,    # Dictionary of named resources
    ResourcesUpdate,   # Resource update payload
)
```

### Span Types

```python
from agentlightning.types import (
    Span,              # Trace span
    SpanContext,       # Trace/span IDs
    SpanLike,          # Span-compatible interface
    SpanCoreFields,    # Required span fields
    TraceStatus,       # ok, error
    Event,             # Span event
    Link,              # Span link
    Attributes,        # Key-value attributes
)
```

## LightningStore Methods

### Rollout Management

```python
# Enqueue new rollout
rollout = await store.enqueue_rollout(
    task: Task,
    config: RolloutConfig = RolloutConfig()
) -> Rollout

# Batch enqueue
rollouts = await store.batch_enqueue_rollouts(
    rollouts: List[EnqueueRolloutRequest]
) -> List[Rollout]

# Dequeue next rollout for processing
rollout = await store.dequeue_rollout(
    worker_id: str = None
) -> Optional[AttemptedRollout]

# Query rollouts
rollouts = await store.query_rollouts(
    status_in: List[RolloutStatus] = None,
    task_id: str = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at"
) -> List[Rollout]

# Get by ID
rollout = await store.get_rollout_by_id(
    rollout_id: str
) -> Optional[Rollout]

# Update rollout
await store.update_rollout(
    rollout_id: str,
    status: RolloutStatus = UNSET,
    result: Any = UNSET,
    error: str = UNSET
)
```

### Span Management

```python
# Add single span
await store.add_span(span: Span)

# Add multiple spans
await store.add_many_spans(spans: List[Span])

# Add OpenTelemetry span
await store.add_otel_span(readable_span: ReadableSpan)

# Query spans
spans = await store.query_spans(
    rollout_id: str = None,
    trace_id: str = None,
    span_name: str = None,
    limit: int = 100
) -> List[Span]
```

### Resource Management

```python
# Add resources
update = await store.add_resources(
    resources: NamedResources,
    checkpoint: bool = False
) -> ResourcesUpdate

# Update existing resources
await store.update_resources(
    resource_id: str,
    resources: NamedResources
)

# Get by ID
resources = await store.get_resources_by_id(
    resource_id: str
) -> Optional[ResourcesUpdate]

# Get latest
resources = await store.get_latest_resources() -> Optional[ResourcesUpdate]
```

## Tracer Methods

```python
from agentlightning import Tracer

tracer = Tracer(store=store)

# Context manager for tracing
with tracer.trace_context(
    task_id: str = None,
    rollout_id: str = None,
    attributes: Dict = None
) -> SpanRecordingContext:
    # Traced code here
    pass

# Get last trace
spans = tracer.get_last_trace() -> List[Span]
```

## Trainer Configuration

```python
import agentlightning as agl

trainer = agl.Trainer(
    # Worker configuration
    n_runners: int = 1,              # Number of parallel runners
    n_algorithm_workers: int = 1,    # Algorithm worker count
    
    # Components
    algorithm: Callable = None,      # Training algorithm
    runner: Callable = None,         # Rollout runner
    store: LightningStore = None,    # Store (creates InMemory if None)
    
    # Server configuration
    server_host: str = "127.0.0.1",
    server_port: int = 8000,
    
    # Execution
    max_rollouts: int = None,        # Stop after N rollouts
    max_time: float = None,          # Stop after N seconds
)

# Run training
trainer.run()

# Async version
await trainer.run_async()
```

## Semantic Conventions

### Span Attribute Names

```python
from agentlightning.semconv import LightningSpanAttributes

# Standard attributes
LightningSpanAttributes.ROLLOUT_ID      # "agl.rollout_id"
LightningSpanAttributes.TASK_ID         # "agl.task_id"
LightningSpanAttributes.WORKER_ID       # "agl.worker_id"
LightningSpanAttributes.INPUT           # "agl.input"
LightningSpanAttributes.OUTPUT          # "agl.output"
LightningSpanAttributes.REWARD          # "agl.reward"
LightningSpanAttributes.TOOL_NAME       # "agl.tool.name"
LightningSpanAttributes.TOOL_ARGS       # "agl.tool.args"
LightningSpanAttributes.TOOL_RESULT     # "agl.tool.result"
```

## Environment Variables

```bash
# Store configuration
AGL_STORE_URL=http://localhost:8000

# Logging
AGL_LOG_LEVEL=INFO
AGL_LOG_FILE=/path/to/agl.log

# Metrics
AGL_METRICS_ENABLED=true
AGL_METRICS_PORT=9090

# Tracing
AGL_OTEL_ENABLED=true
AGL_OTEL_ENDPOINT=http://localhost:4317
```

## Example: Complete Training Loop

```python
import agentlightning as agl
from agentlightning.store.memory import InMemoryLightningStore
from agentlightning.types import Task, RolloutConfig

# 1. Initialize store
store = InMemoryLightningStore()

# 2. Define your agent
async def my_agent(task):
    agl.emit_input(task.prompt)
    response = await llm.generate(task.prompt)
    agl.emit_output(response)
    return response

# 3. Define runner
async def runner(store, worker_id, event):
    tracer = agl.Tracer(store=store)
    
    while not event.is_set():
        rollout = await store.dequeue_rollout()
        if not rollout:
            await asyncio.sleep(0.1)
            continue
            
        with tracer.trace_context(rollout_id=rollout.id):
            try:
                result = await my_agent(rollout.task)
                reward = evaluate(result, rollout.task)
                agl.emit_reward(reward)
                
                await store.update_rollout(
                    rollout_id=rollout.id,
                    status="completed",
                    result={"response": result, "reward": reward}
                )
            except Exception as e:
                await store.update_rollout(
                    rollout_id=rollout.id,
                    status="failed",
                    error=str(e)
                )

# 4. Define algorithm
async def optimize(store, event):
    while not event.is_set():
        rollouts = await store.query_rollouts(status_in=["completed"])
        
        if len(rollouts) >= 32:  # Batch size
            # Extract traces and rewards
            traces = [await store.query_spans(rollout_id=r.id) for r in rollouts]
            rewards = [r.result["reward"] for r in rollouts]
            
            # Your optimization logic here
            new_prompt = optimize_prompt(traces, rewards)
            
            # Push updated resources
            await store.add_resources({
                "system_prompt": PromptTemplate(template=new_prompt)
            })
            
        await asyncio.sleep(5)

# 5. Seed tasks
for task_data in training_data:
    await store.enqueue_rollout(
        task=Task(prompt=task_data["prompt"], expected=task_data["expected"]),
        config=RolloutConfig(max_retries=2, timeout=30)
    )

# 6. Run training
trainer = agl.Trainer(
    n_runners=8,
    algorithm=optimize,
    runner=runner,
    store=store,
    max_rollouts=1000
)

trainer.run()
```
