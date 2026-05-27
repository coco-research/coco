import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity } from 'lucide-react';
import { timeAgo } from '../lib/utils';
import { ErrorState } from '../components/shared/ErrorState';

interface ActivityEntry {
  id: number;
  created_at: string;
  action: string;
  item_type: string;
  item_id: string;
  decided_by: string | null;
  notes: string | null;
}

const ACTION_OPTIONS = [
  'all',
  'approve',
  'reject',
  'ingest',
  'create',
  'update',
  'delete',
  'send',
];

async function fetchActivity(action: string): Promise<ActivityEntry[]> {
  const params = new URLSearchParams({ limit: '50' });
  if (action !== 'all') params.set('action', action);
  const res = await fetch(`/api/activity?${params}`);
  if (!res.ok) throw new Error('Failed to fetch activity');
  return res.json();
}

export default function ActivityPage() {
  const [actionFilter, setActionFilter] = useState('all');

  const { data: entries = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ['activity', actionFilter],
    queryFn: () => fetchActivity(actionFilter),
    refetchInterval: 30_000,
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-foreground">Activity</h1>
        <select
          aria-label="Filter activity by action type"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
        >
          {ACTION_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt === 'all' ? 'All actions' : opt}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-10 bg-muted/50 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          error={error}
          title="Couldn't load activity"
          onRetry={() => void refetch()}
        />
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Activity size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No activity yet</p>
          <p className="text-xs mt-1">Actions will appear here as they happen.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card">
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Timestamp
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Action
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Item Type
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Item ID
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Decision By
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors"
                >
                  <td className="px-4 py-2.5 text-muted-foreground whitespace-nowrap">
                    {timeAgo(entry.created_at)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="inline-block rounded-full bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
                      {entry.action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-foreground">
                    {entry.item_type}
                  </td>
                  <td className="px-4 py-2.5 text-foreground font-mono text-xs">
                    {entry.item_id}
                  </td>
                  <td className="px-4 py-2.5 text-foreground">
                    {entry.decided_by || '-'}
                  </td>
                  <td className="px-4 py-2.5 text-muted-foreground max-w-xs truncate">
                    {entry.notes || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
