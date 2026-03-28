import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  RefreshCw,
  Inbox,
  BookOpen,
  Search,
  MessageCircle,
  ListTodo,
  Radio,
  Settings,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { apiPost } from '../../lib/api';

interface Command {
  cmd: string;
  label: string;
  icon: LucideIcon;
  to?: string;
  action?: string;
}

const commands: Command[] = [
  { cmd: 'process', label: 'Sync now', icon: RefreshCw, to: undefined, action: 'process' },
  { cmd: 'decide', label: 'Review queue', icon: Inbox, to: '/inbox' },
  { cmd: 'briefing', label: 'Catch up', icon: BookOpen, to: '/knowledge' },
  { cmd: 'search', label: 'Find items', icon: Search, to: '/knowledge' },
  { cmd: 'chat', label: 'Talk to CoCo', icon: MessageCircle, to: '/chat' },
  { cmd: 'todos', label: 'My tasks', icon: ListTodo, to: '/todos' },
  { cmd: 'agents', label: 'Team status', icon: Radio, to: '/agents' },
  { cmd: 'settings', label: 'Configure', icon: Settings, to: '/settings' },
];

export function QuickCommandBar() {
  const [processing, setProcessing] = useState(false);

  async function handleProcess() {
    if (processing) return;
    setProcessing(true);
    try {
      await apiPost('/home/process', {});
    } catch {
      // Endpoint may not exist yet
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-zinc-900/50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Zap className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-medium text-foreground">Quick Commands</h3>
      </div>

      <div className="space-y-0.5">
        {commands.map((command) => {
          const Icon = command.icon;
          const isProcess = command.action === 'process';

          const content = (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">&gt;</span>
                <Icon
                  className={cn(
                    'h-3.5 w-3.5 text-accent',
                    isProcess && processing && 'animate-spin',
                  )}
                />
                <span className="font-mono text-sm text-accent">{command.cmd}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {isProcess && processing ? 'Running...' : command.label}
              </span>
            </div>
          );

          const rowClass = cn(
            'block w-full rounded-md px-2 py-1.5 text-left transition-colors hover:bg-accent/10',
          );

          if (command.to) {
            return (
              <Link key={command.cmd} to={command.to} className={rowClass}>
                {content}
              </Link>
            );
          }

          return (
            <button
              key={command.cmd}
              type="button"
              className={rowClass}
              onClick={handleProcess}
              disabled={processing}
            >
              {content}
            </button>
          );
        })}
      </div>

      <div className="mt-3 border-t border-border pt-2 text-center">
        <span className="text-[10px] text-muted-foreground">
          <kbd className="rounded border border-border px-1 py-0.5 text-[10px]">Cmd+K</kbd>{' '}
          for command palette
        </span>
      </div>
    </div>
  );
}
