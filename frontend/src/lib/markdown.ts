/**
 * Lightweight markdown-ish renderer — no heavy deps.
 * Extracted from MessageBubble for reuse across components.
 */

export function renderMarkdownToHtml(raw: string): string {
  // Escape HTML first
  let html = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    const langLabel = lang
      ? `<span class="text-xs text-muted-foreground font-mono block mb-1">${lang}</span>`
      : '';
    const clipboardSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="code-copy-icon inline-block mr-1 align-[-1px] pointer-events-none"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>`;
    // data-code is HTML-attribute encoded; & and " need escaping. The `code` here is already
    // HTML-escaped by the top-of-function pass (so '<' is '&lt;'), which is correct for both
    // <code> content and as the attribute value source. We only need to escape '"' for the attr.
    const trimmed = code.trim();
    const attrEncoded = trimmed.replace(/"/g, '&quot;');
    return `<div class="relative group/code my-2"><pre class="bg-muted/50 font-mono text-sm p-3 rounded-lg overflow-x-auto">${langLabel}<code>${trimmed}</code></pre><button type="button" class="code-copy-btn absolute top-2 right-2 inline-flex items-center px-2 py-1 text-[10px] font-medium rounded bg-muted text-muted-foreground opacity-0 group-hover/code:opacity-100 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent hover:bg-accent hover:text-accent-foreground transition-all" aria-label="Copy code" data-code="${attrEncoded}">${clipboardSvg}<span class="code-copy-label">Copy</span></button></div>`;
  });

  // Inline code (`...`)
  html = html.replace(
    /`([^`]+)`/g,
    '<code class="bg-muted/50 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>',
  );

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
