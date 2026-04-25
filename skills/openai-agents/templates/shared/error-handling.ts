/**
 * Comprehensive error handling patterns for OpenAI Agents SDK
 *
 * Covers all major error types:
 * - MaxTurnsExceededError: Agent hit maximum turns limit
 * - InputGuardrailTripwireTriggered: Input blocked by guardrail
 * - OutputGuardrailTripwireTriggered: Output blocked by guardrail
 * - ToolCallError: Tool execution failed
 * - ModelBehaviorError: Unexpected model behavior
 * - GuardrailExecutionError: Guardrail itself failed
 */

import {
  Agent,
  run,
  MaxTurnsExceededError,
  InputGuardrailTripwireTriggered,
  OutputGuardrailTripwireTriggered,
  ModelBehaviorError,
  ToolCallError,
  GuardrailExecutionError,
} from '@openai/agents';

/**
 * Run agent with comprehensive error handling and retry logic
 */
export async function runAgentWithErrorHandling(
  agent: Agent,
  input: string,
  options: {
    maxRetries?: number;
    maxTurns?: number;
    onError?: (error: Error, attempt: number) => void;
  } = {}
) {
  const { maxRetries = 3, maxTurns = 10, onError } = options;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await run(agent, input, { maxTurns });
      return result;

    } catch (error) {
      // Notify error callback
      if (onError) {
        onError(error as Error, attempt);
      }

      // Handle specific error types
      if (error instanceof MaxTurnsExceededError) {
        console.error('❌ Agent exceeded maximum turns');
        console.error(`   Agent entered an infinite loop after ${maxTurns} turns`);
        throw error; // Don't retry - this is a logic issue

      } else if (error instanceof InputGuardrailTripwireTriggered) {
        console.error('❌ Input blocked by guardrail');
        console.error('   Reason:', error.outputInfo);
        throw error; // Don't retry - input is invalid

      } else if (error instanceof OutputGuardrailTripwireTriggered) {
        console.error('❌ Output blocked by guardrail');
        console.error('   Reason:', error.outputInfo);
        throw error; // Don't retry - output violates policy

      } else if (error instanceof ToolCallError) {
        console.error(`⚠️  Tool call failed (attempt ${attempt}/${maxRetries})`);
        console.error('   Tool:', error.toolName);
        console.error('   Error:', error.message);

        if (attempt === maxRetries) {
          throw error; // Give up after max retries
        }

        // Exponential backoff
        const delay = 1000 * Math.pow(2, attempt - 1);
        console.log(`   Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));

      } else if (error instanceof ModelBehaviorError) {
        console.error('❌ Unexpected model behavior');
        console.error('   Details:', error.message);
        throw error; // Don't retry - model is behaving incorrectly

      } else if (error instanceof GuardrailExecutionError) {
        console.error('❌ Guardrail execution failed');
        console.error('   Guardrail:', error.guardrailName);
        console.error('   Error:', error.message);

        // Option to retry with fallback guardrail
        // See common-errors.md for fallback pattern
        throw error;

      } else {
        // Unknown error - retry with exponential backoff
        console.error(`⚠️  Unknown error (attempt ${attempt}/${maxRetries})`);
        console.error('   Error:', error);

        if (attempt === maxRetries) {
          throw error;
        }

        const delay = 1000 * Math.pow(2, attempt - 1);
        console.log(`   Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw new Error('Max retries exceeded');
}

/**
 * Example usage
 */
export async function exampleUsage() {
  const agent = new Agent({
    name: 'Assistant',
    instructions: 'You are a helpful assistant.',
  });

  try {
    const result = await runAgentWithErrorHandling(
      agent,
      'What is 2+2?',
      {
        maxRetries: 3,
        maxTurns: 10,
        onError: (error, attempt) => {
          console.log(`Error on attempt ${attempt}:`, error.message);
        },
      }
    );

    console.log('✅ Success:', result.finalOutput);
    console.log('Tokens used:', result.usage.totalTokens);

  } catch (error) {
    console.error('❌ Final error:', error);
    process.exit(1);
  }
}

// Uncomment to run example
// exampleUsage();
