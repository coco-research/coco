/**
 * Next.js App Router API Route with OpenAI Agents
 *
 * File: app/api/agent/route.ts
 *
 * Demonstrates:
 * - Creating API routes with agents
 * - Handling POST requests
 * - Streaming responses
 * - Error handling
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// ========================================
// Agent Definition
// ========================================

const searchTool = tool({
  name: 'search',
  description: 'Search for information',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    // Implement your search logic
    return `Search results for: ${query}`;
  },
});

const assistantAgent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant. Use the search tool when you need to find information.',
  tools: [searchTool],
  model: 'gpt-5-mini',
});

// ========================================
// POST /api/agent
// ========================================

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body = await request.json();
    const { message, stream = false } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { error: 'Invalid message' },
        { status: 400 }
      );
    }

    // ========================================
    // Non-Streaming Response
    // ========================================

    if (!stream) {
      const result = await run(assistantAgent, message, {
        maxTurns: 5,
      });

      return NextResponse.json({
        response: result.finalOutput,
        agent: result.currentAgent?.name,
        tokens: result.usage.totalTokens,
        history: result.history.length,
      });
    }

    // ========================================
    // Streaming Response
    // ========================================

    const streamResult = await run(assistantAgent, message, {
      stream: true,
      maxTurns: 5,
    });

    // Create readable stream
    const encoder = new TextEncoder();

    const stream = new ReadableStream({
      async start(controller) {
        try {
          for await (const event of streamResult) {
            if (event.type === 'raw_model_stream_event') {
              const chunk = event.data?.choices?.[0]?.delta?.content || '';
              if (chunk) {
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({ type: 'chunk', content: chunk })}\n\n`)
                );
              }

            } else if (event.type === 'agent_updated_stream_event') {
              controller.enqueue(
                encoder.encode(`data: ${JSON.stringify({
                  type: 'agent_change',
                  agent: event.agent.name
                })}\n\n`)
              );

            } else if (event.type === 'run_item_stream_event') {
              if (event.name === 'tool_call') {
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({
                    type: 'tool_call',
                    name: (event.item as any).name,
                    arguments: (event.item as any).arguments,
                  })}\n\n`)
                );
              }
            }
          }

          await streamResult.completed;

          // Send completion event
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({
              type: 'done',
              tokens: streamResult.result.usage.totalTokens
            })}\n\n`)
          );

          controller.close();

        } catch (error: any) {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({
              type: 'error',
              message: error.message
            })}\n\n`)
          );
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error: any) {
    console.error('API route error:', error);

    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

// ========================================
// GET /api/agent (Info)
// ========================================

export async function GET() {
  return NextResponse.json({
    agent: assistantAgent.name,
    tools: assistantAgent.tools?.map((t: any) => t.name) || [],
    model: assistantAgent.model,
  });
}
