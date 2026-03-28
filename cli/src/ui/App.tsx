import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Box, Text, useApp, useStdin } from 'ink';
import { execSync } from 'node:child_process';
import { StatusBar, VoiceStateLabel } from './StatusBar.js';
import { Dashboard } from './Dashboard.js';
import { CommandInput } from './CommandInput.js';
import { SuggestionBar } from './SuggestionBar.js';
import type { Suggestion } from '../proactive/types.js';
import type { Orchestrator } from '../core/orchestrator.js';
import type { SessionManager } from '../core/session-manager.js';
import type { TaskQueue } from '../core/task-queue.js';
import type { StateManager } from '../core/state.js';
import type { SkillRegistry } from '../core/skill-registry.js';

/**
 * Options-object pattern for App props.
 * Phase 2 additions (sessionManager, taskQueue) are optional so that
 * Phase 1 call-sites continue to work without modification.
 */
interface AppProps {
  orchestrator: Orchestrator;
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
}

export const App: React.FC<AppProps> = ({
  orchestrator,
  state,
  skills,
  sessionManager,
  taskQueue,
}) => {
  const { exit } = useApp();

  // --- State ---
  const [directOutput, setDirectOutput] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [activeSessions, setActiveSessions] = useState(0);
  const [queueDepth, setQueueDepth] = useState(0);
  const [maxConcurrency, setMaxConcurrency] = useState(3);
  const [isProcessing, setIsProcessing] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceStateLabel>('off');
  const [activeSuggestion, setActiveSuggestion] = useState<Suggestion | null>(null);
  const [inputHistory, setInputHistory] = useState<string[]>(() =>
    state.getInputHistory(50)
  );
  const { stdin, setRawMode } = useStdin();

  // --- Project info ---
  const cwd = process.cwd();
  const project = cwd.split('/').pop() || 'unknown';
  let branch = '';
  try {
    branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch {}
  if (!branch) branch = 'no-git';

  // --- Greeting (runs once on mount) ---
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const greeting = orchestrator.getGreeting();
    setDirectOutput([greeting]);
    setReady(true);
  }, []);

  // --- Orchestrator event subscriptions ---
  useEffect(() => {
    const onOutput = (data: { sessionId: string | null; text: string }) => {
      if (!data.sessionId) {
        // Only show non-session output in the direct output area
        setDirectOutput(prev => {
          const next = [...prev, data.text];
          return next.length > 100 ? next.slice(-100) : next;
        });
      }
    };

    const onStatus = (data: { message: string }) => setStatusMessage(data.message);
    const onSessionStart = () => setActiveSessions(prev => prev + 1);
    const onSessionEnd = () => {
      setActiveSessions(prev => Math.max(0, prev - 1));
      setIsProcessing(false);
    };
    const onError = (data: { message: string }) => {
      setDirectOutput(prev => [...prev, `Error: ${data.message}`]);
      setIsProcessing(false);
    };

    const onSystemMessage = (data: { text: string }) => {
      setDirectOutput(prev => {
        const next = [...prev, data.text];
        return next.length > 100 ? next.slice(-100) : next;
      });
    };

    const onVoiceInput = (data: { text: string }) => {
      setDirectOutput(prev => [...prev, `[voice] > ${data.text}`]);
    };

    orchestrator.on('output', onOutput);
    orchestrator.on('status', onStatus);
    orchestrator.on('sessionStart', onSessionStart);
    orchestrator.on('sessionEnd', onSessionEnd);
    orchestrator.on('error', onError);
    orchestrator.on('system_message', onSystemMessage);
    orchestrator.on('voice_input', onVoiceInput);

    return () => {
      orchestrator.off('output', onOutput);
      orchestrator.off('status', onStatus);
      orchestrator.off('sessionStart', onSessionStart);
      orchestrator.off('sessionEnd', onSessionEnd);
      orchestrator.off('error', onError);
      orchestrator.off('system_message', onSystemMessage);
      orchestrator.off('voice_input', onVoiceInput);
    };
  }, [orchestrator]);

  // --- Voice state tracking and PTT wiring ---
  useEffect(() => {
    const voiceMgr = orchestrator.voice;
    if (!voiceMgr) return;

    const onStateChange = (newState: VoiceStateLabel) => {
      setVoiceState(newState);
    };
    voiceMgr.on('state-change', onStateChange);

    // Wire raw stdin to PTT controller
    const ptt = voiceMgr.pttController;
    const onData = (data: Buffer) => ptt.handleRawData(data);
    stdin?.on('data', onData);

    return () => {
      voiceMgr.off('state-change', onStateChange);
      stdin?.off('data', onData);
    };
  }, [orchestrator, stdin]);

  // Phase 5: Proactive engine suggestion subscription
  useEffect(() => {
    const proactive = orchestrator.proactive;
    if (!proactive) return;

    const onSuggestion = (suggestion: Suggestion) => {
      setActiveSuggestion(suggestion);
    };
    const onExpired = () => {
      setActiveSuggestion(null);
    };

    proactive.on('suggestion', onSuggestion);
    proactive.on('suggestionExpired', onExpired);

    return () => {
      proactive.off('suggestion', onSuggestion);
      proactive.off('suggestionExpired', onExpired);
    };
  }, [orchestrator]);

  // Phase 5: Suggestion accept/dismiss handlers
  const handleSuggestionAccept = useCallback(() => {
    const proactive = orchestrator.proactive;
    if (!proactive) return;

    const result = proactive.acceptSuggestion();
    setActiveSuggestion(null);

    if (result) {
      // Route the accepted suggestion through the orchestrator
      orchestrator.handleInput(result.skillRoute + ' ' + result.text);
    }
  }, [orchestrator]);

  const handleSuggestionDismiss = useCallback(() => {
    const proactive = orchestrator.proactive;
    if (!proactive) return;

    proactive.dismissSuggestion();
    setActiveSuggestion(null);
  }, [orchestrator]);

  // Session manager concurrency updates
  useEffect(() => {
    if (!sessionManager) return;
    const onConcurrency = (data: { running: number; max: number; queued: number }) => {
      setActiveSessions(data.running);
      setMaxConcurrency(data.max);
    };
    sessionManager.on('concurrencyChanged', onConcurrency);
    return () => { sessionManager.off('concurrencyChanged', onConcurrency); };
  }, [sessionManager]);

  // Task queue updates
  useEffect(() => {
    if (!taskQueue) return;
    const updateDepth = () => setQueueDepth(taskQueue.depth);
    taskQueue.on('taskEnqueued', updateDepth);
    taskQueue.on('taskDispatched', updateDepth);
    taskQueue.on('taskRemoved', updateDepth);
    taskQueue.on('queueCleared', updateDepth);
    return () => {
      taskQueue.off('taskEnqueued', updateDepth);
      taskQueue.off('taskDispatched', updateDepth);
      taskQueue.off('taskRemoved', updateDepth);
      taskQueue.off('queueCleared', updateDepth);
    };
  }, [taskQueue]);

  // --- Input handler ---
  const handleSubmit = useCallback(async (text: string) => {
    if (/^\/(quit|exit|bye)$/i.test(text)) {
      setDirectOutput(prev => [...prev, 'CoCo signing off.']);
      taskQueue?.stop();
      if (sessionManager) await sessionManager.killAll();
      await orchestrator.shutdown();
      exit();
      return;
    }

    setInputHistory(prev => [...prev, text]);
    setIsProcessing(true);
    setDirectOutput(prev => [...prev, `> ${text}`]);

    try {
      await orchestrator.handleInput(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setDirectOutput(prev => [...prev, `Error: ${msg}`]);
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  }, [orchestrator, sessionManager, taskQueue, exit]);

  // --- Layout ---
  if (!ready) return null;  // Prevent flash of empty UI on first render

  return (
    <Box flexDirection="column" width="100%">
      {/* Status bar */}
      <StatusBar
        project={project}
        branch={branch}
        activeSessions={activeSessions}
        queueDepth={queueDepth}
        maxConcurrency={maxConcurrency}
        skillCount={skills.size}
        voiceState={voiceState}
        message={statusMessage}
      />

      {/* Dashboard: session panels (Phase 2) */}
      {sessionManager ? (
        <Dashboard sessionManager={sessionManager} />
      ) : null}

      {/* Direct output area (non-session output) */}
      <Box flexDirection="column" paddingX={1} flexGrow={1}>
        {directOutput.length === 0 && !isProcessing ? (
          <Box flexDirection="column" paddingY={1}>
            <Text color="cyan" bold>Welcome to CoCo</Text>
            <Text dimColor>Your conversational terminal assistant. Type naturally or use /commands.</Text>
            <Text> </Text>
            <Text dimColor>  <Text color="white">Try:</Text>  "research OAuth patterns"  |  "review the auth service"  |  /help</Text>
            <Text dimColor>  <Text color="white">Voice:</Text> /voice on  then press F5 to talk</Text>
            <Text dimColor>  <Text color="white">Proactive:</Text> /proactive on  to watch files for suggestions</Text>
            <Text dimColor>  <Text color="white">Quit:</Text>  /quit  or Ctrl+C twice</Text>
          </Box>
        ) : (
          directOutput.slice(-20).map((line, i) => (
            <Text key={i} wrap="wrap">
              {line.startsWith('> ') ? (
                <Text><Text color="cyan" bold>&gt; </Text><Text>{line.slice(2)}</Text></Text>
              ) : line.startsWith('Error:') ? (
                <Text color="red">{line}</Text>
              ) : line.startsWith('[voice]') ? (
                <Text color="magenta">{line}</Text>
              ) : (
                <Text>{line}</Text>
              )}
            </Text>
          ))
        )}
      </Box>

      {/* Phase 5: Suggestion bar (above command input) */}
      <SuggestionBar
        suggestion={activeSuggestion}
        onAccept={handleSuggestionAccept}
        onDismiss={handleSuggestionDismiss}
        visible={!isProcessing}
      />

      {/* Command input */}
      <CommandInput
        onSubmit={handleSubmit}
        history={inputHistory}
        disabled={isProcessing}
      />
    </Box>
  );
};
