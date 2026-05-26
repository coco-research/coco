import DOMPurify from 'dompurify';
import { useCallback } from 'react';
import { parseMermaidSegments, hasMermaidBlocks } from '../../lib/mermaid';
import { renderMarkdownToHtml } from '../../lib/markdown';
import { MermaidDiagram } from './MermaidDiagram';
import { cn } from '../../lib/utils';

interface RichContentProps {
  text: string;
  className?: string;
  /** Monospace styling for non-mermaid text (logs, raw output) */
  mono?: boolean;
  /** Render non-diagram text as sanitized HTML with markdown processing */
  html?: boolean;
  /** DOMPurify config overrides for HTML mode */
  purifyConfig?: DOMPurify.Config;
}

const DEFAULT_PURIFY_CONFIG: DOMPurify.Config = {
  ADD_ATTR: ['data-code', 'aria-label', 'type'],
  ADD_TAGS: ['svg', 'rect', 'path'],
  ADD_URI_SAFE_ATTR: [
    'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap',
    'stroke-linejoin', 'd', 'rx', 'ry', 'xmlns',
  ],
};

/**
 * Unified content renderer that detects mermaid fenced blocks and
 * renders them as beautiful-mermaid SVGs inline with the text.
 *
 * - `html` mode: markdown → sanitized HTML (like chat MessageBubble)
 * - `mono` mode: monospace pre-formatted (like agent logs)
 * - default: plain text with whitespace preserved
 */
export function RichContent({
  text,
  className,
  mono = false,
  html = false,
  purifyConfig,
}: RichContentProps) {
  // Delegate click handler for copy buttons in rendered code blocks.
  // Replaces only the label text node — the SVG icon is preserved across
  // the 1.5s "Copied!" feedback. `getAttribute('data-code')` auto-decodes
  // the HTML entities the renderer emitted, so the clipboard receives the
  // original source characters.
  const handleCopyClick = useCallback((e: React.MouseEvent) => {
    const target = (e.target as HTMLElement).closest('.code-copy-btn') as HTMLElement | null;
    if (!target) return;
    const code = target.getAttribute('data-code') ?? '';
    const label = target.querySelector('.code-copy-label');
    const originalLabel = label?.textContent ?? 'Copy';
    void navigator.clipboard.writeText(code).then(
      () => {
        if (label) label.textContent = 'Copied!';
        target.setAttribute('aria-label', 'Code copied');
        window.setTimeout(() => {
          if (label) label.textContent = originalLabel;
          target.setAttribute('aria-label', 'Copy code');
        }, 1500);
      },
      () => {
        if (label) label.textContent = 'Failed';
        window.setTimeout(() => {
          if (label) label.textContent = originalLabel;
        }, 1500);
      },
    );
  }, []);

  // Fast path: no mermaid blocks → render directly without segmenting
  if (!hasMermaidBlocks(text)) {
    return (
      <div onClick={html ? handleCopyClick : undefined} className={className}>
        <TextBlock text={text} mono={mono} html={html} purifyConfig={purifyConfig} />
      </div>
    );
  }

  const segments = parseMermaidSegments(text);

  return (
    <div onClick={html ? handleCopyClick : undefined} className={className}>
      {segments.map((seg, i) => {
        if (seg.type === 'mermaid') {
          return <MermaidDiagram key={i} code={seg.code} />;
        }

        if (seg.type === 'code') {
          // Re-wrap as fenced block so the markdown renderer handles syntax
          // highlighting and copy buttons. Double-parse is intentional: the
          // mermaid parser extracts ALL fenced blocks to find mermaid ones,
          // and non-mermaid blocks are re-assembled for the markdown path.
          const fenced = `\`\`\`${seg.lang}\n${seg.code}\n\`\`\``;
          return (
            <TextBlock key={i} text={fenced} mono={mono} html={html} purifyConfig={purifyConfig} />
          );
        }

        return (
          <TextBlock key={i} text={seg.content} mono={mono} html={html} purifyConfig={purifyConfig} />
        );
      })}
    </div>
  );
}

/** Internal renderer for a single text segment. */
function TextBlock({
  text,
  mono,
  html,
  purifyConfig,
}: {
  text: string;
  mono: boolean;
  html: boolean;
  purifyConfig?: DOMPurify.Config;
}) {
  if (!text.trim()) return null;

  if (html) {
    const rendered = renderMarkdownToHtml(text);
    const clean = DOMPurify.sanitize(rendered, purifyConfig ?? DEFAULT_PURIFY_CONFIG);
    return <span dangerouslySetInnerHTML={{ __html: clean }} />;
  }

  if (mono) {
    return (
      <div className={cn(
        'text-xs text-foreground/90 leading-relaxed whitespace-pre-wrap',
        'font-mono bg-muted/30 rounded-lg p-3',
      )}>
        {text}
      </div>
    );
  }

  return (
    <span className="whitespace-pre-wrap">{text}</span>
  );
}
