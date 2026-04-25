---
paths: "**/*.ts", "**/*.tsx", "**/*openai*.ts"
---

# OpenAI API Corrections

Claude's training may reference older patterns. This project uses **openai@6.9.1**.

## GPT-5.1 Reasoning Defaults Changed

```typescript
/* ❌ GPT-5.1 defaults to reasoning_effort: 'none' (different from GPT-5!) */
const response = await openai.chat.completions.create({
  model: 'gpt-5.1',
  messages: [...],
})

/* ✅ Explicitly set reasoning_effort */
const response = await openai.chat.completions.create({
  model: 'gpt-5.1',
  messages: [...],
  reasoning_effort: 'medium', // Required for reasoning
})
```

## Temperature Not Supported on GPT-5

```typescript
/* ❌ Will fail on GPT-5/GPT-5.1 */
const response = await openai.chat.completions.create({
  model: 'gpt-5',
  temperature: 0.7, // Not supported!
})

/* ✅ Use reasoning_effort instead, or fall back to GPT-4o */
const response = await openai.chat.completions.create({
  model: 'gpt-5',
  reasoning_effort: 'medium',
})

// For temperature control, use GPT-4o:
const response = await openai.chat.completions.create({
  model: 'gpt-4o',
  temperature: 0.7,
})
```

## Current Model Names (2025)

```typescript
/* ❌ Deprecated models */
'gpt-3.5-turbo'  // Deprecated
'gpt-4'          // Deprecated

/* ✅ Current models */
'gpt-5.1'        // Latest (Nov 2025)
'gpt-5'          // Previous flagship
'gpt-5-mini'     // Cost-efficient
'gpt-5-nano'     // Lightweight
'gpt-4o'         // Still supported, has temperature
```

## Streaming SSE Parsing

```typescript
/* ❌ Missing error handling */
for await (const chunk of stream) {
  console.log(chunk.choices[0].delta.content)
}

/* ✅ Handle [DONE] signal and errors */
for await (const chunk of stream) {
  if (chunk.choices[0]?.finish_reason === 'stop') break
  const content = chunk.choices[0]?.delta?.content
  if (content) process.stdout.write(content)
}
```

## DALL-E 3 Single Image Only

```typescript
/* ❌ n > 1 not supported */
const response = await openai.images.generate({
  model: 'dall-e-3',
  n: 4, // Error!
})

/* ✅ DALL-E 3 only supports n: 1 */
const response = await openai.images.generate({
  model: 'dall-e-3',
  n: 1,
})
```

## Quick Fixes

| If Claude suggests... | Use instead... |
|----------------------|----------------|
| `temperature` on GPT-5 | `reasoning_effort` |
| `gpt-3.5-turbo` or `gpt-4` | `gpt-5.1`, `gpt-5`, or `gpt-4o` |
| `n: 4` with DALL-E 3 | `n: 1` (only supported value) |
| Missing stream error handling | Check `finish_reason` and `[DONE]` |
| Image URLs for storage | Use `response_format: 'b64_json'` (URLs expire 1hr) |
