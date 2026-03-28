import { useQuery } from '@tanstack/react-query';
import DOMPurify from 'dompurify';
import { apiFetch } from '../../lib/api';
import { Brain } from 'lucide-react';

interface BrainData {
  people?: Record<string, unknown>;
  rules?: unknown[];
  sessions?: unknown[];
  [key: string]: unknown;
}

function SyntaxHighlight({ json }: { json: string }) {
  // Simple syntax highlighting: keys, strings, numbers, booleans
  const lines = json.split('\n');

  return (
    <pre className="text-sm font-mono leading-relaxed overflow-x-auto p-4">
      {lines.map((line, i) => {
        const highlighted = line
          // Keys (before colon)
          .replace(
            /^(\s*)"([^"]+)":/,
            '$1<span class="text-accent">"$2"</span>:',
          )
          // String values
          .replace(
            /:\s*"([^"]*)"/g,
            ': <span class="text-foreground">"$1"</span>',
          )
          // Numbers
          .replace(
            /:\s*(\d+\.?\d*)/g,
            ': <span class="text-warning">$1</span>',
          )
          // Booleans
          .replace(
            /:\s*(true|false)/g,
            ': <span class="text-info">$1</span>',
          )
          // null
          .replace(
            /:\s*(null)/g,
            ': <span class="text-muted-foreground">$1</span>',
          );

        return (
          <div key={i} className="hover:bg-accent/50/30">
            <span
              className="text-muted-foreground select-none mr-4 inline-block w-8 text-right"
            >
              {i + 1}
            </span>
            <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(highlighted) }} />
          </div>
        );
      })}
    </pre>
  );
}

export function BrainViewer() {
  const { data: brain, isLoading } = useQuery<BrainData>({
    queryKey: ['brain'],
    queryFn: () => apiFetch<BrainData>('/brain'),
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="bg-accent/50 rounded h-8 w-48" />
        <div className="bg-accent/50 rounded h-96" />
      </div>
    );
  }

  if (!brain) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Brain size={48} className="mb-3 opacity-40" />
        <p className="text-lg font-medium">No brain data found.</p>
      </div>
    );
  }

  const peopleCount = brain.people ? Object.keys(brain.people).length : 0;
  const rulesCount = Array.isArray(brain.rules) ? brain.rules.length : 0;
  const sessionsCount = Array.isArray(brain.sessions) ? brain.sessions.length : 0;

  const jsonString = JSON.stringify(brain, null, 2);

  return (
    <div className="space-y-4">
      {/* Stats summary */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">People:</span>
          <span className="text-sm font-mono font-medium text-foreground">{peopleCount}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Rules:</span>
          <span className="text-sm font-mono font-medium text-foreground">{rulesCount}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Sessions:</span>
          <span className="text-sm font-mono font-medium text-foreground">{sessionsCount}</span>
        </div>
      </div>

      {/* JSON viewer */}
      <div className="bg-card border border-border rounded-xl overflow-hidden max-h-[600px] overflow-y-auto">
        <div className="px-4 py-2 border-b border-border flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            brain.json
          </span>
          <span className="text-xs text-muted-foreground">
            {(jsonString.length / 1024).toFixed(1)} KB
          </span>
        </div>
        <SyntaxHighlight json={jsonString} />
      </div>
    </div>
  );
}
