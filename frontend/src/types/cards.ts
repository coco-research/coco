// ─── Card Type System ────────────────────────────────────────────────────────

export type CardType =
  | 'todo_list'
  | 'project_detail'
  | 'health_detail'
  | 'approval_batch'
  | 'metric_grid'
  | 'text_response'
  | 'navigate_hint';

// ─── Per-Type Data Shapes ────────────────────────────────────────────────────

export interface TodoItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  due_date: string | null;
  project_name: string | null;
}

export interface TodoListData {
  title: string;
  todos: TodoItem[];
}

export interface ProjectDetailData {
  id: string;
  name: string;
  email_count: number;
  jira_count: number;
  todo_open: number;
  todo_done: number;
  recent_activity: Array<{ summary: string; timestamp: string }>;
}

export interface HealthSourceData {
  source: string;
  status: string;
  stale_hours: number | null;
  last_sync: string | null;
  items_synced: number;
}

export interface HealthDetailData {
  sources: HealthSourceData[];
  overall_pct: number;
}

export interface ApprovalItem {
  id: string;
  title: string;
  project_name: string | null;
  draft_type: string;
  preview: string;
}

export interface ApprovalBatchData {
  drafts: ApprovalItem[];
}

export interface MetricItem {
  label: string;
  value: number;
  previous?: number;
  color?: string;
}

export interface MetricGridData {
  metrics: MetricItem[];
}

export interface TextResponseData {
  text: string;
}

export interface NavigateHintData {
  destination: string;
  url: string;
}

// ─── Card Actions ────────────────────────────────────────────────────────────

export interface CardAction {
  label: string;
  action: string;
  endpoint?: string;
  method?: 'POST' | 'PATCH' | 'DELETE';
  payload?: Record<string, unknown>;
}

// ─── Card Data (discriminated union) ─────────────────────────────────────────

export interface CardData {
  id: string;
  type: CardType;
  data: TodoListData | ProjectDetailData | HealthDetailData
    | ApprovalBatchData | MetricGridData | TextResponseData
    | NavigateHintData;
  actions?: CardAction[];
}

// ─── Command Response ────────────────────────────────────────────────────────

export interface CommandResponse {
  reply: string;
  action: string | null;
  url: string | null;
  cards: CardData[];
}
