import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';

interface CommandInputProps {
  onSubmit: (text: string) => void;
  history: string[];
  disabled?: boolean;
}

export const CommandInput: React.FC<CommandInputProps> = ({
  onSubmit,
  history,
  disabled = false,
}) => {
  const [value, setValue] = useState('');
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cursorVisible, setCursorVisible] = useState(true);

  // Blink cursor
  React.useEffect(() => {
    const interval = setInterval(() => setCursorVisible(v => !v), 500);
    return () => clearInterval(interval);
  }, []);

  useInput((input, key) => {
    if (disabled) return;

    if (key.return) {
      if (value.trim()) {
        onSubmit(value.trim());
        setValue('');
        setHistoryIndex(-1);
      }
      return;
    }

    if (key.backspace || key.delete) {
      setValue(v => v.slice(0, -1));
      return;
    }

    if (key.upArrow) {
      if (history.length === 0) return;
      const newIndex = Math.min(historyIndex + 1, history.length - 1);
      setHistoryIndex(newIndex);
      setValue(history[history.length - 1 - newIndex] || '');
      return;
    }

    if (key.downArrow) {
      if (historyIndex <= 0) {
        setHistoryIndex(-1);
        setValue('');
        return;
      }
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setValue(history[history.length - 1 - newIndex] || '');
      return;
    }

    // Ctrl+C is handled by Ink's exit
    if (key.escape) {
      setValue('');
      setHistoryIndex(-1);
      return;
    }

    // Regular character input
    if (input && !key.ctrl && !key.meta) {
      setValue(v => v + input);
    }
  });

  return (
    <Box flexDirection="column">
      <Box paddingX={1} borderStyle="single" borderColor={disabled ? 'gray' : 'cyan'} borderTop={true} borderBottom={false} borderLeft={false} borderRight={false}>
        <Text color={disabled ? 'gray' : 'cyan'} bold>{disabled ? '... ' : 'coco > '}</Text>
        <Text color={disabled ? 'gray' : undefined}>
          {value}
          {!disabled && (cursorVisible ? '\u2588' : ' ')}
        </Text>
        {disabled && <Text dimColor> processing</Text>}
      </Box>
    </Box>
  );
};
