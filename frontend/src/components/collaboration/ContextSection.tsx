import React, { useState } from 'react';
import { ChevronRight, FileText, Pencil, Save, X } from 'lucide-react';
import { cn, timeAgo } from '../../lib/utils';
import { ROLE_META } from '../agents/AgentCard';

export interface ContextEntry {
  id: string;
  section: string;
  title: string | null;
  content: string;
  author_role: string;
  created_at: string;
}

export interface ContextSectionProps {
  entry: ContextEntry;
  onEdit?: (id: string, content: string) => void;
}

export const ContextSection = React.memo(function ContextSection({
  entry, onEdit,
}: ContextSectionProps) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(entry.content);
  const meta = ROLE_META[entry.author_role] ?? ROLE_META['custom'];

  const handleSave = () => {
    onEdit?.(entry.id, draft);
    setEditing(false);
  };

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-muted/50 transition-colors"
      >
        <ChevronRight size={14} className={cn('text-muted-foreground transition-transform', open && 'rotate-90')} />
        <FileText size={14} className="text-muted-foreground shrink-0" />
        <span className="text-sm font-medium text-foreground truncate flex-1">
          {entry.title ?? entry.section}
        </span>
        <span className={cn('text-[10px] px-1.5 py-0.5 rounded font-medium', meta.color)}>
          {meta.abbr}
        </span>
        <span className="text-[10px] text-muted-foreground">{timeAgo(entry.created_at)}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-border pt-3">
          {editing ? (
            <>
              <textarea
                className="w-full min-h-[120px] rounded-lg border border-border bg-background p-3 text-sm font-mono resize-y focus:outline-none focus:ring-1 focus:ring-accent"
                value={draft}
                onChange={e => setDraft(e.target.value)}
              />
              <div className="flex gap-2 mt-2">
                <button onClick={handleSave} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 transition-all">
                  <Save size={12} /> Save
                </button>
                <button onClick={() => { setDraft(entry.content); setEditing(false); }} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg text-muted-foreground hover:bg-muted transition-all">
                  <X size={12} /> Cancel
                </button>
              </div>
            </>
          ) : (
            <>
              <pre className="text-sm text-foreground whitespace-pre-wrap">{entry.content}</pre>
              {onEdit && (
                <button onClick={() => setEditing(true)} className="inline-flex items-center gap-1 mt-3 px-3 py-1.5 text-xs rounded-lg text-muted-foreground hover:bg-muted transition-all">
                  <Pencil size={12} /> Edit
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
});
