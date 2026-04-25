/**
 * Multi-Agent Handoffs (Triage Pattern)
 *
 * Demonstrates:
 * - Creating specialized agents
 * - Using handoffs for agent delegation
 * - Agent routing based on user intent
 * - Accessing current agent after handoff
 */

import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// ========================================
// Specialized Agents
// ========================================

// Billing tools
const checkInvoiceTool = tool({
  name: 'check_invoice',
  description: 'Look up invoice details by ID',
  parameters: z.object({
    invoiceId: z.string(),
  }),
  execute: async ({ invoiceId }) => {
    return `Invoice ${invoiceId}: $99.99, due date: 2025-11-15, status: paid`;
  },
});

const processRefundTool = tool({
  name: 'process_refund',
  description: 'Process a refund for a given invoice',
  parameters: z.object({
    invoiceId: z.string(),
    reason: z.string(),
  }),
  execute: async ({ invoiceId, reason }) => {
    return `Refund initiated for invoice ${invoiceId}. Reason: ${reason}. Expect 5-7 business days.`;
  },
});

// Technical tools
const checkSystemStatusTool = tool({
  name: 'check_system_status',
  description: 'Check the status of system services',
  parameters: z.object({}),
  execute: async () => {
    return 'All systems operational. API: ✅, Database: ✅, CDN: ✅';
  },
});

const createTicketTool = tool({
  name: 'create_ticket',
  description: 'Create a support ticket',
  parameters: z.object({
    title: z.string(),
    description: z.string(),
    priority: z.enum(['low', 'medium', 'high']),
  }),
  execute: async ({ title, priority }) => {
    const ticketId = `TICKET-${Math.floor(Math.random() * 10000)}`;
    return `Created ${priority} priority ticket ${ticketId}: ${title}`;
  },
});

// ========================================
// Specialized Agents
// ========================================

const billingAgent = new Agent({
  name: 'Billing Specialist',
  instructions: 'You handle billing inquiries, payment issues, refunds, and invoice questions. Be professional and helpful.',
  handoffDescription: 'Transfer here for billing, payments, invoices, and refund requests',
  tools: [checkInvoiceTool, processRefundTool],
});

const technicalAgent = new Agent({
  name: 'Technical Support',
  instructions: 'You help with technical issues, bugs, system status, and feature questions. Provide clear technical guidance.',
  handoffDescription: 'Transfer here for technical problems, bugs, feature questions, and system status',
  tools: [checkSystemStatusTool, createTicketTool],
});

// ========================================
// Triage Agent (Entry Point)
// ========================================

// Use Agent.create for proper type inference with handoffs
const triageAgent = Agent.create({
  name: 'Customer Service Triage',
  instructions: 'You are the first point of contact for customer service. Analyze the customer inquiry and route them to the appropriate specialist. Be friendly and professional.',
  handoffs: [billingAgent, technicalAgent],
});

// ========================================
// Usage Example
// ========================================

async function main() {
  const queries = [
    'I was charged twice for my subscription last month',
    'The API keeps returning 500 errors',
    'How do I upgrade my plan?',
  ];

  for (const query of queries) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Query: ${query}`);
    console.log('='.repeat(60));

    try {
      const result = await run(triageAgent, query);

      console.log('🤖 Handled by:', result.currentAgent?.name || 'Triage Agent');
      console.log('💬 Response:', result.finalOutput);
      console.log('📊 Tokens:', result.usage.totalTokens);

    } catch (error) {
      console.error('❌ Error:', error);
    }
  }
}

// Uncomment to run
// main();

export { triageAgent, billingAgent, technicalAgent };
