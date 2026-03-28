import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Pencil } from 'lucide-react';
import { cn } from '../../lib/utils';

interface InlineEditorProps {
  value: string;
  onSave: (newValue: string) => void | Promise<void>;
  className?: string;
  inputClassName?: string;
  placeholder?: string;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span';
  editable?: boolean;
  maxLength?: number;
}

export function InlineEditor({ value, onSave, className, inputClassName,
  placeholder = 'Click to edit...', as: Tag = 'span', editable = true, maxLength,
}: InlineEditorProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { setDraft(value); }, [value]);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const save = async () => {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === value) {
      setDraft(value);
      setEditing(false);
      return;
    }
    try {
      setSaving(true);
      await onSave(trimmed);
    } finally {
      setSaving(false);
      setEditing(false);
    }
  };

  const cancel = () => { setDraft(value); setEditing(false); };
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') { e.preventDefault(); void save(); }
    if (e.key === 'Escape') cancel();
  };

  if (editing && editable) {
    return (
      <input
        ref={inputRef}
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => void save()}
        maxLength={maxLength}
        className={cn(
          'bg-transparent outline-none border-b-2 border-accent w-full',
          saving && 'opacity-50',
          className,
          inputClassName,
        )}
      />
    );
  }

  return (
    <Tag
      className={cn(
        'group/inline inline-flex items-center gap-1.5 cursor-text',
        !value && 'text-muted-foreground',
        className,
      )}
      onClick={() => editable && setEditing(true)}
    >
      {value || placeholder}
      {editable && (
        <Pencil
          size={12}
          className="shrink-0 opacity-0 group-hover/inline:opacity-60 transition-opacity text-muted-foreground"
        />
      )}
    </Tag>
  );
}
