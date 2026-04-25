/**
 * Basic Realtime Voice Agent
 *
 * Demonstrates:
 * - Creating a realtime voice agent
 * - Defining tools for voice agents
 * - Configuring voice and instructions
 * - Understanding WebRTC vs WebSocket transports
 *
 * NOTE: This runs in the browser or in a Node.js environment with WebRTC support
 */

import { z } from 'zod';
import { RealtimeAgent, tool } from '@openai/agents-realtime';

// ========================================
// Tools for Voice Agent
// ========================================

// Note: Tools for realtime agents execute in the client environment
// For sensitive operations, make HTTP requests to your backend

const checkWeatherTool = tool({
  name: 'check_weather',
  description: 'Check current weather for a city',
  parameters: z.object({
    city: z.string().describe('City name'),
    units: z.enum(['celsius', 'fahrenheit']).optional().default('celsius'),
  }),
  execute: async ({ city, units }) => {
    // In production, call a real weather API
    const temp = Math.floor(Math.random() * 30) + 10;
    return `The weather in ${city} is sunny and ${temp}°${units === 'celsius' ? 'C' : 'F'}`;
  },
});

const setReminderTool = tool({
  name: 'set_reminder',
  description: 'Set a reminder for the user',
  parameters: z.object({
    message: z.string(),
    timeMinutes: z.number().describe('Minutes from now'),
  }),
  execute: async ({ message, timeMinutes }) => {
    // In production, save to database via API call
    console.log(`Reminder set: "${message}" in ${timeMinutes} minutes`);
    return `I'll remind you about "${message}" in ${timeMinutes} minutes`;
  },
});

const searchDocsTool = tool({
  name: 'search_docs',
  description: 'Search documentation',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    // In production, call your search API
    return `Found documentation about: ${query}`;
  },
});

// ========================================
// Create Realtime Voice Agent
// ========================================

const voiceAssistant = new RealtimeAgent({
  name: 'Voice Assistant',

  // Instructions for the agent's behavior
  instructions: `You are a friendly and helpful voice assistant.
  - Keep responses concise and conversational
  - Use natural speech patterns
  - When using tools, explain what you're doing
  - Be proactive in offering help`,

  // Tools available to the agent
  tools: [checkWeatherTool, setReminderTool, searchDocsTool],

  // Voice configuration (OpenAI voice options)
  voice: 'alloy', // Options: alloy, echo, fable, onyx, nova, shimmer

  // Model (realtime API uses specific models)
  model: 'gpt-5-realtime', // Default for realtime

  // Turn detection (when to consider user done speaking)
  turnDetection: {
    type: 'server_vad', // Voice Activity Detection on server
    threshold: 0.5, // Sensitivity (0-1)
    prefix_padding_ms: 300, // Audio before speech starts
    silence_duration_ms: 500, // Silence to end turn
  },

  // Additional configuration
  temperature: 0.7, // Response creativity (0-1)
  maxOutputTokens: 4096, // Maximum response length
});

// ========================================
// Example: Create Session (Node.js)
// ========================================

/**
 * For Node.js environments, you need to manually manage the session.
 * See realtime-session-browser.tsx for browser usage.
 */
async function createNodeSession() {
  // Note: WebRTC transport requires browser environment
  // For Node.js, use WebSocket transport

  const { OpenAIRealtimeWebSocket } = await import('@openai/agents-realtime');

  const transport = new OpenAIRealtimeWebSocket({
    apiKey: process.env.OPENAI_API_KEY,
  });

  // Create session
  const session = await voiceAssistant.createSession({
    transport,
  });

  // Handle events
  session.on('connected', () => {
    console.log('✅ Voice session connected');
  });

  session.on('disconnected', () => {
    console.log('🔌 Voice session disconnected');
  });

  session.on('error', (error) => {
    console.error('❌ Session error:', error);
  });

  // Audio transcription events
  session.on('audio.transcription.completed', (event) => {
    console.log('User said:', event.transcript);
  });

  session.on('agent.audio.done', (event) => {
    console.log('Agent said:', event.transcript);
  });

  // Tool call events
  session.on('tool.call', (event) => {
    console.log('Tool called:', event.name, event.arguments);
  });

  session.on('tool.result', (event) => {
    console.log('Tool result:', event.result);
  });

  // Connect to start session
  await session.connect();

  // To disconnect later
  // await session.disconnect();

  return session;
}

// ========================================
// Transport Options
// ========================================

/**
 * WebRTC Transport (recommended for browser)
 * - Lower latency
 * - Better for real-time voice
 * - Requires browser environment
 *
 * WebSocket Transport
 * - Works in Node.js
 * - Slightly higher latency
 * - Simpler setup
 */

// Uncomment to run in Node.js
// createNodeSession().catch(console.error);

export {
  voiceAssistant,
  checkWeatherTool,
  setReminderTool,
  searchDocsTool,
  createNodeSession,
};
