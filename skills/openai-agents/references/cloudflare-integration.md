# Cloudflare Workers Integration

**Status**: Experimental Support

OpenAI Agents SDK has experimental support for Cloudflare Workers. Some features work, others have limitations.

---

## Compatibility

### What Works ✅
- Text agents (`Agent`, `run()`)
- Basic tool calling
- Structured outputs with Zod
- Streaming responses (with caveats)
- Environment variable access

### What Doesn't Work ❌
- Realtime voice agents (WebRTC not supported in Workers)
- Some Node.js APIs (timers, crypto edge cases)
- Long-running operations (CPU time limits)

### What's Experimental ⚠️
- Multi-agent handoffs (works but untested at scale)
- Large context windows (may hit memory limits)
- Complex tool executions (CPU time limits)

---

## Setup

### 1. Install Dependencies

```bash
npm install @openai/agents zod hono
```

### 2. Configure wrangler.jsonc

```jsonc
{
  "name": "openai-agents-worker",
  "main": "src/index.ts",
  "compatibility_date": "2025-10-26",
  "compatibility_flags": ["nodejs_compat"],
  "node_compat": true, // Required for OpenAI SDK

  "observability": {
    "enabled": true
  },

  "limits": {
    "cpu_ms": 30000 // Adjust based on agent complexity
  }
}
```

### 3. Set Environment Variable

```bash
# Set OPENAI_API_KEY secret
wrangler secret put OPENAI_API_KEY

# Enter your OpenAI API key when prompted
```

---

## Basic Worker Example

```typescript
import { Agent, run } from '@openai/agents';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const { message } = await request.json();

      // Set API key from environment
      process.env.OPENAI_API_KEY = env.OPENAI_API_KEY;

      const agent = new Agent({
        name: 'Assistant',
        instructions: 'You are helpful.',
        model: 'gpt-5-mini', // Use smaller models for faster response
      });

      const result = await run(agent, message, {
        maxTurns: 5, // Limit turns to control execution time
      });

      return new Response(JSON.stringify({
        response: result.finalOutput,
        tokens: result.usage.totalTokens,
      }), {
        headers: { 'Content-Type': 'application/json' },
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  },
};

interface Env {
  OPENAI_API_KEY: string;
}
```

---

## Hono Integration

```typescript
import { Hono } from 'hono';
import { Agent, run } from '@openai/agents';

const app = new Hono<{ Bindings: { OPENAI_API_KEY: string } }>();

app.post('/api/agent', async (c) => {
  const { message } = await c.req.json();

  process.env.OPENAI_API_KEY = c.env.OPENAI_API_KEY;

  const agent = new Agent({
    name: 'Assistant',
    instructions: 'You are helpful.',
  });

  const result = await run(agent, message);

  return c.json({
    response: result.finalOutput,
  });
});

export default app;
```

**See Template**: `templates/cloudflare-workers/worker-agent-hono.ts`

---

## Streaming Responses

Streaming works but requires careful handling:

```typescript
const stream = await run(agent, message, { stream: true });

const { readable, writable } = new TransformStream();
const writer = writable.getWriter();
const encoder = new TextEncoder();

// Stream in background
(async () => {
  try {
    for await (const event of stream) {
      if (event.type === 'raw_model_stream_event') {
        const chunk = event.data?.choices?.[0]?.delta?.content || '';
        if (chunk) {
          await writer.write(encoder.encode(`data: ${chunk}\n\n`));
        }
      }
    }
    await stream.completed;
  } finally {
    await writer.close();
  }
})();

return new Response(readable, {
  headers: {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
  },
});
```

---

## Known Limitations

### 1. CPU Time Limits
Workers have CPU time limits (default 50ms, up to 30s with paid plans).

**Solution**: Use smaller models and limit `maxTurns`:

```typescript
const result = await run(agent, message, {
  maxTurns: 3, // Limit turns
  model: 'gpt-5-mini', // Faster model
});
```

### 2. Memory Limits
Large context windows may hit memory limits (128MB default).

**Solution**: Keep conversations concise, summarize history:

```typescript
const agent = new Agent({
  instructions: 'Keep responses concise. Summarize context when needed.',
});
```

### 3. No Realtime Voice
WebRTC not supported in Workers runtime.

**Solution**: Use realtime agents in Next.js or other Node.js environments.

### 4. Cold Starts
First request after inactivity may be slow.

**Solution**: Use warm-up requests or keep Workers warm with cron triggers.

---

## Performance Tips

### 1. Use Smaller Models
```typescript
model: 'gpt-5-mini' // Faster than gpt-5
```

### 2. Limit Turns
```typescript
maxTurns: 3 // Prevent long-running loops
```

### 3. Stream Responses
```typescript
stream: true // Start returning data faster
```

### 4. Cache Results
```typescript
// Cache frequent queries in KV
const cached = await env.KV.get(cacheKey);
if (cached) return cached;

const result = await run(agent, message);
await env.KV.put(cacheKey, result, { expirationTtl: 3600 });
```

### 5. Use Durable Objects for State
```typescript
// Store agent state in Durable Objects for long conversations
class AgentSession {
  async fetch(request) {
    // Maintain conversation state across requests
  }
}
```

---

## Deployment

```bash
# Build and deploy
npm run build
wrangler deploy

# Test locally
wrangler dev
```

---

## Cost Considerations

**Workers Costs**:
- Requests: $0.15 per million (after 100k free/day)
- CPU Time: $0.02 per million CPU-ms (after 10ms free per request)

**OpenAI Costs**:
- GPT-4o-mini: $0.15 / 1M input tokens, $0.60 / 1M output tokens
- GPT-4o: $2.50 / 1M input tokens, $10.00 / 1M output tokens

**Example**: 1M agent requests (avg 500 tokens each)
- Workers: ~$1.50
- GPT-4o-mini: ~$75
- **Total**: ~$76.50

**Use gpt-5-mini for cost efficiency!**

---

## Monitoring

```typescript
// Log execution time
const start = Date.now();
const result = await run(agent, message);
const duration = Date.now() - start;

console.log(`Agent execution: ${duration}ms`);
console.log(`Tokens used: ${result.usage.totalTokens}`);
```

Enable Workers observability in wrangler.jsonc:

```jsonc
"observability": {
  "enabled": true,
  "head_sampling_rate": 0.1
}
```

---

## Error Handling

```typescript
try {
  const result = await run(agent, message, {
    maxTurns: 5,
  });
  return result;

} catch (error) {
  if (error.message.includes('CPU time limit')) {
    // Hit Workers CPU limit - reduce complexity
    return { error: 'Request too complex' };
  }

  if (error.message.includes('memory')) {
    // Hit memory limit - reduce context
    return { error: 'Context too large' };
  }

  throw error;
}
```

---

## Alternatives

If Workers limitations are problematic:

1. **Cloudflare Pages Functions** (same runtime, may not help)
2. **Next.js on Vercel** (better Node.js support)
3. **Node.js on Railway/Render** (full Node.js environment)
4. **AWS Lambda** (longer timeouts, more memory)

---

**Last Updated**: 2025-10-26
**Status**: Experimental - test thoroughly before production use
