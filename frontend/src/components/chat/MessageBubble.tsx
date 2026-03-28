import { useCallback, useRef } from 'react';
import DOMPurify from 'dompurify';
import { cn } from '../../lib/utils';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  created_at: string;
}

function formatTime(date: string): string {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/** Lightweight markdown-ish renderer — no heavy deps. */
function renderContent(raw: string): string {
  // Escape HTML first
  let html = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    const langLabel = lang ? `<span class="text-xs text-muted-foreground font-mono block mb-1">${lang}</span>` : '';
    const clipboardSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block mr-1 align-[-1px]"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>`;
    return `<div class="relative group/code my-2"><pre class="bg-muted/50 font-mono text-sm p-3 rounded-lg overflow-x-auto">${langLabel}<code>${code.trim()}</code></pre><button class="code-copy-btn absolute top-2 right-2 px-2 py-1 text-[10px] font-medium rounded bg-muted text-muted-foreground opacity-0 group-hover/code:opacity-100 hover:bg-accent hover:text-accent-foreground transition-all" data-code="${code.trim().replace(/"/g, '&quot;')}">${clipboardSvg}Copy</button></div>`;
  });

  // Inline code (`...`)
  html = html.replace(/`([^`]+)`/g, '<code class="bg-muted/50 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');

  // Bold (**...**)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic (*...*)
  html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

  // Links [text](url)
  html = html.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-accent underline hover:text-accent/80">$1</a>',
  );

  // Bullet lists: lines starting with "- "
  html = html.replace(/(^|\n)(- .+(?:\n- .+)*)/g, (_m, prefix, block) => {
    const items = block
      .split('\n')
      .map((line: string) => `<li class="ml-4">${line.replace(/^- /, '')}</li>`)
      .join('');
    return `${prefix}<ul class="list-disc list-inside my-1">${items}</ul>`;
  });

  // Line breaks (but not inside <pre>)
  html = html.replace(/\n/g, '<br/>');
  // Clean up extra <br/> inside pre blocks
  html = html.replace(/<pre([^>]*)>([\s\S]*?)<\/pre>/g, (_m, attrs, inner) => {
    return `<pre${attrs}>${inner.replace(/<br\/>/g, '\n')}</pre>`;
  });

  return html;
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const contentRef = useRef<HTMLDivElement>(null);

  // Delegate click handler for copy buttons inside rendered code blocks
  const handleCopyClick = useCallback((e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (!target.classList.contains('code-copy-btn')) return;
    const code = target.getAttribute('data-code') ?? '';
    navigator.clipboard.writeText(code).then(() => {
      target.textContent = 'Copied!';
      setTimeout(() => { target.textContent = 'Copy'; }, 1500);
    });
  }, []);

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
          onClick={handleCopyClick}
          className={cn(
            'text-sm leading-relaxed chat-content',
            isUser ? 'text-accent-foreground' : 'text-foreground',
          )}
        >
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(renderContent(message.content), { ADD_ATTR: ['data-code'], ADD_TAGS: ['svg', 'rect', 'path'], ADD_URI_SAFE_ATTR: ['viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'd', 'rx', 'ry', 'xmlns'] }) }} />
          {isStreaming && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-accent animate-pulse rounded-sm align-text-bottom" />
          )}
        </div>
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
