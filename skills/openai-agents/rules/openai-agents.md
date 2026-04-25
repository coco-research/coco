---
paths: "**/*agent*.ts", "**/*agent*.tsx", "**/*.ts"
---

# OpenAI Agents SDK Corrections

Claude's training may reference older patterns. This project uses **@openai/agents v0.2.1**.

## Zod Schema Must Be Inline

```typescript
/* ❌ Imported schema causes type errors (GitHub #188) */
import { mySchema } from './schemas'
const tool = { parameters: mySchema }

/* ✅ Define inline */
const tool = {
  parameters: z.object({
    location: z.string().describe('City name'),
  }),
}
```

## MCP Tracing Required

```typescript
/* ❌ "No existing trace found" error */
const result = await agent.run()

/* ✅ Initialize tracing first */
import { initializeTracing } from '@openai/agents'
initializeTracing()
const result = await agent.run()
```

## Prevent Infinite Loops (MaxTurnsExceeded)

```typescript
/* ❌ Default maxTurns often too low */
const agent = new Agent({ tools })

/* ✅ Increase maxTurns and improve instructions */
const agent = new Agent({
  tools,
  maxTurns: 20, // Increase from default
  instructions: 'Complete the task, then return final_answer tool',
})
```

## Voice Agent Handoffs

```typescript
/* ❌ Cannot change voice/model during handoff */
handoff({ voice: 'different-voice', model: 'gpt-5' })

/* ✅ Voice and model must match original agent */
handoff({ voice: originalVoice, model: 'gpt-5-realtime' })
```

## Never Send API Key to Browser

```typescript
/* ❌ Security vulnerability */
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
// Sending to frontend...

/* ✅ Generate ephemeral tokens server-side */
const session = await client.realtime.sessions.create({ model: 'gpt-5-realtime' })
// Send session.client_secret.value to frontend (expires in 60s)
```

## Quick Fixes

| If Claude suggests... | Use instead... |
|----------------------|----------------|
| Imported Zod schemas | Define schemas inline |
| Missing tracing | Call `initializeTracing()` |
| Agent loops forever | Increase `maxTurns`, improve instructions |
| Changing voice in handoff | Keep voice/model consistent |
| API key in browser | Use ephemeral session tokens |
