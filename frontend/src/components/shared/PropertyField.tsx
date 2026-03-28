import { useState } from 'react';
import { cn } from '../../lib/utils';

interface PropertyFieldProps {
  label: string;
  value: string | number | null;
  onSave?: (value: string) => void;
  type?: 'text' | 'select' | 'textarea' | 'readonly';
  options?: { value: string; label: string }[];
  placeholder?: string;
}

export function PropertyField({
  label,
  value,
  onSave,
  type = onSave ? 'text' : 'readonly',
  options,
  placeholder,
}: PropertyFieldProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(value ?? ''));

  const commit = () => {
    setEditing(false);
    if (draft !== String(value ?? '')) onSave?.(draft);
  };

  const display = String(value ?? '—');

  if (!editing || type === 'readonly') {
    return (
      <div className="mb-3">
        <span className="block text-xs text-muted-foreground mb-0.5">{label}</span>
        <span
          onClick={() => {
            if (type !== 'readonly' && onSave) {
              setDraft(String(value ?? ''));
              setEditing(true);
            }
          }}
          className={cn(
            'block text-sm text-foreground break-words',
            type !== 'readonly' && onSave && 'cursor-pointer hover:bg-accent/30 rounded px-1 -mx-1',
          )}
        >
          {display}
        </span>
      </div>
    );
  }

  if (type === 'select' && options) {
    return (
      <div className="mb-3">
        <span className="block text-xs text-muted-foreground mb-0.5">{label}</span>
        <select
          autoFocus
          value={draft}
          onChange={(e) => { setDraft(e.target.value); }}
          onBlur={commit}
          className="w-full text-sm bg-input border border-border rounded-md px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div className="mb-3">
        <span className="block text-xs text-muted-foreground mb-0.5">{label}</span>
        <textarea
          autoFocus
          rows={4}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          placeholder={placeholder}
          className="w-full text-sm bg-input border border-border rounded-md px-2 py-1 text-foreground resize-y focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
    );
  }

  return (
    <div className="mb-3">
      <span className="block text-xs text-muted-foreground mb-0.5">{label}</span>
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === 'Enter' && commit()}
        placeholder={placeholder}
        className="w-full text-sm bg-input border border-border rounded-md px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
      />
    </div>
  );
}
