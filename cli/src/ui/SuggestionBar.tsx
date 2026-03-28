/**
 * Phase 5: Suggestion Bar
 *
 * Non-intrusive bar above the command input that shows proactive suggestions.
 * - Enter = accept suggestion, dispatch to orchestrator
 * - Esc = dismiss suggestion
 * - Auto-dismiss after TTL or when user starts typing
 * - Dim yellow text for non-intrusiveness
 */

import React, { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import type { Suggestion } from '../proactive/types.js';

interface SuggestionBarProps {
  suggestion: Suggestion | null;
  onAccept: () => void;
  onDismiss: () => void;
  visible: boolean;
}

export const SuggestionBar: React.FC<SuggestionBarProps> = ({
  suggestion,
  onAccept,
  onDismiss,
  visible,
}) => {
  const [fadeIn, setFadeIn] = useState(true);

  // Fade-in effect: dim for 500ms, then normal
  useEffect(() => {
    if (!suggestion) return;
    setFadeIn(true);
    const timer = setTimeout(() => setFadeIn(false), 500);
    return () => clearTimeout(timer);
  }, [suggestion?.id]);

  // Handle Enter/Esc keys (only when suggestion is visible and active)
  useInput((input, key) => {
    if (!suggestion || !visible) return;

    if (key.return) {
      onAccept();
    } else if (key.escape) {
      onDismiss();
    }
  }, { isActive: visible && suggestion !== null });

  if (!suggestion || !visible) return null;

  return (
    <Box
      paddingX={1}
      borderStyle="single"
      borderColor="yellow"
    >
      <Text color="yellow" dimColor={fadeIn}>
        {'* '}
      </Text>
      <Text color="yellow" dimColor={fadeIn} wrap="truncate-end">
        {suggestion.text}
      </Text>
      <Text dimColor>
        {' [Enter/Esc]'}
      </Text>
    </Box>
  );
};
