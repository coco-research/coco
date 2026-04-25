/**
 * Streaming Agent Responses
 *
 * Demonstrates:
 * - Enabling streaming with stream: true
 * - Handling different stream event types
 * - Processing raw model chunks
 * - Detecting agent handoffs in streams
 * - Tool call events
 */

import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// Define a slow tool to see streaming behavior
const searchDocsTool = tool({
  name: 'search_docs',
  description: 'Search documentation for relevant information',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    // Simulate slow search
    await new Promise(resolve => setTimeout(resolve, 1000));
    return `Found 3 articles about "${query}":
    1. Getting Started Guide
    2. Advanced Patterns
    3. Troubleshooting Common Issues`;
  },
});

const docsAgent = new Agent({
  name: 'Documentation Assistant',
  instructions: 'You help users find information in documentation. Use the search_docs tool when needed.',
  tools: [searchDocsTool],
});

// ========================================
// Example 1: Basic Streaming (Text Only)
// ========================================

async function streamBasicResponse() {
  console.log('\n📡 Streaming Basic Response:\n');

  const stream = await run(
    docsAgent,
    'Explain how to set up authentication',
    { stream: true }
  );

  // Pipe raw text stream to stdout
  stream
    .toTextStream({ compatibleWithNodeStreams: true })
    .pipe(process.stdout);

  // Wait for completion
  await stream.completed;
  console.log('\n\n✅ Stream completed');
  console.log('Tokens used:', stream.result.usage.totalTokens);
}

// ========================================
// Example 2: Detailed Event Streaming
// ========================================

async function streamWithEvents() {
  console.log('\n📡 Streaming with Event Handling:\n');

  const stream = await run(
    docsAgent,
    'Search for information about multi-agent patterns',
    { stream: true }
  );

  for await (const event of stream) {
    if (event.type === 'raw_model_stream_event') {
      // Raw model response chunks
      const chunk = event.data?.choices?.[0]?.delta?.content || '';
      if (chunk) {
        process.stdout.write(chunk);
      }

    } else if (event.type === 'agent_updated_stream_event') {
      // Agent handoff occurred
      console.log(`\n\n🔄 Agent changed to: ${event.agent.name}\n`);

    } else if (event.type === 'run_item_stream_event') {
      // Tool calls, outputs, or other run items
      if (event.name === 'tool_call_started') {
        const toolCall = event.item as any;
        console.log(`\n\n🛠️  Calling tool: ${toolCall.name}`);
        console.log(`   Arguments:`, JSON.stringify(toolCall.arguments, null, 2));

      } else if (event.name === 'tool_call_completed') {
        const toolResult = event.item as any;
        console.log(`\n✅ Tool result received`);

      } else if (event.name === 'agent_message') {
        // Agent produced a message
        // (already handled by raw_model_stream_event above)
      }
    }
  }

  await stream.completed;
  console.log('\n\n✅ Stream completed');
  console.log('Tokens used:', stream.result.usage.totalTokens);
}

// ========================================
// Example 3: Streaming with Multiple Agents
// ========================================

const specialistAgent = new Agent({
  name: 'Advanced Specialist',
  instructions: 'You provide advanced technical guidance.',
  handoffDescription: 'Transfer for advanced technical questions',
});

const triageAgent = Agent.create({
  name: 'Triage',
  instructions: 'Route questions to specialists if they are advanced.',
  handoffs: [specialistAgent],
});

async function streamMultiAgent() {
  console.log('\n📡 Streaming Multi-Agent Response:\n');

  let currentAgent = 'Triage';

  const stream = await run(
    triageAgent,
    'I need advanced help with distributed systems architecture',
    { stream: true }
  );

  for await (const event of stream) {
    if (event.type === 'agent_updated_stream_event') {
      currentAgent = event.agent.name;
      console.log(`\n${'='.repeat(50)}`);
      console.log(`🔄 Handoff to: ${currentAgent}`);
      console.log('='.repeat(50) + '\n');

    } else if (event.type === 'raw_model_stream_event') {
      const chunk = event.data?.choices?.[0]?.delta?.content || '';
      if (chunk) {
        process.stdout.write(chunk);
      }
    }
  }

  await stream.completed;
  console.log('\n\n✅ Final agent:', stream.result.currentAgent?.name);
}

// ========================================
// Usage
// ========================================

async function main() {
  try {
    await streamBasicResponse();
    console.log('\n' + '='.repeat(60) + '\n');

    await streamWithEvents();
    console.log('\n' + '='.repeat(60) + '\n');

    await streamMultiAgent();

  } catch (error) {
    console.error('\n❌ Error:', error);
    process.exit(1);
  }
}

// Uncomment to run
// main();

export { streamBasicResponse, streamWithEvents, streamMultiAgent };
