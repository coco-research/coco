---
name: ai-product
description: "Expert in shipping production-grade AI-powered features — LLM integration patterns, RAG architecture, prompt engineering that scales, AI UX that users trust, safety and guardrails, streaming, and cost optimization."
domain: pm
supports: [claude-code, cursor, codex, generic]
version: 0.1.0
---

# AI Product Development

Expert in shipping production-grade AI-powered features — LLM integration patterns, RAG architecture, prompt engineering that scales, AI UX that users trust, safety and guardrails, streaming, and cost optimization. Treats prompts as code, validates all outputs, and never trusts an LLM blindly.

**Use when**: building AI features into a product, integrating LLMs, designing RAG pipelines, implementing AI safety/guardrails, optimizing AI costs, building AI UX patterns, prompt engineering for production, handling hallucinations, streaming LLM responses, or evaluating AI output quality.

---

## When This Skill Is Activated

1. Read this file fully before proceeding
2. Understand what AI feature the user is building
3. Apply the relevant patterns below (integration, RAG, UX, safety, cost)
4. Always address: output validation, error handling, cost awareness, user trust

---

## Core Principle

Demos are easy. Production is hard. Every pattern below exists because something broke in production.

---

## LLM Integration Patterns

### Structured Output with Validation

Never parse free-text LLM output with regex. Use structured output modes and validate with a schema.

```typescript
import { z } from "zod";
import OpenAI from "openai";

// 1. Define your schema
const ProductReviewSchema = z.object({
  sentiment: z.enum(["positive", "negative", "neutral"]),
  score: z.number().min(0).max(10),
  summary: z.string().max(200),
  keyTopics: z.array(z.string()).max(5),
});

type ProductReview = z.infer<typeof ProductReviewSchema>;

// 2. Call with structured output
const openai = new OpenAI();

async function analyzeReview(reviewText: string): Promise<ProductReview> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    response_format: { type: "json_object" },
    messages: [
      {
        role: "system",
        content: `Analyze the product review. Return JSON matching this schema:
          { sentiment: "positive"|"negative"|"neutral", score: 0-10, summary: string, keyTopics: string[] }`,
      },
      { role: "user", content: reviewText },
    ],
  });

  const raw = JSON.parse(response.choices[0].message.content!);

  // 3. Always validate — the model can return anything
  const result = ProductReviewSchema.parse(raw);
  return result;
}
```

### Streaming with Progress

Stream LLM responses to reduce perceived latency. Show users something is happening immediately.

```typescript
async function streamResponse(prompt: string, onChunk: (text: string) => void) {
  const stream = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }],
    stream: true,
  });

  let fullText = "";
  for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta?.content || "";
    fullText += delta;
    onChunk(delta); // Update UI incrementally
  }

  return fullText;
}

// React example: streaming into state
function useStreamingAI() {
  const [text, setText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const generate = async (prompt: string) => {
    setIsStreaming(true);
    setText("");
    await streamResponse(prompt, (chunk) => {
      setText((prev) => prev + chunk);
    });
    setIsStreaming(false);
  };

  return { text, isStreaming, generate };
}
```

### Prompt Versioning and Testing

Treat prompts as code. Version them. Test with regression suites.

```typescript
// prompts/v3-review-analyzer.ts
export const REVIEW_ANALYZER_PROMPT = {
  version: "3.0",
  system: `You are a product review analyst. Extract sentiment, score, summary, and topics.
    Always return valid JSON. Never hallucinate topics not mentioned in the review.`,
  temperature: 0.1, // Low temp for consistent structured output
  maxTokens: 500,
};

// tests/prompts/review-analyzer.test.ts
describe("Review Analyzer Prompt v3", () => {
  const testCases = [
    {
      input: "This product is amazing! Great battery life and beautiful screen.",
      expected: { sentiment: "positive", minScore: 7 },
    },
    {
      input: "Terrible. Broke after 2 days. Worst purchase ever.",
      expected: { sentiment: "negative", maxScore: 3 },
    },
    {
      input: "It's okay. Does what it says but nothing special.",
      expected: { sentiment: "neutral", minScore: 4, maxScore: 6 },
    },
  ];

  test.each(testCases)("correctly analyzes: $input", async ({ input, expected }) => {
    const result = await analyzeReview(input);
    expect(result.sentiment).toBe(expected.sentiment);
    if (expected.minScore) expect(result.score).toBeGreaterThanOrEqual(expected.minScore);
    if (expected.maxScore) expect(result.score).toBeLessThanOrEqual(expected.maxScore);
  });
});
```

