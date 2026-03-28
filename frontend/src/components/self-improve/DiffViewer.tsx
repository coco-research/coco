import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Copy, Check } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface DiffViewerProps {
  improvementId: string;
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function parseDiffLines(raw: string) {
  return raw.split('\n').map((line, idx) => {
    let type: 'add' | 'remove' | 'header' | 'context' = 'context';
    if (line.startsWith('+++') || line.startsWith('---')) {
      type = 'header';
    } else if (line.startsWith('@@')) {
      type = 'header';
    } else if (line.startsWith('+')) {
      type = 'add';
    } else if (line.startsWith('-')) {
      type = 'remove';
    } else if (line.startsWith('diff ')) {
      type = 'header';
    }
    return { idx, line, type };
  });
}

export function DiffViewer({ improvementId, title, open, onOpenChange }: DiffViewerProps) {
  const [copied, setCopied] = useState(false);

  const { data: diffText, isLoading } = useQuery({
    queryKey: ['self-improve', 'diff', improvementId],
    queryFn: () => apiFetch<string>(`/self-improve/improvements/${improvementId}/diff`),
    enabled: open,
  });

  async function handleCopy() {
    if (!diffText) return;
    await navigator.clipboard.writeText(diffText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const lines = diffText ? parseDiffLines(diffText) : [];

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-[5%] left-1/2 -translate-x-1/2 z-50 w-full max-w-4xl max-h-[90vh] bg-card border border-border rounded-xl shadow-xl animate-fade-in focus:outline-none flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
            <Dialog.Title className="text-sm font-semibold text-foreground truncate">
              Diff: {title}
            </Dialog.Title>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy'}
              </button>
              <Dialog.Close className="text-muted-foreground hover:text-foreground transition-colors">
                <X size={18} />
              </Dialog.Close>
            </div>
          </div>

          {/* Diff content */}
          <div className="overflow-auto flex-1 p-0">
            {isLoading ? (
              <div className="flex items-center justify-center h-40">
                <div className="h-6 w-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : !diffText ? (
              <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
                No diff available
              </div>
            ) : (
              <pre className="text-xs font-mono leading-relaxed">
                {lines.map(({ idx, line, type }) => (
                  <div
                    key={idx}
                    className={cn(
                      'px-4 py-0.5',
                      type === 'add' && 'bg-green-500/10 text-green-400',
                      type === 'remove' && 'bg-red-500/10 text-red-400',
                      type === 'header' && 'bg-blue-500/10 text-blue-400 font-semibold',
                      type === 'context' && 'text-muted-foreground',
                    )}
                  >
                    <span className="select-none text-muted-foreground/50 inline-block w-10 text-right mr-3">
                      {idx + 1}
                    </span>
                    {line}
                  </div>
                ))}
              </pre>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
