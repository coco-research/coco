/**
 * Output Guardrails for Content Filtering
 *
 * Demonstrates:
 * - Creating output guardrails
 * - Filtering PII (phone numbers, emails, etc.)
 * - Blocking inappropriate content
 * - Handling structured output guardrails
 */

import { z } from 'zod';
import {
  Agent,
  run,
  OutputGuardrail,
  OutputGuardrailTripwireTriggered,
} from '@openai/agents';

// ========================================
// Output Guardrails
// ========================================

const piiGuardrail: OutputGuardrail = {
  name: 'PII Detection',
  execute: async ({ agentOutput }) => {
    // Detect phone numbers
    const phoneRegex = /\b\d{3}[-. ]?\d{3}[-. ]?\d{4}\b/;
    const hasPhoneNumber = phoneRegex.test(agentOutput as string);

    // Detect email addresses
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
    const hasEmail = emailRegex.test(agentOutput as string);

    // Detect SSN patterns
    const ssnRegex = /\b\d{3}-\d{2}-\d{4}\b/;
    const hasSSN = ssnRegex.test(agentOutput as string);

    const piiDetected = hasPhoneNumber || hasEmail || hasSSN;

    return {
      tripwireTriggered: piiDetected,
      outputInfo: {
        phoneNumber: hasPhoneNumber,
        email: hasEmail,
        ssn: hasSSN,
      },
    };
  },
};

const profanityGuardrail: OutputGuardrail = {
  name: 'Profanity Filter',
  execute: async ({ agentOutput }) => {
    // Simple profanity detection (use a real library in production)
    const bannedWords = ['badword1', 'badword2', 'offensive'];
    const text = (agentOutput as string).toLowerCase();

    const found = bannedWords.filter(word => text.includes(word));

    return {
      tripwireTriggered: found.length > 0,
      outputInfo: {
        foundWords: found,
      },
    };
  },
};

// ========================================
// Structured Output Guardrail
// ========================================

const structuredPIIGuardrail: OutputGuardrail = {
  name: 'Structured PII Check',
  execute: async ({ agentOutput }) => {
    // For structured output, check specific fields
    const output = agentOutput as any;

    const phoneRegex = /\b\d{3}[-. ]?\d{3}[-. ]?\d{4}\b/;

    const piiInResponse = output.response
      ? phoneRegex.test(output.response)
      : false;
    const piiInReasoning = output.reasoning
      ? phoneRegex.test(output.reasoning)
      : false;

    return {
      tripwireTriggered: piiInResponse || piiInReasoning,
      outputInfo: {
        phone_in_response: piiInResponse,
        phone_in_reasoning: piiInReasoning,
      },
    };
  },
};

// ========================================
// Agents with Output Guardrails
// ========================================

// Text agent with PII filtering
const customerServiceAgent = new Agent({
  name: 'Customer Service',
  instructions: 'You help customers with their questions. Be helpful and professional.',
  outputGuardrails: [piiGuardrail, profanityGuardrail],
});

// Structured output agent with PII filtering
const infoExtractorAgent = new Agent({
  name: 'Info Extractor',
  instructions: 'Extract user information from the input.',
  outputType: z.object({
    reasoning: z.string(),
    response: z.string(),
    userName: z.string().nullable(),
  }),
  outputGuardrails: [structuredPIIGuardrail],
});

// ========================================
// Example Usage
// ========================================

async function testTextOutputGuardrails() {
  console.log('\n🛡️  Testing Text Output Guardrails\n');

  const testCases = [
    {
      input: 'What are your business hours?',
      shouldPass: true,
    },
    {
      input: 'My phone number is 650-123-4567, can you call me?',
      shouldPass: false,
    },
    {
      input: 'Tell me about your products',
      shouldPass: true,
    },
  ];

  for (const test of testCases) {
    console.log('='.repeat(60));
    console.log('Input:', test.input);
    console.log('Expected:', test.shouldPass ? 'PASS' : 'BLOCK');
    console.log('='.repeat(60));

    try {
      const result = await run(customerServiceAgent, test.input);
      console.log('✅ PASSED guardrails');
      console.log('Response:', result.finalOutput);

    } catch (error) {
      if (error instanceof OutputGuardrailTripwireTriggered) {
        console.log('❌ BLOCKED by output guardrail');
        console.log('Guardrail:', error.guardrailName);
        console.log('Details:', JSON.stringify(error.outputInfo, null, 2));
        console.log('\nUser-facing message: "Sorry, I cannot provide that information for privacy reasons."');
      } else {
        console.error('⚠️  Unexpected error:', error);
      }
    }

    console.log('\n');
  }
}

async function testStructuredOutputGuardrails() {
  console.log('\n🛡️  Testing Structured Output Guardrails\n');

  const testCases = [
    {
      input: 'My name is Alice Johnson',
      shouldPass: true,
    },
    {
      input: 'I am Bob Smith and my number is 555-1234',
      shouldPass: false,
    },
  ];

  for (const test of testCases) {
    console.log('='.repeat(60));
    console.log('Input:', test.input);
    console.log('Expected:', test.shouldPass ? 'PASS' : 'BLOCK');
    console.log('='.repeat(60));

    try {
      const result = await run(infoExtractorAgent, test.input);
      console.log('✅ PASSED guardrails');
      console.log('Response:', JSON.stringify(result.finalOutput, null, 2));

    } catch (error) {
      if (error instanceof OutputGuardrailTripwireTriggered) {
        console.log('❌ BLOCKED by output guardrail');
        console.log('Guardrail:', error.guardrailName);
        console.log('Details:', JSON.stringify(error.outputInfo, null, 2));
      } else {
        console.error('⚠️  Unexpected error:', error);
      }
    }

    console.log('\n');
  }
}

async function main() {
  try {
    await testTextOutputGuardrails();
    await testStructuredOutputGuardrails();
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

// Uncomment to run
// main();

export {
  customerServiceAgent,
  infoExtractorAgent,
  piiGuardrail,
  profanityGuardrail,
  structuredPIIGuardrail,
};
