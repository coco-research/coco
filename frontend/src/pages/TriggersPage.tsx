import { useState } from 'react';
import { Zap, Clock, Webhook, FolderSearch } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import { TriggerList, type Trigger } from '../components/triggers/TriggerList';
import { TriggerForm } from '../components/triggers/TriggerForm';

/**
 * Dedicated full-page view for the trigger/automation system.
 *
 * The TriggerList + TriggerForm components also render inside the
 * Settings "Automations" tab; this page surfaces them as a first-class
 * destination with summary counts so users can find automations
 * without drilling into Settings.
 */
export default function TriggersPage() {
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null);
  const [showForm, setShowForm] = useState(false);

  const { data: triggers = [] } = useQuery<Trigger[]>({
    queryKey: ['triggers'],
    queryFn: () => apiFetch<Trigger[]>('/triggers'),
    refetchInterval: 30_000,
  });

  const counts = {
    total: triggers.length,
    enabled: triggers.filter((t) => t.enabled).length,
    cron: triggers.filter((t) => t.trigger_type === 'cron').length,
    webhook: triggers.filter((t) => t.trigger_type === 'webhook').length,
    file_watch: triggers.filter((t) => t.trigger_type === 'file_watch').length,
  };

  const handleEdit = (t: Trigger) => {
    setEditingTrigger(t);
    setShowForm(true);
  };

  const handleDone = () => {
    setEditingTrigger(null);
    setShowForm(false);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-amber-400" />
          <div>
            <h2 className="text-sm font-semibold text-foreground">Triggers</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Automate actions based on schedules, webhooks, or file changes.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            setEditingTrigger(null);
            setShowForm((s) => !s);
          }}
          className="px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          {showForm && !editingTrigger ? 'Cancel' : 'New Trigger'}
        </button>
      </div>

      {/* Summary chips */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4 shrink-0">
        <SummaryChip label="Total" value={counts.total} />
        <SummaryChip label="Enabled" value={counts.enabled} tone="success" />
        <SummaryChip label="Cron" value={counts.cron} icon={Clock} />
        <SummaryChip label="Webhook" value={counts.webhook} icon={Webhook} />
        <SummaryChip label="File-watch" value={counts.file_watch} icon={FolderSearch} />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-6">
        <TriggerList onEdit={handleEdit} />

        {showForm && (
          <div className="border-t border-border pt-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">
              {editingTrigger ? `Edit "${editingTrigger.name}"` : 'New Trigger'}
            </h3>
            <TriggerForm editingTrigger={editingTrigger} onDone={handleDone} />
          </div>
        )}
      </div>
    </div>
  );
}

interface SummaryChipProps {
  label: string;
  value: number;
  tone?: 'default' | 'success';
  icon?: typeof Clock;
}

function SummaryChip({ label, value, tone = 'default', icon: Icon }: SummaryChipProps) {
  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-border bg-card">
      <div className="flex items-center gap-1.5 min-w-0">
        {Icon && <Icon size={12} className="text-muted-foreground shrink-0" />}
        <span className="text-[11px] text-muted-foreground truncate">{label}</span>
      </div>
      <span
        className={
          tone === 'success'
            ? 'text-sm font-semibold text-emerald-400'
            : 'text-sm font-semibold text-foreground'
        }
      >
        {value}
      </span>
    </div>
  );
}
