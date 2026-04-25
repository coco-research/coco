# Common Errors and Solutions

This reference documents known issues with OpenAI Agents SDK and their workarounds.

---

## Error 1: Zod Schema Type Errors with Tool Parameters

**Issue**: Type errors occur when using Zod schemas as tool parameters, even when structurally compatible.

**GitHub Issue**: [#188](https://github.com/openai/openai-agents-js/issues/188)

**Symptoms**:
```typescript
// This causes TypeScript errors
const myTool = tool({
  name: 'my_tool',
  parameters: myZodSchema, // ❌ Type error
  execute: async (input) => { /* ... */ },
});
```

**Workaround**:
```typescript
// Define schema inline
const myTool = tool({
  name: 'my_tool',
  parameters: z.object({
    field1: z.string(),
    field2: z.number(),
  }), // ✅ Works
  execute: async (input) => { /* ... */ },
});

// Or use type assertion (temporary fix)
const myTool = tool({
  name: 'my_tool',
  parameters: myZodSchema as any, // ⚠️ Loses type safety
  execute: async (input) => { /* ... */ },
});
```

**Status**: Known issue as of SDK v0.2.1
**Expected Fix**: Future SDK version

---

## Error 2: MCP Server Tracing Errors

**Issue**: "No existing trace found" error when initializing RealtimeAgent with MCP servers.

**GitHub Issue**: [#580](https://github.com/openai/openai-agents-js/issues/580)

**Symptoms**:
```
UnhandledPromiseRejection: Error: No existing trace found
  at RealtimeAgent.init with MCP server
```

**Workaround**:
```typescript
// Ensure tracing is initialized before creating agent
import { initializeTracing } from '@openai/agents/tracing';

await initializeTracing();

// Then create realtime agent with MCP
const agent = new RealtimeAgent({
  // ... agent config with MCP servers
});
```

**Status**: Reported October 2025
**Affects**: @openai/agents-realtime v0.0.8 - v0.1.9

---

## Error 3: MaxTurnsExceededError

**Issue**: Agent enters infinite loop and hits turn limit.

**Cause**: Agent keeps calling tools or delegating without reaching conclusion.

**Symptoms**:
```
MaxTurnsExceededError: Agent exceeded maximum turns (10)
```

**Solutions**:

1. **Increase maxTurns**:
```typescript
const result = await run(agent, input, {
  maxTurns: 20, // Increase limit
});
```

2. **Improve Instructions**:
```typescript
const agent = new Agent({
  instructions: `You are a helpful assistant.

  IMPORTANT: After using tools or delegating, provide a final answer.
  Do not endlessly loop or delegate back and forth.`,
});
```

3. **Add Exit Criteria**:
```typescript
const agent = new Agent({
  instructions: `Answer the question using up to 3 tool calls.
  After 3 tool calls, synthesize a final answer.`,
});
```

**Prevention**: Write clear instructions with explicit completion criteria.

---

## Error 4: ToolCallError (Transient Failures)

**Issue**: Tool execution fails temporarily (network, rate limits, external API issues).

**Symptoms**:
```
ToolCallError: Failed to execute tool 'search_api'
```

**Solution**: Implement retry logic with exponential backoff.

```typescript
import { ToolCallError } from '@openai/agents';

async function runWithRetry(agent, input, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await run(agent, input);
    } catch (error) {
      if (error instanceof ToolCallError && attempt < maxRetries) {
        const delay = 1000 * Math.pow(2, attempt - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
}
```

**See Template**: `templates/shared/error-handling.ts`

---

## Error 5: GuardrailExecutionError with Fallback

**Issue**: Guardrail itself fails (e.g., guardrail agent unavailable).

**Symptoms**:
```
GuardrailExecutionError: Guardrail 'safety_check' failed to execute
```

**Solution**: Implement fallback guardrails.

```typescript
import { GuardrailExecutionError } from '@openai/agents';

const primaryGuardrail = { /* ... */ };
const fallbackGuardrail = { /* simple keyword filter */ };

const agent = new Agent({
  inputGuardrails: [primaryGuardrail],
});

try {
  const result = await run(agent, input);
} catch (error) {
  if (error instanceof GuardrailExecutionError && error.state) {
    // Retry with fallback guardrail
    agent.inputGuardrails = [fallbackGuardrail];
    const result = await run(agent, error.state);
  }
}
```

**See Template**: `templates/text-agents/agent-guardrails-input.ts`

---

## Error 6: Schema Mismatch (outputType vs Actual Output)

**Issue**: Agent returns data that doesn't match declared `outputType` schema.

**Cause**: Model sometimes deviates from schema despite instructions.

**Symptoms**:
```
Validation Error: Output does not match schema
```

**Solutions**:

1. **Add Validation Instructions**:
```typescript
const agent = new Agent({
  instructions: `You MUST return data matching this exact schema.
  Double-check your output before finalizing.`,
  outputType: mySchema,
});
```

2. **Use Stricter Models**:
```typescript
const agent = new Agent({
  model: 'gpt-5', // More reliable than gpt-5-mini for structured output
  outputType: mySchema,
});
```

3. **Catch and Retry**:
```typescript
try {
  const result = await run(agent, input);
  // Validate output
  mySchema.parse(result.finalOutput);
} catch (error) {
  // Retry with stronger prompt
  const retryResult = await run(agent,
    `CRITICAL: Your previous output was invalid. Return valid JSON matching the schema exactly. ${input}`
  );
}
```

---

## Error 7: Ollama Integration Failures

**Issue**: TypeScript Agent SDK fails to connect with Ollama models.

**GitHub Issue**: [#136](https://github.com/openai/openai-agents-js/issues/136)

**Symptoms**:
```
TypeError: Cannot read properties of undefined (reading 'completions')
```

**Cause**: SDK designed for OpenAI API format; Ollama requires adapter.

**Workaround**: Use Vercel AI SDK adapter or stick to OpenAI-compatible models.

**Status**: Experimental support; not officially supported.

---

## Error 8: Built-in webSearchTool Intermittent Errors

**Issue**: Built-in `webSearchTool()` sometimes throws exceptions.

**Symptoms**: Unpredictable failures when invoking web search.

**Workaround**:
```typescript
// Use custom search tool with error handling
const customSearchTool = tool({
  name: 'search',
  description: 'Search the web',
  parameters: z.object({ query: z.string() }),
  execute: async ({ query }) => {
    try {
      // Your search API (Tavily, Google, etc.)
      const results = await fetch(`https://api.example.com/search?q=${query}`);
      return await results.json();
    } catch (error) {
      return { error: 'Search temporarily unavailable' };
    }
  },
});
```

**Status**: Known issue in early SDK versions.

---

## Error 9: Agent Builder Export Bugs

**Issue**: Code exported from Agent Builder has bugs (template string escaping, state typing).

**Source**: [OpenAI Community](https://community.openai.com/t/bugs-in-agent-builder-exported-code-typescript-template-string-escaping-state-typing-and-property-naming/1362119)

**Symptoms**: Exported code doesn't compile or run.

**Solution**: Manually review and fix exported code before use.

---

## General Error Handling Pattern

**Comprehensive error handling template**:

```typescript
import {
  MaxTurnsExceededError,
  InputGuardrailTripwireTriggered,
  OutputGuardrailTripwireTriggered,
  ToolCallError,
  GuardrailExecutionError,
  ModelBehaviorError,
} from '@openai/agents';

