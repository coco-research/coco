/**
 * Cloudflare Workers with OpenAI Agents SDK
 *
 * Demonstrates:
 * - Running text agents in Cloudflare Workers
 * - Handling agent requests via fetch()
 * - Streaming responses to clients
 * - Error handling in Workers environment
 *
 * NOTE: OpenAI Agents SDK has experimental Cloudflare Workers support
 * Some features may not work due to runtime limitations
 */

import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// ========================================
// Agent Definition
// ========================================

const searchTool = tool({
  name: 'search_docs',
  description: 'Search documentation',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    // In production, query a vector database or search API
    return `Found documentation about: ${query}`;
  },
});

const docsAgent = new Agent({
  name: 'Documentation Assistant',
  instructions: 'Help users find information in our documentation. Use the search tool when needed.',
  tools: [searchTool],
  model: 'gpt-5-mini', // Use smaller model for cost efficiency
});

// ========================================
// Cloudflare Worker
// ========================================

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      // Parse request body
      const { message, stream = false } = await request.json() as {
        message: string;
        stream?: boolean;
      };

      if (!message || typeof message !== 'string') {
        return new Response(JSON.stringify({ error: 'Invalid message' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // Set OPENAI_API_KEY from environment
      process.env.OPENAI_API_KEY = env.OPENAI_API_KEY;

      // ========================================
      // Non-Streaming Response
      // ========================================

      if (!stream) {
        const result = await run(docsAgent, message, {
          maxTurns: 5,
        });

        return new Response(JSON.stringify({
          response: result.finalOutput,
          agent: result.currentAgent?.name,
          tokens: result.usage.totalTokens,
        }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }

      // ========================================
      // Streaming Response
      // ========================================

      const streamResult = await run(docsAgent, message, {
        stream: true,
        maxTurns: 5,
      });

      // Create readable stream for response
      const { readable, writable } = new TransformStream();
      const writer = writable.getWriter();
      const encoder = new TextEncoder();

      // Stream events to client
      (async () => {
        try {
          for await (const event of streamResult) {
            if (event.type === 'raw_model_stream_event') {
              const chunk = event.data?.choices?.[0]?.delta?.content || '';
              if (chunk) {
                await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'chunk', content: chunk })}\n\n`));
              }
            } else if (event.type === 'agent_updated_stream_event') {
              await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'agent_change', agent: event.agent.name })}\n\n`));
            }
          }

          await streamResult.completed;

          // Send final message
          await writer.write(encoder.encode(`data: ${JSON.stringify({
            type: 'done',
            tokens: streamResult.result.usage.totalTokens
          })}\n\n`));

        } catch (error: any) {
          await writer.write(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: error.message })}\n\n`));
        } finally {
          await writer.close();
        }
      })();

      return new Response(readable, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
        },
      });

    } catch (error: any) {
      console.error('Worker error:', error);

      return new Response(JSON.stringify({
        error: error.message || 'Internal server error',
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }
  },
};

// ========================================
// Environment Types
// ========================================

interface Env {
  OPENAI_API_KEY: string;
}
