import { useState, useRef, useCallback } from 'react';

export interface QASource {
  gid: string;
  title: string;
  snippet: string;
  relevance: number;
}

export interface ToolCall {
  tool: string;
  input: Record<string, unknown>;
  elapsed_s: number;
  round: number;
}

export type StreamPhase = 'idle' | 'searching' | 'generating' | 'done' | 'error';
export type QAMode = 'lightning' | 'ultrathink';

interface StreamState {
  phase: StreamPhase;
  answer: string;
  sources: QASource[];
  confidence: number;
  model: string;
  tokens: { input: number; output: number };
  thinking: string | null;
  toolCalls: ToolCall[];
  rounds: number;
  error: string | null;
}

const INITIAL_STATE: StreamState = {
  phase: 'idle',
  answer: '',
  sources: [],
  confidence: 0,
  model: '',
  tokens: { input: 0, output: 0 },
  thinking: null,
  toolCalls: [],
  rounds: 1,
  error: null,
};

export function useStreamingQA() {
  const [state, setState] = useState<StreamState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState(INITIAL_STATE);
  }, []);

  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const ask = useCallback(async (question: string, mode: QAMode = 'lightning') => {
    // Abort any in-flight request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ ...INITIAL_STATE, phase: 'searching' });

    try {
      const response = await fetch('/api/knowledge/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, max_sources: 5, mode }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('ReadableStream not supported');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let accAnswer = '';
      let accSources: QASource[] = [];
      let accConfidence = 0;
      let accModel = '';
      let accInputTokens = 0;
      let accOutputTokens = 0;
      let accThinking: string | null = null;
      let accToolCalls: ToolCall[] = [];
      let accRounds = 1;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const rawData = line.slice(5).trim();
            if (!rawData) continue;

            try {
              switch (currentEvent) {
                case 'status': {
                  const statusData = JSON.parse(rawData);
                  setState((s) => ({ ...s, phase: statusData.phase === 'generating' ? 'generating' : 'searching' }));
                  break;
                }
                case 'sources': {
                  accSources = JSON.parse(rawData) as QASource[];
                  setState((s) => ({ ...s, sources: accSources }));
                  break;
                }
                case 'chunk': {
                  const chunkData = JSON.parse(rawData);
                  accAnswer += chunkData.text;
                  setState((s) => ({ ...s, answer: accAnswer, phase: 'generating' }));
                  break;
                }
                case 'thinking': {
                  accThinking = JSON.parse(rawData);
                  setState((s) => ({ ...s, thinking: accThinking }));
                  break;
                }
                case 'tool_call': {
                  const tc = JSON.parse(rawData) as ToolCall;
                  accToolCalls = [...accToolCalls, tc];
                  setState((s) => ({ ...s, toolCalls: accToolCalls }));
                  break;
                }
                case 'usage': {
                  const usage = JSON.parse(rawData);
                  accInputTokens = usage.input_tokens ?? 0;
                  accOutputTokens = usage.output_tokens ?? 0;
                  setState((s) => ({ ...s, tokens: { input: accInputTokens, output: accOutputTokens } }));
                  break;
                }
                case 'done': {
                  const doneData = JSON.parse(rawData);
                  accConfidence = doneData.confidence ?? 0;
                  accModel = doneData.model ?? '';
                  accRounds = doneData.rounds ?? 1;
                  accInputTokens = doneData.input_tokens ?? accInputTokens;
                  accOutputTokens = doneData.output_tokens ?? accOutputTokens;
                  setState({
                    phase: 'done',
                    answer: accAnswer,
                    sources: accSources,
                    confidence: accConfidence,
                    model: accModel,
                    tokens: { input: accInputTokens, output: accOutputTokens },
                    thinking: accThinking,
                    toolCalls: accToolCalls,
                    rounds: accRounds,
                    error: null,
                  });
                  break;
                }
                case 'error': {
                  const errData = JSON.parse(rawData);
                  setState((s) => ({ ...s, error: errData.message ?? rawData, phase: 'error' }));
                  break;
                }
              }
            } catch {
              if (currentEvent === 'chunk') {
                accAnswer += rawData;
                setState((s) => ({ ...s, answer: accAnswer }));
              }
            }
            currentEvent = '';
          }
        }
      }

      // If we accumulated an answer but never got a 'done' event, mark as done
      if (accAnswer) {
        setState((prev) => prev.phase === 'done' || prev.phase === 'error' ? prev : {
          ...prev,
          phase: 'done',
          answer: accAnswer,
          sources: accSources,
          confidence: accConfidence,
          model: accModel,
          tokens: { input: accInputTokens, output: accOutputTokens },
          thinking: accThinking,
          toolCalls: accToolCalls,
          rounds: accRounds,
        });
      }

      return {
        answer: accAnswer,
        sources: accSources,
        confidence: accConfidence,
        model: accModel,
        input_tokens: accInputTokens,
        output_tokens: accOutputTokens,
        thinking: accThinking,
        tool_calls: accToolCalls,
        rounds: accRounds,
      };
    } catch (err) {
      if ((err as Error).name === 'AbortError') return null;

      // Fallback to non-streaming endpoint — use a fresh abort signal
      try {
        const fallbackController = new AbortController();
        abortRef.current = fallbackController;
        const res = await fetch('/api/knowledge/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question, max_sources: 5, mode }),
          signal: fallbackController.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setState({
          phase: 'done',
          answer: data.answer,
          sources: data.sources,
          confidence: data.confidence,
          model: data.model,
          tokens: { input: data.input_tokens, output: data.output_tokens },
          thinking: data.thinking,
          toolCalls: data.tool_calls ?? [],
          rounds: data.rounds ?? 1,
          error: null,
        });
        return data;
      } catch (fallbackErr) {
        const msg = (fallbackErr as Error)?.message || 'Unknown error';
        setState((s) => ({ ...s, error: msg, phase: 'error' }));
        return null;
      }
    }
  }, []);

  return {
    ...state,
    isStreaming: state.phase === 'searching' || state.phase === 'generating',
    hasResult: state.phase === 'done' && !!state.answer,
    hasError: state.phase === 'error',
    ask,
    abort,
    reset,
  };
}
