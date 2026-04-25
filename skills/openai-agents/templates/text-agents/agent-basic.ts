/**
 * Basic Agent with Tools
 *
 * Demonstrates:
 * - Creating an agent with instructions
 * - Defining tools with Zod schemas
 * - Running an agent and getting results
 */

import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

// Define a tool with automatic schema generation
const getWeatherTool = tool({
  name: 'get_weather',
  description: 'Get the current weather for a given city',
  parameters: z.object({
    city: z.string().describe('The city name'),
    units: z.enum(['celsius', 'fahrenheit']).optional().default('celsius'),
  }),
  execute: async (input) => {
    // Simulate API call
    const temp = Math.floor(Math.random() * 30) + 10;
    return `The weather in ${input.city} is sunny and ${temp}°${input.units === 'celsius' ? 'C' : 'F'}`;
  },
});

// Create agent with tools
const weatherAgent = new Agent({
  name: 'Weather Assistant',
  instructions: 'You are a friendly weather assistant. When users ask about weather, use the get_weather tool to provide accurate information.',
  tools: [getWeatherTool],
  model: 'gpt-5-mini', // Default model
});

// Run the agent
async function main() {
  try {
    const result = await run(
      weatherAgent,
      'What is the weather like in San Francisco?'
    );

    console.log('✅ Agent Response:', result.finalOutput);
    console.log('📊 Tokens Used:', result.usage.totalTokens);
    console.log('🔄 Turns:', result.history.length);

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

// Uncomment to run
// main();

export { weatherAgent, getWeatherTool };
