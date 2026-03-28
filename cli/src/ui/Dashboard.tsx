import React, { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { SessionPanel } from './SessionPanel.js';
import type { Session, SessionManager } from '../core/session-manager.js';

interface DashboardProps {
  sessionManager: SessionManager;
}

export const Dashboard: React.FC<DashboardProps> = ({ sessionManager }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());

  // Subscribe to session manager events
  useEffect(() => {
    const updateSessions = () => {
      const all = sessionManager.getAll();
      // Sort: running first, then queued, then complete, then error
      const statusOrder: Record<string, number> = {
        running: 0,
        'rate-limited': 1,
        queued: 2,
        detached: 3,
        complete: 4,
        error: 5,
        interrupted: 6,
      };
      all.sort((a, b) => (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9));
      setSessions(all);
    };

    // Throttled version for high-frequency events (sessionOutput).
    let throttleTimer: ReturnType<typeof setTimeout> | null = null;
    let pendingUpdate = false;
    const throttledUpdateSessions = () => {
      if (throttleTimer) {
        pendingUpdate = true;
        return;
      }
      updateSessions();
      throttleTimer = setTimeout(() => {
        throttleTimer = null;
        if (pendingUpdate) {
          pendingUpdate = false;
          updateSessions();
        }
      }, 250);
    };

    sessionManager.on('sessionSpawned', updateSessions);
    sessionManager.on('sessionComplete', updateSessions);
    sessionManager.on('sessionError', updateSessions);
    sessionManager.on('sessionDetached', updateSessions);
    sessionManager.on('sessionOutput', throttledUpdateSessions);
    sessionManager.on('sessionLayerChange', throttledUpdateSessions);
    sessionManager.on('sessionProgress', throttledUpdateSessions);

    // Initial load
    updateSessions();

    return () => {
      if (throttleTimer) clearTimeout(throttleTimer);
      sessionManager.off('sessionSpawned', updateSessions);
      sessionManager.off('sessionComplete', updateSessions);
      sessionManager.off('sessionError', updateSessions);
      sessionManager.off('sessionDetached', updateSessions);
      sessionManager.off('sessionOutput', throttledUpdateSessions);
      sessionManager.off('sessionLayerChange', throttledUpdateSessions);
      sessionManager.off('sessionProgress', throttledUpdateSessions);
    };
  }, [sessionManager]);

  // Keyboard navigation for session panels
  useInput((input, key) => {
    if (sessions.length === 0) return;

    // Tab / Shift+Tab to navigate between sessions
    if (key.tab) {
      setFocusedIndex(prev =>
        key.shift
          ? (prev - 1 + sessions.length) % sessions.length
          : (prev + 1) % sessions.length
      );
      return;
    }

    // Enter to toggle expand/collapse of focused session
    if (key.return && sessions[focusedIndex]) {
      const sessionId = sessions[focusedIndex].id;
      setExpandedSessions(prev => {
        const next = new Set(prev);
        if (next.has(sessionId)) {
          next.delete(sessionId);
        } else {
          next.add(sessionId);
        }
        return next;
      });
      return;
    }

    // 'e' to expand all, 'c' to collapse all
    if (input === 'e') {
      setExpandedSessions(new Set(sessions.map(s => s.id)));
      return;
    }
    if (input === 'c') {
      setExpandedSessions(new Set());
      return;
    }
  });

  if (sessions.length === 0) {
    return null;  // Welcome screen in App.tsx handles empty state
  }

  // Auto-expand running sessions
  const effectiveExpanded = new Set(expandedSessions);
  for (const session of sessions) {
    if (session.status === 'running') {
      effectiveExpanded.add(session.id);
    }
  }

  return (
    <Box flexDirection="column" flexGrow={1}>
      {/* Navigation hint */}
      <Box paddingX={1}>
        <Text dimColor>
          Tab: navigate | Enter: expand/collapse | e: expand all | c: collapse all
        </Text>
      </Box>

      {/* Session panels */}
      {sessions.map((session, index) => (
        <SessionPanel
          key={session.id}
          session={session}
          isExpanded={effectiveExpanded.has(session.id)}
          isFocused={index === focusedIndex}
          onToggle={() => {
            setExpandedSessions(prev => {
              const next = new Set(prev);
              if (next.has(session.id)) {
                next.delete(session.id);
              } else {
                next.add(session.id);
              }
              return next;
            });
          }}
        />
      ))}
    </Box>
  );
};
