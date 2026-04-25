/**
 * Cloudflare Workers + Hono + OpenAI Agents
 *
 * Demonstrates:
 * - Integrating agents with Hono framework
 * - Multiple agent endpoints
 * - Streaming with Hono
 * - Type-safe routing
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// ========================================
// Agents
// ========================================

const summarizerAgent = new Agent({
  name: 'Summarizer',
  instructions: 'Summarize text concisely in 2-3 sentences.',
  model: 'gpt-5-mini',
});

const translatorAgent = new Agent({
  name: 'Translator',
  instructions: 'Translate text accurately while preserving meaning and tone.',
  model: 'gpt-5-mini',
});

const analyzerTool = tool({
  name: 'analyze_sentiment',
  description: 'Analyze sentiment',
  parameters: z.object({
    text: z.string(),
  }),
  execute: async ({ text }) => {
    // Simplified sentiment analysis
    const positive = ['good', 'great', 'excellent', 'love', 'amazing'];
    const negative = ['bad', 'terrible', 'hate', 'awful', 'poor'];

    const lowerText = text.toLowerCase();
    const posCount = positive.filter(w => lowerText.includes(w)).length;
    const negCount = negative.filter(w => lowerText.includes(w)).length;

    if (posCount > negCount) return 'Positive sentiment detected';
    if (negCount > posCount) return 'Negative sentiment detected';
    return 'Neutral sentiment detected';
  },
});

const analyzerAgent = new Agent({
  name: 'Analyzer',
  instructions: 'Analyze text for sentiment, tone, and key themes.',
  tools: [analyzerTool],
  model: 'gpt-5-mini',
});

// ========================================
// Hono App
// ========================================

type Bindings = {
  OPENAI_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Enable CORS
app.use('/*', cors());

// Health check
app.get('/', (c) => {
  return c.json({
    service: 'OpenAI Agents API',
    version: '1.0.0',
    agents: ['summarizer', 'translator', 'analyzer'],
  });
});

// ========================================
// Summarizer Endpoint
// ========================================

app.post('/api/summarize', async (c) => {
  try {
    const { text } = await c.req.json();

    if (!text) {
      return c.json({ error: 'Missing text parameter' }, 400);
    }

    // Set API key from environment
    process.env.OPENAI_API_KEY = c.env.OPENAI_API_KEY;

    const result = await run(summarizerAgent, text);

    return c.json({
      summary: result.finalOutput,
      tokens: result.usage.totalTokens,
    });

  } catch (error: any) {
    return c.json({ error: error.message }, 500);
  }
});

// ========================================
// Translator Endpoint
// ========================================

app.post('/api/translate', async (c) => {
  try {
    const { text, targetLanguage } = await c.req.json();

    if (!text || !targetLanguage) {
      return c.json({ error: 'Missing required parameters' }, 400);
    }

    process.env.OPENAI_API_KEY = c.env.OPENAI_API_KEY;

    const result = await run(
      translatorAgent,
      `Translate the following to ${targetLanguage}: ${text}`
    );

    return c.json({
      translation: result.finalOutput,
      sourceLanguage: 'auto-detected',
      targetLanguage,
      tokens: result.usage.totalTokens,
    });

  } catch (error: any) {
    return c.json({ error: error.message }, 500);
  }
});

// ========================================
// Analyzer Endpoint (with Streaming)
// ========================================

app.post('/api/analyze', async (c) => {
  try {
    const { text, stream = false } = await c.req.json();

    if (!text) {
      return c.json({ error: 'Missing text parameter' }, 400);
    }

    process.env.OPENAI_API_KEY = c.env.OPENAI_API_KEY;

    // Non-streaming
    if (!stream) {
      const result = await run(analyzerAgent, `Analyze this text: ${text}`);
      return c.json({
        analysis: result.finalOutput,
        tokens: result.usage.totalTokens,
      });
    }

    // Streaming
    const streamResult = await run(analyzerAgent, `Analyze: ${text}`, {
      stream: true,
    });

    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Stream in background
    (async () => {
      try {
        for await (const event of streamResult) {
          if (event.type === 'raw_model_stream_event') {
            const chunk = event.data?.choices?.[0]?.delta?.content || '';
            if (chunk) {
              await writer.write(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
            }
          }
        }

        await streamResult.completed;
        await writer.write(encoder.encode(`data: ${JSON.stringify({ done: true })}\n\n`));
      } catch (error: any) {
        await writer.write(encoder.encode(`data: ${JSON.stringify({ error: error.message })}\n\n`));
      } finally {
        await writer.close();
      }
    })();

    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error: any) {
    return c.json({ error: error.message }, 500);
  }
});

// ========================================
// Export Worker
// ========================================

export default app;
