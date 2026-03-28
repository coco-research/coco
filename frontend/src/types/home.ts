export interface Todo {
  id: string;
  title: string;
  project_id: string | null;
  owner: string | null;
  due_date: string | null;
  priority: string;
  status: string;
  source_type: string | null;
  jira_key: string | null;
  tags: string | null;
}

export interface HomeProject {
  id: string;
  name: string;
  item_count: number;
  todo_open: number;
  todo_done: number;
  todo_total: number;
  active: boolean;
  sources: { email: number; voice: number; jira: number; confluence: number };
}

export interface SourceHealth {
  source: string;
  status: string;
  last_sync: string | null;
  items_synced: number;
  stale_hours: number | null;
}

export interface AttentionCounts {
  unsorted_count: number;
  pending_drafts: number;
  overdue_todos: number;
  health_alerts: number;
}

export interface QueueSummary {
  total: number;
  urgent: number;
  drafts: number;
  classify: number;
}

export interface HomeData {
  greeting: string;
  date: string;
  since_last_session: { hours_ago: number | null; label: string | null } | null;
  attention: AttentionCounts;
  health: SourceHealth[];
  todos: {
    total_open: number;
    high_priority: Todo[];
    medium_priority: Todo[];
    overdue: Todo[];
  };
  projects: HomeProject[];
  queue: QueueSummary;
  costs: { today_usd: number; month_usd: number };
  session: { last_started: string | null; last_focus: string | null; last_launch_type: string | null };
}
