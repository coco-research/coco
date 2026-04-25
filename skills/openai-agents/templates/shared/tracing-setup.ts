/**
 * Tracing and debugging configuration for OpenAI Agents SDK
 *
 * Built-in tracing helps visualize agent execution:
 * - Agent transitions (handoffs)
 * - Tool calls
 * - LLM requests
 * - Guardrail executions
 * - Token usage
 *
 * Tracing is automatically enabled when you import from '@openai/agents'
 */

import { Agent, run } from '@openai/agents';

/**
 * Enable detailed logging for debugging
 */
export function enableVerboseLogging() {
  // Set environment variable for debug mode
  process.env.DEBUG = '@openai/agents:*';
}

/**
 * Run agent with detailed trace logging
 */
export async function runWithTracing(agent: Agent, input: string) {
  console.log('🔍 Starting traced agent execution...\n');

  const result = await run(agent, input);

  // Log execution summary
  console.log('\n📊 Execution Summary:');
  console.log('─────────────────────────────────────');
  console.log('Final Output:', result.finalOutput);
  console.log('Current Agent:', result.currentAgent?.name || 'N/A');
  console.log('Total Tokens:', result.usage.totalTokens);
  console.log('Input Tokens:', result.usage.inputTokens);
  console.log('Output Tokens:', result.usage.outputTokens);
  console.log('Conversation Turns:', result.history.length);
  console.log('─────────────────────────────────────\n');

  // Log conversation history
  console.log('💬 Conversation History:');
  result.history.forEach((message, index) => {
    console.log(`\n[${index + 1}] ${message.role}:`);
    if (message.role === 'user' || message.role === 'assistant') {
      console.log(message.content);
    } else if (message.role === 'tool') {
      console.log(`  Tool: ${message.name}`);
      console.log(`  Result:`, message.result);
    }
  });

  return result;
}

/**
 * Stream agent execution with event logging
 */
export async function runWithStreamTracing(agent: Agent, input: string) {
  console.log('🔍 Starting streamed agent execution...\n');

  const stream = await run(agent, input, { stream: true });

  for await (const event of stream) {
    if (event.type === 'raw_model_stream_event') {
      // Raw model response chunk
      const chunk = event.data?.choices?.[0]?.delta?.content || '';
      if (chunk) {
        process.stdout.write(chunk);
      }

    } else if (event.type === 'agent_updated_stream_event') {
      // Agent handoff occurred
      console.log(`\n🔄 Handoff to: ${event.agent.name}`);

    } else if (event.type === 'run_item_stream_event') {
      // Tool call, output, or other run item
      if (event.name === 'tool_call') {
        console.log(`\n🛠️  Tool call: ${event.item.name}`);
        console.log(`   Arguments:`, event.item.arguments);
      } else if (event.name === 'tool_result') {
        console.log(`✅ Tool result:`, event.item.result);
      }
    }
  }

  // Wait for completion
  await stream.completed;
  const result = stream.result;

  console.log('\n\n📊 Stream Summary:');
  console.log('─────────────────────────────────────');
  console.log('Total Tokens:', result.usage.totalTokens);
  console.log('─────────────────────────────────────\n');

  return result;
}

/**
 * Example: Debug a complex multi-agent workflow
 */
export async function exampleTracedWorkflow() {
  // Enable verbose logging
  enableVerboseLogging();

  const agent = new Agent({
    name: 'Debug Agent',
    instructions: 'You are a debugging assistant.',
  });

  // Run with tracing
  await runWithTracing(
    agent,
    'Explain how to debug a TypeScript application'
  );

  // Run with stream tracing
  await runWithStreamTracing(
    agent,
    'What are the best debugging tools for Node.js?'
  );
}

// Uncomment to run example
// exampleTracedWorkflow();