---

## RAG Architecture

### When to Use RAG

| Approach | When | Example |
|----------|------|---------|
| Prompt only | Model already knows the answer | General knowledge questions |
| RAG | Answer depends on your data | "What's our refund policy?" |
| Fine-tuning | Model needs new behavior/style | Domain-specific tone or format |
| RAG + Fine-tuning | Both custom data and custom behavior | Enterprise support bot |

### RAG Pipeline

```
User Query
    ↓
Query Processing (rewrite, expand, decompose)
    ↓
Embedding (text → vector)
    ↓
Vector Search (find relevant chunks)
    ↓
Re-ranking (order by relevance)
    ↓
Context Assembly (fit within token budget)
    ↓
LLM Generation (with retrieved context)
    ↓
Citation Extraction + Validation
    ↓
Response with Sources
```

### Implementation

```typescript
import { OpenAI } from "openai";

const openai = new OpenAI();

// 1. Chunk documents at ingest time
function chunkDocument(text: string, maxChunkSize = 500, overlap = 50): string[] {
  const sentences = text.split(/(?<=[.!?])\s+/);
  const chunks: string[] = [];
  let current = "";

  for (const sentence of sentences) {
    if ((current + sentence).length > maxChunkSize && current) {
      chunks.push(current.trim());
      // Keep overlap for context continuity
      const words = current.split(" ");
      current = words.slice(-overlap).join(" ") + " " + sentence;
    } else {
      current += " " + sentence;
    }
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks;
}

// 2. Embed and store
async function embedChunks(chunks: string[]) {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: chunks,
  });
  return response.data.map((d, i) => ({
    text: chunks[i],
    embedding: d.embedding,
  }));
}

// 3. Retrieve relevant context
async function retrieve(query: string, topK = 5) {
  const queryEmbedding = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: query,
  });

  // Search your vector DB (Pinecone, Weaviate, pgvector, etc.)
  const results = await vectorDB.search({
    vector: queryEmbedding.data[0].embedding,
    topK,
  });

  return results.map((r) => r.metadata.text);
}

// 4. Generate with context
async function ragGenerate(query: string) {
  const context = await retrieve(query);

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: `Answer based ONLY on the provided context. If the context doesn't contain the answer, say "I don't have enough information to answer that."
        
Context:
${context.map((c, i) => `[${i + 1}] ${c}`).join("\n\n")}`,
      },
      { role: "user", content: query },
    ],
  });

  return response.choices[0].message.content;
}
```

### RAG Quality Checklist

- Chunk size tuned for your content type (code: larger, FAQ: smaller)
- Overlap between chunks prevents losing context at boundaries
- Query rewriting improves retrieval for vague user questions
- Re-ranking (Cohere, cross-encoder) boosts relevance over pure vector similarity
- Token budget management — don't exceed context window
- Citation tracking — map output claims back to source chunks
- Evaluation set — measure retrieval recall and answer quality regularly

---

## AI UX Patterns — Building Trust

### Show Your Work

Users trust AI more when they can see why it produced an answer.

| Pattern | Implementation | Trust Impact |
|---------|---------------|--------------|
| **Citations** | "Based on [Source A] and [Source B]..." | High |
| **Confidence indicators** | Color-coded confidence bars | Medium |
| **Editable output** | Let users modify AI-generated content | High |
| **Explain reasoning** | Step-by-step breakdown | High |
| **Show alternatives** | "Here are 3 options..." | Medium |
| **Undo/regenerate** | One-click to try again | High |

### Loading States for AI

```typescript
// Bad: Spinner for 10 seconds with no context
<Spinner />

// Good: Progressive disclosure
function AILoadingState({ stage }: { stage: string }) {
  return (
    <div className="ai-loading">
      <div className="pulse-dot" />
      <span className="text-sm text-muted">{stage}</span>
    </div>
  );
}

// Usage with stages
const stages = [
  "Understanding your question...",
  "Searching relevant documents...",
  "Generating response...",
];
```

