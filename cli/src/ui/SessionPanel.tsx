import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import type { Session } from '../core/session-manager.js';

interface SessionPanelProps {
  session: Session;
  isExpanded: boolean;
  isFocused: boolean;
  onToggle: () => void;
  maxOutputLines?: number;
}

// --- Status color mapping ---
const STATUS_COLORS: Record<string, string> = {
  queued: 'gray',
  running: 'yellow',
  complete: 'green',
  error: 'red',
  'rate-limited': 'magenta',
  interrupted: 'red',
  detached: 'blue',
};

// --- Status icons ---
const STATUS_ICONS: Record<string, string> = {
  queued: '...',
  running: '>>>',
  complete: '[ok]',
  error: '[!!]',
  'rate-limited': '[rl]',
  interrupted: '[--]',
  detached: '[dh]',
};

// --- Elapsed time formatter ---
function formatElapsed(startedAt: number, completedAt: number | null): string {
  const end = completedAt || Date.now();
  const seconds = Math.floor((end - startedAt) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSec = seconds % 60;
  if (minutes < 60) return `${minutes}m${remainingSec}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h${minutes % 60}m`;
}

export const SessionPanel: React.FC<SessionPanelProps> = ({
  session,
  isExpanded,
  isFocused,
  onToggle,
  maxOutputLines = 20,
}) => {
  // Force re-render every second while running so elapsed time updates live
  const [, setTick] = useState(0);
  useEffect(() => {
    if (session.status !== 'running' && session.status !== 'queued') return;
    const interval = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, [session.status]);

  const statusColor = STATUS_COLORS[session.status] || 'white';
  const statusIcon = STATUS_ICONS[session.status] || '   ';
  const elapsed = formatElapsed(session.startedAt, session.completedAt);

  // Layer progress display for /team pipelines
  const layerDisplay = session.currentLayer
    ? `L${session.currentLayer} ${session.layerName || ''}`
    : session.skill;

  const progressDisplay = session.progress || '';

  // Collapsed: one-line summary
  if (!isExpanded) {
    return (
      <Box paddingX={1}>
        <Text color={statusColor}>{statusIcon} </Text>
        <Text bold={isFocused} color={isFocused ? 'cyan' : undefined}>
          [{session.skill}]
        </Text>
        <Text> {layerDisplay} </Text>
        {progressDisplay ? <Text dimColor>{progressDisplay} </Text> : null}
        <Text dimColor>
          {'.'.repeat(Math.max(0, 30 - layerDisplay.length - progressDisplay.length))}
        </Text>
        <Text dimColor> {elapsed}</Text>
        <Text dimColor> {isExpanded ? '(^)' : '(v)'}</Text>
      </Box>
    );
  }

  // Expanded: show last N lines of output
  const visibleOutput = session.outputBuffer.slice(-maxOutputLines);

  return (
    <Box flexDirection="column" paddingX={1}>
      {/* Header line */}
      <Box>
        <Text color={statusColor}>{statusIcon} </Text>
        <Text bold color={isFocused ? 'cyan' : undefined}>
          [{session.skill}]
        </Text>
        <Text> {layerDisplay} </Text>
        {progressDisplay ? <Text dimColor>{progressDisplay} </Text> : null}
        <Text dimColor> {elapsed}</Text>
        <Text dimColor> (^)</Text>
      </Box>

      {/* Layer progress bar for /team pipelines */}
      {session.currentLayer ? (
        <Box paddingLeft={2}>
          {[1, 2, 3, 4].map(layer => {
            const isActive = layer === session.currentLayer;
            const isDone = layer < (session.currentLayer || 0);
            const name = ['Research', 'Execute', 'Review', 'Synthesis'][layer - 1];
            return (
              <Box key={layer} marginRight={1}>
                <Text
                  color={isDone ? 'green' : isActive ? 'yellow' : 'gray'}
                  bold={isActive}
                >
                  L{layer}
                </Text>
                <Text
                  color={isDone ? 'green' : isActive ? 'yellow' : 'gray'}
                  dimColor={!isActive && !isDone}
                >
                  {' '}{name}
                </Text>
              </Box>
            );
          })}
        </Box>
      ) : null}

      {/* Output lines */}
      <Box flexDirection="column" paddingLeft={4} borderStyle="single" borderColor="gray">
        {visibleOutput.length === 0 ? (
          <Text dimColor>Waiting for output...</Text>
        ) : null}
        {visibleOutput.map((line, i) => (
          <Text key={i} wrap="truncate-end">
            {line}
          </Text>
        ))}
      </Box>
    </Box>
  );
};
