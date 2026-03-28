import { useState, useMemo } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Copy, Check, Columns, AlignJustify } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface DiffViewerProps {
  improvementId: string;
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type DiffLineType = 'add' | 'remove' | 'header' | 'context';
type ViewMode = 'unified' | 'split';

interface DiffLine {
  idx: number;
  line: string;
  type: DiffLineType;
}

interface FileDiff {
  filename: string;
  lines: DiffLine[];
}

function classifyLine(line: string): DiffLineType {
  if (line.startsWith('+++') || line.startsWith('---')) return 'header';
  if (line.startsWith('@@')) return 'header';
  if (line.startsWith('diff ')) return 'header';
  if (line.startsWith('+')) return 'add';
  if (line.startsWith('-')) return 'remove';
  return 'context';
}

function parseDiffIntoFiles(raw: string): FileDiff[] {
  const allLines = raw.split('\n');
  const files: FileDiff[] = [];
  let currentFile: FileDiff | null = null;
  let lineIdx = 0;

  for (const line of allLines) {
    if (line.startsWith('diff --git')) {
      // Extract filename from "diff --git a/foo.ts b/foo.ts"
      const match = line.match(/diff --git a\/(.*?) b\/(.*)/);
      const filename = match ? match[2] : line;
      currentFile = { filename, lines: [] };
      files.push(currentFile);
    }

    const type = classifyLine(line);
    if (currentFile) {
      currentFile.lines.push({ idx: lineIdx, line, type });
    } else {
      // Lines before any diff header — create a default file
      if (files.length === 0) {
        currentFile = { filename: 'Changes', lines: [] };
        files.push(currentFile);
      }
      currentFile!.lines.push({ idx: lineIdx, line, type });
    }
    lineIdx++;
  }

  return files.length > 0 ? files : [{ filename: 'Changes', lines: allLines.map((line, idx) => ({ idx, line, type: classifyLine(line) })) }];
}

// Detect language from filename for syntax class
function langClass(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  const map: Record<string, string> = {
    ts: 'lang-typescript', tsx: 'lang-tsx', js: 'lang-javascript', jsx: 'lang-jsx',
    py: 'lang-python', rs: 'lang-rust', go: 'lang-go', sql: 'lang-sql',
    json: 'lang-json', yaml: 'lang-yaml', yml: 'lang-yaml', toml: 'lang-toml',
    md: 'lang-markdown', css: 'lang-css', html: 'lang-html', sh: 'lang-shell',
  };
  return map[ext] ?? '';
}

// ------------- Split View Logic -----------------

interface SplitPair {
  left: DiffLine | null;
  right: DiffLine | null;
  leftNum: number | null;
  rightNum: number | null;
}

function buildSplitPairs(lines: DiffLine[]): SplitPair[] {
  const pairs: SplitPair[] = [];
  let leftNum = 0;
  let rightNum = 0;
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.type === 'header') {
      // Hunk header — try to parse line numbers
      const hunkMatch = line.line.match(/@@ -(\d+)/);
      if (hunkMatch) {
        const rightMatch = line.line.match(/\+(\d+)/);
        leftNum = parseInt(hunkMatch[1], 10) - 1;
        rightNum = rightMatch ? parseInt(rightMatch[1], 10) - 1 : leftNum;
      }
      pairs.push({ left: line, right: line, leftNum: null, rightNum: null });
      i++;
      continue;
    }

    if (line.type === 'remove') {
      // Collect consecutive removes and adds to pair them
      const removes: DiffLine[] = [];
      while (i < lines.length && lines[i].type === 'remove') {
        removes.push(lines[i]);
        i++;
      }
      const adds: DiffLine[] = [];
      while (i < lines.length && lines[i].type === 'add') {
        adds.push(lines[i]);
        i++;
      }
      const maxLen = Math.max(removes.length, adds.length);
      for (let j = 0; j < maxLen; j++) {
        const rm = j < removes.length ? removes[j] : null;
        const ad = j < adds.length ? adds[j] : null;
        pairs.push({
          left: rm,
          right: ad,
          leftNum: rm ? ++leftNum : null,
          rightNum: ad ? ++rightNum : null,
        });
      }
      continue;
    }

    if (line.type === 'add') {
      rightNum++;
      pairs.push({ left: null, right: line, leftNum: null, rightNum });
      i++;
      continue;
    }

    // Context line
    leftNum++;
    rightNum++;
    pairs.push({ left: line, right: line, leftNum, rightNum });
    i++;
  }

  return pairs;
}

// ------------- Unified View -----------------

function UnifiedView({ lines, lang }: { lines: DiffLine[]; lang: string }) {
  return (
    <pre className={cn('text-xs font-mono leading-relaxed', lang)}>
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
  );
}