try {
  const result = await run(agent, input, { maxTurns: 10 });
  return result;

} catch (error) {
  if (error instanceof MaxTurnsExceededError) {
    // Agent hit turn limit - logic issue
    console.error('Agent looped too many times');
    throw error;

  } else if (error instanceof InputGuardrailTripwireTriggered) {
    // Input blocked by guardrail - don't retry
    console.error('Input blocked:', error.outputInfo);
    return { error: 'Input not allowed' };

  } else if (error instanceof OutputGuardrailTripwireTriggered) {
    // Output blocked by guardrail - don't retry
    console.error('Output blocked:', error.outputInfo);
    return { error: 'Response blocked for safety' };

  } else if (error instanceof ToolCallError) {
    // Tool failed - retry with backoff
    console.error('Tool failed:', error.toolName);
    return retryWithBackoff(agent, input);

  } else if (error instanceof GuardrailExecutionError) {
    // Guardrail failed - use fallback
    console.error('Guardrail failed');
    return runWithFallbackGuardrail(agent, input);

  } else if (error instanceof ModelBehaviorError) {
    // Unexpected model behavior - don't retry
    console.error('Model behavior error');
    throw error;

  } else {
    // Unknown error
    console.error('Unknown error:', error);
    throw error;
  }
}
```

**See Template**: `templates/shared/error-handling.ts`

---

**Last Updated**: 2025-10-26
**Sources**:
- [GitHub Issues](https://github.com/openai/openai-agents-js/issues)
- [OpenAI Community](https://community.openai.com/)
- SDK Documentation