### Error States

```typescript
// Always have AI-specific error handling
function AIErrorBoundary({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const messages: Record<string, string> = {
    RATE_LIMITED: "Too many requests. Please wait a moment.",
    CONTEXT_TOO_LONG: "Your input is too long. Try shortening it.",
    SAFETY_FILTERED: "This request couldn't be processed. Try rephrasing.",
    API_ERROR: "AI service is temporarily unavailable.",
  };

  return (
    <div className="ai-error">
      <p>{messages[error.message] || "Something went wrong."}</p>
      <button onClick={onRetry}>Try Again</button>
    </div>
  );
}
```

---

## Safety and Guardrails

### Input Sanitization

```typescript
function sanitizeInput(userInput: string): string {
  // 1. Length limit
  if (userInput.length > 10_000) {
    throw new Error("CONTEXT_TOO_LONG");
  }

  // 2. Strip known injection patterns
  const cleaned = userInput
    .replace(/ignore (all |previous |above )?instructions/gi, "[filtered]")
    .replace(/you are now/gi, "[filtered]")
    .replace(/system:\s/gi, "[filtered]");

  return cleaned;
}
```

### Output Validation

```typescript
async function safeGenerate(prompt: string) {
  const response = await generate(prompt);

  // 1. Check for refusal (model declined to answer)
  if (response.includes("I cannot") || response.includes("I'm not able to")) {
    return { type: "refused", content: response };
  }

  // 2. Check for hallucinated URLs/emails
  const urls = response.match(/https?:\/\/[^\s]+/g) || [];
  const validatedUrls = await Promise.all(urls.map(validateUrl));
  if (validatedUrls.some((v) => !v)) {
    return { type: "contains_hallucinated_links", content: stripInvalidUrls(response) };
  }

  // 3. Content policy check (use a classifier or moderation endpoint)
  const moderation = await openai.moderations.create({ input: response });
  if (moderation.results[0].flagged) {
    return { type: "flagged", content: "Response filtered for safety." };
  }

  return { type: "ok", content: response };
}
```

### Guardrail Layers

| Layer | What It Catches | Implementation |
|-------|----------------|----------------|
| Input validation | Injection, abuse, length | Regex + length checks |
| System prompt | Role boundaries | Strong system instructions |
| Output validation | Hallucinated links/data, PII leakage | Post-processing checks |
| Moderation API | Harmful content | OpenAI moderation endpoint |
| Human review queue | Edge cases | Flag low-confidence outputs |

---

## Cost Optimization

### Token Budget Management

```typescript
function estimateTokens(text: string): number {
  // Rough estimate: 1 token ≈ 4 characters for English
  return Math.ceil(text.length / 4);
}

function fitWithinBudget(
  systemPrompt: string,
  context: string[],
  userQuery: string,
  maxTokens: number = 120_000 // model context window
): string[] {
  const reservedForOutput = 4_000;
  const systemTokens = estimateTokens(systemPrompt);
  const queryTokens = estimateTokens(userQuery);
  let budget = maxTokens - reservedForOutput - systemTokens - queryTokens;

  const fitted: string[] = [];
  for (const chunk of context) {
    const chunkTokens = estimateTokens(chunk);
    if (chunkTokens <= budget) {
      fitted.push(chunk);
      budget -= chunkTokens;
    } else {
      break;
    }
  }
  return fitted;
}
```

### Cost Tracking Per Feature

```typescript
async function trackAICost(feature: string, userId: string, apiCall: () => Promise<any>) {
  const start = Date.now();
  const result = await apiCall();
  const duration = Date.now() - start;

  await analytics.track("ai_usage", {
    feature,         // "review-analyzer", "chat", "summarizer"
    userId,
    model: result.model,
    inputTokens: result.usage.prompt_tokens,
    outputTokens: result.usage.completion_tokens,
    cost: calculateCost(result.model, result.usage),
    latency: duration,
    cached: result.usage.prompt_tokens_details?.cached_tokens > 0,
  });

  return result;
}
```