// ------------- Split View -----------------

function SplitView({ lines, lang }: { lines: DiffLine[]; lang: string }) {
  const pairs = useMemo(() => buildSplitPairs(lines), [lines]);

  return (
    <div className={cn('text-xs font-mono leading-relaxed', lang)}>
      {pairs.map((pair, i) => {
        const isHeader = pair.left?.type === 'header';

        if (isHeader) {
          return (
            <div key={i} className="bg-blue-500/10 text-blue-400 font-semibold px-4 py-0.5">
              {pair.left!.line}
            </div>
          );
        }

        return (
          <div key={i} className="flex">
            {/* Left (old) */}
            <div
              className={cn(
                'flex-1 px-3 py-0.5 border-r border-border min-w-0 overflow-hidden',
                pair.left?.type === 'remove' && 'bg-red-500/10 text-red-400',
                !pair.left && 'bg-muted/20',
                pair.left?.type === 'context' && 'text-muted-foreground',
              )}
            >
              <span className="select-none text-muted-foreground/50 inline-block w-8 text-right mr-2">
                {pair.leftNum ?? ''}
              </span>
              <span className="break-all">{pair.left?.line ?? ''}</span>
            </div>
            {/* Right (new) */}
            <div
              className={cn(
                'flex-1 px-3 py-0.5 min-w-0 overflow-hidden',
                pair.right?.type === 'add' && 'bg-green-500/10 text-green-400',
                !pair.right && 'bg-muted/20',
                pair.right?.type === 'context' && 'text-muted-foreground',
              )}
            >
              <span className="select-none text-muted-foreground/50 inline-block w-8 text-right mr-2">
                {pair.rightNum ?? ''}
              </span>
              <span className="break-all">{pair.right?.line ?? ''}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ------------- Main Component -----------------

export function DiffViewer({ improvementId, title, open, onOpenChange }: DiffViewerProps) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('unified');
  const [activeFileIdx, setActiveFileIdx] = useState(0);

  const { data: diffData, isLoading } = useQuery({
    queryKey: ['self-improve', 'diff', improvementId],
    queryFn: () => apiFetch<{ diff: string }>(`/self-improve/improvements/${improvementId}/diff`),
    enabled: open,
  });

  const diffText = diffData?.diff ?? '';
  const files = useMemo(() => parseDiffIntoFiles(diffText), [diffText]);
  const activeFile = files[activeFileIdx] ?? files[0];

  async function handleCopy() {
    if (!diffText) return;
    await navigator.clipboard.writeText(diffText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-[5%] left-1/2 -translate-x-1/2 z-50 w-full max-w-5xl max-h-[90vh] bg-card border border-border rounded-xl shadow-xl animate-fade-in focus:outline-none flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
            <Dialog.Title className="text-sm font-semibold text-foreground truncate">
              Diff: {title}
            </Dialog.Title>
            <div className="flex items-center gap-2">
              {/* View mode toggle */}
              <div className="flex items-center bg-muted/50 rounded-lg p-0.5">
                <button
                  onClick={() => setViewMode('unified')}
                  className={cn(
                    'flex items-center gap-1 px-2.5 py-1 rounded-md text-xs transition-colors',
                    viewMode === 'unified'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                  title="Unified view"
                >
                  <AlignJustify size={12} />
                  Unified
                </button>
                <button
                  onClick={() => setViewMode('split')}
                  className={cn(
                    'flex items-center gap-1 px-2.5 py-1 rounded-md text-xs transition-colors',
                    viewMode === 'split'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                  title="Split view"
                >
                  <Columns size={12} />
                  Split
                </button>
              </div>

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

          {/* File tabs */}
          {files.length > 1 && (
            <div className="flex items-center gap-0 overflow-x-auto border-b border-border bg-muted/20 shrink-0">
              {files.map((file, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveFileIdx(idx)}
                  className={cn(
                    'px-4 py-2 text-xs font-mono whitespace-nowrap border-b-2 transition-colors',
                    idx === activeFileIdx
                      ? 'border-accent text-accent bg-card'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40',
                  )}
                >
                  {file.filename.split('/').pop()}
                  <span className="ml-1.5 text-muted-foreground/50 hidden sm:inline">
                    {file.filename.includes('/') ? file.filename.substring(0, file.filename.lastIndexOf('/') + 1) : ''}
                  </span>
                </button>
              ))}
            </div>
          )}

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
            ) : viewMode === 'unified' ? (
              <UnifiedView lines={activeFile?.lines ?? []} lang={langClass(activeFile?.filename ?? '')} />
            ) : (
              <SplitView lines={activeFile?.lines ?? []} lang={langClass(activeFile?.filename ?? '')} />
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
