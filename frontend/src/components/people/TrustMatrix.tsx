import { useQuery } from '@tanstack/react-query';
import { Shield } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface CocoConfig {
  autonomy?: Record<string, Record<string, string>>;
  [key: string]: unknown;
}

const LEVEL_STYLES: Record<string, string> = {
  auto: 'bg-success/20 text-success',
  confirm: 'bg-warning/20 text-warning',
  blocked: 'bg-destructive/20 text-destructive',
};

const LEVEL_LABEL: Record<string, string> = {
  auto: 'Auto',
  confirm: 'Confirm',
  blocked: 'Blocked',
};

const PERMISSION_LEVELS = ['auto', 'confirm', 'blocked'] as const;

export function TrustMatrix() {
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => apiFetch<CocoConfig>('/config'),
  });

  const autonomy = config?.autonomy ?? {};
  const agents = Object.keys(autonomy);

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading trust matrix...</p>;
  }

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Shield size={40} className="mb-3 opacity-40" />
        <p className="text-sm">No autonomy settings configured yet.</p>
        <p className="text-xs mt-1">Configure agent permissions in config.json</p>
      </div>
    );
  }

  // Collect all unique action types across all agents
  const allActions = new Set<string>();
  for (const agentConfig of Object.values(autonomy)) {
    for (const action of Object.keys(agentConfig)) {
      allActions.add(action);
    }
  }
  const actions = Array.from(allActions).sort();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Trust Matrix
        </h2>
        <div className="flex items-center gap-3 text-xs">
          {PERMISSION_LEVELS.map((level) => (
            <div key={level} className="flex items-center gap-1.5">
              <span className={cn('h-2.5 w-2.5 rounded-sm', LEVEL_STYLES[level])} />
              <span className="text-muted-foreground">{LEVEL_LABEL[level]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-2 px-3 border-b border-border">
                Agent / Action
              </th>
              {actions.map((action) => (
                <th
                  key={action}
                  className="text-center text-xs font-medium text-muted-foreground uppercase tracking-wider py-2 px-3 border-b border-border"
                >
                  {action.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent} className="border-b border-border/50 hover:bg-accent/50/30">
                <td className="py-2.5 px-3 text-sm font-medium text-foreground">
                  {agent.replace(/_/g, ' ')}
                </td>
                {actions.map((action) => {
                  const level = autonomy[agent]?.[action] ?? '';
                  return (
                    <td key={action} className="py-2.5 px-3 text-center">
                      {level ? (
                        <span
                          className={cn(
                            'inline-block rounded px-2 py-0.5 text-[10px] font-semibold uppercase',
                            LEVEL_STYLES[level] ?? 'bg-border/30 text-muted-foreground',
                          )}
                        >
                          {LEVEL_LABEL[level] ?? level}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs">-</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        Read-only view. Edit autonomy settings in ~/.coco/config.json or via the Settings page.
      </p>
    </div>
  );
}
