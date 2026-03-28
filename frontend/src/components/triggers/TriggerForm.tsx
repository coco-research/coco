import { useState, useEffect, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost, apiPatch } from '../../lib/api';
import type { Trigger } from './TriggerList';
import { cn } from '../../lib/utils';

type TriggerType = Trigger['trigger_type'];
type ActionType = Trigger['action_type'];

interface TriggerFormProps {
  editingTrigger?: Trigger | null;
  onDone?: () => void;
}

const labelCls = 'block text-xs font-medium text-muted-foreground mb-1';
const inputCls = cn(
  'w-full px-3 py-1.5 text-sm rounded-md border border-border bg-background text-foreground',
  'placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-ring',
);
const selectCls = cn(inputCls, 'appearance-none');

export function TriggerForm({ editingTrigger, onDone }: TriggerFormProps) {
  const queryClient = useQueryClient();
  const isEditing = !!editingTrigger;

  const [name, setName] = useState('');
  const [triggerType, setTriggerType] = useState<TriggerType>('cron');
  const [cronExpression, setCronExpression] = useState('');
  const [filePath, setFilePath] = useState('');
  const [filePatterns, setFilePatterns] = useState('');
  const [actionType, setActionType] = useState<ActionType>('notify');
  const [actionValue, setActionValue] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');

  // Populate form when editing
  useEffect(() => {
    if (editingTrigger) {
      setName(editingTrigger.name);
      setTriggerType(editingTrigger.trigger_type);
      setActionType(editingTrigger.action_type);

      const cfg = editingTrigger.config ?? {};
      if (editingTrigger.trigger_type === 'cron') {
        setCronExpression((cfg.expression as string) ?? '');
      } else if (editingTrigger.trigger_type === 'file_watch') {
        setFilePath((cfg.path as string) ?? '');
        setFilePatterns(((cfg.patterns as string[]) ?? []).join(', '));
      } else if (editingTrigger.trigger_type === 'webhook') {
        setWebhookUrl((cfg.url as string) ?? '');
      }

      const acfg = editingTrigger.action_config ?? {};
      setActionValue(
        (acfg.command as string) ??
          (acfg.message as string) ??
          (acfg.agent_name as string) ??
          (acfg.title as string) ??
          '',
      );
    } else {
      resetForm();
    }
  }, [editingTrigger]);

  function resetForm() {
    setName('');
    setTriggerType('cron');
    setCronExpression('');
    setFilePath('');
    setFilePatterns('');
    setActionType('notify');
    setActionValue('');
    setWebhookUrl('');
  }

  function buildConfig(): Record<string, unknown> {
    switch (triggerType) {
      case 'cron':
        return { expression: cronExpression };
      case 'webhook':
        return { url: webhookUrl };
      case 'file_watch':
        return {
          path: filePath,
          patterns: filePatterns
            .split(',')
            .map((p) => p.trim())
            .filter(Boolean),
        };
    }
  }

  function buildActionConfig(): Record<string, unknown> {
    switch (actionType) {
      case 'spawn_agent':
        return { agent_name: actionValue };
      case 'create_todo':
        return { title: actionValue };
      case 'notify':
        return { message: actionValue };
      case 'run_command':
        return { command: actionValue };
    }
  }

  const createMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiPost<Trigger>('/triggers', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
      resetForm();
      onDone?.();
    },
  });

  const updateMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiPatch<Trigger>(`/triggers/${editingTrigger!.id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
      resetForm();
      onDone?.();
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const body = {
      name,
      trigger_type: triggerType,
      config: buildConfig(),
      action_type: actionType,
      action_config: buildActionConfig(),
      enabled: editingTrigger?.enabled ?? true,
    };
    if (isEditing) {
      updateMut.mutate(body);
    } else {
      createMut.mutate(body);
    }
  }

  const isSaving = createMut.isPending || updateMut.isPending;

  const actionPlaceholders: Record<ActionType, string> = {
    spawn_agent: 'Agent name to spawn',
    create_todo: 'Todo title',
    notify: 'Notification message',
    run_command: 'Shell command to run',
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">
        {isEditing ? 'Edit Trigger' : 'New Trigger'}
      </h3>

      {/* Name */}
      <div>
        <label className={labelCls}>Name</label>
        <input
          className={inputCls}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Daily standup reminder"
          required
        />
      </div>

      {/* Trigger type */}
      <div>
        <label className={labelCls}>Trigger Type</label>
        <select
          className={selectCls}
          value={triggerType}
          onChange={(e) => setTriggerType(e.target.value as TriggerType)}
        >
          <option value="cron">Cron Schedule</option>
          <option value="webhook">Webhook</option>
          <option value="file_watch">File Watch</option>
        </select>
      </div>

      {/* Config fields based on type */}
      {triggerType === 'cron' && (
        <div>
          <label className={labelCls}>Cron Expression</label>
          <input
            className={inputCls}
            value={cronExpression}
            onChange={(e) => setCronExpression(e.target.value)}
            placeholder="*/5 * * * * (every 5 minutes)"
            required
          />
        </div>
      )}

      {triggerType === 'webhook' && (
        <div>
          <label className={labelCls}>Webhook URL</label>
          <input
            className={cn(inputCls, 'font-mono text-xs')}
            value={webhookUrl}
            readOnly
            placeholder="URL will be generated on save"
          />
          <p className="text-[10px] text-muted-foreground mt-1">
            The webhook URL is auto-generated by the server.
          </p>
        </div>
      )}

      {triggerType === 'file_watch' && (
        <>
          <div>
            <label className={labelCls}>Watch Path</label>
            <input
              className={inputCls}
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="/path/to/watch"
              required
            />
          </div>
          <div>
            <label className={labelCls}>File Patterns (comma-separated)</label>
            <input
              className={inputCls}
              value={filePatterns}
              onChange={(e) => setFilePatterns(e.target.value)}
              placeholder="*.md, *.txt"
            />
          </div>
        </>
      )}

      {/* Action type */}
      <div>
        <label className={labelCls}>Action</label>
        <select
          className={selectCls}
          value={actionType}
          onChange={(e) => setActionType(e.target.value as ActionType)}
        >
          <option value="spawn_agent">Spawn Agent</option>
          <option value="create_todo">Create Todo</option>
          <option value="notify">Send Notification</option>
          <option value="run_command">Run Command</option>
        </select>
      </div>

      {/* Action config */}
      <div>
        <label className={labelCls}>Action Config</label>
        <input
          className={inputCls}
          value={actionValue}
          onChange={(e) => setActionValue(e.target.value)}
          placeholder={actionPlaceholders[actionType]}
          required
        />
      </div>

      {/* Buttons */}
      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={isSaving || !name.trim()}
          className={cn(
            'px-4 py-1.5 text-sm font-medium rounded-md transition-colors',
            'bg-primary text-primary-foreground hover:bg-primary/90',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {isSaving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
        </button>
        {isEditing && (
          <button
            type="button"
            onClick={() => {
              resetForm();
              onDone?.();
            }}
            className="px-4 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
