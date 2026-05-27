import { useRef, useState } from 'react';
import { cn } from '../../lib/utils';
import { RichContent } from '../shared/RichContent';

export type InlineActionType =
  | 'create_todo'
  | 'approve_decision'
  | 'open_project'
  | 'open_link';

export interface InlineAction {
  type: InlineActionType;
  label: string;
  payload?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  created_at: string;
  actions?: InlineAction[];
}

function formatTime(date: string): string {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  onAction?: (action: InlineAction) => void | Promise<void>;
}

export function MessageBubble({ message, isStreaming = false, onAction }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const contentRef = useRef<HTMLDivElement>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [doneActions, setDoneActions] = useState<Set<string>>(new Set());

  const actions = !isUser && !isStreaming ? message.actions ?? [] : [];

  const actionKey = (a: InlineAction, i: number) => `${a.type}:${i}`;

  const handleAction = async (a: InlineAction, key: string) => {
    if (!onAction || busyAction || doneActions.has(key)) return;
    setBusyAction(key);
    try {
      await onAction(a);
      setDoneActions((prev) => new Set(prev).add(key));
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {/* CoCo avatar for assistant */}
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-accent flex items-center justify-center mt-1">
          <span className="text-xs font-bold text-accent-foreground">C</span>
        </div>
      )}

      <div
        className={cn(
          'max-w-[70%] px-4 py-2',
          isUser
            ? 'bg-accent text-accent-foreground rounded-2xl rounded-br-sm'
            : 'bg-card border border-border rounded-2xl rounded-bl-sm',
        )}
      >
        <div
          ref={contentRef}
          className={cn(
            'text-sm leading-relaxed chat-content',
            isUser ? 'text-accent-foreground' : 'text-foreground',
          )}
        >
          <RichContent text={message.content} html />
          {isStreaming && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-accent animate-pulse rounded-sm align-text-bottom" />
          )}
        </div>
        {actions.length > 0 && (
          <div
            className="mt-2 -mb-1 flex flex-wrap gap-1.5"
            data-testid="inline-actions"
          >
            {actions.map((a, i) => {
              const key = actionKey(a, i);
              const isBusy = busyAction === key;
              const isDone = doneActions.has(key);
              return (
                <button
                  key={key}
                  type="button"
                  disabled={isBusy || isDone}
                  onClick={() => handleAction(a, key)}
                  className={cn(
                    'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5',
                    'text-xs font-medium transition-colors',
                    'border-border bg-background/60 text-muted-foreground',
                    'hover:bg-accent/40 hover:text-foreground',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                  )}
                  title={a.label}
                >
                  {isDone ? 'Done' : isBusy ? '...' : a.label}
                </button>
              );
            })}
          </div>
        )}
        <p className={cn(
          'text-xs mt-1 text-right',
          isUser ? 'text-accent-foreground/70' : 'text-muted-foreground',
        )}>
          {isStreaming ? (
            <span className="italic">Streaming...</span>
          ) : (
            <>
              {formatTime(message.created_at)}
              {message.model && <span className="ml-2 font-mono">{message.model}</span>}
            </>
          )}
        </p>
      </div>
    </div>
  );
}
