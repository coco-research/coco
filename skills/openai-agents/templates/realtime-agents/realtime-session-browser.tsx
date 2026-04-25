/**
 * Realtime Voice Session - React Browser Client
 *
 * Demonstrates:
 * - Creating a voice session in the browser
 * - Using WebRTC transport for low latency
 * - Handling audio I/O automatically
 * - Managing session lifecycle
 * - Displaying transcripts and tool calls
 *
 * IMPORTANT: Generate ephemeral API keys server-side, never expose your main API key
 */

import React, { useState, useEffect, useRef } from 'react';
import { RealtimeSession, RealtimeAgent } from '@openai/agents-realtime';
import { z } from 'zod';

// ========================================
// Voice Agent Definition
// ========================================

import { tool } from '@openai/agents-realtime';

const weatherTool = tool({
  name: 'get_weather',
  description: 'Get weather for a city',
  parameters: z.object({
    city: z.string(),
  }),
  execute: async ({ city }) => {
    // Call your backend API
    const response = await fetch(`/api/weather?city=${city}`);
    const data = await response.json();
    return data.weather;
  },
});

const voiceAgent = new RealtimeAgent({
  name: 'Voice Assistant',
  instructions: 'You are a helpful voice assistant. Keep responses concise and friendly.',
  tools: [weatherTool],
  voice: 'alloy',
});

// ========================================
// React Component
// ========================================

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ToolCall {
  name: string;
  arguments: Record<string, any>;
  result?: any;
}

export function VoiceAssistant() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [error, setError] = useState<string | null>(null);

  const sessionRef = useRef<RealtimeSession | null>(null);

  // ========================================
  // Initialize Session
  // ========================================

  useEffect(() => {
    let session: RealtimeSession;

    async function initSession() {
      try {
        // Get ephemeral API key from your backend
        const response = await fetch('/api/generate-session-key');
        const { apiKey } = await response.json();

        // Create session with WebRTC transport (low latency)
        session = new RealtimeSession(voiceAgent, {
          apiKey,
          transport: 'webrtc', // or 'websocket'
        });

        sessionRef.current = session;

        // ========================================
        // Session Event Handlers
        // ========================================

        session.on('connected', () => {
          console.log('✅ Connected to voice session');
          setIsConnected(true);
          setError(null);
        });

        session.on('disconnected', () => {
          console.log('🔌 Disconnected from voice session');
          setIsConnected(false);
          setIsListening(false);
        });

        session.on('error', (err) => {
          console.error('❌ Session error:', err);
          setError(err.message);
        });

        // ========================================
        // Transcription Events
        // ========================================

        session.on('audio.transcription.completed', (event) => {
          // User finished speaking
          setMessages(prev => [...prev, {
            role: 'user',
            content: event.transcript,
            timestamp: new Date(),
          }]);
          setIsListening(false);
        });

        session.on('audio.transcription.started', () => {
          // User started speaking
          setIsListening(true);
        });

        session.on('agent.audio.done', (event) => {
          // Agent finished speaking
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: event.transcript,
            timestamp: new Date(),
          }]);
        });

        // ========================================
        // Tool Call Events
        // ========================================

        session.on('tool.call', (event) => {
          console.log('🛠️  Tool call:', event.name, event.arguments);
          setToolCalls(prev => [...prev, {
            name: event.name,
            arguments: event.arguments,
          }]);
        });

        session.on('tool.result', (event) => {
          console.log('✅ Tool result:', event.result);
          setToolCalls(prev => prev.map(tc =>
            tc.name === event.name
              ? { ...tc, result: event.result }
              : tc
          ));
        });

        // Connect to start session
        await session.connect();

      } catch (err: any) {
        console.error('Failed to initialize session:', err);
        setError(err.message);
      }
    }

    initSession();

    // Cleanup on unmount
    return () => {
      if (session) {
        session.disconnect();
      }
    };
  }, []);

  // ========================================
  // Manual Control Functions
  // ========================================

  const handleInterrupt = () => {
    if (sessionRef.current) {
      sessionRef.current.interrupt();
    }
  };

  const handleDisconnect = () => {
    if (sessionRef.current) {
      sessionRef.current.disconnect();
    }
  };

  // ========================================
  // Render UI
  // ========================================

  return (
    <div className="voice-assistant">
      <div className="status-bar">
        <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
        {isListening && <div className="listening">🎤 Listening...</div>}
      </div>

      {error && (
        <div className="error">
          ❌ Error: {error}
        </div>
      )}

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="role">{msg.role === 'user' ? '👤' : '🤖'}</div>
            <div className="content">
              <p>{msg.content}</p>
              <span className="timestamp">
                {msg.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      {toolCalls.length > 0 && (
        <div className="tool-calls">
          <h3>🛠️ Tool Calls</h3>
          {toolCalls.map((tc, i) => (
            <div key={i} className="tool-call">
              <strong>{tc.name}</strong>
              <pre>{JSON.stringify(tc.arguments, null, 2)}</pre>
              {tc.result && (
                <div className="result">
                  Result: {JSON.stringify(tc.result)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="controls">
        <button
          onClick={handleInterrupt}
          disabled={!isConnected}
        >
          ⏸️ Interrupt
        </button>
        <button
          onClick={handleDisconnect}
          disabled={!isConnected}
        >
          🔌 Disconnect
        </button>
      </div>

      <style jsx>{`
        .voice-assistant {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }
        .status-bar {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }
        .status {
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 14px;
        }
        .status.connected {
          background: #d4edda;
          color: #155724;
        }
        .status.disconnected {
          background: #f8d7da;
          color: #721c24;
        }
        .listening {
          padding: 8px 16px;
          background: #fff3cd;
          color: #856404;
          border-radius: 20px;
          font-size: 14px;
        }
        .error {
          padding: 12px;
          background: #f8d7da;
          color: #721c24;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .messages {
          height: 400px;
          overflow-y: auto;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
        }
        .message {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }
        .message.user {
          justify-content: flex-end;
        }
        .content {
          max-width: 70%;
          padding: 12px;
          border-radius: 12px;
        }
        .message.user .content {
          background: #007bff;
          color: white;
        }
        .message.assistant .content {
          background: #f1f3f4;
          color: #000;
        }
        .timestamp {
          font-size: 11px;
          opacity: 0.6;
        }
        .tool-calls {
          margin-bottom: 20px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        .tool-call {
          margin: 8px 0;
          padding: 8px;
          background: white;
          border-radius: 4px;
        }
        .controls {
          display: flex;
          gap: 12px;
        }
        button {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 8px;
          background: #007bff;
          color: white;
          cursor: pointer;
        }
        button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
        button:hover:not(:disabled) {
          background: #0056b3;
        }
      `}</style>
    </div>
  );
}

export default VoiceAssistant;
