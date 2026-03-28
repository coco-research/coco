import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';

export type VoiceStateLabel = 'off' | 'ready' | 'recording' | 'transcribing' | 'speaking' | 'unavailable';

interface StatusBarProps {
  project: string;
  branch: string;
  activeSessions: number;
  queueDepth: number;
  maxConcurrency: number;
  skillCount: number;
  voiceState?: VoiceStateLabel;
  message?: string;
  classificationConfidence?: number;
}

function VoiceIndicator({ state }: { state: VoiceStateLabel }): React.ReactElement | null {
  switch (state) {
    case 'off':
      return null;
    case 'ready':
      return <Text color="green"> MIC:ready </Text>;
    case 'recording':
      return <Text color="red" bold> MIC:REC </Text>;
    case 'transcribing':
      return <Text color="yellow"> MIC:... </Text>;
    case 'speaking':
      return <Text color="cyan"> TTS </Text>;
    case 'unavailable':
      return <Text dimColor> MIC:N/A </Text>;
  }
}

function SessionIndicator({ active, max, queue }: { active: number; max: number; queue: number }): React.ReactElement {
  if (active === 0 && queue === 0) {
    return <Text color="green"> idle </Text>;
  }
  const parts: string[] = [];
  if (active > 0) parts.push(`${active}/${max} running`);
  if (queue > 0) parts.push(`${queue} queued`);
  return <Text color="yellow"> {parts.join(' | ')} </Text>;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  project,
  branch,
  activeSessions,
  queueDepth,
  maxConcurrency,
  skillCount,
  voiceState,
  message,
  classificationConfidence,
}) => {
  const [clock, setClock] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(
        `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box flexDirection="column">
      {/* Main status bar */}
      <Box
        borderStyle="round"
        borderColor="cyan"
        paddingX={1}
        justifyContent="space-between"
      >
        <Text bold color="cyan">CoCo</Text>
        <Text> <Text color="white" bold>{project}</Text> <Text dimColor>({branch})</Text> </Text>
        <Text dimColor>{skillCount} skills</Text>
        <SessionIndicator active={activeSessions} max={maxConcurrency} queue={queueDepth} />

        {/* Phase 4: Classification confidence */}
        {classificationConfidence !== undefined && classificationConfidence > 0 ? (
          <Text color={classificationConfidence >= 0.7 ? 'green' : classificationConfidence >= 0.4 ? 'yellow' : 'red'}>
            conf:{(classificationConfidence * 100).toFixed(0)}%
          </Text>
        ) : null}

        {/* Voice state indicator */}
        {voiceState && voiceState !== 'off' && (
          <VoiceIndicator state={voiceState} />
        )}

        <Text dimColor>{clock}</Text>
      </Box>

      {/* Status message line (below bar, only when active) */}
      {message ? (
        <Box paddingX={2}>
          <Text color="gray" italic>{message}</Text>
        </Box>
      ) : null}
    </Box>
  );
};
