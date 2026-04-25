/**
 * Realtime Agent Handoffs (Voice)
 *
 * Demonstrates:
 * - Multi-agent voice workflows
 * - Handoffs between voice agents
 * - Automatic conversation history passing
 * - Voice/model constraints during handoffs
 *
 * IMPORTANT: Unlike text agents, realtime agent handoffs have constraints:
 * - Cannot change voice during handoff
 * - Cannot change model during handoff
 * - Conversation history automatically passed
 */

import { z } from 'zod';
import { RealtimeAgent, tool } from '@openai/agents-realtime';

// ========================================
// Specialized Agent Tools
// ========================================

const checkAccountTool = tool({
  name: 'check_account',
  description: 'Look up account information',
  parameters: z.object({
    accountId: z.string(),
  }),
  execute: async ({ accountId }) => {
    return `Account ${accountId}: Premium tier, billing current, last login: 2025-10-20`;
  },
});

const processPaymentTool = tool({
  name: 'process_payment',
  description: 'Process a payment',
  parameters: z.object({
    accountId: z.string(),
    amount: z.number(),
  }),
  execute: async ({ accountId, amount }) => {
    return `Payment of $${amount} processed for account ${accountId}`;
  },
});

const checkSystemTool = tool({
  name: 'check_system',
  description: 'Check system status',
  parameters: z.object({}),
  execute: async () => {
    return 'All systems operational: API ✅, Database ✅, CDN ✅';
  },
});

const createTicketTool = tool({
  name: 'create_ticket',
  description: 'Create support ticket',
  parameters: z.object({
    title: z.string(),
    priority: z.enum(['low', 'medium', 'high']),
  }),
  execute: async ({ title, priority }) => {
    const id = `TICKET-${Math.floor(Math.random() * 10000)}`;
    return `Created ${priority} priority ticket ${id}: ${title}`;
  },
});

// ========================================
// Specialized Voice Agents
// ========================================

const billingAgent = new RealtimeAgent({
  name: 'Billing Specialist',
  instructions: `You handle billing and payment questions.
  - Be professional and empathetic
  - Explain charges clearly
  - Process payments when requested
  - Keep responses concise for voice`,
  handoffDescription: 'Transfer for billing, payments, or account questions',
  tools: [checkAccountTool, processPaymentTool],
  voice: 'nova', // All agents must use same voice as parent
});

const technicalAgent = new RealtimeAgent({
  name: 'Technical Support',
  instructions: `You handle technical issues and system problems.
  - Diagnose issues systematically
  - Provide clear troubleshooting steps
  - Create tickets for complex issues
  - Use simple language for voice`,
  handoffDescription: 'Transfer for technical problems, bugs, or system issues',
  tools: [checkSystemTool, createTicketTool],
  voice: 'nova', // Must match triage agent voice
});

// ========================================
// Triage Agent (Entry Point)
// ========================================

const triageVoiceAgent = new RealtimeAgent({
  name: 'Customer Service',
  instructions: `You are the first point of contact.
  - Greet customers warmly
  - Understand their issue
  - Route to the right specialist
  - Explain the transfer before handing off`,
  handoffs: [billingAgent, technicalAgent],
  voice: 'nova', // This voice will be used by all agents
  model: 'gpt-5-realtime', // This model will be used by all agents
});

// ========================================
// Important Notes about Voice Handoffs
// ========================================

/**
 * KEY DIFFERENCES from text agent handoffs:
 *
 * 1. VOICE CONSTRAINT
 *    - All agents in a handoff chain must use the same voice
 *    - Voice is set by the initial agent
 *    - Cannot change voice during handoff
 *
 * 2. MODEL CONSTRAINT
 *    - All agents must use the same model
 *    - Model is set by the initial agent
 *    - Cannot change model during handoff
 *
 * 3. AUTOMATIC HISTORY
 *    - Conversation history automatically passed to delegated agent
 *    - No need to manually manage context
 *    - Specialist agents can see full conversation
 *
 * 4. SEAMLESS AUDIO
 *    - Audio stream continues during handoff
 *    - User doesn't need to reconnect
 *    - Tools execute in same session
 */

// ========================================
// Example: Create Session with Handoffs
// ========================================

async function createVoiceSessionWithHandoffs() {
  const { OpenAIRealtimeWebSocket } = await import('@openai/agents-realtime');

  const transport = new OpenAIRealtimeWebSocket({
    apiKey: process.env.OPENAI_API_KEY,
  });

  const session = await triageVoiceAgent.createSession({
    transport,
  });

  // Track which agent is currently active
  let currentAgent = 'Customer Service';

  session.on('connected', () => {
    console.log('✅ Voice session connected');
    console.log('🎙️  Current agent:', currentAgent);
  });

  // Listen for agent changes (handoffs)
  session.on('agent.changed', (event: any) => {
    currentAgent = event.agent.name;
    console.log('\n🔄 HANDOFF to:', currentAgent);
  });

  session.on('audio.transcription.completed', (event) => {
    console.log(`👤 User: ${event.transcript}`);
  });

  session.on('agent.audio.done', (event) => {
    console.log(`🤖 ${currentAgent}: ${event.transcript}`);
  });

  session.on('tool.call', (event) => {
    console.log(`\n🛠️  Tool: ${event.name}`);
    console.log(`   Arguments:`, event.arguments);
  });

  session.on('tool.result', (event) => {
    console.log(`✅ Result:`, event.result, '\n');
  });

  await session.connect();

  console.log('\n💡 Try saying:');
  console.log('  - "I have a question about my bill"');
  console.log('  - "The API is returning errors"');
  console.log('  - "I need to update my payment method"');
  console.log('\n');

  return session;
}

// ========================================
// Example: Manual Handoff Triggering
// ========================================

/**
 * While handoffs usually happen automatically via LLM routing,
 * you can also programmatically trigger them if needed via
 * backend delegation patterns (see agent-patterns.md reference).
 */

// Uncomment to run
// createVoiceSessionWithHandoffs().catch(console.error);

export {
  triageVoiceAgent,
  billingAgent,
  technicalAgent,
  createVoiceSessionWithHandoffs,
};