### Cost Reduction Playbook

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Route simple queries to cheaper models | 10–50x | Slight quality drop on edge cases |
| Cache identical queries (Redis/KV) | 40–80% | Stale results for dynamic content |
| Prompt caching (Anthropic/OpenAI) | Up to 90% on input tokens | Only for repeated system prompts |
| Batch non-urgent requests | 50% (OpenAI Batch API) | 24-hour turnaround |
| Truncate context to relevant chunks only | Variable | Requires good retrieval |
| Use embeddings for classification instead of LLM | 95%+ | Only works for classify/match tasks |

---

## Resilience Patterns

### Retry with Fallback

```typescript
async function resilientGenerate(prompt: string) {
  const providers = [
    { name: "openai", fn: () => callOpenAI(prompt) },
    { name: "anthropic", fn: () => callAnthropic(prompt) },
    { name: "cached", fn: () => getCachedFallback(prompt) },
  ];

  for (const provider of providers) {
    try {
      return await withRetry(provider.fn, { maxRetries: 2, backoff: "exponential" });
    } catch (error) {
      console.error(`${provider.name} failed:`, error);
      continue;
    }
  }

  throw new Error("API_ERROR");
}

async function withRetry<T>(
  fn: () => Promise<T>,
  opts: { maxRetries: number; backoff: "exponential" }
): Promise<T> {
  let lastError: Error;
  for (let i = 0; i <= opts.maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < opts.maxRetries) {
        await sleep(Math.pow(2, i) * 1000); // 1s, 2s, 4s
      }
    }
  }
  throw lastError!;
}
```

### Async Processing for Heavy AI Tasks

```typescript
// Don't block request handlers with LLM calls

// API: enqueue the job
app.post("/api/analyze", async (req, res) => {
  const jobId = await queue.add("analyze", {
    userId: req.user.id,
    input: req.body.input,
  });
  res.json({ jobId, status: "processing" });
});

// Worker: process async
queue.process("analyze", async (job) => {
  const result = await analyzeWithAI(job.data.input);
  await db.results.create({ jobId: job.id, ...result });
  await notify(job.data.userId, { jobId: job.id, status: "complete" });
});

// Client: poll or use websocket
app.get("/api/analyze/:jobId", async (req, res) => {
  const result = await db.results.findUnique({ where: { jobId: req.params.jobId } });
  res.json(result || { status: "processing" });
});
```

---

## Anti-Patterns

### Demo-ware

**Why it fails**: Demos deceive. "Works on my laptop" with hand-picked inputs. Production reveals every edge case — hallucinations, latency spikes, cost overruns, adversarial users.

**Instead**: Test with adversarial inputs from day one. Build evaluation sets. Monitor output quality in production. Ship with guardrails, not just a happy path.

### Context Window Stuffing

**Why it fails**: Expensive (paying for irrelevant tokens), slow (larger prompts = higher latency), hits context limits, dilutes relevant signal with noise.

**Instead**: Retrieve only the most relevant context. Use re-ranking. Calculate token budget before sending. Summarize long documents before injecting.

### Unstructured Output Parsing

**Why it fails**: Regex on free-text breaks randomly. Format changes between calls. Injection risks when users control part of the prompt.

**Instead**: Use JSON mode / function calling. Validate with Zod or similar schema library. Always have a fallback for malformed output.

---

## Sharp Edges — Quick Reference

| Issue | Severity | Solution |
|-------|----------|----------|
| Trusting LLM output without validation | Critical | Zod schema validation on every response |
| User input directly in prompts | Critical | Sanitize input, separate system/user roles |
| Context window stuffing | High | Token budget + retrieve only relevant chunks |
| Blocking UI on LLM response | High | Stream responses, show progressive loading states |
| No cost monitoring | High | Track per-request cost, set alerts, usage caps |
| App breaks when LLM API fails | High | Retry + provider fallback + cached fallback |
| Hallucinated facts in output | Critical | Ground with RAG, validate claims, show citations |
| Synchronous LLM in request handler | High | Queue heavy tasks, process async, notify on completion |

---

## Related Skills

Works well with: `ai-wrapper-product`, `openai-api`, `openai-agents`, `api-design-principles`, `frontend-design`
